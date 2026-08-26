"""Extensible tool registry. Tools declare whether they are read-only or sensitive."""
from dataclasses import dataclass
from typing import Callable, Any
from agent.core.security import check


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    handler: Callable[[dict], Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def definitions(self) -> list[dict]:
        return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.schema}} for t in self._tools.values()]

    def execute(self, name: str, args: dict, confirmed: bool = False) -> dict:
        tool = self._tools.get(name)
        if not tool:
            return {"ok": False, "error": "unknown_tool"}
        decision = check(name, args)
        if not decision.allowed:
            return {"ok": False, "error": decision.reason}
        if decision.requires_confirmation and not confirmed:
            return {"ok": False, "confirmation_required": True, "reason": decision.reason}
        try:
            return {"ok": True, "result": tool.handler(args)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
