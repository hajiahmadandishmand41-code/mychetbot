import pytest

from core.errors import ProviderError
from interfaces.telegram import TelegramClient


@pytest.mark.asyncio
async def test_telegram_search_uses_central_ai_agent(monkeypatch):
    client = TelegramClient()
    sent = []
    calls = []

    async def fake_call(method, payload):
        sent.append((method, payload))
        return {"ok": True}

    class FakeAgent:
        async def ask(self, prompt):
            calls.append(prompt)
            return "پاسخ نهایی توسط Agent مرکزی ساخته شد."

    monkeypatch.setattr(client, "_call", fake_call)
    monkeypatch.setattr(client, "_agent", lambda _session: FakeAgent())
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    client.token = "test-token"
    client.base_url = "https://api.telegram.org/bottest-token"

    await client.handle_update({"message": {"chat": {"id": 123}, "from": {"id": 123}, "text": "/search OpenAI"}})

    assert calls == ["از اینترنت درباره این موضوع جستجوی دقیق انجام بده و منابع را خلاصه کن: OpenAI"]
    messages = [payload["text"] for method, payload in sent if method == "sendMessage"]
    assert "پاسخ نهایی توسط Agent مرکزی ساخته شد." in messages


def test_telegram_provider_failure_is_not_hidden():
    exc = ProviderError("nara", "rate_limit", "quota reached")
    assert "محدودیت" in TelegramClient._provider_failure(exc)
    assert "در پردازش درخواست خطایی رخ داد" not in TelegramClient._provider_failure(exc)


def test_removed_direct_web_formatter_path():
    assert not hasattr(TelegramClient, "_direct_web_search")
    assert not hasattr(TelegramClient, "_format_web_result")
