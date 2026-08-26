from __future__ import annotations
import base64, hashlib, hmac, os, re, secrets
from cryptography.fernet import Fernet
from core.config import config

DANGEROUS = re.compile(r"(rm\s+-rf\s+/|mkfs|:\(\)\{|dd\s+if=|>\s*/dev/sd|chmod\s+777\s+/)")

def _master_key() -> bytes:
    key = os.getenv("MYCHATBOT_MASTER_KEY")
    path = os.path.join(config.data_dir, ".master.key")
    if not key:
        if os.path.exists(path):
            key = open(path).read().strip()
        else:
            key = Fernet.generate_key().decode()
            with open(path, "w") as f:
                f.write(key)
            os.chmod(path, 0o600)
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

def is_command_allowed(cmd: str) -> tuple[bool, str]:
    if not config.allow_shell:
        return False, "اجرای شل غیرفعال است (ALLOW_SHELL=false)"
    if DANGEROUS.search(cmd):
        return False, "دستور خطرناک مسدود شد"
    head = cmd.strip().split()[0] if cmd.strip() else ""
    if head not in config.shell_whitelist:
        return False, f"دستور '{head}' در whitelist نیست"
    return True, "ok"

def redact(text: str) -> str:
    return re.sub(r"(sk-[A-Za-z0-9_\-]{8,})", "sk-***", text)
