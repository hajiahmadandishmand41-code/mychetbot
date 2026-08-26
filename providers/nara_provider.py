from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class NaraProvider(BaseProvider):
    name = "nara"
    default_model = "deepseek-v4-flash"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        headers = {
            "Authorization": f"Bearer {config.nara_key}",
            "Content-Type": "application/json",
        }
        data = await self._post(
            f"{config.nara_base_url}/chat/completions",
            headers,
            {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": kw.get("temperature", 0.4),
            },
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("NaraRouter returned an unexpected response") from exc
