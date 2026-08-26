"""Safe baseline tools for files and Termux. Sensitive operations require confirmation."""
import subprocess
from pathlib import Path
from agent.memory.store import MemoryStore


def build_tools(store: MemoryStore):
    def list_files(a):
        p = Path(a.get("path", ".")).expanduser()
        return [x.name for x in p.iterdir()][:200]

    def read_file(a):
        p = Path(a["path"]).expanduser()
        return p.read_text(encoding="utf-8")[:50000]

    def write_file(a):
        p = Path(a["path"]).expanduser(); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(a["content"], encoding="utf-8")
        return f"written: {p}"

    def delete_file(a):
        p = Path(a["path"]).expanduser(); p.unlink()
        return f"deleted: {p}"

    def terminal(a):
        command = a["command"]
        cp = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=min(int(a.get("timeout", 30)), 120))
        return (cp.stdout + cp.stderr)[-12000:]

    return {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
        "delete_file": delete_file,
        "terminal": terminal,
    }
