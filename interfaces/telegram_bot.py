from __future__ import annotations

import asyncio
import os
from collections import defaultdict

import httpx

from core.config import config
from core.agent import Agent
from core.logger import get_logger

log = get_logger("telegram")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
MAX_INPUT = 4000
MAX_OUTPUT = 4096
MAX_AGENTS = 256
RETRY_DELAYS = (1, 2, 4)


def _allowed_chat_ids() -> set[int]:
    raw = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
    result: set[int] = set()
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            result.add(int(value))
        except ValueError:
            log.warning("ignoring invalid TELEGRAM_ALLOWED_CHAT_IDS entry")
    return result


async def _request(client: httpx.AsyncClient, method: str, **kwargs) -> dict:
    endpoint = kwargs.pop("endpoint")
    last_error: Exception | None = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            response = await client.request(method, f"{API}/{endpoint}", **kwargs)
            if response.status_code == 429 or 500 <= response.status_code < 600:
                raise httpx.HTTPStatusError("temporary telegram failure", request=response.request, response=response)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok", False):
                raise RuntimeError(f"Telegram API error: {payload.get('description', 'unknown error')}")
            return payload
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt >= len(RETRY_DELAYS):
                break
            delay = RETRY_DELAYS[attempt]
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
                try:
                    delay = max(delay, int(exc.response.headers.get("Retry-After", delay)))
                except (TypeError, ValueError):
                    pass
            await asyncio.sleep(delay)
    raise RuntimeError("Telegram request failed after retries") from last_error


def _chunks(text: str) -> list[str]:
    text = text or "(پاسخی دریافت نشد)"
    return [text[i : i + MAX_OUTPUT] for i in range(0, len(text), MAX_OUTPUT)] or ["(پاسخی دریافت نشد)"]


def _get_agent(agents: dict[int, Agent], chat_id: int) -> Agent:
    agent = agents.get(chat_id)
    if agent is not None:
        return agent
    if len(agents) >= MAX_AGENTS:
        oldest_chat_id = next(iter(agents))
        evicted = agents.pop(oldest_chat_id)
        evicted.memory.close()
    agent = Agent(session=f"tg:{chat_id}", tool_profile=config.tool_profile)
    agents[chat_id] = agent
    return agent


async def main() -> None:
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN تنظیم نشده است")

    allowed = _allowed_chat_ids()
    if config.telegram_require_allowlist and not allowed:
        raise SystemExit("TELEGRAM_ALLOWED_CHAT_IDS must be configured in production")

    agents: dict[int, Agent] = {}
    locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
    offset = 0
    timeout = httpx.Timeout(connect=10, read=65, write=15, pool=10)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        log.info("Telegram bot started")
        try:
            while True:
                try:
                    data = await _request(
                        client,
                        "GET",
                        endpoint="getUpdates",
                        params={"offset": offset, "timeout": 50, "allowed_updates": ["message"]},
                    )
                    for upd in data.get("result", []):
                        update_id = int(upd["update_id"])
                        msg = upd.get("message") or {}
                        text = str(msg.get("text") or "").strip()
                        chat = (msg.get("chat") or {}).get("id")
                        if not text or chat is None:
                            offset = max(offset, update_id + 1)
                            continue
                        chat_id = int(chat)

                        if allowed and chat_id not in allowed:
                            offset = max(offset, update_id + 1)
                            continue

                        if len(text) > MAX_INPUT:
                            await _request(
                                client,
                                "POST",
                                endpoint="sendMessage",
                                json={"chat_id": chat_id, "text": "پیام بیش از حد طولانی است. حداکثر ۴۰۰۰ نویسه بفرستید."},
                            )
                            offset = max(offset, update_id + 1)
                            continue

                        agent = _get_agent(agents, chat_id)
                        async with locks[chat_id]:
                            try:
                                reply = await agent.ask(text)
                            except Exception:  # noqa: BLE001
                                log.exception("message processing failed")
                                reply = "در پردازش درخواست مشکلی رخ داد. دوباره تلاش کنید."

                        for chunk in _chunks(reply):
                            await _request(
                                client,
                                "POST",
                                endpoint="sendMessage",
                                json={"chat_id": chat_id, "text": chunk},
                            )
                        offset = max(offset, update_id + 1)
                except asyncio.CancelledError:
                    raise
                except Exception:  # noqa: BLE001
                    log.exception("Telegram polling loop failed; retrying without advancing offset")
                    await asyncio.sleep(2)
        finally:
            for agent in agents.values():
                agent.memory.close()
            log.info("Telegram bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Telegram bot interrupted")
