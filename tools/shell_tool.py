from __future__ import annotations

import shlex
import subprocess

from core.security import is_command_allowed


def shell(command: str, timeout: int = 20) -> str:
    ok, reason = is_command_allowed(command)
    if not ok:
        return f"[blocked] {reason}"
    try:
        argv = shlex.split(command, posix=True)
        if not argv:
            return "[arg-error] دستور خالی است"
        process = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=max(1, min(int(timeout), 60)),
            check=False,
        )
        output = (process.stdout or "") + (process.stderr or "")
        return output.strip()[:4000] or "(بدون خروجی)"
    except ValueError as exc:
        return f"[arg-error] {exc}"
    except subprocess.TimeoutExpired:
        return "[timeout] دستور بیش از حد طول کشید"
