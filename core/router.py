from __future__ import annotations

from core.config import config
from core.errors import ConfigurationError, ProviderError
from providers.nara_provider import NaraProvider


class Router:
    """Single conversational router using the configured AI Provider for intent planning and responses."""

    def __init__(self):
        self.provider = "nara"
        self.model = config.default_model
        self._provider = NaraProvider()

    @staticmethod
    def _local_tool_plan(messages: list[dict]) -> dict | None:
        """Legacy compatibility hook; automatic tool decisions must go through the AI Provider."""
        return None

    @staticmethod
    def _provider_user_message(error: ProviderError) -> str:
        messages = {
            "invalid_api_key": "کلید اتصال هوش مصنوعی معتبر نیست یا در محیط اجرای Telegram تنظیم نشده است.",
            "forbidden_model": "Provider این مدل را برای حساب فعلی مجاز نمی‌داند؛ مدل جایگزین در حال بررسی است.",
            "rate_limit": "سقف درخواست Provider موقتاً پر شده است؛ لطفاً چند لحظه بعد دوباره تلاش کنید.",
            "model_or_request_invalid": "Provider مدل یا قالب درخواست را نپذیرفت؛ تنظیمات مدل/درخواست باید بررسی شود.",
            "timeout": "اتصال به Provider بیش از زمان مجاز طول کشید.",
            "connection_failure": "اتصال شبکه به Provider برقرار نشد.",
            "http_5xx": "خود Provider موقتاً خطای سرور برگرداند.",
            "invalid_response": "Provider پاسخ نامعتبر برگرداند.",
        }
        return f"اتصال هوش مصنوعی هوشان با مشکل روبه‌رو شد: {messages.get(error.code, 'خطای ناشناخته در Provider')}"

    async def complete(self, messages: list[dict], **kw) -> dict:
        if not config.nara_key:
            raise ConfigurationError("NARA_API_KEY is not configured")

        # Never short-circuit tool planning locally. The configured AI Provider
        # is the sole intelligence/control plane for selecting capabilities.
        try:
            text = await self._provider.chat(messages, model=kw.pop("model", self.model), **kw)
            return {"content": text}
        except ProviderError as exc:
            raise ProviderError(exc.provider, exc.code, self._provider_user_message(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderError("nara", "unexpected_error", "chat provider request failed") from exc

    async def aclose(self) -> None:
        await self._provider.aclose()
