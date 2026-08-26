from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}

@dataclass
class Config:
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "openrouter")
    default_model: str = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    gemini_key: str = os.getenv("GEMINI_API_KEY", "")
    openrouter_key: str = os.getenv("OPENROUTER_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    allow_shell: bool = _bool(os.getenv("ALLOW_SHELL"), False)
    shell_whitelist: list[str] = field(default_factory=lambda: [
        c.strip() for c in os.getenv("SHELL_WHITELIST", "ls,pwd,whoami").split(",") if c.strip()
    ])
    api_token: str = os.getenv("API_TOKEN", "change-me")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8765"))
    data_dir: str = os.getenv("MYCHATBOT_DATA", os.path.expanduser("~/.mychatbot"))

    def available_providers(self) -> list[str]:
        out = ["ollama"]
        if self.openai_key: out.append("openai")
        if self.anthropic_key: out.append("anthropic")
        if self.gemini_key: out.append("gemini")
        if self.openrouter_key: out.append("openrouter")
        return out

config = Config()
os.makedirs(config.data_dir, exist_ok=True)
