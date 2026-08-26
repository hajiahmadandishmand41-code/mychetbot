from __future__ import annotations

from core.config import config
from core.errors import ConfigurationError, ProviderError
from core.logger import get_logger
from providers.registry import get_provider, list_providers

log = get_logger("router")
FALLBACK_ORDER = ["openrouter", "openai", "anthropic", "gemini", "ollama"]


class Router:
    """Select a configured provider and fall back on normalized provider failures."""

    def __init__(self, preferred: str | None = None, model: str | None = None):
        self.preferred = (preferred or config.default_provider).strip()
        self.model = (model or config.default_model).strip()

    def _chain(self) -> list[str]:
        available = list_providers()
        chain = [self.preferred] + [p for p in FALLBACK_ORDER if p != self.preferred]
        return [p for p in chain if p in available]

    async def complete(self, messages: list[dict], **kw) -> dict:
        chain = self._chain()
        if not chain:
            raise ConfigurationError("API provider is not configured")

        errors: list[str] = []
        requested_model = kw.get("model", self.model)
        for name in chain:
            try:
                provider = get_provider(name)
                text = await provider.chat(messages, model=requested_model)
                return {"provider": name, "model": requested_model, "content": text}
            except ProviderError as exc:
                log.warning("provider %s failed: %s", name, exc.code)
                errors.append(f"{name}: {exc.code}")
            except Exception as exc:  # noqa: BLE001
                log.exception("unexpected provider failure: %s", name)
                errors.append(f"{name}: unexpected_error")

        raise ProviderError("router", "all_providers_failed", "; ".join(errors))
