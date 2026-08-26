from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from core.agent import Agent
from core.config import config
from core.security import constant_time_eq
from providers.registry import list_providers
from tools.registry import tool_specs

app = FastAPI(title="MyChatBot API", version="0.1.0")
_agents: dict[str, Agent] = {}

class ChatIn(BaseModel):
    message: str
    session: str = "mobile"
    provider: str | None = None
    model: str | None = None

def _auth(token: str | None) -> None:
    if not token or not constant_time_eq(token.replace("Bearer ", ""), config.api_token):
        raise HTTPException(status_code=401, detail="unauthorized")

@app.get("/health")
def health():
    return {"status": "ok", "providers": list_providers()}

@app.get("/tools")
def tools(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"tools": tool_specs()}

@app.post("/chat")
async def chat(body: ChatIn, authorization: str | None = Header(default=None)):
    _auth(authorization)
    key = f"{body.session}:{body.provider}:{body.model}"
    agent = _agents.setdefault(key, Agent(body.session, body.provider, body.model))
    answer = await agent.ask(body.message)
    return {"reply": answer, "session": body.session}

@app.get("/history/{session}")
def history(session: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    agent = _agents.setdefault(session, Agent(session))
    return {"messages": [m.to_dict() for m in agent.memory.history(session, 50)]}
