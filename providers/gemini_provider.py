from __future__ import annotations

from core.config import config
from providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    default_model = "gemini-2.0-flash"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        contents = [
            {
                "role": "user" if m["role"] != "assistant" else "model",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
            if m["role"] != "system"
        ]
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        payload = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        mdl = model or self.default_model
        data = await self._post(
            f"{self.base_url}/models/{mdl}:generateContent?key={config.gemini_key}",
            {"Content-Type": "application/json"},
            payload,
        )
        return data["candidates"][0]["content"]["parts"][0]["text"]
