from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from core.config import config
from core.security import redact

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_TIMEOUT = 30

SAFE_OPERATIONS: dict[str, dict[str, Any]] = {
    "health": {"description": "basic runtime health", "argv": [sys.executable, "-c", "print('ok')"], "risk": "low"},
    "version": {"description": "runtime and Python version", "argv": [sys.executable, "--version"], "risk": "low"},
    "filesystem": {"description": "inspect project files", "kind": "filesystem", "risk": "low"},
    "diagnostics": {"description": "application diagnostics", "argv": [sys.executable, "-c", "import sys; print(sys.version); print(sys.platform)"], "risk": "low"},
    "dependencies": {"description": "inspect installed dependencies", "argv": [sys.executable, "-m", "pip", "list", "--format=freeze"], "risk": "low"},
    "logs": {"description": "inspect recent redacted application logs", "kind": "logs", "risk": "low"},
}


def _preexec() -> None:
    try:
        import resource

        memory = int(config.server_memory_limit_mb) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_TIMEOUT, MAX_TIMEOUT + 1))
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (config.server_process_limit, config.server_process_limit))
    except (ImportError, OSError, ValueError):
        pass


def _project_path(relative_path: str) -> Path:
    value = (relative_path or ".").strip()
    candidate = (PROJECT_ROOT / value).resolve()
    if candidate != PROJECT_ROOT and PROJECT_ROOT not in candidate.parents:
        raise ValueError("path is outside the project directory")
    return candidate


def _filesystem(relative_path: str = ".") -> dict[str, Any]:
    path = _project_path(relative_path)
    if not path.exists():
        raise FileNotFoundError("path does not exist")
    if path.is_file():
        stat = path.stat()
        return {"path": str(path.relative_to(PROJECT_ROOT)), "type": "file", "size": stat.st_size}
    entries = []
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower())[:100]:
        entries.append({"name": child.name, "type": "dir" if child.is_dir() else "file"})
    return {"path": str(path.relative_to(PROJECT_ROOT)) or ".", "type": "directory", "entries": entries}


def _logs(max_lines: int = 200) -> dict[str, Any]:
    log_path = Path(config.data_dir) / "mychatbot.log"
    if not log_path.exists():
        return {"path": str(log_path), "lines": []}
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, min(max_lines, 200)):]
    return {"path": str(log_path), "lines": [redact(line)[:1000] for line in lines]}


def _allowed_script(name: str) -> list[str] | None:
    requested = (name or "").strip()
    for script in config.server_safe_scripts:
        script_path = _project_path(script)
        if script_path.name == requested and script_path.is_file() and script_path.suffix == ".py":
            return [sys.executable, str(script_path)]
    return None


def execute(operation: str, path: str = ".", script: str = "", timeout: int = 15) -> str:
    started = time.monotonic()
    request_id = f"server-{int(time.time() * 1000)}"
    op = (operation or "").strip().lower()
    if op not in SAFE_OPERATIONS and op != "safe_script":
        return json.dumps({"status": "denied", "data": {}, "warnings": ["operation is not allowlisted"], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
    try:
        if not config.server_execution_enabled:
            raise PermissionError("server execution is disabled")
        if op == "filesystem":
            data = _filesystem(path)
            return json.dumps({"status": "success", "data": data, "warnings": [], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
        if op == "logs":
            data = _logs()
            return json.dumps({"status": "success", "data": data, "warnings": [], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
        if op == "safe_script":
            argv = _allowed_script(script)
            if argv is None:
                raise PermissionError("script is not allowlisted")
        else:
            argv = list(SAFE_OPERATIONS[op]["argv"])
        run_timeout = max(1, min(int(timeout), min(config.server_timeout_seconds, MAX_TIMEOUT)))
        env = {k: v for k, v in os.environ.items() if k in config.server_allowed_env}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            argv,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
            start_new_session=True,
            preexec_fn=_preexec if os.name == "posix" else None,
        )
        try:
            output, _ = process.communicate(timeout=run_timeout)
        except subprocess.TimeoutExpired:
            if process.pid:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except OSError:
                    process.kill()
            process.communicate()
            return json.dumps({"status": "timeout", "data": {}, "warnings": ["execution timed out"], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
        clipped = redact((output or "")[: config.server_output_limit])
        status = "success" if process.returncode == 0 else "error"
        return json.dumps({"status": status, "data": {"stdout": clipped, "returncode": process.returncode}, "warnings": [] if status == "success" else ["command returned non-zero status"], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"status": "denied" if isinstance(exc, PermissionError) else "error", "data": {}, "warnings": [redact(str(exc))], "source": "render-runtime", "duration_ms": int((time.monotonic() - started) * 1000), "request_id": request_id}, ensure_ascii=False)
