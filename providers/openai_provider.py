from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.openai_model).strip()
        if not selected_model:
            raise ValueError("OPENAI_MODEL is not configured")
        headers = {
            "Authorization": f"Bearer {config.openai_key}",
            "Content-Type": "application/json",
        }
        data = await self._post(
            f"{self.base_url}/chat/completions",
            headers,
            {"model": selected_model, "messages": messages, "temperature": kw.get("temperature", 0.4)},
        )
        return data["choices"][0]["message"]["content"]
