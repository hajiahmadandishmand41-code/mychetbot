from __future__ import annotations
import json, os, sqlite3, time
from dataclasses import dataclass, asdict
from core.config import config

SCHEMA = '''
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS facts (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session);
'''

@dataclass
class Message:
    role: str
    content: str
    ts: float = 0.0
    def to_dict(self): return {"role": self.role, "content": self.content}

class Memory:
    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(config.data_dir, "memory.db")
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.executescript(SCHEMA); self.conn.commit()

    def add(self, session: str, role: str, content: str) -> None:
        self.conn.execute("INSERT INTO messages(session, role, content, ts) VALUES (?,?,?,?)",
                          (session, role, content, time.time()))
        self.conn.commit()

    def history(self, session: str, limit: int = 20) -> list[Message]:
        rows = self.conn.execute(
            "SELECT role, content, ts FROM messages WHERE session=? ORDER BY id DESC LIMIT ?",
            (session, limit)).fetchall()
        return [Message(r[0], r[1], r[2]) for r in reversed(rows)]

    def remember(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO facts(key, value, ts) VALUES (?,?,?)",
                          (key, value, time.time()))
        self.conn.commit()

    def recall(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def all_facts(self) -> dict[str, str]:
        return {k: v for k, v in self.conn.execute("SELECT key, value FROM facts")}

    def clear(self, session: str) -> None:
        self.conn.execute("DELETE FROM messages WHERE session=?", (session,))
        self.conn.commit()

    def export_jsonl(self, session: str, out_path: str) -> str:
        with open(out_path, "w", encoding="utf-8") as f:
            for m in self.history(session, limit=10_000):
                f.write(json.dumps(asdict(m), ensure_ascii=False) + "\n")
        return out_path
