from __future__ import annotations

import json
import re
from typing import Any

from core.config import config
from core.logger import get_logger
from core.memory import Memory
from core.router import Router
from tools.notes_tool import session_context
from tools.registry import run_tool, tool_specs

log = get_logger("agent")

SYSTEM_PROMPT = """تو MyChatBot هستی، یک دستیار شخصی هوشمند روی Android/Termux.
- کوتاه، دقیق و فارسی پاسخ بده (مگر کاربر زبان دیگری بخواهد).
- اگر برای پاسخ نیاز به ابزار داری، فقط یک بلاک JSON معتبر بفرست:
  {"tool": "<name>", "args": {...}}
- بعد از دریافت نتیجه ابزار، پاسخ نهایی را به زبان طبیعی بده.
- ابزارهای Wi-Fi فقط برای Security Audit قانونی، read-only و OS-managed هستند.
- هیچ‌گاه درخواست یا پیشنهاد password cracking، handshake/PMKID capture، WPS PIN attack، deauthentication، packet injection، root/permission bypass یا CAPTCHA bypass نده.
ابزارهای موجود:
"""

TOOL_RE = re.compile(r'\{\s*"tool"\s*:\s*"[^"\n]+"\s*,\s*"args"\s*:\s*\{.*?\}\s*\}', re.S)


class Agent:
    def __init__(
        self,
        session: str = "default",
        provider: str | None = None,
        model: str | None = None,
        tool_profile: str | None = None,
    ):
        self.session = session
        self.memory = Memory()
        self.router = Router(provider, model)
        self.tool_profile = (tool_profile or config.tool_profile).strip().lower()

    def _system(self) -> dict[str, str]:
        specs = "\n".join(
            f"- {s['name']}: {s['description']} args={s['args']}"
            for s in tool_specs(self.tool_profile)
        )
        facts = self.memory.all_facts(self.session)
        extra = (
            "\nحقایق ذخیره‌شده درباره این session: "
            + json.dumps(facts, ensure_ascii=False)
            if facts
            else ""
        )
        return {"role": "system", "content": SYSTEM_PROMPT + specs + extra}

    async def ask(self, user_input: str, max_tool_steps: int = 3) -> str:
        if not user_input.strip():
            raise ValueError("user_input must not be empty")
        max_steps = max(0, min(int(max_tool_steps), 8))
        self.memory.add(self.session, "user", user_input)
        messages = [self._system()] + [m.to_dict() for m in self.memory.history(self.session)]

        for _ in range(max_steps + 1):
            result = await self.router.complete(messages)
            content = str(result.get("content", "")).strip()
            call = self._extract_tool_call(content)
            if not call:
                self.memory.add(self.session, "assistant", content)
                return content

            tool_name = call.get("tool")
            args = call.get("args") or {}
            if not isinstance(tool_name, str) or not isinstance(args, dict):
                self.memory.add(self.session, "assistant", "درخواست ابزار نامعتبر بود.")
                return "درخواست ابزار نامعتبر بود."

            log.info("tool call: %s profile=%s", tool_name, self.tool_profile)
            with session_context(self.session):
                output = run_tool(tool_name, args, profile=self.tool_profile)
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": f"نتیجه ابزار {tool_name}: {str(output)[:8000]}",
                }
            )

        final = "به حد مجاز فراخوانی ابزار رسیدم. لطفاً درخواست را ساده‌تر بیان کنید."
        self.memory.add(self.session, "assistant", final)
        return final

    @staticmethod
    def _extract_tool_call(text: str) -> dict[str, Any] | None:
        for match in TOOL_RE.finditer(text):
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("tool"), str) and isinstance(parsed.get("args", {}), dict):
                return parsed
        return None
