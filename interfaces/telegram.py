from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from core.agent import Agent
from core.logger import get_logger

log = get_logger("telegram")


class TelegramClient:
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", os.getenv("RENDER_EXTERNAL_URL", "")).strip()
        self.webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
        self.require_allowlist = os.getenv("TELEGRAM_REQUIRE_ALLOWLIST", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.allowlist = {x.strip() for x in os.getenv("TELEGRAM_ALLOWLIST", "").split(",") if x.strip()}
        self._agents: dict[str, Agent] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._client: httpx.AsyncClient | None = None
        self._client_loop: object | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.webhook_url)

    def _agent(self, session: str) -> Agent:
        agent = self._agents.get(session)
        if agent is None:
            agent = Agent(session)
            self._agents[session] = agent
        return agent

    def _lock(self, session: str) -> asyncio.Lock:
        return self._locks.setdefault(session, asyncio.Lock())

    def _get_client(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        if self._client is None or self._client.is_closed or self._client_loop is not loop:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=5.0),
                limits=httpx.Limits(max_connections=40, max_keepalive_connections=20, keepalive_expiry=30.0),
            )
            self._client_loop = loop
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._client_loop = None
        for agent in self._agents.values():
            try:
                await agent.router._provider.aclose()
            except Exception:
                log.debug("agent provider close failed", exc_info=True)

    async def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        response = await self._get_client().post(f"{self.base_url}/{method}", json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown error')}")
        return data

    async def configure_webhook(self) -> None:
        if not self.enabled:
            log.info("Telegram integration disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_WEBHOOK_URL is missing")
            return
        me = await self._call("getMe", {})
        log.info("Telegram bot connected: %s", me.get("result", {}).get("username", "unknown"))
        webhook = self.webhook_url.rstrip("/") + "/telegram/webhook"
        payload: dict[str, Any] = {
            "url": webhook,
            "allowed_updates": ["message"],
            "drop_pending_updates": False,
        }
        if self.webhook_secret:
            payload["secret_token"] = self.webhook_secret
        await self._call("setWebhook", payload)
        await self._call(
            "setMyName",
            {"name": "هوشان"},
        )
        await self._call(
            "setMyShortDescription",
            {"short_description": "هوشان؛ دستیار هوشمند، جستجوگر وب و یار برنامه‌نویسی"},
        )
        await self._call(
            "setMyDescription",
            {
                "description": "هوشان یک دستیار هوشمند گفت‌وگویی و جستجوگر اطلاعات است؛ برای تحقیق وب، اخبار، اطلاعات روز، برنامه‌نویسی و موضوعات فنی و آموزشی طراحی شده است. سازنده پروژه: حاجی احمد صالحی. تیم پروژه: اندیشه فردا."
            },
        )
        await self._call(
            "setMyCommands",
            {
                "commands": [
                    {"command": "start", "description": "شروع و معرفی هوشان"},
                    {"command": "news", "description": "جستجوی آخرین اخبار"},
                    {"command": "search", "description": "جستجوی اینترنتی"},
                    {"command": "wifi", "description": "اطلاعات Wi-Fi"},
                    {"command": "about", "description": "درباره هوشان"},
                ]
            },
        )

    @staticmethod
    def _command_prompt(text: str) -> tuple[str, bool]:
        normalized = text.strip()
        if normalized == "/start":
            return "خودت را معرفی کن و امکانات اصلی هوشان را به فارسی/دری توضیح بده.", True
        if normalized == "/about":
            return "خودت را با نام هوشان معرفی کن و درباره سازنده پروژه، تیم اندیشه فردا و حوزه‌های کاری پروژه توضیح دقیق بده.", True
        if normalized == "/news":
            return "آخرین اخبار مهم امروز را از اینترنت جستجو کن و با ذکر زمان و منابع، خلاصه دقیق بده.", False
        if normalized.startswith("/search"):
            query = normalized[len("/search"):].strip()
            return (f"از اینترنت درباره این موضوع جستجوی دقیق انجام بده و منابع را خلاصه کن: {query}", False) if query else ("یک جستجوی اینترنتی عمومی برای اطلاعات روز انجام بده و چند موضوع مهم را با منابع معرفی کن.", False)
        if normalized == "/wifi":
            return "وضعیت و اطلاعات اتصال Wi-Fi فعلی را بررسی کن.", False
        return text, False

    async def _send(self, chat_id: int, text: str, **extra: Any) -> None:
        payload = {"chat_id": chat_id, "text": text, **extra}
        await self._call("sendMessage", payload)

    async def _send_start_keyboard(self, chat_id: int) -> None:
        keyboard = {
            "keyboard": [
                [{"text": "/start"}, {"text": "/news"}],
                [{"text": "/search"}, {"text": "/wifi"}],
                [{"text": "/about"}],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
            "input_field_placeholder": "پیام یا سؤال خود را بنویسید…",
        }
        await self._send(chat_id, "از منوی زیر استفاده کنید یا سؤال خود را مستقیم بنویسید:", reply_markup=keyboard)

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
        if self.require_allowlist and str(sender.get("id")) not in self.allowlist:
            log.warning("Rejected Telegram user not in allowlist")
            return

        session = f"telegram:{chat_id}"
        prompt, show_keyboard = self._command_prompt(text)
        async with self._lock(session):
            try:
                await self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
                answer = await self._agent(session).ask(prompt)
            except Exception:
                log.exception("Telegram message processing failed")
                answer = "متأسفم، در پردازش درخواست خطایی رخ داد. لطفاً دوباره تلاش کنید."
        for i in range(0, len(answer) or 1, 4096):
            extra: dict[str, Any] = {}
            if show_keyboard and i == 0:
                extra["reply_markup"] = {
                    "keyboard": [
                        [{"text": "/start"}, {"text": "/news"}],
                        [{"text": "/search"}, {"text": "/wifi"}],
                        [{"text": "/about"}],
                    ],
                    "resize_keyboard": True,
                    "is_persistent": True,
                }
            await self._send(chat_id, answer[i:i + 4096] or "متأسفم، پاسخی دریافت نشد.", **extra)


telegram_client = TelegramClient()
