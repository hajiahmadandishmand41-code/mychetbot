from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import httpx

from core.agent import Agent
from core.errors import ConfigurationError, ProviderError
from core.logger import get_logger
from tools.registry import run_tool

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
        await self._call("setMyName", {"name": "هوشان"})
        await self._call("setMyShortDescription", {"short_description": "هوشان؛ دستیار هوشمند، جستجوگر وب و یار برنامه‌نویسی"})
        await self._call(
            "setMyDescription",
            {"description": "هوشان یک دستیار هوشمند گفت‌وگویی و جستجوگر اطلاعات است؛ برای تحقیق وب، اخبار، اطلاعات روز، برنامه‌نویسی و موضوعات فنی و آموزشی طراحی شده است. سازنده پروژه: حاجی احمد صالحی. تیم پروژه: اندیشه فردا."},
        )
        await self._call(
            "setMyCommands",
            {
                "commands": [
                    {"command": "start", "description": "شروع و معرفی هوشان"},
                    {"command": "news", "description": "جستجوی آخرین اخبار"},
                    {"command": "search", "description": "جستجوی اینترنتی"},
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
        return text, False

    @staticmethod
    def _web_request(text: str) -> tuple[bool, bool, str]:
        normalized = text.strip()
        lowered = normalized.lower()
        if normalized == "/news":
            return True, True, "آخرین اخبار مهم امروز"
        if lowered.startswith("/search"):
            query = normalized[len("/search"):].strip()
            return True, False, query or "آخرین اخبار مهم امروز"
        markers = (
            "آخرین", "جدیدترین", "اخبار", "خبر", "قیمت امروز", "اطلاعات روز", "اطلاعات فعلی",
            "تحقیق", "جستجو", "جست‌وجو", "از اینترنت", "از وب", "روی وب", "آنلاین", "منبع", "منابع",
            "بررسی آنلاین", "http://", "https://", "www.",
        )
        return any(marker in lowered for marker in markers), False, normalized

    @staticmethod
    def _format_web_result(raw: str, query: str, news: bool) -> str:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return "جستجوی وب پاسخ نامعتبری برگرداند. لطفاً دوباره تلاش کنید."

        if payload.get("status") != "success":
            warnings = payload.get("warnings") or []
            warning = str(warnings[0]) if warnings else "سرویس جستجوی وب در دسترس نبود."
            return f"در حال حاضر جستجوی وب موفق نشد انجام شود.\nجزئیات: {warning[:500]}"

        data = payload.get("data") or {}
        rows: list[tuple[str, str, str]] = []
        for item in data.get("results") or []:
            if not isinstance(item, dict):
                continue
            search = item.get("search_result") or {}
            page = item.get("page") or {}
            if not isinstance(search, dict) or not isinstance(page, dict):
                continue
            title = str(page.get("title") or search.get("title") or "بدون عنوان").strip()
            url = str(page.get("url") or search.get("url") or "").strip()
            snippet = str(search.get("snippet") or page.get("text") or page.get("warning") or "").strip()
            rows.append((title[:240], snippet[:900], url[:1000]))

        for page in data.get("pages") or []:
            if not isinstance(page, dict):
                continue
            title = str(page.get("title") or "بدون عنوان").strip()
            url = str(page.get("url") or "").strip()
            snippet = str(page.get("text") or page.get("warning") or "").strip()
            rows.append((title[:240], snippet[:900], url[:1000]))

        deduped: list[tuple[str, str, str]] = []
        seen: set[str] = set()
        for row in rows:
            key = row[2] or row[0]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)

        if not deduped:
            return "از جستجوی وب نتیجه قابل استفاده‌ای دریافت نشد."

        header = "📰 اخبار و اطلاعات روز" if news else "🔎 نتیجه جستجوی وب"
        lines = [header, f"موضوع: {query}", ""]
        for index, (title, snippet, url) in enumerate(deduped[:8], 1):
            lines.append(f"{index}. {title}")
            if snippet:
                lines.append(snippet)
            if url:
                lines.append(f"منبع: {url}")
            lines.append("")
        lines.append("نتایج از جستجوی عمومی وب جمع‌آوری شده‌اند؛ محتوای منابع را با احتیاط بررسی کنید.")
        return "\n".join(lines).strip()

    async def _direct_web_search(self, session: str, query: str, news: bool) -> str:
        profile = os.getenv("TOOL_PROFILE", "local").strip() or "local"
        raw = await asyncio.to_thread(run_tool, "web_search", {"query": query[:500]}, profile, session)
        return self._format_web_result(raw, query, news)

    @staticmethod
    def _provider_failure(exc: ProviderError) -> str:
        messages = {
            "invalid_api_key": "اتصال سرویس هوش مصنوعی معتبر نیست. کلید دسترسی Provider را در محیط اجرا بررسی کنید.",
            "forbidden_model": "مدل انتخاب‌شده برای این اتصال مجاز نیست. مدل مجاز یا fallback را بررسی کنید.",
            "rate_limit": "سرویس هوش مصنوعی فعلاً به محدودیت درخواست یا سهمیه رسیده است. چند لحظه بعد دوباره تلاش کنید.",
            "model_or_request_invalid": "مدل یا درخواست ارسالی توسط سرویس هوش مصنوعی پذیرفته نشد. تنظیم مدل و Provider را بررسی کنید.",
            "timeout": "پاسخ سرویس هوش مصنوعی دیر رسید و زمان درخواست تمام شد. دوباره تلاش کنید.",
            "connection_error": "اتصال به سرویس هوش مصنوعی برقرار نشد. وضعیت اتصال Provider را بررسی کنید.",
            "http_5xx": "سرویس هوش مصنوعی خطای داخلی موقت برگرداند. دوباره تلاش کنید.",
            "invalid_response": "سرویس هوش مصنوعی پاسخ معتبری برنگرداند. تنظیمات Provider را بررسی کنید.",
        }
        return messages.get(exc.code, "سرویس هوش مصنوعی درخواست را نپذیرفت؛ وضعیت مدل و اتصال Provider را بررسی کنید.")

    async def _send(self, chat_id: int, text: str, **extra: Any) -> None:
        payload = {"chat_id": chat_id, "text": text, **extra}
        await self._call("sendMessage", payload)

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
        is_web, is_news, query = self._web_request(text)
        async with self._lock(session):
            try:
                await self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
                if is_web:
                    answer = await self._direct_web_search(session, query, is_news)
                else:
                    answer = await self._agent(session).ask(prompt)
            except ProviderError as exc:
                log.error("Telegram provider failure: code=%s provider=%s", exc.code, exc.provider, exc_info=True)
                answer = self._provider_failure(exc)
            except ConfigurationError:
                log.exception("Telegram configuration failure")
                answer = "اتصال هوش مصنوعی در محیط اجرا تنظیم نشده است. کلید و تنظیمات Provider را بررسی کنید."
            except Exception:
                log.exception("Telegram message processing failed")
                answer = "در پردازش درخواست خطایی رخ داد. جزئیات فنی در گزارش سرویس ثبت شد. لطفاً دوباره تلاش کنید."

        for i in range(0, len(answer) or 1, 4096):
            extra: dict[str, Any] = {}
            if show_keyboard and i == 0:
                extra["reply_markup"] = {
                    "keyboard": [
                        [{"text": "/start"}, {"text": "/news"}],
                        [{"text": "/search"}, {"text": "/about"}],
                    ],
                    "resize_keyboard": True,
                    "is_persistent": True,
                }
            await self._send(chat_id, answer[i:i + 4096] or "متأسفم، پاسخی دریافت نشد.", **extra)


telegram_client = TelegramClient()
