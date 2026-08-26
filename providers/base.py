from __future__ import annotations
from abc import ABC, abstractmethod
import httpx

class BaseProvider(ABC):
    name: str = "base"
    timeout: float = 60.0

    @abstractmethod
    async def chat(self, messages: list[dict], model: str | None = None, **kw) -> str: ...

    async def _post(self, url: str, headers: dict, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()
