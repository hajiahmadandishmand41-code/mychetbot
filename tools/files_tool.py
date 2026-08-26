from __future__ import annotations

import os
from pathlib import Path

from core.config import config

ROOT = os.path.realpath(os.path.expanduser("~"))
MAX_WRITE_BYTES = 1_000_000
MAX_READ_BYTES = 1_000_000
BLOCKED_SECRET_NAMES = {".env", ".master.key"}
BLOCKED_SECRET_DIRS = {".ssh", ".gnupg"}
BLOCKED_FILE_SUFFIXES = (".pem", ".key")


def _safe(path: str) -> str:
    candidate = os.path.realpath(os.path.join(ROOT, os.path.expanduser(path)))
    try:
        inside = os.path.commonpath([ROOT, candidate]) == ROOT
    except ValueError:
        inside = False
    if not inside:
        raise PermissionError("خارج از دایرکتوری مجاز")
    return candidate


def _is_secret_path(candidate: str) -> bool:
    path = Path(candidate)
    if path.name in BLOCKED_SECRET_NAMES:
        return True
    if path.name.startswith(".env."):
        return True
    if any(part in BLOCKED_SECRET_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in BLOCKED_FILE_SUFFIXES:
        return True
    return False


def _safe_read(path: str) -> str:
    candidate = _safe(path)
    if _is_secret_path(candidate):
        raise PermissionError("خواندن فایل secrets از طریق Agent مجاز نیست")
    return candidate


def _safe_write(path: str) -> str:
    candidate = _safe(path)
    if _is_secret_path(candidate):
        raise PermissionError("نوشتن فایل secrets از طریق Agent مجاز نیست")
    if os.path.realpath(os.path.join(config.data_dir, ".master.key")) == candidate:
        raise PermissionError("master key قابل تغییر توسط Agent نیست")
    return candidate


def list_dir(path: str = ".") -> str:
    candidate = _safe(path)
    entries = []
    for name in sorted(os.listdir(candidate)):
        child = os.path.join(candidate, name)
        entries.append("[secret]" if _is_secret_path(child) else name)
    return "\n".join(entries) or "(خالی)"


def read_file(path: str, max_bytes: int = 8000) -> str:
    safe_max = max(1, min(int(max_bytes), MAX_READ_BYTES))
    with open(_safe_read(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(safe_max)


def write_file(path: str, content: str) -> str:
    p = _safe_write(path)
    if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
        raise ValueError("فایل بزرگ‌تر از حد مجاز 1MB است")
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(p, "w", encoding="utf-8") as handle:
        handle.write(content)
    return f"نوشته شد: {p} ({len(content)} کاراکتر)"
