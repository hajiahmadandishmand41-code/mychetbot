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
    calls = 0

    async def fake(messages, **kw):
        nonlocal calls
        calls += 1
        assert messages[0]["role"] == "system"
        assert "MyChatBot" in messages[0]["content"]
        return {"content": "پاسخ تستی"}

    monkeypatch.setattr(a.router, "complete", fake)
    assert await a.ask("سلام") == "پاسخ تستی"
    assert calls == 2
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
async def test_remember_language_preference(monkeypatch, isolated_memory):
    a = Agent(session="language-user")

    async def fake(messages, **kw):
        return {"content": "حتماً."}

    monkeypatch.setattr(a.router, "complete", fake)
    await a.ask("یادت باشه من فارسی صحبت می‌کنم")
    assert a.memory.recall("language_preference", "language-user") is not None
    a.memory.close()


@pytest.mark.asyncio
async def test_identity_prompt_forbids_provider_identity(monkeypatch, isolated_memory):
    a = Agent(session="identity")

    async def fake(messages, **kw):
        return {"content": "من MyChatBot هستم؛ یک دستیار هوشمند گفت‌وگویی هستم."}

    monkeypatch.setattr(a.router, "complete", fake)
    answer = await a.ask("تو چه مدلی هستی؟")
    assert "MyChatBot" in answer
    assert "حاجی احمد صالحی" in a._identity_response("سازنده‌ات کیست؟")
    a.memory.close()


@pytest.mark.asyncio
async def test_read_only_tool_is_internal_and_result_enters_context(monkeypatch, isolated_memory):
    monkeypatch.setattr(config, "tool_profile", "device")
    a = Agent(session="tool-user")
    calls = []

    async def fake(messages, **kw):
        calls.append(messages)
        if len(calls) == 1:
            return {"content": '{"tool":"wifi_info","args":{}}'}
        return {"content": "وضعیت اتصال دریافت شد."}

    def fake_tool(name, args, profile="local"):
        assert name == "wifi_info"
        assert args == {}
        assert profile == "device"
        return '{"status":"ok","ssid":"TestWiFi","security":"WPA2"}'

    monkeypatch.setattr(a.router, "complete", fake)
    monkeypatch.setattr("core.agent_impl.run_tool", fake_tool)
    await a.ask("وضعیت Wi-Fi فعلی را بررسی کن")
    assert any(m["role"] == "tool" and "TestWiFi" in m["content"] for m in a.memory.history("tool-user"))
    final_system = calls[-1][0]["content"]
    assert "Internal tool result (wifi_info)" in final_system
    assert "TestWiFi" in final_system
    a.memory.close()


@pytest.mark.asyncio
async def test_disallowed_tool_choice_is_not_executed(monkeypatch, isolated_memory):
    a = Agent(session="safe")
    executed = False

    async def fake(messages, **kw):
        return {"content": '{"tool":"shell","args":{"command":"rm -rf /"}}'}

    def fake_tool(*args, **kwargs):
        nonlocal executed
        executed = True
        return "bad"

    monkeypatch.setattr(a.router, "complete", fake)
    monkeypatch.setattr("core.agent.run_tool", fake_tool)
    answer = await a.ask("این را اجرا کن")
    assert not executed
    assert answer.startswith('{"tool"')
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
