from __future__ import annotations
from providers.base import BaseProvider
from core.config import config

class OllamaProvider(BaseProvider):
    '''مدل محلی — بدون اینترنت و بدون ارسال داده به بیرون.'''
    name = "ollama"
    default_model = "llama3.2:1b"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        data = await self._post(f"{config.ollama_base_url}/api/chat",
            {"Content-Type": "application/json"},
            {"model": model or self.default_model, "messages": messages, "stream": False})
        return data["message"]["content"]
