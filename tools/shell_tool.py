from __future__ import annotations
import subprocess
from core.security import is_command_allowed

def shell(command: str, timeout: int = 20) -> str:
    ok, reason = is_command_allowed(command)
    if not ok:
        return f"[blocked] {reason}"
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return out.strip()[:4000] or "(بدون خروجی)"
    except subprocess.TimeoutExpired:
        return "[timeout] دستور بیش از حد طول کشید"
