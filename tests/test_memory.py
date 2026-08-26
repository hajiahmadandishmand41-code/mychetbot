import os

from core.config import config
from core.memory import Memory


def test_memory_persists_and_is_session_isolated(tmp_path):
    path = os.path.join(tmp_path, "memory.db")
    first = Memory(path)
    first.remember("name", "احمد", "a")
    first.remember("name", "علی", "b")
    first.add("a", "user", "سلام")
    first.close()

    second = Memory(path)
    assert second.recall("name", "a") == "احمد"
    assert second.recall("name", "b") == "علی"
    assert second.history("a")[0].content == "سلام"
    assert second.history("b") == []
    second.close()


def test_memory_message_growth_is_bounded(tmp_path, monkeypatch):
    path = os.path.join(tmp_path, "memory.db")
    monkeypatch.setattr(config, "memory_max_messages", 3)
    memory = Memory(path)
    for index in range(6):
        memory.add("bounded", "user", f"message-{index}")
    assert len(memory.history("bounded", 20)) == 3
    assert memory.history("bounded", 20)[0].content == "message-3"
    memory.close()
