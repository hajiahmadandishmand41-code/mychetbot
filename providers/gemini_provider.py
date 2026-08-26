from __future__ import annotations

from typing import Any

from core.config import config
from providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        contents: list[dict[str, Any]] = [
            {
                "role": "user" if m["role"] != "assistant" else "model",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
            if m["role"] != "system"
        ]
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        payload: dict[str, Any] = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        selected_model = (model or config.gemini_model).strip()
        if not selected_model:
            raise ValueError("GEMINI_MODEL is not configured")
        data = await self._post(
            f"{self.base_url}/models/{selected_model}:generateContent?key={config.gemini_key}",
            {"Content-Type": "application/json"},
            payload,
        )
        return data["candidates"][0]["content"]["parts"][0]["text"]
