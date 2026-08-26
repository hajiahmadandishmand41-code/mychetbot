import pytest
from core.router import Router

@pytest.mark.asyncio
async def test_fallback(monkeypatch):
    import core.router as R
    monkeypatch.setattr(R, "list_providers", lambda: ["openai", "ollama"])
    class Bad:
        async def chat(self, *a, **k): raise RuntimeError("boom")
    class Good:
        async def chat(self, *a, **k): return "سلام"
    monkeypatch.setattr(R, "get_provider", lambda n: Bad() if n == "openai" else Good())
    r = Router(preferred="openai")
    out = await r.complete([{"role": "user", "content": "hi"}])
    assert out["provider"] == "ollama" and out["content"] == "سلام"
