from __future__ import annotations

import json
import re

from core.config import config
from core.errors import ConfigurationError, ProviderError
from providers.nara_provider import NaraProvider


class Router:
    """Single conversational router with a local fast path for tool intent planning."""

    def __init__(self):
        self.provider = "nara"
        self.model = config.default_model
        self._provider = NaraProvider()

    @staticmethod
    def _local_tool_plan(messages: list[dict]) -> dict | None:
        """Avoid spending a provider request just to classify obvious tool intents."""
        if not messages or "Intent/Tool Planner" not in str(messages[0].get("content", "")):
            return None
        text = str(messages[-1].get("content", "")).strip()
        low = text.lower()
        if not text:
            return {"tool": None, "args": {}}

        def has(*terms: str) -> bool:
            return any(term in text or term in low for term in terms)

        if has("آخرین اخبار", "اخبار امروز", "خبرهای امروز", "قیمت امروز", "اطلاعات امروز", "latest news", "current news"):
            return {"tool": "web_search", "args": {"query": text}}
        if has("جستجو کن", "از اینترنت", "در اینترنت", "از وب", "تحقیق کن", "web search", "search the web"):
            return {"tool": "web_search", "args": {"query": text}}
        if "http://" in low or "https://" in low:
            urls = re.findall(r"https?://[^\s]+", text)
            if len(urls) >= 2 and has("مقایسه", "compare"):
                return {"tool": "web_compare", "args": {"urls_json": json.dumps(urls[:5], ensure_ascii=False)}}
            if urls and has("بررسی", "خلاصه", "تحلیل", "صفحه", "آدرس", "url", "تحقیق"):
                return {"tool": "web_research", "args": {"url": urls[0]}}

        if has("وضعیت وای فای", "وضعیت wi-fi", "wifi status", "اطلاعات وای فای"):
            return {"tool": "wifi_info", "args": {}}
        if has("شبکه های اطراف", "شبکه‌های اطراف", "wifi scan", "وای‌فای‌های اطراف"):
            return {"tool": "wifi_scan", "args": {}}
        if has("تشخیص اتصال", "اتصال اینترنت", "dns", "wifi diagnostics"):
            return {"tool": "wifi_diagnostics", "args": {}}
        if has("گزارش امنیتی وای فای", "wifi security"):
            return {"tool": "wifi_security_report", "args": {}}
        if has("باتری", "battery"):
            return {"tool": "battery", "args": {}}
        if has("آی پی", "ip address", "آدرس ip"):
            return {"tool": "local_ip", "args": {}}
        if has("وضعیت سرور", "وضعیت سرویس", "server diagnostics", "runtime", "diagnostics"):
            return {"tool": "server_diagnostics", "args": {"operation": "diagnostics"}}
        return {"tool": None, "args": {}}

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

        local_plan = self._local_tool_plan(messages)
        if local_plan is not None:
            return {"content": json.dumps(local_plan, ensure_ascii=False)}

        try:
            text = await self._provider.chat(messages, model=kw.pop("model", self.model), **kw)
            return {"content": text}
        except ProviderError as exc:
            raise ProviderError(exc.provider, exc.code, self._provider_user_message(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderError("nara", "unexpected_error", "chat provider request failed") from exc

    async def aclose(self) -> None:
        await self._provider.aclose()
