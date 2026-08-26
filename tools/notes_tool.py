from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from core.memory import Memory

_mem = Memory()
_current_session: ContextVar[str] = ContextVar("mychatbot_session", default="default")


@contextmanager
def session_context(session: str):
    token = _current_session.set(session or "default")
    try:
        yield
    finally:
        _current_session.reset(token)


def remember(key: str, value: str) -> str:
    _mem.remember(key, value, session=_current_session.get())
    return f"ذخیره شد: {key}"


def recall(key: str) -> str:
    return _mem.recall(key, session=_current_session.get()) or "(چیزی یافت نشد)"


def list_facts() -> str:
    facts = _mem.all_facts(session=_current_session.get())
    return "\n".join(f"{k}: {v}" for k, v in facts.items()) or "(خالی)"
