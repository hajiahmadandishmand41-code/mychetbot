from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from core.config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'tool')),
  content TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS facts (
  session TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  ts REAL NOT NULL,
  PRIMARY KEY (session, key)
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session);
"""


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    ts: float = 0.0

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class Memory:
    """SQLite-backed memory with locking, WAL and session-isolated facts."""

    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(config.data_dir, "memory.db")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=5.0)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._lock = threading.RLock()

    def add(self, session: str, role: str, content: str) -> None:
        if not session:
            raise ValueError("session must not be empty")
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError(f"unsupported role: {role}")
        with self._lock:
            self.conn.execute(
                "INSERT INTO messages(session, role, content, ts) VALUES (?,?,?,?)",
                (session, role, content, time.time()),
            )
            self.conn.commit()

    def history(self, session: str, limit: int = 20) -> list[Message]:
        safe_limit = max(1, min(int(limit), 500))
        with self._lock:
            rows = self.conn.execute(
                "SELECT role, content, ts FROM messages WHERE session=? ORDER BY id DESC LIMIT ?",
                (session, safe_limit),
            ).fetchall()
        return [Message(r[0], r[1], r[2]) for r in reversed(rows)]

    def remember(self, key: str, value: str, session: str = "default") -> None:
        if not session or not key:
            raise ValueError("session and key must not be empty")
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO facts(session, key, value, ts) VALUES (?,?,?,?)",
                (session, key, value, time.time()),
            )
            self.conn.commit()

    def recall(self, key: str, session: str = "default") -> str | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT value FROM facts WHERE session=? AND key=?",
                (session, key),
            ).fetchone()
        return row[0] if row else None

    def all_facts(self, session: str = "default") -> dict[str, str]:
        with self._lock:
            return {
                k: v
                for k, v in self.conn.execute(
                    "SELECT key, value FROM facts WHERE session=?", (session,)
                )
            }

    def clear(self, session: str) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM messages WHERE session=?", (session,))
            self.conn.execute("DELETE FROM facts WHERE session=?", (session,))
            self.conn.commit()

    def export_jsonl(self, session: str, out_path: str) -> str:
        destination = Path(out_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for message in self.history(session, limit=10_000):
                handle.write(json.dumps(asdict(message), ensure_ascii=False) + "\n")
        return str(destination)

    def close(self) -> None:
        with self._lock:
            self.conn.close()
