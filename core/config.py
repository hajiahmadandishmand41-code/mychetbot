from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


@dataclass
class Config:
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "openrouter")
    default_model: str = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    gemini_key: str = os.getenv("GEMINI_API_KEY", "")
    openrouter_key: str = os.getenv("OPENROUTER_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    allow_shell: bool = _bool(os.getenv("ALLOW_SHELL"), False)
    shell_whitelist: list[str] = field(default_factory=lambda: [
        item.strip().split()[0]
        for item in os.getenv("SHELL_WHITELIST", "ls,pwd,whoami,df,uname,ping,curl").split(",")
        if item.strip()
    ])
    api_token: str = os.getenv("API_TOKEN", "")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = _int(os.getenv("API_PORT"), 8765)
    data_dir: str = os.getenv("MYCHATBOT_DATA", os.path.expanduser("~/.mychatbot"))

    def available_providers(self) -> list[str]:
        providers = ["ollama"]
        if self.openai_key:
            providers.append("openai")
        if self.anthropic_key:
            providers.append("anthropic")
        if self.gemini_key:
            providers.append("gemini")
        if self.openrouter_key:
            providers.append("openrouter")
        return providers

    def provider_configured(self, provider: str) -> bool:
        return provider in self.available_providers()

    def ensure_data_dir(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)


config = Config()
config.ensure_data_dir()
