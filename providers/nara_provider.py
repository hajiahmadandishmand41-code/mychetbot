from __future__ import annotations

from core.config import config
from core.errors import ProviderError
from providers.base import BaseProvider


class NaraProvider(BaseProvider):
    name = "nara"
    fallback_model = "mimo-v2.5-free"

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        # Keep the payload minimal for broad OpenAI-compatible model support.
        primary_model = (model or config.default_model).strip()
        selected_model = primary_model or self.fallback_model
        headers = {
            "Authorization": f"Bearer {config.nara_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": selected_model, "messages": messages}
        try:
            data = await self._post(
                f"{config.nara_base_url}/chat/completions",
                headers,
                payload,
            )
        except ProviderError as exc:
            # A stale/unsupported DEFAULT_MODEL should not make the bot entirely
            # unusable. Retry once with a known OpenAI-compatible fallback.
            if exc.code != "model_or_request_invalid" or selected_model == self.fallback_model:
                raise
            data = await self._post(
                f"{config.nara_base_url}/chat/completions",
                headers,
                {"model": self.fallback_model, "messages": messages},
            )
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("NaraRouter returned an unexpected response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("NaraRouter returned empty assistant content")
        return content
