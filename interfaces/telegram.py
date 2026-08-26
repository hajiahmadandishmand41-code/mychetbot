from __future__ import annotations

import asyncio
from typing import Any

import httpx

from core.agent import Agent
from core.config import config
from core.logger import get_logger

log = get_logger("telegram")


class TelegramClient:
    def __init__(self) -> None:
        self.token = config.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self.webhook_url = config.telegram_webhook_url
        self.webhook_secret = config.telegram_webhook_secret
        self._agents: dict[str, Agent] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.webhook_url and self.webhook_secret)

    def _agent(self, session: str) -> Agent:
        agent = self._agents.get(session)
        if agent is None:
            agent = Agent(session, tool_profile=config.telegram_tool_profile)
            self._agents[session] = agent
        return agent

    def _lock(self, session: str) -> asyncio.Lock:
        return self._locks.setdefault(session, asyncio.Lock())

    async def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.base_url}/{method}", json=payload)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown error')}")
            return data

    async def configure_webhook(self) -> None:
        if not self.enabled:
            log.info("Telegram integration disabled: required environment variables are missing")
            return
        webhook = self.webhook_url.rstrip("/") + "/telegram/webhook"
        await self._call(
            "setWebhook",
            {
                "url": webhook,
                "secret_token": self.webhook_secret,
                "allowed_updates": ["message"],
                "drop_pending_updates": False,
            },
        )
        log.info("Telegram webhook configured")

    async def handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not isinstance(message, dict):
            return
        chat = message.get("chat")
        sender = message.get("from") or {}
        text = message.get("text")
        if not isinstance(chat, dict) or not isinstance(text, str) or not text.strip():
            return
        chat_id = chat.get("id")
        if chat_id is None:
            return
        if config.telegram_require_allowlist and str(sender.get("id")) not in config.telegram_allowlist:
            log.warning("Rejected Telegram user not in allowlist: %s", sender.get("id"))
            return

        session = f"telegram:{chat_id}"
        async with self._lock(session):
            try:
                answer = await self._agent(session).ask(text.strip())
            except Exception:
                log.exception("Telegram message processing failed")
                answer = "متأسفم، در پردازش درخواست خطایی رخ داد."
        await self._call("sendMessage", {"chat_id": chat_id, "text": answer[:4096]})


telegram_client = TelegramClient()
