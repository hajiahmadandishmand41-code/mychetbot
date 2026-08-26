"""Small persistent JSONL memory/session store for Termux."""
import json
from pathlib import Path
from datetime import datetime, timezone


class MemoryStore:
    def __init__(self, root: str = "runtime"):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.file = self.root / "memory.jsonl"

    def save(self, kind: str, content: str, metadata: dict | None = None):
        row = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, "content": content, "metadata": metadata or {}}
        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def search(self, query: str, limit: int = 10) -> list[dict]:
        q = query.lower().strip()
        if not q or not self.file.exists():
            return []
        out = []
        for line in reversed(self.file.read_text(encoding="utf-8").splitlines()):
            try:
                row = json.loads(line)
                if q in row.get("content", "").lower():
                    out.append(row)
                    if len(out) >= limit:
                        break
            except json.JSONDecodeError:
                continue
        return out
