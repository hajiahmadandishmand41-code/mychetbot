import pytest
from core.agent import Agent

def test_extract_tool_call():
    txt = 'باشه {"tool": "ping", "args": {"host": "8.8.8.8"}}'
    call = Agent._extract_tool_call(txt)
    assert call["tool"] == "ping"

def test_no_tool_call():
    assert Agent._extract_tool_call("سلام دنیا") is None

@pytest.mark.asyncio
async def test_agent_plain_reply(monkeypatch, tmp_path):
    a = Agent(session="t")
    async def fake(messages, **kw):
        return {"provider": "mock", "model": "m", "content": "پاسخ تستی"}
    monkeypatch.setattr(a.router, "complete", fake)
    assert await a.ask("سلام") == "پاسخ تستی"
