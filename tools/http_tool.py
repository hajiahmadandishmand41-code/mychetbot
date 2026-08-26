from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "host.docker.internal"}
MAX_RESPONSE_BYTES = 1_000_000


def _validate_public_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False, "[error] فقط http/https"
    if parsed.username or parsed.password:
        return False, "[blocked] userinfo در URL مجاز نیست"
    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname or hostname in BLOCKED_HOSTS:
        return False, "[blocked] مقصد محلی/metadata مجاز نیست"
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError:
        return False, "[error] نام میزبان resolve نشد"

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False, "[blocked] مقصد به شبکه داخلی یا آدرس ویژه اشاره می‌کند"
    return True, "ok"


def http_get(url: str, max_chars: int = 4000) -> str:
    ok, reason = _validate_public_url(url)
    if not ok:
        return reason
    safe_chars = max(1, min(int(max_chars), 100_000))
    timeout = httpx.Timeout(connect=10, read=20, write=10, pool=10)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            with client.stream("GET", url, headers={"User-Agent": "MyChatBot/1.0"}) as response:
                if 300 <= response.status_code < 400:
                    return "[blocked] redirect خودکار برای جلوگیری از SSRF غیرفعال است"
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) >= MAX_RESPONSE_BYTES:
                        break
                text = bytes(body[:MAX_RESPONSE_BYTES]).decode(response.encoding or "utf-8", errors="replace")
                return f"HTTP {response.status_code}\n{text[:safe_chars]}"
    except httpx.TimeoutException:
        return "[timeout] درخواست بیش از حد طول کشید"
    except httpx.HTTPStatusError as exc:
        return f"[http-error] HTTP {exc.response.status_code}"
    except httpx.RequestError:
        return "[connection-error] اتصال برقرار نشد"
