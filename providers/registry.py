from __future__ import annotations
from core.config import config
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.ollama_provider import OllamaProvider

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
        raise KeyError(f"provider ناشناخته: {name}")
    if name not in _CACHE:
        _CACHE[name] = _CLASSES[name]()
    return _CACHE[name]
