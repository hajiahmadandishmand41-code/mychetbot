from __future__ import annotations
import os

ROOT = os.path.expanduser("~")

def _safe(path: str) -> str:
    full = os.path.realpath(os.path.join(ROOT, os.path.expanduser(path)))
    if not full.startswith(os.path.realpath(ROOT)):
        raise PermissionError("خارج از دایرکتوری مجاز")
    return full

def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(os.listdir(_safe(path)))) or "(خالی)"

def read_file(path: str, max_bytes: int = 8000) -> str:
    with open(_safe(path), "r", encoding="utf-8", errors="replace") as f:
        return f.read(max_bytes)

def write_file(path: str, content: str) -> str:
    p = _safe(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"نوشته شد: {p} ({len(content)} کاراکتر)"
