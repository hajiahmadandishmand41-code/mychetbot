from __future__ import annotations

import os

ROOT = os.path.realpath(os.path.expanduser("~"))


def _safe(path: str) -> str:
    candidate = os.path.realpath(os.path.join(ROOT, os.path.expanduser(path)))
    try:
        inside = os.path.commonpath([ROOT, candidate]) == ROOT
    except ValueError:
        inside = False
    if not inside:
        raise PermissionError("خارج از دایرکتوری مجاز")
    return candidate


def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(os.listdir(_safe(path)))) or "(خالی)"


def read_file(path: str, max_bytes: int = 8000) -> str:
    with open(_safe(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(max(1, min(int(max_bytes), 1_000_000)))


def write_file(path: str, content: str) -> str:
    p = _safe(path)
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(p, "w", encoding="utf-8") as handle:
        handle.write(content)
    return f"نوشته شد: {p} ({len(content)} کاراکتر)"
