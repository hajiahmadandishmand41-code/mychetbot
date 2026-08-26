import json

import pytest

from core.agent import Agent
from core.config import config


@pytest.fixture
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "data_dir", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_creator_identity_uses_afkaran_and_key_topics(isolated_memory):
    agent = Agent(session="creator")
    answer = await agent.ask("سازنده و تیم شما کیست؟")
    assert "حاجی احمد صالحی" in answer
    assert "افکاران" in answer
    for topic in ("Web Research", "Memory", "Telegram/API", "Android/Termux", "Wi‑Fi", "Server/Render"):
        assert topic in answer
    agent.memory.close()


@pytest.mark.asyncio
async def test_topic_question_selects_web_search(monkeypatch, isolated_memory):
    monkeypatch.setattr(config, "tool_profile", "local")
    agent = Agent(session="web-topic")
    calls = []

    async def fake_complete(messages, **kwargs):
        calls.append(messages)
        if len(calls) == 1:
            return {"content": json.dumps({"tool": "web_search", "args": {"query": "آخرین اطلاعات درباره X"}})}
        return {"content": "بر اساس منابع عمومی دریافت‌شده، پاسخ تهیه شد."}

    async def fake_run(plan):
        assert plan["tool"] == "web_search"
        assert plan["args"]["query"] == "آخرین اطلاعات درباره X"
        return json.dumps({"status": "success", "data": {"results": [{"page": {"title": "X", "text": "Public data"}}]}}, ensure_ascii=False)

    monkeypatch.setattr(agent.router, "complete", fake_complete)
    monkeypatch.setattr(agent, "_run_internal_tool", fake_run)

    answer = await agent.ask("آخرین اطلاعات درباره X را پیدا کن")
    assert "پاسخ" in answer
    assert len(calls) == 2
    agent.memory.close()


@pytest.mark.asyncio
async def test_agent_tool_execution_preserves_session(monkeypatch, isolated_memory):
    agent = Agent(session="tg:12345")
    captured = {}

    def fake_run_tool(name, args, profile, session):
        captured.update(name=name, args=args, profile=profile, session=session)
        return json.dumps({"status": "success", "data": {"ok": True}}, ensure_ascii=False)

    monkeypatch.setattr("core.agent_impl.run_tool", fake_run_tool)
    monkeypatch.setattr(config, "tool_profile", "local")

    result = await agent._run_internal_tool({"tool": "local_ip", "args": {}})
    assert json.loads(result)["status"] == "success"
    assert captured["session"] == "tg:12345"
    agent.memory.close()
