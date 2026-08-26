"""Compatibility facade for the unified conversational agent.

The implementation remains in :mod:`core.agent_impl`; this facade preserves
stable public hooks for legacy callers/tests without removing any capability.
"""

import json
import re
from typing import Any

from core.agent_impl import SYSTEM_PROMPT, TOOL_PLANNER_PROMPT
from core.agent_impl import Agent as _Agent
from tools.registry import run_tool

_NAME_QUERY = re.compile(
    r"(?:اسم|نام)\s*(?:من\s*)?(?:چی|چه|کدام|کدوم)\s*(?:بود|هست|است)?\s*[؟?]?$"
    r"|(?:what(?:'s| is)\s+my\s+name|what\s+was\s+my\s+name)\s*[?]?$",
    re.I,
)


class Agent(_Agent):
    """Stable public Agent facade with legacy hooks preserved."""

    def _remember_from_message(self, user_input: str) -> None:
        # A recall question must never overwrite the stored name fact.
        if _NAME_QUERY.search(user_input.strip()):
            return
        super()._remember_from_message(user_input)

    async def _run_internal_tool(self, plan: dict[str, Any]) -> str:
        tool = plan["tool"]
        # Preserve the per-chat session so server_execute and future scoped tools
        # cannot accidentally lose Telegram/API permission isolation.
        result = await self._run_tool_with_timeout(
            tool,
            plan.get("args", {}),
            run_tool,
        )
        self.memory.add(
            self.session,
            "tool",
            json.dumps({"tool": tool, "result": result}, ensure_ascii=False),
        )
        return result

    async def _run_tool_with_timeout(self, tool: str, args: dict[str, Any], runner) -> str:
        # Delegate to the canonical orchestrator implementation while retaining
        # this compatibility hook. The implementation has already validated the
        # tool, profile, session and resource limits.
        return await super()._run_internal_tool({"tool": tool, "args": args})


__all__ = ["Agent", "SYSTEM_PROMPT", "TOOL_PLANNER_PROMPT", "run_tool"]
