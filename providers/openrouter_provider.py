from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.openrouter_model).strip()
        if not selected_model:
            raise ValueError("OPENROUTER_MODEL is not configured")
        headers = {
            "Authorization": f"Bearer {config.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hajiahmadandishmand41-code/mychetbot",
            "X-Title": "MyChatBot",
        }
        data = await self._post(
            f"{self.base_url}/chat/completions",
            headers,
            {"model": selected_model, "messages": messages, "temperature": kw.get("temperature", 0.4)},
        )
        return data["choices"][0]["message"]["content"]
