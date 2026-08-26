from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class NaraProvider(BaseProvider):
    name = "nara"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.default_model).strip()
        if not selected_model:
            raise ValueError("DEFAULT_MODEL is not configured")
        headers = {
            "Authorization": f"Bearer {config.nara_key}",
            "Content-Type": "application/json",
        }
        data = await self._post(
            f"{config.nara_base_url}/chat/completions",
            headers,
            {
                "model": selected_model,
                "messages": messages,
                "temperature": kw.get("temperature", 0.4),
            },
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("NaraRouter returned an unexpected response") from exc
