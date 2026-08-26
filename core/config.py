from __future__ import annotations

import os
from dataclasses import dataclass
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


def _csv(value: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass
class Config:
    # Provider/model selection is environment-only: no model is baked into source.
    default_model: str = os.getenv("DEFAULT_MODEL", "").strip()
    nara_key: str = os.getenv("NARA_API_KEY", "").strip()
    nara_base_url: str = os.getenv("NARA_BASE_URL", "https://router.bynara.id/v1").rstrip("/")

    # Legacy provider configuration is retained for module compatibility; Router enables Nara only.
    openai_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openrouter_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    gemini_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    openai_model: str = os.getenv("OPENAI_MODEL", "").strip()
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "").strip()
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "").strip()
    ollama_model: str = os.getenv("OLLAMA_MODEL", "").strip()

    api_token: str = os.getenv("API_TOKEN", "").strip()
    api_host: str = os.getenv("API_HOST", "127.0.0.1").strip()
    api_port: int = _int(os.getenv("API_PORT"), 8765)
    data_dir: str = os.path.expanduser(os.getenv("MYCHATBOT_DATA", "~/.mychatbot").strip())
    trust_proxy: bool = _bool(os.getenv("TRUST_PROXY"), False)
    telegram_require_allowlist: bool = _bool(os.getenv("TELEGRAM_REQUIRE_ALLOWLIST"), False)
    max_input_chars: int = _int(os.getenv("MAX_INPUT_CHARS"), 12000)
    recent_history_messages: int = _int(os.getenv("RECENT_HISTORY_MESSAGES"), 12)
    memory_context_messages: int = _int(os.getenv("MEMORY_CONTEXT_MESSAGES"), 8)
    memory_context_facts: int = _int(os.getenv("MEMORY_CONTEXT_FACTS"), 12)
    memory_max_messages: int = _int(os.getenv("MEMORY_MAX_MESSAGES"), 1000)
    memory_max_facts: int = _int(os.getenv("MEMORY_MAX_FACTS"), 100)
    memory_max_message_chars: int = _int(os.getenv("MEMORY_MAX_MESSAGE_CHARS"), 12000)
    rate_limit_requests: int = _int(os.getenv("RATE_LIMIT_REQUESTS"), 30)
    rate_limit_window_seconds: int = _int(os.getenv("RATE_LIMIT_WINDOW_SECONDS"), 60)
    allow_shell: bool = _bool(os.getenv("ALLOW_SHELL"), False)
    shell_whitelist: tuple[str, ...] = _csv(os.getenv("SHELL_WHITELIST"), ("pwd", "ls", "whoami", "uname", "date"))
    auto_tools: tuple[str, ...] = _csv(
        os.getenv("AUTO_TOOLS"),
        (
            "wifi_capabilities", "wifi_info", "wifi_scan", "wifi_diagnostics", "wifi_security_report",
            "battery", "local_ip", "ping", "dns_lookup", "port_check",
        ),
    )
    tool_profile: str = os.getenv("TOOL_PROFILE", "local").strip() or "local"

    def __post_init__(self) -> None:
        if not 1 <= self.api_port <= 65535:
            raise ValueError("API_PORT must be between 1 and 65535")
        self.max_input_chars = max(1000, min(self.max_input_chars, 50000))
        self.recent_history_messages = max(2, min(self.recent_history_messages, 30))
        self.memory_context_messages = max(0, min(self.memory_context_messages, 20))
        self.memory_context_facts = max(0, min(self.memory_context_facts, 50))
        self.memory_max_messages = max(100, min(self.memory_max_messages, 100_000))
        self.memory_max_facts = max(10, min(self.memory_max_facts, 10_000))
        self.memory_max_message_chars = max(1000, min(self.memory_max_message_chars, 50_000))
        self.rate_limit_requests = max(1, min(self.rate_limit_requests, 10_000))
        self.rate_limit_window_seconds = max(1, min(self.rate_limit_window_seconds, 86_400))

    def ensure_data_dir(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True, mode=0o700)


config = Config()
config.ensure_data_dir()
