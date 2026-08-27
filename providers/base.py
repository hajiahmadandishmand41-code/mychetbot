from __future__ import annotations

import asyncio
import random

import httpx

from core.errors import ProviderError


class BaseProvider:
    name = "base"
    timeout: float = 45.0
    max_retries: int = 2

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        raise NotImplementedError

    @staticmethod
    def _retryable(code: str) -> bool:
        return code in {"timeout", "connection_failure", "rate_limit", "http_5xx"}

    async def _post(self, url: str, headers: dict, payload: dict) -> dict:
        last_error: ProviderError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                last_error = ProviderError(self.name, "timeout", "provider request timed out")
                last_error.__cause__ = exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in {401, 403}:
                    code = "invalid_api_key"
                    message = "provider rejected the API credentials"
                elif status == 429:
                    code = "rate_limit"
                    message = "provider rate limit reached"
                elif status in {404, 400}:
                    code = "model_or_request_invalid"
                    message = f"provider rejected the request (HTTP {status})"
                elif 500 <= status <= 599:
                    code = "http_5xx"
                    message = f"provider returned HTTP {status}"
                else:
                    code = "http_error"
                    message = f"provider returned HTTP {status}"
                last_error = ProviderError(self.name, code, message)
                last_error.__cause__ = exc
            except httpx.RequestError as exc:
                last_error = ProviderError(self.name, "connection_failure", "could not connect to provider")
                last_error.__cause__ = exc
            except ValueError as exc:
                raise ProviderError(self.name, "invalid_response", "provider returned invalid JSON") from exc

            assert last_error is not None
            if attempt >= self.max_retries or not self._retryable(last_error.code):
                raise last_error

            # Keep retries quick while yielding to other requests; 0.35s, 0.7s.
            delay = 0.35 * (2**attempt) + random.uniform(0, 0.15)
            await asyncio.sleep(delay)

        raise last_error or ProviderError(self.name, "http_error", "provider request failed")
