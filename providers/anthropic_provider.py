from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    base_url = "https://api.anthropic.com/v1"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.anthropic_model).strip()
        if not selected_model:
            raise ValueError("ANTHROPIC_MODEL is not configured")
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        convo = [m for m in messages if m["role"] != "system"]
        data = await self._post(
            f"{self.base_url}/messages",
            {
                "x-api-key": config.anthropic_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            {
                "model": selected_model,
                "max_tokens": kw.get("max_tokens", 1024),
                "system": system,
                "messages": convo,
            },
        )
        return "".join(b.get("text", "") for b in data.get("content", []))
