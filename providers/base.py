from __future__ import annotations

import httpx

from core.errors import ProviderError


class BaseProvider:
    name = "base"
    timeout: float = 60.0

    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str:
        raise NotImplementedError

    async def _post(self, url: str, headers: dict, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise ProviderError(self.name, "timeout", "provider request timed out") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in {401, 403}:
                code = "invalid_api_key"
                message = "provider rejected the API credentials"
            elif status == 429:
                code = "rate_limit"
                message = "provider rate limit reached"
            elif status == 400:
                code = "model_or_request_invalid"
                # Keep provider diagnostics useful without exposing response bodies,
                # credentials, headers, or upstream secrets to the chat user.
                message = "provider rejected the request (HTTP 400); check DEFAULT_MODEL and request compatibility"
            elif status == 404:
                code = "endpoint_not_found"
                message = "provider endpoint was not found"
            else:
                code = "http_error"
                message = f"provider returned HTTP {status}"
            raise ProviderError(self.name, code, message) from exc
        except httpx.RequestError as exc:
            raise ProviderError(self.name, "connection_failure", "could not connect to provider") from exc
        except ValueError as exc:
            raise ProviderError(self.name, "invalid_response", "provider returned invalid JSON") from exc
