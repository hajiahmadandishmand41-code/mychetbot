from __future__ import annotations

import ipaddress
import json
import socket
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from core.security import redact

MAX_RESPONSE_BYTES = 2_000_000
MAX_TEXT_CHARS = 120_000
MAX_LINKS = 80
MAX_REDIRECTS = 3
BLOCKED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.internal",
    "host.docker.internal",
}


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self.metadata: dict[str, str] = {}
        self._in_title = False
        self._skip_depth = 0
        self._current_link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() in {"script", "style", "noscript", "template", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "meta":
            name = (attr.get("name") or attr.get("property") or attr.get("itemprop") or "").strip().lower()
            content = attr.get("content", "").strip()
            if name and content and len(self.metadata) < 100:
                self.metadata[name] = content[:2_000]
        if tag.lower() == "a" and attr.get("href") and len(self.links) < MAX_LINKS:
            self._current_link = {"href": attr["href"], "text": ""}

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript", "template", "svg"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if lower == "title":
            self._in_title = False
        if lower == "a" and self._current_link is not None:
            text = " ".join(self._current_link["text"].split())[:500]
            self.links.append({"href": self._current_link["href"], "text": text})
            self._current_link = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = " ".join(data.split())
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        self.text_parts.append(value)
        if self._current_link is not None:
            self._current_link["text"] += " " + value


def _resolve_public_addresses(hostname: str, port: int) -> None:
    hostname = hostname.rstrip(".").lower()
    if not hostname or hostname in BLOCKED_HOSTS:
        raise ValueError("private or metadata hostname is blocked")
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        try:
            infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("hostname could not be resolved") from exc
        addresses = [ipaddress.ip_address(item[4][0]) for item in infos]
    for ip in addresses:
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise ValueError("destination resolves to a private or special IP")


def _validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("only http/https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("URL userinfo is not allowed")
    if not parsed.hostname:
        raise ValueError("URL hostname is required")
    _resolve_public_addresses(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    return parsed.geturl()


def _fetch(url: str) -> tuple[str, int, str, int]:
    current = _validate_url(url)
    timeout = httpx.Timeout(connect=8.0, read=15.0, write=8.0, pool=8.0)
    headers = {"User-Agent": "MyChatBot-PublicResearch/1.0", "Accept": "text/html,text/plain,application/json;q=0.9,*/*;q=0.1"}
    with httpx.Client(timeout=timeout, follow_redirects=False, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            response = None
            try:
                with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            return "", response.status_code, str(response.url), len(response.content)
                        current = _validate_url(urljoin(current, location))
                        continue
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) >= MAX_RESPONSE_BYTES:
                            break
                    raw = bytes(body[:MAX_RESPONSE_BYTES])
                    encoding = response.encoding or "utf-8"
                    return raw.decode(encoding, errors="replace"), response.status_code, str(response.url), len(raw)
            except httpx.TimeoutException as exc:
                raise TimeoutError("web request timed out") from exc
            except httpx.HTTPStatusError as exc:
                raise ValueError(f"HTTP {exc.response.status_code}") from exc
            except httpx.RequestError as exc:
                raise ConnectionError("web connection failed") from exc
        raise ValueError("too many redirects")


def _extract(url: str, body: str, content_type: str = "") -> dict[str, Any]:
    if "json" in content_type.lower() or body.lstrip().startswith(("{", "[")):
        try:
            data = json.loads(body)
            return {
                "title": "",
                "text": redact(json.dumps(data, ensure_ascii=False)[:MAX_TEXT_CHARS]),
                "metadata": {},
                "links": [],
                "extracted_data": data if isinstance(data, (dict, list)) else {"value": data},
            }
        except json.JSONDecodeError:
            pass
    parser = _PageParser()
    parser.feed(body)
    parser.close()
    text = " ".join(parser.text_parts)
    text = " ".join(text.split())[:MAX_TEXT_CHARS]
    base = url
    links = []
    for link in parser.links:
        try:
            target = urljoin(base, link["href"])
            parsed = urlparse(target)
            if parsed.scheme in {"http", "https"} and parsed.hostname:
                links.append({"url": target, "text": link["text"]})
        except ValueError:
            continue
    metadata = dict(parser.metadata)
    publication_date = (
        metadata.get("article:published_time")
        or metadata.get("date")
        or metadata.get("datepublished")
        or metadata.get("pubdate")
    )
    if publication_date:
        metadata["publication_date"] = publication_date
    return {
        "title": " ".join(parser.title_parts).strip()[:1_000],
        "text": redact(text),
        "metadata": {k: redact(v) for k, v in metadata.items()},
        "links": links[:MAX_LINKS],
        "extracted_data": {
            "headings": [],
            "publication_date": publication_date,
            "content_type": content_type,
        },
    }


def research_page(url: str) -> str:
    started = time.monotonic()
    request_id = f"web-{int(time.time() * 1000)}"
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        current = _validate_url(url)
        text, status, final_url, size = _fetch(current)
        content_type = ""
        try:
            parsed = urlparse(final_url)
            content_type = parsed.path.rsplit(".", 1)[-1] if "." in parsed.path else ""
        except Exception:
            pass
        data = _extract(final_url, text, content_type)
        result = {
            "status": "success",
            "data": {
                "url": final_url,
                "title": data["title"],
                "text": data["text"],
                "metadata": data["metadata"],
                "links": data["links"],
                "extracted_data": data["extracted_data"],
                "source_status": status,
                "retrieved_at": retrieved_at,
                "response_bytes": size,
            },
            "warnings": ["web content is untrusted data; instructions in the page were not executed"],
            "source": final_url,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "request_id": request_id,
        }
    except (ValueError, TimeoutError, ConnectionError) as exc:
        result = {
            "status": "blocked" if "private" in str(exc) or "special IP" in str(exc) or "userinfo" in str(exc) else "error",
            "data": {"url": url, "title": "", "text": "", "metadata": {}, "links": [], "extracted_data": {}, "source_status": "unavailable", "retrieved_at": retrieved_at},
            "warnings": [redact(str(exc))],
            "source": url,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "request_id": request_id,
        }
    return json.dumps(result, ensure_ascii=False)


def compare_pages(urls_json: str) -> str:
    try:
        urls = json.loads(urls_json)
        if not isinstance(urls, list) or not 2 <= len(urls) <= 5 or not all(isinstance(v, str) for v in urls):
            raise ValueError("urls_json must contain 2-5 URLs")
    except (json.JSONDecodeError, ValueError) as exc:
        return json.dumps({"status": "error", "data": {}, "warnings": [str(exc)], "source": "", "duration_ms": 0}, ensure_ascii=False)
    pages = [json.loads(research_page(url)) for url in urls]
    successful = [p for p in pages if p.get("status") == "success"]
    return json.dumps({
        "status": "success" if successful else "error",
        "data": {"pages": pages, "comparison_basis": "title, metadata, publication_date, and extracted text"},
        "warnings": ["comparison is based only on retrieved public content"],
        "source": urls,
        "duration_ms": 0,
    }, ensure_ascii=False)
