from __future__ import annotations

import shutil
import subprocess


def _run(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return f"[unavailable] {cmd[0]} در دسترس نیست"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=25, check=False)
    except subprocess.TimeoutExpired:
        return "[timeout] عملیات Termux بیش از حد طول کشید"
    return (p.stdout or p.stderr).strip() or "ok"


def battery() -> str:
    return _run(["termux-battery-status"])


def notify(title: str, content: str) -> str:
    return _run(["termux-notification", "--title", title, "--content", content])


def clipboard_get() -> str:
    return _run(["termux-clipboard-get"])


def clipboard_set(text: str) -> str:
    return _run(["termux-clipboard-set", text])


def toast(text: str) -> str:
    return _run(["termux-toast", text])


def location() -> str:
    return _run(["termux-location", "-p", "network"])


def speak(text: str) -> str:
    return _run(["termux-tts-speak", text])
