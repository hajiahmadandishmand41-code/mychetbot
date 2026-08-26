from __future__ import annotations
from providers.base import BaseProvider
from core.config import config

class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    default_model = "openai/gpt-4o-mini"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        headers = {"Authorization": f"Bearer {config.openrouter_key}", "Content-Type": "application/json"}
        headers["HTTP-Referer"] = "https://github.com/hajiahmadandishmand41-code/mychetbot"
        headers["X-Title"] = "MyChatBot"
        data = await self._post(f"{self.base_url}/chat/completions", headers, {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": kw.get("temperature", 0.4),
        })
        return data["choices"][0]["message"]["content"]
