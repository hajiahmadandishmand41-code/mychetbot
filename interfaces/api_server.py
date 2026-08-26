from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from core.agent import Agent
from core.config import config
from core.errors import ConfigurationError, ProviderError
from core.security import constant_time_eq, redact
from providers.registry import list_providers
from tools.registry import tool_specs

app = FastAPI(title="MyChatBot API", version="0.2.0")
_agents: dict[str, Agent] = {}


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    session: str = Field(default="mobile", min_length=1, max_length=100)
    provider: str | None = None
    model: str | None = None


def _auth(authorization: str | None) -> None:
    if not config.api_token:
        raise HTTPException(status_code=503, detail="API_TOKEN is not configured")
    token = (authorization or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or not constant_time_eq(token, config.api_token):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "providers": list_providers(),
        "api_auth_configured": bool(config.api_token),
    }


@app.get("/tools")
def tools(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"tools": tool_specs()}


@app.post("/chat")
async def chat(body: ChatIn, authorization: str | None = Header(default=None)):
    _auth(authorization)
    key = f"{body.session}:{body.provider}:{body.model}"
    agent = _agents.setdefault(key, Agent(body.session, body.provider, body.model))
    try:
        answer = await agent.ask(body.message)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=redact(exc.message)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="internal server error") from exc
    return {"reply": answer, "session": body.session}


@app.get("/history/{session}")
def history(session: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    agent = _agents.setdefault(session, Agent(session))
    return {"messages": [m.to_dict() for m in agent.memory.history(session, 50)]}
