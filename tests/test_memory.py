import os, tempfile
from core.memory import Memory

def test_history_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        m = Memory(os.path.join(d, "t.db"))
        m.add("s", "user", "سلام")
        m.add("s", "assistant", "درود")
        h = m.history("s")
        assert [x.role for x in h] == ["user", "assistant"]
        assert h[0].content == "سلام"

def test_facts():
    with tempfile.TemporaryDirectory() as d:
        m = Memory(os.path.join(d, "t.db"))
        m.remember("name", "Ahmad")
        assert m.recall("name") == "Ahmad"
        assert m.all_facts()["name"] == "Ahmad"
