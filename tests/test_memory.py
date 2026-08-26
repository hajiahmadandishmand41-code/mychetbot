import os
import tempfile

from core.memory import Memory


def test_history_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        m = Memory(os.path.join(d, "t.db"))
        m.add("s", "user", "سلام")
        m.add("s", "assistant", "درود")
        h = m.history("s")
        assert [x.role for x in h] == ["user", "assistant"]
        assert h[0].content == "سلام"
        m.close()


def test_facts_are_session_isolated():
    with tempfile.TemporaryDirectory() as d:
        m = Memory(os.path.join(d, "t.db"))
        m.remember("name", "Ahmad", session="a")
        m.remember("name", "Other", session="b")
        assert m.recall("name", session="a") == "Ahmad"
        assert m.recall("name", session="b") == "Other"
        assert m.all_facts(session="a") == {"name": "Ahmad"}
        m.close()
