"""Compatibility facade for the unified conversational agent.

The implementation remains in :mod:`core.agent_impl`; this facade preserves
stable public hooks for legacy callers/tests and normalizes user-facing
identity for every interface without duplicating orchestration logic.
"""

import re
from typing import Any

from core.agent_impl import SYSTEM_PROMPT as _BASE_SYSTEM_PROMPT
from core.agent_impl import TOOL_PLANNER_PROMPT
from core.agent_impl import Agent as _Agent
from tools.registry import run_tool

_NAME_QUERY = re.compile(
    r"(?:اسم|نام)\s*(?:من\s*)?(?:چی|چه|کدام|کدوم)\s*(?:بود|هست|است)?\s*[؟?]?$"
    r"|(?:what(?:'s| is)\s+my\s+name|what\s+was\s+my\s+name)\s*[?]?$",
    re.I,
)

TEAM_IDENTITY = "تیم ربات‌های سازنده @فکر کن"
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT.replace("تیم سازنده: افکاران", f"تیم سازنده: {TEAM_IDENTITY}")


class Agent(_Agent):
    """Stable public Agent facade with legacy hooks preserved."""

    def _remember_from_message(self, user_input: str) -> None:
        # A recall question must never overwrite the stored name fact.
        if _NAME_QUERY.search(user_input.strip()):
            return
        super()._remember_from_message(user_input)

    def _system(self, user_input: str, extra: str | None = None) -> dict[str, str]:
        message = super()._system(user_input, extra)
        message["content"] = message["content"].replace("تیم سازنده: افکاران", f"تیم سازنده: {TEAM_IDENTITY}")
        return message

    def _identity_response(self, text: str) -> str | None:
        response = super()._identity_response(text)
        if response is None:
            return None
        if "سازنده MyChatBot" in response:
            return (
                "سازنده MyChatBot حاجی احمد صالحی است و تیم سازنده آن "
                f"{TEAM_IDENTITY} است. موضوعات کلیدی پروژه شامل هوش مصنوعی گفت‌وگویی یکپارچه، "
                "Web Research، Memory، Telegram/API، Android/Termux، Wi‑Fi diagnostics قانونی و Server/Render diagnostics و امنیت است."
            )
        return response

    @staticmethod
    def _needs_tool_planner(text: str) -> bool:
        """Avoid a second model call for ordinary conversation.

        Tool planning is only worthwhile when the user's wording clearly asks
        for live data, diagnostics, a URL/page analysis, or another tool-like
        operation. This preserves tool support while keeping normal chat fast.
        """
        lowered = text.lower().strip()
        if not lowered:
            return False
        signals = (
            "http://", "https://", "www.",
            "آخرین", "جدیدترین", "اخبار", "قیمت", "وضعیت فعلی", "تحقیق", "جستجو", "پیدا کن",
            "وب", "لینک", "صفحه", "سرور", "backend", "render", "diagnostic", "diagnostics",
            "وای فای", "wifi", "اینترنت", "dns", "پینگ", "ping", "ip", "شبکه", "باتری",
            "دستگاه", "filesystem", "runtime", "نسخه", "server",
        )
        return any(signal in lowered for signal in signals)

    async def _plan_tool(self, text: str) -> dict[str, Any] | None:
        if not self._needs_tool_planner(text):
            return None
        return await super()._plan_tool(text)

    async def _run_internal_tool(self, plan: dict[str, Any]) -> str:
        # Delegate to canonical implementation so profile/session/resource
        # policy remains identical across Telegram, API, CLI and Web.
        return await super()._run_internal_tool(plan)


__all__ = ["Agent", "SYSTEM_PROMPT", "TOOL_PLANNER_PROMPT", "TEAM_IDENTITY", "run_tool"]
