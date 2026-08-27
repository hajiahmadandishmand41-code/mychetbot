from __future__ import annotations

from core.config import config
from core.errors import ConfigurationError, ProviderError
from providers.nara_provider import NaraProvider


class Router:
    """Single-provider chat router. Provider and model are environment-controlled."""

    def __init__(self):
        self.provider = "nara"
        self.model = config.default_model
        self._provider = NaraProvider()

    async def complete(self, messages: list[dict], **kw) -> dict:
        if not config.nara_key:
            raise ConfigurationError("NARA_API_KEY is not configured")
        try:
            text = await self._provider.chat(messages, model=kw.pop("model", self.model), **kw)
            return {"content": text}
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError("nara", "unexpected_error", "chat provider request failed") from exc

    async def aclose(self) -> None:
        await self._provider.aclose()
