from __future__ import annotations

from core.config import config
from core.errors import ConfigurationError
from providers.nara_provider import NaraProvider

_CACHE: NaraProvider | None = None


def list_providers() -> list[str]:
    return ["nara"] if config.nara_key else []


def get_provider(name: str = "nara") -> NaraProvider:
    if name != "nara":
        raise ConfigurationError("only the Nara chat provider is enabled")
    if not config.nara_key:
        raise ConfigurationError("NARA_API_KEY is not configured")
    global _CACHE
    if _CACHE is None:
        _CACHE = NaraProvider()
    return _CACHE
