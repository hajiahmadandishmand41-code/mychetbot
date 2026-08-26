"""Local bridge server for Flutter/Android <-> Termux agent."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.core.agent import Agent
from agent.memory.store import MemoryStore
from agent.tools.builtin import build_tools
from agent.tools.registry import Tool, ToolRegistry

app = FastAPI(title="MyChatBot Bridge", version="0.1.0")
store = MemoryStore(os.getenv("MYCHATBOT_DATA", "runtime"))
registry = ToolRegistry()
handlers = build_tools(store)
for name, fn in handlers.items():
    registry.register(Tool(name, f"MyChatBot {name} tool", {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "command": {"type": "string"}, "timeout": {"type": "integer"}}}, fn))
agent = Agent(registry, store)


class ChatRequest(BaseModel):
    message: str
    provider: str | None = None
    model: str | None = None
    history: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok", "provider": os.getenv("AI_PROVIDER", "openai"), "model": os.getenv("AI_MODEL", "gpt-5.6-luna")}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        return agent.run(req.message, req.provider, req.model, req.history)
    except KeyError as exc:
        raise HTTPException(503, f"Missing configuration: {exc}")
    except Exception as exc:
        raise HTTPException(500, str(exc))
