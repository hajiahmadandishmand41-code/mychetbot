from __future__ import annotations
from providers.base import BaseProvider
from core.config import config

class OpenAIProvider(BaseProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        headers = {"Authorization": f"Bearer {config.openai_key}", "Content-Type": "application/json"}
        
        data = await self._post(f"{self.base_url}/chat/completions", headers, {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": kw.get("temperature", 0.4),
        })
        return data["choices"][0]["message"]["content"]
