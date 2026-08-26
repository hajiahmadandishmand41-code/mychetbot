"""Provider-neutral AI adapters.

OpenAI and OpenRouter use OpenAI-compatible Chat Completions. Gemini also exposes
an OpenAI-compatible endpoint, while Claude is normalized from its native
Messages API into the same internal tool-call shape used by the Agent.
"""
import os
from abc import ABC, abstractmethod
from typing import Any
import requests


class Provider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], model: str, tools: list[dict] | None = None) -> dict:
        raise NotImplementedError


class OpenAICompatible(Provider):
    def __init__(self, api_key: str, base_url: str, provider: str):
        self.api_key, self.base_url, self.provider = api_key, base_url.rstrip("/"), provider

    def chat(self, messages, model, tools=None):
        payload = {"model": model, "messages": messages, "max_tokens": 4096}
        if tools:
            payload["tools"] = tools
        r = requests.post(f"{self.base_url}/chat/completions", json=payload, headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"
        }, timeout=90)
        r.raise_for_status()
        return r.json()


class Anthropic(Provider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def chat(self, messages, model, tools=None):
        system = ""
        converted = []
        for m in messages:
            role = m.get("role")
            if role == "system":
                system = str(m.get("content", ""))
            elif role == "tool":
                converted.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": m.get("tool_call_id", ""), "content": str(m.get("content", ""))
                }]})
            elif role == "assistant" and m.get("tool_calls"):
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": str(m["content"])})
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {})
                    import json
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except Exception:
                        args = {}
                    blocks.append({"type": "tool_use", "id": tc.get("id", fn.get("name", "call")), "name": fn.get("name", ""), "input": args})
                converted.append({"role": "assistant", "content": blocks})
            else:
                converted.append({"role": "user" if role == "user" else "assistant", "content": m.get("content", "")})
        payload = {"model": model, "max_tokens": 4096, "messages": converted}
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [t.get("function", t) for t in tools]
        r = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers={
            "x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"
        }, timeout=90)
        r.raise_for_status()
        data = r.json()
        import json
        text = "".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text")
        calls = []
        for x in data.get("content", []):
            if x.get("type") == "tool_use":
                calls.append({"id": x.get("id", x.get("name", "call")), "type": "function", "function": {"name": x.get("name", ""), "arguments": json.dumps(x.get("input", {}), ensure_ascii=False)}})
        msg = {"role": "assistant", "content": text}
        if calls:
            msg["tool_calls"] = calls
        return {"choices": [{"message": msg}]}


def get_provider(name: str | None = None) -> Provider:
    name = (name or os.getenv("AI_PROVIDER", "openai")).lower()
    if name == "openai":
        return OpenAICompatible(os.environ["OPENAI_API_KEY"], os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), name)
    if name == "openrouter":
        return OpenAICompatible(os.environ["OPENROUTER_API_KEY"], os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), name)
    if name in {"claude", "anthropic"}:
        return Anthropic(os.environ["ANTHROPIC_API_KEY"])
    if name == "gemini":
        return OpenAICompatible(os.environ["GEMINI_API_KEY"], os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"), name)
    raise ValueError(f"Unsupported AI provider: {name}")
