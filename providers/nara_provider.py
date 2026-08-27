from __future__ import annotations

import asyncio

from core.config import config
from core.errors import ProviderError
from providers.base import BaseProvider


class NaraProvider(BaseProvider):
    name = "nara"

    @staticmethod
    def _needs_model_fallback(error: ProviderError) -> bool:
        # A model-specific incompatibility or a transient model/tier outage
        # should move to the next configured model rather than fail the chat.
        return error.code in {
            "model_or_request_invalid",
            "forbidden_model",
            "http_5xx",
            "rate_limit",
        }

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        selected_model = (model or config.default_model).strip()
        if not selected_model:
            raise ValueError("DEFAULT_MODEL is not configured")

        models: list[str] = []
        for candidate in (selected_model, *config.nara_fallback_models):
            candidate = candidate.strip()
            if candidate and candidate not in models:
                models.append(candidate)

        if not models:
            raise ValueError("No Nara models are configured")

        headers = {
            "Authorization": f"Bearer {config.nara_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        last_error: ProviderError | None = None

        for index, selected in enumerate(models):
            try:
                data = await self._post(
                    f"{config.nara_base_url}/chat/completions",
                    headers,
                    {
                        "model": selected,
                        "messages": messages,
                        "temperature": kw.get("temperature", 0.7),
                        "max_tokens": kw.get("max_tokens", 4096),
                        "reasoning_effort": kw.get("reasoning_effort", "medium"),
                    },
                )
                try:
                    content = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise ValueError("NaraRouter returned an unexpected response") from exc
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("NaraRouter returned empty assistant content")
                return content
            except ProviderError as exc:
                last_error = exc
                if not self._needs_model_fallback(exc) or index >= len(models) - 1:
                    raise
                # Move immediately to another model/tier. BaseProvider already
                # performs bounded retries for transient transport/gateway errors.
                await asyncio.sleep(0)

        raise last_error or ProviderError(self.name, "http_error", "provider request failed")
