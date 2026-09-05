from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
from typing import Any

import httpx

from core.agent import Agent
from core.errors import ConfigurationError, ProviderError
from core.logger import get_logger

log = get_logger("whatsapp")


class WhatsAppClient:
    """Official WhatsApp Cloud API adapter with an isolated local mock mode for testing."""

    def __init__(self) -> None:
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v23.0").strip() or "v23.0"
        self.graph_base_url = os.getenv("WHATSAPP_GRAPH_BASE_URL", "https://graph.facebook.com").rstrip("/")
        self.require_signature = os.getenv("WHATSAPP_REQUIRE_SIGNATURE", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.mock_mode = os.getenv("WHATSAPP_MOCK_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
        self._client: httpx.AsyncClient | None = None
        self._client_loop: object | None = None
        self._agents: dict[str, Agent] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._seen_ids: set[str] = set()
        self._seen_order: list[str] = []
        self._seen_limit = 4096

    @property
    def enabled(self) -> bool:
        return self.mock_mode or bool(self.access_token and self.phone_number_id)

    @property
    def webhook_configured(self) -> bool:
        return self.mock_mode or bool(self.verify_token and self.app_secret)

    def _get_client(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        if self._client is None or self._client.is_closed or self._client_loop is not loop:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0),
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

    def verify_challenge(self, mode: str | None, token: str | None, challenge: str | None) -> str:
        if mode != "subscribe" or not challenge:
            raise ValueError("invalid webhook verification request")
        if self.mock_mode:
            expected = self.verify_token or "mychetbot-test"
            if not token or not hmac.compare_digest(token, expected):
                raise PermissionError("invalid verification token")
            return challenge
        if not self.verify_token or not token:
            raise ValueError("invalid webhook verification request")
        if not hmac.compare_digest(token, self.verify_token):
            raise PermissionError("invalid verification token")
        return challenge

    def verify_signature(self, body: bytes, signature: str | None) -> bool:
        if self.mock_mode and not self.app_secret:
            return True
        if not self.app_secret:
            return not self.require_signature
        if not signature or not signature.startswith("sha256="):
            return False
        provided = signature[7:]
        expected = hmac.new(self.app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided, expected)

    def _is_duplicate(self, message_id: str) -> bool:
        if not message_id:
            return False
        if message_id in self._seen_ids:
            return True
        self._seen_ids.add(message_id)
        self._seen_order.append(message_id)
        if len(self._seen_order) > self._seen_limit:
            stale = self._seen_order.pop(0)
            self._seen_ids.discard(stale)
        return False

    async def _send_text(self, to: str, text: str, reply_to: str | None = None) -> None:
        if self.mock_mode:
            log.info("WhatsApp MOCK reply to=%s reply_to=%s text=%s", to, reply_to, text[:4096])
            return
        if not self.enabled:
            raise RuntimeError("WhatsApp Cloud API is not configured")
        url = f"{self.graph_base_url}/{self.api_version}/{self.phone_number_id}/messages"
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text[:4096]},
        }
        if reply_to:
            payload["context"] = {"message_id": reply_to}
        response = await self._get_client().post(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )
        if response.status_code >= 400:
            log.error("WhatsApp send failed: status=%s body=%s", response.status_code, response.text[:1000])
        response.raise_for_status()

    def _agent(self, session: str) -> Agent:
        agent = self._agents.get(session)
        if agent is None:
            agent = Agent(session)
            self._agents[session] = agent
        return agent

    def _lock(self, session: str) -> asyncio.Lock:
        return self._locks.setdefault(session, asyncio.Lock())

    @staticmethod
    def _provider_failure(exc: ProviderError) -> str:
        messages = {
            "invalid_api_key": "اتصال سرویس هوش مصنوعی معتبر نیست. تنظیمات دسترسی را بررسی کنید.",
            "forbidden_model": "مدل انتخاب‌شده برای این اتصال مجاز نیست. تنظیمات مدل را بررسی کنید.",
            "rate_limit": "سرویس هوش مصنوعی فعلاً به محدودیت درخواست یا سهمیه رسیده است. دوباره تلاش کنید.",
            "model_or_request_invalid": "درخواست توسط سرویس هوش مصنوعی پذیرفته نشد. تنظیمات مدل و Provider را بررسی کنید.",
            "timeout": "پاسخ سرویس هوش مصنوعی دیر رسید. دوباره تلاش کنید.",
            "connection_error": "اتصال به سرویس هوش مصنوعی برقرار نشد. وضعیت اتصال را بررسی کنید.",
            "http_5xx": "سرویس هوش مصنوعی خطای موقت داخلی برگرداند. دوباره تلاش کنید.",
            "invalid_response": "سرویس هوش مصنوعی پاسخ معتبری برنگرداند.",
        }
        return messages.get(exc.code, "در پردازش درخواست خطایی از سرویس هوش مصنوعی دریافت شد. دوباره تلاش کنید.")

    async def process_test_message(self, sender: str, text: str, message_id: str = "test-message") -> str:
        """Run the same conversational pipeline without sending anything to Meta."""
        sender = sender.strip() or "test-user"
        text = text.strip()
        if not text:
            raise ValueError("text must not be blank")
        session = f"whatsapp:{sender}"
        if self._is_duplicate(message_id):
            return "پیام تکراری بود و دوباره پردازش نشد."
        async with self._lock(session):
            try:
                return await self._agent(session).ask(text)
            except ProviderError as exc:
                log.error("WhatsApp test provider failure: code=%s provider=%s", exc.code, exc.provider, exc_info=True)
                return self._provider_failure(exc)
            except ConfigurationError:
                log.exception("WhatsApp test configuration failure")
                return "اتصال هوش مصنوعی در محیط اجرا تنظیم نشده است. تنظیمات سرویس را بررسی کنید."

    async def handle_payload(self, payload: dict[str, Any]) -> None:
        if payload.get("object") != "whatsapp_business_account":
            return
        for entry in payload.get("entry", []):
            if not isinstance(entry, dict):
                continue
            for change in entry.get("changes", []):
                if not isinstance(change, dict) or change.get("field") != "messages":
                    continue
                value = change.get("value") or {}
                messages = value.get("messages") or []
                for message in messages:
                    if not isinstance(message, dict) or message.get("type") != "text":
                        continue
                    sender = str(message.get("from", "")).strip()
                    text_obj = message.get("text") or {}
                    text = text_obj.get("body") if isinstance(text_obj, dict) else None
                    message_id = str(message.get("id", "")).strip()
                    if not sender or not isinstance(text, str) or not text.strip():
                        continue
                    if self._is_duplicate(message_id):
                        log.info("Ignoring duplicate WhatsApp message: %s", message_id)
                        continue
                    session = f"whatsapp:{sender}"
                    async with self._lock(session):
                        try:
                            answer = await self._agent(session).ask(text.strip())
                        except ProviderError as exc:
                            log.error("WhatsApp provider failure: code=%s provider=%s", exc.code, exc.provider, exc_info=True)
                            answer = self._provider_failure(exc)
                        except ConfigurationError:
                            log.exception("WhatsApp configuration failure")
                            answer = "اتصال هوش مصنوعی در محیط اجرا تنظیم نشده است. تنظیمات سرویس را بررسی کنید."
                        except Exception:
                            log.exception("WhatsApp message processing failed")
                            answer = "در پردازش درخواست خطایی رخ داد. لطفاً دوباره تلاش کنید."
                    for start in range(0, len(answer) or 1, 4096):
                        await self._send_text(sender, answer[start:start + 4096] or "متأسفم، پاسخی دریافت نشد.", reply_to=message_id if start == 0 else None)


whatsapp_client = WhatsAppClient()
