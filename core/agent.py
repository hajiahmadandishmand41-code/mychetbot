"""Compatibility facade for the unified conversational agent.

The implementation remains in :mod:`core.agent_impl`; this facade preserves
stable public hooks for legacy callers/tests, normalizes user-facing identity,
and guarantees that internal tool payloads never leak to Telegram/Web users.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

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
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT.replace("MyChatBot", ASSISTANT_NAME).replace("تیم ربات‌های سازنده @فکر کن", TEAM_IDENTITY)

HOOSHAN_PROFILE = (
    "نام من «هوشان» است؛ یک دستیار هوشمند گفت‌وگویی و جستجوگر اطلاعات. "
    "هوشان برای گفتگو، تحقیق و جستجوی اطلاعات روز، تحلیل منابع عمومی وب، خلاصه‌سازی، "
    "پاسخ‌گویی فارسی و دری، و کمک در برنامه‌نویسی و مسائل فنی طراحی شده است. "
    f"سازنده و بنیان‌گذار این پروژه {CREATOR_NAME} است و این پروژه با {TEAM_IDENTITY} شناخته می‌شود. "
    "حاجی احمد صالحی در معرفی این پروژه به‌عنوان سخنران حوزه موفقیت، برنامه‌نویس و فعال در زمینه‌های گوناگون فنی و آموزشی معرفی می‌شود. "
    "هوشان باید برای اخبار، قیمت‌ها، رویدادهای روز و هر اطلاعات وابسته به زمان ابتدا از وب جستجو کند، "
    "نتایج را از چند منبع تا حد امکان مقایسه کند، تاریخ و تازگی را بررسی کند و میان واقعیت تأییدشده و ادعای تأییدنشده تفاوت بگذارد. "
    "اگر جستجو در دسترس نباشد، محدودیت را صادقانه اعلام می‌کند و چیزی را جعل نمی‌کند. "
    "نام Provider یا مدل پشت‌صحنه هویت هوشان نیست و در پاسخ‌های عادی درباره خودش مطرح نمی‌شود."
)

_TOOL_LEAK_RE = re.compile(r"(?:^|\n)\s*(?:tool|ابزار)\s*:\s*", re.I)
_TODAY_WORDS = ("امروز", "جدیدترین", "آخرین", "اخبار", "خبر", "خبرهای", "خبر داغ", "به‌روز", "فعلی")


def _afghan_today() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kabul"))


def _json_from_tool_block(text: str, start: int) -> tuple[dict[str, Any] | None, int]:
    """Parse a JSON object following a tool: prefix using balanced braces."""
    brace = text.find("{", start)
    if brace < 0:
        return None, start
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                candidate = text[brace : index + 1]
                try:
                    data = json.loads(candidate)
                except (json.JSONDecodeError, TypeError):
                    return None, index + 1
                return data if isinstance(data, dict) else None, index + 1
    return None, len(text)


def _extract_tool_objects(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    position = 0
    while True:
        match = _TOOL_LEAK_RE.search(text, position)
        if not match:
            break
        data, position = _json_from_tool_block(text, match.end())
        if data:
            objects.append(data)
    return objects


def _tool_result_payload(obj: dict[str, Any]) -> dict[str, Any] | None:
    result = obj.get("result")
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _format_web_results(results: list[dict[str, Any]], query: str, news: bool) -> str:
    now = _afghan_today().strftime("%Y/%m/%d")
    header = "📰 جمع‌بندی اخبار" if news else "🔎 نتیجه جستجوی وب"
    lines = [f"{header} — {now}", "", f"موضوع جستجو: {query}"]
    usable = []
    for item in results[:8]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        snippet = str(item.get("snippet") or item.get("description") or "").strip()
        url = str(item.get("url") or "").strip()
        date = str(item.get("date") or item.get("published") or "").strip()
        if not title and not snippet:
            continue
        usable.append((title, snippet, url, date))
    if not usable:
        return "اطلاعات قابل استفاده‌ای از جستجوی وب دریافت نشد."

    for index, (title, snippet, url, date) in enumerate(usable, 1):
        lines.append(f"**{index}. {title or 'بدون عنوان'}**")
        if date:
            lines.append(f"تاریخ منبع: {date}")
        if snippet:
            lines.append(snippet)
        if url:
            lines.append(f"منبع: {url}")
        lines.append("")

    if news:
        lines.append("⚠️ این جمع‌بندی بر اساس نتایج جستجوی عمومی وب است. برای خبرهای حساس، نظامی، سیاسی، مالی یا حوادث، قبل از قطعی دانستن ادعاها منابع مستقل را مقایسه کنید.")
    return "\n".join(lines).strip()


class Agent(_Agent):
    """Stable public Agent facade with fast intent routing and Hooshan identity."""

    def _remember_from_message(self, user_input: str) -> None:
        if _NAME_QUERY.search(user_input.strip()):
            return
        super()._remember_from_message(user_input)

    def _system(self, user_input: str, extra: str | None = None) -> dict[str, str]:
        message = super()._system(user_input, extra)
        message["content"] = message["content"].replace("MyChatBot", ASSISTANT_NAME)
        message["content"] = message["content"].replace("تیم ربات‌های سازنده @فکر کن", TEAM_IDENTITY)
        message["content"] += (
            "\n\nهویت کاربر-facing: نام دستیار «هوشان» است. تیم پروژه: «اندیشه فردا». "
            "نتیجه ابزارها را هرگز به شکل JSON، tool:، request_id، warning یا payload خام به کاربر نشان نده. "
            "برای نتایج وب، داده را به زبان طبیعی و دقیق جمع‌بندی کن و منابع را جداگانه ذکر کن."
        )
        return message

    def _identity_response(self, text: str) -> str | None:
        normalized = text.strip()
        if _SELF_QUERY.search(normalized):
            return HOOSHAN_PROFILE
        response = super()._identity_response(normalized)
        if response is None:
            return None
        return HOOSHAN_PROFILE

    @staticmethod
    def _needs_tool_planner(text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False
        signals = (
            "http://", "https://", "www.", "آخرین", "جدیدترین", "اخبار", "خبر", "قیمت", "قیمت امروز",
            "وضعیت فعلی", "تحقیق", "جستجو", "جست‌وجو", "پیدا کن", "پیدا کن از اینترنت", "اینترنت", "آنلاین",
            "وب", "روی وب", "از وب", "منبع", "منابع", "اطلاعات تازه", "اطلاعات روز", "اطلاعات فعلی", "بررسی کن",
            "بررسی آنلاین", "لینک", "صفحه", "سرور", "backend", "render", "diagnostic", "diagnostics", "وای فای",
            "wifi", "dns", "پینگ", "ping", "ip", "شبکه", "باتری", "دستگاه", "filesystem", "runtime", "نسخه", "server",
        )
        return any(signal in lowered for signal in signals)

    @staticmethod
    def _fast_tool_plan(text: str) -> dict[str, Any] | None:
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
            "پیدا کن", "روی وب", "از وب", "از اینترنت", "اینترنت", "آنلاین", "اطلاعات فعلی", "اطلاعات تازه",
            "اطلاعات روز", "وضعیت فعلی", "منبع", "منابع", "بررسی آنلاین",
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

    async def ask(self, user_input: str) -> str:
        """Run the unified agent, then guarantee clean user-facing web output.

        Some providers occasionally echo internal tool payloads. Never expose those
        payloads; when they contain a successful web result, render the result
        directly instead of returning the provider's misleading apology.
        """
        answer = await super().ask(user_input)
        leaked = _extract_tool_objects(answer)
        if not leaked:
            return answer

        web_items: list[dict[str, Any]] = []
        had_news = any(marker in user_input.lower() for marker in _TODAY_WORDS)
        query = user_input.strip()
        for obj in leaked:
            tool_name = str(obj.get("tool") or "")
            if tool_name not in {"web_search", "web_research", "web_compare"}:
                continue
            payload = _tool_result_payload(obj)
            if not payload or payload.get("status") != "success":
                continue
            data = payload.get("data")
            if isinstance(data, dict):
                results = data.get("results")
                if isinstance(results, list):
                    web_items.extend(item for item in results if isinstance(item, dict))
                if data.get("query"):
                    query = str(data["query"])

        if web_items:
            # Keep order while removing duplicate URLs/titles.
            seen: set[str] = set()
            deduped: list[dict[str, Any]] = []
            for item in web_items:
                key = str(item.get("url") or item.get("title") or "").strip().lower()
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                deduped.append(item)
            return _format_web_results(deduped, query, news=had_news)

        # Strip internal payloads even if the tool result was unavailable.
        clean = _TOOL_LEAK_RE.sub("\n", answer)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
        return clean or "در حال حاضر نتیجه قابل استفاده‌ای از ابزار دریافت نشد."


__all__ = ["Agent", "SYSTEM_PROMPT", "TOOL_PLANNER_PROMPT", "TEAM_IDENTITY", "run_tool"]
