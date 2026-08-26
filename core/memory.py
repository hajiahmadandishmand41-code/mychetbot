from __future__ import annotations

import json
import os
import re
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
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session, id);
CREATE INDEX IF NOT EXISTS idx_facts_session ON facts(session);
"""

_STOPWORDS = frozenset("و در از به که این آن برای با را یک می شود است هست یا ولی اگر چه من تو شما ما او هم خیلی فقط درباره چگونه چرا چی چطور the and for with this that is are was were a an to of in on".split())
_TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    ts: float = 0.0

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class Memory:
    """SQLite-backed persistent memory with isolated sessions and relevance retrieval."""

    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(config.data_dir, "memory.db")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._lock = threading.RLock()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1 and t.lower() not in _STOPWORDS}

    def add(self, session: str, role: str, content: str) -> None:
        if not session:
            raise ValueError("session must not be empty")
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError(f"unsupported role: {role}")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must not be empty")
        with self._lock:
            self.conn.execute(
                "INSERT INTO messages(session, role, content, ts) VALUES (?,?,?,?)",
                (session, role, content, time.time()),
            )
            self.conn.commit()

    def recent_history(self, session: str, limit: int = 12) -> list[dict[str, str]]:
        return [m.to_dict() for m in self.history(session, limit=limit)]

    def history(self, session: str, limit: int = 20) -> list[Message]:
        safe_limit = max(1, min(int(limit), 500))
        with self._lock:
            rows = self.conn.execute(
                "SELECT role, content, ts FROM messages WHERE session=? ORDER BY id DESC LIMIT ?",
                (session, safe_limit),
            ).fetchall()
        return [Message(r[0], r[1], r[2]) for r in reversed(rows)]

    def relevant_context(self, session: str, query: str, max_messages: int = 8, candidate_limit: int = 80) -> list[dict[str, str]]:
        """Return recent/semantically overlapping messages without growing the prompt indefinitely."""
        max_messages = max(0, min(int(max_messages), 20))
        candidate_limit = max(10, min(int(candidate_limit), 200))
        if max_messages == 0:
            return []
        query_tokens = self._tokens(query)
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, role, content FROM messages WHERE session=? ORDER BY id DESC LIMIT ?",
                (session, candidate_limit),
            ).fetchall()
        scored: list[tuple[float, int, str, str]] = []
        for row_id, role, content in rows:
            tokens = self._tokens(content)
            overlap = len(query_tokens & tokens)
            recency = 1.0 / (1.0 + (rows[0][0] - row_id) if rows else 1.0)
            role_bonus = 0.15 if role == "user" else 0.0
            score = overlap * 3.0 + recency + role_bonus
            if overlap > 0:
                scored.append((score, row_id, role, content))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        selected_ids = {item[1] for item in scored[:max_messages]}
        recent = [row for row in rows if row[0] in selected_ids]
        recent.sort(key=lambda r: r[0])
        return [{"role": role, "content": content} for _, role, content in recent]

    def remember(self, key: str, value: str, session: str = "default") -> None:
        key = key.strip()
        value = value.strip()
        if not session or not key or not value:
            raise ValueError("session, key and value must not be empty")
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO facts(session, key, value, ts) VALUES (?,?,?,?)",
                (session, key, value[:500], time.time()),
            )
            self.conn.commit()

    def forget(self, key: str, session: str = "default") -> None:
        with self._lock:
            self.conn.execute("DELETE FROM facts WHERE session=? AND key=?", (session, key))
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
                    "SELECT key, value FROM facts WHERE session=? ORDER BY ts DESC", (session,)
                )
            }

    def relevant_facts(self, session: str, query: str, max_facts: int = 12) -> dict[str, str]:
        max_facts = max(0, min(int(max_facts), 50))
        facts = self.all_facts(session)
        if max_facts == 0 or not facts:
            return {}
        query_tokens = self._tokens(query)
        scored: list[tuple[float, str, str]] = []
        for key, value in facts.items():
            tokens = self._tokens(f"{key} {value}")
            overlap = len(query_tokens & tokens)
            direct_bonus = 1.5 if key.lower() in {t.lower() for t in query_tokens} else 0.0
            scored.append((overlap * 3.0 + direct_bonus, key, value))
        scored.sort(key=lambda item: item[0], reverse=True)
        # Identity/preferences are always useful context, even when query overlap is zero.
        priority = [key for key in ("name", "response_preference", "language_preference") if key in facts]
        selected: dict[str, str] = {}
        for key in priority:
            if key in facts and len(selected) < max_facts:
                selected[key] = facts[key]
        for _, key, value in scored:
            if key not in selected and len(selected) < max_facts:
                selected[key] = value
        return selected

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
