from __future__ import annotations

import asyncio
import re
import threading
import time
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from core.agent import Agent
from core.config import config
from core.errors import ConfigurationError, ProviderError
from core.logger import get_logger
from core.security import constant_time_eq, redact
from interfaces.telegram import telegram_client
from providers.registry import list_providers
from tools.registry import tool_specs

log = get_logger("api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await telegram_client.configure_webhook()
    except Exception:
        log.exception("Telegram webhook configuration failed")
    yield


app = FastAPI(title="MyChatBot API", version="0.4.0", lifespan=lifespan)
_agents: dict[str, Agent] = {}
_agent_locks: dict[str, asyncio.Lock] = {}
_agents_lock = threading.RLock()
_SESSION_RE = re.compile(r"^[A-Za-z0-9:_-]{1,100}$")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    session: str = Field(default="mobile", min_length=1, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=200)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value

    @field_validator("session")
    @classmethod
    def validate_session(cls, value: str) -> str:
        value = value.strip()
        if not _SESSION_RE.fullmatch(value):
            raise ValueError("session contains unsupported characters")
        return value

    @field_validator("provider", "model")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None


class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            if len(self._hits) > 2048:
                stale = [k for k, q in self._hits.items() if not q or now - q[-1] >= self.window_seconds]
                for key_to_remove in stale[:512]:
                    self._hits.pop(key_to_remove, None)
            return True


_rate_limiter = RateLimiter()


def _auth(authorization: str | None) -> None:
    if not config.api_token:
        raise HTTPException(status_code=503, detail="API_TOKEN is not configured")
    token = (authorization or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or not constant_time_eq(token, config.api_token):
        raise HTTPException(status_code=401, detail="unauthorized")


def _rate_limit_key(body: ChatIn, request: Request) -> str:
    source = request.client.host if request.client else "unknown"
    if config.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        source = forwarded or source
    return f"{source}:{body.session}"


def _agent_key(body: ChatIn) -> str:
    return f"{body.session}:{body.provider or ''}:{body.model or ''}"


def _get_agent(body: ChatIn) -> Agent:
    key = _agent_key(body)
    with _agents_lock:
        agent = _agents.get(key)
        if agent is None:
            if len(_agents) >= 128:
                oldest_key = next(iter(_agents))
                oldest = _agents.pop(oldest_key)
                oldest.memory.close()
                _agent_locks.pop(oldest_key, None)
            agent = Agent(body.session, body.provider, body.model, tool_profile=config.api_tool_profile)
            _agents[key] = agent
        return agent


def _get_agent_lock(key: str) -> asyncio.Lock:
    with _agents_lock:
        return _agent_locks.setdefault(key, asyncio.Lock())


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "providers": list_providers(),
        "api_auth_configured": bool(config.api_token),
        "tool_profile": config.api_tool_profile,
        "telegram_configured": telegram_client.enabled,
    }


@app.get("/tools")
def tools(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"tools": tool_specs(config.api_tool_profile)}


@app.post("/telegram/webhook")
async def telegram_webhook(
    update: dict,
    telegram_secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
):
    expected = telegram_client.webhook_secret
    if not expected or not telegram_secret or not constant_time_eq(telegram_secret, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    if not telegram_client.enabled:
        raise HTTPException(status_code=503, detail="Telegram integration is not configured")
    asyncio.create_task(telegram_client.handle_update(update))
    return {"ok": True}


@app.post("/chat")
async def chat(body: ChatIn, request: Request, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not _rate_limiter.allow(_rate_limit_key(body, request)):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    key = _agent_key(body)
    agent = _get_agent(body)
    async with _get_agent_lock(key):
        try:
            answer = await agent.ask(body.message)
        except ConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ProviderError as exc:
            log.warning("provider error: %s", exc.code)
            raise HTTPException(status_code=502, detail=redact(exc.message)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            log.exception("unhandled chat error")
            raise HTTPException(status_code=500, detail="internal server error") from exc
    return {"reply": answer, "session": body.session}


@app.get("/history/{session}")
def history(session: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    session = session.strip()
    if not _SESSION_RE.fullmatch(session):
        raise HTTPException(status_code=400, detail="invalid session")
    body = ChatIn(message="history", session=session)
    agent = _get_agent(body)
    return {"messages": [m.to_dict() for m in agent.memory.history(session, 50)]}
