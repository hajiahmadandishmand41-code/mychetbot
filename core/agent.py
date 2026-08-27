"""Compatibility facade for the unified conversational agent.

The implementation remains in :mod:`core.agent_impl`; this facade preserves
stable public hooks for legacy callers/tests and normalizes user-facing
identity for every interface.
"""

import json
import re
from typing import Any

from core.agent_impl import SYSTEM_PROMPT as _BASE_SYSTEM_PROMPT
from core.agent_impl import TOOL_PLANNER_PROMPT
from core.agent_impl import Agent as _Agent
from tools.registry import TOOLS, run_tool

_NAME_QUERY = re.compile(
    r"(?:اسم|نام)\s*(?:من\s*)?(?:چی|چه|کدام|کدوم)\s*(?:بود|هست|است)?\s*[؟?]?$"
    r"|(?:what(?:'s| is)\s+my\s+name|what\s+was\s+my\s+name)\s*[?]?$",
    re.I,
)
_SELF_QUERY = re.compile(
    r"(?:درباره|راجع(?:‌به| به)|معرفی)\s+(?:خودت|خودت رو|خودت را|ربات|بات|هوشان|این ربات)"
    r"|(?:کی|چی|چه)\s+هستی(?:؟|\?)?"
    r"|(?:خودت|ربات|بات)\s+(?:را|رو)?\s*(?:معرفی|توضیح|بگو)"
    r"|what\s+(?:are|is)\s+hooshan|tell me about (?:hooshan|yourself)",
    re.I,
)

TEAM_IDENTITY = "تیم اندیشه فردا"
ASSISTANT_NAME = "هوشان"
CREATOR_NAME = "حاجی احمد صالحی"
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT

HOOSHAN_PROFILE = (
    "نام من «هوشان» است؛ یک دستیار هوشمند گفت‌وگویی و جستجوگر اطلاعات. "
    "هوشان برای گفتگو، تحقیق و جستجوی اطلاعات روز، تحلیل منابع عمومی وب، خلاصه‌سازی، "
    "پاسخ‌گویی فارسی و دری، و کمک در برنامه‌نویسی و مسائل فنی طراحی شده است. "
    f"سازنده و بنیان‌گذار این پروژه {CREATOR_NAME} است و این پروژه با {TEAM_IDENTITY} شناخته می‌شود. "
    "حاجی احمد صالحی در معرفی این پروژه به‌عنوان سخنران حوزه موفقیت، برنامه‌نویس و فعال در زمینه‌های گوناگون فنی و آموزشی معرفی می‌شود. "
    "هوشان باید در موضوعات وابسته به زمان، اخبار، قیمت‌ها و اطلاعات بیرونی ابتدا از ابزار جستجوی وب استفاده کند؛ "
    "اگر جستجو در دسترس نباشد، محدودیت را صادقانه اعلام می‌کند و چیزی را جعل نمی‌کند. "
    "نام Provider یا مدل پشت‌صحنه هویت هوشان نیست و در پاسخ‌های عادی درباره خودش مطرح نمی‌شود."
)


class Agent(_Agent):
    """Stable public Agent facade with fast intent routing and Hooshan identity."""

    def _remember_from_message(self, user_input: str) -> None:
        if _NAME_QUERY.search(user_input.strip()):
            return
        super()._remember_from_message(user_input)

    def _system(self, user_input: str, extra: str | None = None) -> dict[str, str]:
        message = super()._system(user_input, extra)
        message["content"] = message["content"].replace("MyChatBot", ASSISTANT_NAME)
        message["content"] += "\n\nهویت کاربر-facing: نام دستیار «هوشان» است. تیم پروژه: «اندیشه فردا»."
        return message

    def _identity_response(self, text: str) -> str | None:
        normalized = text.strip()
        if _SELF_QUERY.search(normalized):
            return HOOSHAN_PROFILE
        response = super()._identity_response(normalized)
        if response is None:
            return None
        # Never expose provider/model identity as the assistant identity.
        if "MyChatBot" in response or "مدل" in response or "هوش" in normalized.lower():
            return HOOSHAN_PROFILE
        return response

    @staticmethod
    def _needs_tool_planner(text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False
        signals = (
            "http://", "https://", "www.",
            "آخرین", "جدیدترین", "اخبار", "خبر", "قیمت", "قیمت امروز", "وضعیت فعلی",
            "تحقیق", "جستجو", "جست‌وجو", "پیدا کن", "پیدا کن از اینترنت", "اینترنت", "آنلاین",
            "وب", "روی وب", "از وب", "منبع", "منابع", "اطلاعات تازه", "اطلاعات روز", "اطلاعات فعلی",
            "بررسی کن", "بررسی آنلاین",
            "لینک", "صفحه", "سرور", "backend", "render", "diagnostic", "diagnostics",
            "وای فای", "wifi", "اینترنت", "dns", "پینگ", "ping", "ip", "شبکه", "باتری",
            "دستگاه", "filesystem", "runtime", "نسخه", "server",
        )
        return any(signal in lowered for signal in signals)

    @staticmethod
    def _fast_tool_plan(text: str) -> dict[str, Any] | None:
        """Choose safe, obvious tools without an extra LLM round-trip."""
        lowered = text.lower().strip()
        if not lowered:
            return None

        urls = re.findall(r"https?://\S+", text)
        if len(urls) == 1:
            return {"tool": "web_research", "args": {"url": urls[0].rstrip(".,!?)]}")}}
        if 2 <= len(urls) <= 5:
            return {"tool": "web_compare", "args": {"urls_json": json.dumps(urls, ensure_ascii=False)}}

        search_markers = (
            "آخرین", "جدیدترین", "اخبار", "خبر", "قیمت", "قیمت امروز", "تحقیق", "جستجو", "جست‌وجو",
            "پیدا کن", "روی وب", "از وب", "از اینترنت", "اینترنت", "آنلاین", "اطلاعات فعلی",
            "اطلاعات تازه", "اطلاعات روز", "وضعیت فعلی", "منبع", "منابع", "بررسی آنلاین",
        )
        if any(marker in lowered for marker in search_markers):
            return {"tool": "web_search", "args": {"query": text}}

        exact_tools = (
            (("وضعیت وای فای", "اطلاعات وای فای", "wifi info", "wi-fi info"), "wifi_info"),
            (("شبکه‌های اطراف", "شبکه های اطراف", "اسکن وای فای", "wifi scan"), "wifi_scan"),
            (("تشخیص اتصال", "تشخیص اینترنت", "wifi diagnostics"), "wifi_diagnostics"),
            (("گزارش امنیتی وای فای", "wifi security"), "wifi_security_report"),
            (("وضعیت باتری", "battery"), "battery"),
            (("آی‌پی محلی", "ip محلی", "local ip"), "local_ip"),
        )
        for markers, tool in exact_tools:
            if any(marker in lowered for marker in markers):
                return {"tool": tool, "args": {}}
        return None

    async def _plan_tool(self, text: str) -> dict[str, Any] | None:
        fast_plan = self._fast_tool_plan(text)
        if fast_plan:
            tool = fast_plan["tool"]
            meta = TOOLS.get(tool)
            if meta and meta.available_in(self._tool_profile()) and not meta.dangerous and meta.auto_selectable:
                if not (set(fast_plan["args"]) - set(meta.args)):
                    return fast_plan
        if not self._needs_tool_planner(text):
            return None
        return await super()._plan_tool(text)

    def _tool_profile(self) -> str:
        from core.config import config
        return config.tool_profile

    async def _run_internal_tool(self, plan: dict[str, Any]) -> str:
        return await super()._run_internal_tool(plan)


__all__ = ["Agent", "SYSTEM_PROMPT", "TOOL_PLANNER_PROMPT", "TEAM_IDENTITY", "run_tool"]
