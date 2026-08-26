"""Provider-neutral AI interface with OpenAI-compatible, Anthropic and Gemini adapters."""
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
        r = requests.post(f"{self.base_url}/chat/completions", json=payload,
                          headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, timeout=90)
        r.raise_for_status()
        return r.json()


class Anthropic(Provider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def chat(self, messages, model, tools=None):
        system = ""
        clean = []
        for m in messages:
            if m["role"] == "system":
                system = m.get("content", "")
            else:
                clean.append(m)
        payload = {"model": model, "max_tokens": 4096, "messages": clean}
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [t["function"] for t in tools]
        r = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers={
            "x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"
        }, timeout=90)
        r.raise_for_status()
        data = r.json()
        text = "".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text")
        return {"choices": [{"message": {"role": "assistant", "content": text}}]}


class Gemini(Provider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def chat(self, messages, model, tools=None):
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        r = requests.post(url, params={"key": self.api_key}, json={"contents": contents}, timeout=90)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0].get("text", "")
        return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def get_provider(name: str | None = None) -> Provider:
    name = (name or os.getenv("AI_PROVIDER", "openai")).lower()
    if name == "openai":
        return OpenAICompatible(os.environ["OPENAI_API_KEY"], os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), name)
    if name == "openrouter":
        return OpenAICompatible(os.environ["OPENROUTER_API_KEY"], os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), name)
    if name == "claude" or name == "anthropic":
        return Anthropic(os.environ["ANTHROPIC_API_KEY"])
    if name == "gemini":
        return Gemini(os.environ["GEMINI_API_KEY"])
    raise ValueError(f"Unsupported AI provider: {name}")
