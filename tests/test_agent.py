import os

import pytest

from core.agent import Agent
from core.config import config
from core.memory import Memory


@pytest.fixture
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "data_dir", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_agent_plain_reply(monkeypatch, isolated_memory):
    a = Agent(session="t")

    async def fake(messages, **kw):
        assert messages[0]["role"] == "system"
        assert "MyChatBot" in messages[0]["content"]
        return {"content": "پاسخ تستی"}

    monkeypatch.setattr(a.router, "complete", fake)
    assert await a.ask("سلام") == "پاسخ تستی"
    assert a.memory.history("t")[-1].content == "پاسخ تستی"
    a.memory.close()


@pytest.mark.asyncio
async def test_automatic_name_memory_and_recall(monkeypatch, isolated_memory):
    a = Agent(session="user-a")
    captured = []

    async def fake(messages, **kw):
        captured.append(messages)
        return {"content": "باشه."}

    monkeypatch.setattr(a.router, "complete", fake)
    await a.ask("اسم من احمد است")
    assert a.memory.recall("name", "user-a") == "احمد"
    await a.ask("اسم من چی بود؟")
    system_text = captured[-1][0]["content"]
    assert "name: احمد" in system_text
    a.memory.close()


@pytest.mark.asyncio
async def test_identity_prompt_forbids_provider_identity(monkeypatch, isolated_memory):
    a = Agent(session="identity")
    captured = []

    async def fake(messages, **kw):
        captured.extend(messages)
        return {"content": "من MyChatBot هستم؛ یک دستیار هوشمند گفت‌وگویی هستم."}

    monkeypatch.setattr(a.router, "complete", fake)
    answer = await a.ask("تو چه مدلی هستی؟")
    assert "MyChatBot" in answer
    system_text = captured[0]["content"]
    assert "Provider" in system_text
    assert "هویت" in system_text
    a.memory.close()


def test_memory_persists_after_restart(tmp_path):
    path = os.path.join(tmp_path, "memory.db")
    first = Memory(path)
    first.remember("name", "احمد", "persistent")
    first.add("persistent", "user", "سلام")
    first.close()
    second = Memory(path)
    assert second.recall("name", "persistent") == "احمد"
    assert second.history("persistent")[0].content == "سلام"
    second.close()


def test_sessions_are_isolated(tmp_path):
    memory = Memory(os.path.join(tmp_path, "memory.db"))
    memory.remember("name", "احمد", "a")
    memory.remember("name", "علی", "b")
    assert memory.recall("name", "a") == "احمد"
    assert memory.recall("name", "b") == "علی"
    memory.close()
