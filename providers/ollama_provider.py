from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """مدل محلی — بدون اینترنت و بدون ارسال داده به بیرون."""

    name = "ollama"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.ollama_model).strip()
        if not selected_model:
            raise ValueError("OLLAMA_MODEL is not configured")
        data = await self._post(
            f"{config.ollama_base_url}/api/chat",
            {"Content-Type": "application/json"},
            {"model": selected_model, "messages": messages, "stream": False},
        )
        return data["message"]["content"]
