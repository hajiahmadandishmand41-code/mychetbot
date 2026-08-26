from __future__ import annotations
from providers.registry import get_provider, list_providers
from core.config import config
from core.logger import get_logger

log = get_logger("router")

FALLBACK_ORDER = ["openrouter", "openai", "anthropic", "gemini", "ollama"]

class Router:
    '''انتخاب provider با fallback خودکار در صورت خطا.'''

    def __init__(self, preferred: str | None = None, model: str | None = None):
        self.preferred = preferred or config.default_provider
        self.model = model or config.default_model

    def _chain(self) -> list[str]:
        available = list_providers()
        chain = [self.preferred] + [p for p in FALLBACK_ORDER if p != self.preferred]
        return [p for p in chain if p in available]

    async def complete(self, messages: list[dict], **kw) -> dict:
        errors = []
        for name in self._chain():
            try:
                provider = get_provider(name)
                text = await provider.chat(messages, model=kw.get("model", self.model))
                return {"provider": name, "model": kw.get("model", self.model), "content": text}
            except Exception as exc:  # noqa: BLE001
                log.warning("provider %s failed: %s", name, type(exc).__name__)
                errors.append(f"{name}: {type(exc).__name__}")
        raise RuntimeError("همه providerها ناموفق بودند -> " + "; ".join(errors))
