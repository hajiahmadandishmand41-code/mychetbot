from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from core.agent import Agent
from core.errors import ConfigurationError, ProviderError
from core.logger import get_logger

log = get_logger("telegram")


class TelegramAPIError(RuntimeError):
    """Sanitized Telegram API failure; deliberately never contains the request URL or token."""

    def __init__(self, method: str, status_code: int | None, error_code: int | None = None):
        self.method = method
        self.status_code = status_code
        self.error_code = error_code
        status = str(status_code) if status_code is not None else "network"
        code = f", api_code={error_code}" if error_code is not None else ""
        super().__init__(f"Telegram {method} failed (HTTP {status}{code})")


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
            raise TelegramAPIError(method, None)

        try:
            response = await self._get_client().post(f"{self.base_url}/{method}", json=payload)
        except httpx.TimeoutException:
            raise TelegramAPIError(method, None) from None
        except httpx.RequestError:
            # httpx exceptions include the full request URL, which contains the bot token.
            raise TelegramAPIError(method, None) from None

        try:
            data = response.json()
        except ValueError:
            raise TelegramAPIError(method, response.status_code) from None

        error_code = data.get("error_code") if isinstance(data, dict) else None
        if response.is_error or not isinstance(data, dict) or not data.get("ok"):
            raise TelegramAPIError(
                method,
                response.status_code,
                error_code if isinstance(error_code, int) else None,
            ) from None
        return data

    async def configure_webhook(self) -> None:
        if not self.enabled:
            log.info("Telegram integration disabled: required configuration is missing")
            return

        me = await self._call("getMe", {})
        username = me.get("result", {}).get("username", "unknown")
        log.info("Telegram bot authentication succeeded")

        webhook = self.webhook_url.rstrip("/") + "/telegram/webhook"
        payload: dict[str, Any] = {
            "url": webhook,
            "allowed_updates": ["message"],
            "drop_pending_updates": False,
        }
        if self.webhook_secret:
            payload["secret_token"] = self.webhook_secret
        await self._call("setWebhook", payload)
        log.info("Telegram webhook configured for bot @%s", username)

        # Bot profile and command metadata are intentionally not rewritten on
        # every process start. Repeated setMyName calls were being rate-limited
        # during frequent deploys and are not needed to receive messages.

    @staticmethod
    def _command_prompt(text: str) -> tuple[str, bool]:
        normalized = text.strip()
        if not normalized:
            return "", False
        parts = normalized.split(maxsplit=1)
        command = parts[0].split("@", 1)[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""

        if command == "/start":
            return "خودت را معرفی کن و امکانات اصلی هوشان را به فارسی/دری توضیح بده.", True
        if command == "/about":
            return "خودت را با نام هوشان معرفی کن و درباره سازنده پروژه، تیم اندیشه فردا و حوزه‌های کاری پروژه توضیح دقیق بده.", True
        if command == "/news":
            return "آخرین اخبار مهم امروز را از اینترنت جستجو کن و با ذکر زمان و منابع، خلاصه دقیق بده.", False
        if command == "/search":
            return (
                f"از اینترنت درباره این موضوع جستجوی دقیق انجام بده و منابع را خلاصه کن: {argument}"
                if argument
                else "یک جستجوی اینترنتی عمومی برای اطلاعات روز انجام بده و چند موضوع مهم را با منابع معرفی کن.",
                False,
            )
        return text, False

    @staticmethod
    def _provider_failure(exc: ProviderError) -> str:
        messages = {
            "invalid_api_key": "کلید اتصال هوش مصنوعی معتبر نیست یا در تنظیمات سرور ثبت نشده است. کلید NaraRouter را در Render بررسی کنید.",
            "payment_required": "اعتبار یا سهمیه حساب NaraRouter کافی نیست. وارد پنل NaraRouter شوید و وضعیت اعتبار و طرح حساب را بررسی کنید.",
            "forbidden_model": "مدل انتخاب‌شده برای این حساب مجاز نیست. نام مدل‌های مجاز را از فهرست مدل‌های NaraRouter بررسی کنید.",
            "rate_limit": "سرویس هوش مصنوعی به محدودیت درخواست رسیده است. کمی بعد دوباره تلاش کنید.",
            "model_or_request_invalid": "مدل یا قالب درخواست توسط NaraRouter پذیرفته نشد. نام مدل و تنظیمات درخواست را بررسی کنید.",
            "timeout": "پاسخ سرویس هوش مصنوعی دیر رسید و زمان درخواست تمام شد. دوباره تلاش کنید.",
            "connection_failure": "اتصال به سرویس هوش مصنوعی برقرار نشد. وضعیت شبکه و NaraRouter را بررسی کنید.",
            "connection_error": "اتصال به سرویس هوش مصنوعی برقرار نشد. وضعیت شبکه و NaraRouter را بررسی کنید.",
            "http_5xx": "سرویس هوش مصنوعی موقتاً خطای داخلی برگرداند. کمی بعد دوباره تلاش کنید.",
            "invalid_response": "سرویس هوش مصنوعی پاسخ معتبری برنگرداند. تنظیمات Provider را بررسی کنید.",
        }
        return messages.get(exc.code, "سرویس هوش مصنوعی درخواست را نپذیرفت؛ وضعیت اعتبار، مدل و اتصال Provider را بررسی کنید.")

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
        async with self._lock(session):
            # A typing indicator is optional. A 403 here must never prevent the
            # assistant from generating the actual answer.
            try:
                await self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
            except TelegramAPIError as exc:
                log.info("Telegram typing indicator unavailable: method=%s status=%s", exc.method, exc.status_code)

            try:
                answer = await self._agent(session).ask(prompt)
            except ProviderError as exc:
                log.error("Telegram provider failure: code=%s provider=%s", exc.code, exc.provider)
                answer = self._provider_failure(exc)
            except ConfigurationError:
                log.error("Telegram AI configuration is incomplete")
                answer = "اتصال هوش مصنوعی در محیط اجرا تنظیم نشده است. کلید و تنظیمات Provider را بررسی کنید."
            except Exception:
                log.exception("Telegram message processing failed")
                answer = "در پردازش درخواست خطایی رخ داد. لطفاً کمی بعد دوباره تلاش کنید."

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
            try:
                await self._send(chat_id, answer[i:i + 4096] or "متأسفم، پاسخی دریافت نشد.", **extra)
            except TelegramAPIError as exc:
                # A 403 can mean the user blocked the bot or the bot lacks
                # permission in the target chat. Never log the token-bearing URL.
                log.warning(
                    "Telegram reply delivery failed: method=%s status=%s api_code=%s",
                    exc.method,
                    exc.status_code,
                    exc.error_code,
                )
                return


telegram_client = TelegramClient()
