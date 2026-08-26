from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import stat
from pathlib import Path

from cryptography.fernet import Fernet

from core.config import config

DANGEROUS = re.compile(
    r"(?:\brm\s+-rf\b|\bmkfs(?:\.|\s)|:\(\)\s*\{|\bdd\s+if=|>\s*/dev/|\bchmod\s+777\b|\bshutdown\b|\breboot\b|\bpoweroff\b|\bmount\b|\bumount\b|\bnsenter\b|\bunshare\b|\bchroot\b)",
    re.IGNORECASE,
)
SHELL_META = re.compile(r"[;&|<>`$()]|\n|\r")
SECRET_PATTERNS = [
    re.compile(r"(?:sk-[A-Za-z0-9_-]{8,})"),
    re.compile(r"(?:AKIA[0-9A-Z]{16})"),
    re.compile(r"(?:Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"(?:Basic\s+)[A-Za-z0-9+/=]{12,}", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|token|password|passwd|secret|cookie|authorization|database_url|telegram_bot_token|nara_api_key)\s*[=:]\s*[^\s,;]+", re.IGNORECASE),
    re.compile(r"(?:https?://)([^\s/@]+):([^\s/@]+)@", re.IGNORECASE),
]


def _master_key() -> bytes:
    config.ensure_data_dir()
    env_key = os.getenv("MYCHATBOT_MASTER_KEY", "").strip()
    path = Path(config.data_dir) / ".master.key"
    if env_key:
        return env_key.encode()
    if path.exists():
        return path.read_text(encoding="utf-8").strip().encode()
    key = Fernet.generate_key().decode()
    path.write_text(key + "\n", encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return key.encode()


def encrypt(plain: str) -> str:
    return Fernet(_master_key()).encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    return Fernet(_master_key()).decrypt(token.encode()).decode()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def new_token(n: int = 32) -> str:
    return secrets.token_urlsafe(n)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def contains_secret(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)


def is_command_allowed(cmd: str) -> tuple[bool, str]:
    command = cmd.strip()
    if not config.allow_shell:
        return False, "اجرای شل غیرفعال است (ALLOW_SHELL=false)"
    if not command:
        return False, "دستور خالی است"
    if SHELL_META.search(command):
        return False, "کاراکترهای shell chaining/redirection مجاز نیستند"
    if DANGEROUS.search(command):
        return False, "دستور خطرناک مسدود شد"
    head = command.split()[0]
    if head not in config.shell_whitelist:
        return False, f"دستور '{head}' در whitelist نیست"
    return True, "ok"


def redact(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("***REDACTED***", redacted)
    redacted = re.sub(r"(?i)(authorization\s*:\s*)([^\r\n]+)", r"\1***REDACTED***", redacted)
    redacted = re.sub(r"(?i)(cookie\s*:\s*)([^\r\n]+)", r"\1***REDACTED***", redacted)
    redacted = re.sub(r"(?i)(database_url\s*[=:]\s*)([^\s]+)", r"\1***REDACTED***", redacted)
    redacted = re.sub(
        r"\b([0-9A-Fa-f]{2}:){2,5}[0-9A-Fa-f]{2}\b",
        lambda m: ":".join(m.group(0).split(":")[:3]) + ":xx:xx:xx",
        redacted,
    )
    return redacted
