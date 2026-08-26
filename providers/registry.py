from __future__ import annotations

from core.config import config
from core.errors import ConfigurationError
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.ollama_provider import OllamaProvider
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider

_CLASSES = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}
_CACHE: dict[str, object] = {}


def list_providers() -> list[str]:
    return config.available_providers()


def get_provider(name: str):
    if name not in _CLASSES:
        raise ConfigurationError(f"provider ناشناخته: {name}")
    if not config.provider_configured(name):
        raise ConfigurationError(f"provider '{name}' تنظیم نشده است")
    if name not in _CACHE:
        _CACHE[name] = _CLASSES[name]()
    return _CACHE[name]
