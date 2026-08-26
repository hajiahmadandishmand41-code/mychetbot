"""Core file, Termux, archive, phone and Wi-Fi tool adapters."""
import re
import shutil
import subprocess
from pathlib import Path
from agent.memory.store import MemoryStore
from agent.tools.wifi.manager import build_wifi_tools
from agent.tools.wifi.wifite_tool import build_wifite_tools
from agent.tools.phone.system import build_phone_tools
from agent.tools.filesystem.archive import build_archive_tools


def _safe_path(value: str) -> Path:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (Path.home() / p).resolve()
    else:
        p = p.resolve()
    return p


def build_tools(store: MemoryStore):
    def list_files(a):
        p = _safe_path(a.get("path", "."))
        if not p.exists() or not p.is_dir():
            raise FileNotFoundError(str(p))
        return [{"name": x.name, "directory": x.is_dir(), "size": x.stat().st_size if x.is_file() else None} for x in list(p.iterdir())[:500]]

    def read_file(a):
        p = _safe_path(a["path"])
        if not p.is_file():
            raise FileNotFoundError(str(p))
        return p.read_text(encoding="utf-8", errors="replace")[:100000]

    def write_file(a):
        p = _safe_path(a["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(a["content"]), encoding="utf-8")
        return f"written: {p}"

    def delete_file(a):
        p = _safe_path(a["path"])
        if p.is_dir():
            raise IsADirectoryError("delete_file accepts files only")
        p.unlink()
        return f"deleted: {p}"

    def terminal(a):
        command = str(a["command"]).strip()
        if not command:
            return "empty command"
        timeout = min(max(int(a.get("timeout", 30)), 1), 120)
        cp = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return (cp.stdout + ("\n" if cp.stderr else "") + cp.stderr)[-16000:]

    def memory_search(a):
        return store.search(str(a.get("query", "")), int(a.get("limit", 10)))

    def memory_save(a):
        content = str(a.get("content", "")).strip()
        if not content:
            raise ValueError("content is required")
        store.save(str(a.get("kind", "note")), content)
        return "memory_saved"

    tools = {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
        "delete_file": delete_file,
        "terminal": terminal,
        "memory_search": memory_search,
        "memory_save": memory_save,
    }
    tools.update(build_wifi_tools())
    tools.update(build_wifite_tools())
    tools.update(build_phone_tools())
    tools.update(build_archive_tools())
    return tools
