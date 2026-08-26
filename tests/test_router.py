import pytest

from core.errors import ConfigurationError, ProviderError
from core.router import Router


@pytest.mark.asyncio
async def test_router_uses_nara_and_environment_model(monkeypatch):
    import core.router as router_module

    monkeypatch.setattr(router_module.config, "nara_key", "test-key")
    monkeypatch.setattr(router_module.config, "default_model", "env-model")
    calls = {}

    async def fake_chat(messages, model=None, **kwargs):
        calls["model"] = model
        return "سلام"

    monkeypatch.setattr(router_module.NaraProvider, "chat", fake_chat)
    out = await Router().complete([{"role": "user", "content": "hi"}])
    assert out["content"] == "سلام"
    assert calls["model"] == "env-model"


@pytest.mark.asyncio
async def test_router_requires_nara_key(monkeypatch):
    import core.router as router_module

    monkeypatch.setattr(router_module.config, "nara_key", "")
    with pytest.raises(ConfigurationError):
        await Router().complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_router_surfaces_provider_failure(monkeypatch):
    import core.router as router_module

    monkeypatch.setattr(router_module.config, "nara_key", "test-key")

    async def fail(*args, **kwargs):
        raise ProviderError("nara", "timeout", "timed out")

    monkeypatch.setattr(router_module.NaraProvider, "chat", fail)
    with pytest.raises(ProviderError):
        await Router().complete([{"role": "user", "content": "hi"}])
