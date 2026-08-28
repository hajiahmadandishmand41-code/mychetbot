import json

import pytest

from core.errors import ProviderError
from interfaces.telegram import TelegramClient


@pytest.mark.asyncio
async def test_telegram_search_does_not_call_ai_provider(monkeypatch):
    client = TelegramClient()
    sent = []

    async def fake_call(method, payload):
        sent.append((method, payload))
        return {"ok": True}

    async def fail_agent(_session):
        raise AssertionError("AI agent must not be called for web search")

    raw = json.dumps(
        {
            "status": "success",
            "data": {
                "query": "OpenAI",
                "results": [
                    {
                        "search_result": {"title": "Search title", "url": "https://example.com", "snippet": "A useful snippet"},
                        "page": {"title": "Example page", "url": "https://example.com", "text": "Full public page text"},
                    }
                ],
            },
        },
        ensure_ascii=False,
    )
    monkeypatch.setattr("interfaces.telegram.run_tool", lambda *args: raw)
    monkeypatch.setattr(client, "_call", fake_call)
    monkeypatch.setattr(client, "_agent", fail_agent)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    client.token = "test-token"
    client.base_url = "https://api.telegram.org/bottest-token"

    await client.handle_update({"message": {"chat": {"id": 123}, "from": {"id": 123}, "text": "/search OpenAI"}})

    messages = [payload["text"] for method, payload in sent if method == "sendMessage"]
    assert any("Example page" in text and "https://example.com" in text for text in messages)


def test_telegram_provider_failure_is_not_hidden():
    exc = ProviderError("nara", "rate_limit", "quota reached")
    assert "محدودیت" in TelegramClient._provider_failure(exc)
    assert "در پردازش درخواست خطایی رخ داد" not in TelegramClient._provider_failure(exc)


def test_web_result_formatter_supports_nested_results():
    raw = json.dumps(
        {
            "status": "success",
            "data": {
                "results": [
                    {
                        "search_result": {"title": "Search", "url": "https://example.com", "snippet": "Snippet"},
                        "page": {"title": "Page", "url": "https://example.com", "text": "Page text"},
                    }
                ]
            },
        },
        ensure_ascii=False,
    )
    output = TelegramClient._format_web_result(raw, "test", False)
    assert "Page" in output
    assert "https://example.com" in output
    assert "Snippet" in output
