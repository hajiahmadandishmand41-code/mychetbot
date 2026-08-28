from __future__ import annotations

import asyncio

from core.config import config
from core.errors import ProviderError
from providers.base import BaseProvider


class NaraProvider(BaseProvider):
    name = "nara"

    @staticmethod
    def _needs_model_fallback(error: ProviderError) -> bool:
        # Switch immediately on model/tier/gateway failures.  Authentication
        # errors must not be retried because every model uses the same key.
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
                payload = {
                    "model": selected,
                    "messages": messages,
                    "temperature": kw.get("temperature", 0.7),
                    "max_tokens": kw.get("max_tokens", 4096),
                }
                # Only send optional provider-specific reasoning controls when
                # explicitly requested. This keeps the OpenAI-compatible payload
                # compatible with every model behind the gateway.
                if kw.get("reasoning_effort") is not None:
                    payload["reasoning_effort"] = kw["reasoning_effort"]

                data = await self._post(
                    f"{config.nara_base_url}/chat/completions",
                    headers,
                    payload,
                )
                try:
                    content = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise ProviderError(self.name, "invalid_response", "NaraRouter returned an unexpected response") from exc
                if not isinstance(content, str) or not content.strip():
                    raise ProviderError(self.name, "invalid_response", "NaraRouter returned empty assistant content")
                return content
            except ProviderError as exc:
                last_error = exc
                if not self._needs_model_fallback(exc) or index >= len(models) - 1:
                    raise
                await asyncio.sleep(0)

        raise last_error or ProviderError(self.name, "http_error", "provider request failed")
