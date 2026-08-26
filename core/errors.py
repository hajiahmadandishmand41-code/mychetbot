from __future__ import annotations


class MyChatBotError(Exception):
    """Base error for user-facing application failures."""


class ConfigurationError(MyChatBotError):
    """Required configuration is missing or invalid."""


class ProviderError(MyChatBotError):
    """Normalized provider failure."""

    def __init__(self, provider: str, code: str, message: str):
        self.provider = provider
        self.code = code
        self.message = message
        super().__init__(f"{provider}:{code}: {message}")
