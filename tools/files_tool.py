from __future__ import annotations

import os

from core.config import config

ROOT = os.path.realpath(os.path.expanduser("~"))
MAX_WRITE_BYTES = 1_000_000
BLOCKED_WRITE_NAMES = {".env", ".master.key"}
BLOCKED_WRITE_DIRS = {".ssh", ".gnupg"}


def _safe(path: str) -> str:
    candidate = os.path.realpath(os.path.join(ROOT, os.path.expanduser(path)))
    try:
        inside = os.path.commonpath([ROOT, candidate]) == ROOT
    except ValueError:
        inside = False
    if not inside:
        raise PermissionError("خارج از دایرکتوری مجاز")
    return candidate


def _safe_write(path: str) -> str:
    candidate = _safe(path)
    if os.path.basename(candidate) in BLOCKED_WRITE_NAMES:
        raise PermissionError("نوشتن فایل secrets از طریق Agent مجاز نیست")
    if any(part in BLOCKED_WRITE_DIRS for part in os.path.normpath(candidate).split(os.sep)):
        raise PermissionError("نوشتن در credential directory مجاز نیست")
    if os.path.realpath(os.path.join(config.data_dir, ".master.key")) == candidate:
        raise PermissionError("master key قابل تغییر توسط Agent نیست")
    return candidate


def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(os.listdir(_safe(path)))) or "(خالی)"


def read_file(path: str, max_bytes: int = 8000) -> str:
    safe_max = max(1, min(int(max_bytes), MAX_WRITE_BYTES))
    with open(_safe(path), "r", encoding="utf-8", errors="replace") as handle:
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
