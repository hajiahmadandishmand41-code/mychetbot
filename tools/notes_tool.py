from __future__ import annotations
from core.memory import Memory

_mem = Memory()

def remember(key: str, value: str) -> str:
    _mem.remember(key, value)
    return f"ذخیره شد: {key}"

def recall(key: str) -> str:
    return _mem.recall(key) or "(چیزی یافت نشد)"

def list_facts() -> str:
    facts = _mem.all_facts()
    return "\n".join(f"{k}: {v}" for k, v in facts.items()) or "(خالی)"
