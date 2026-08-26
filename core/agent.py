from __future__ import annotations
import json, re
from core.memory import Memory
from core.router import Router
from core.logger import get_logger
from tools.registry import tool_specs, run_tool

log = get_logger("agent")

SYSTEM_PROMPT = '''تو MyChatBot هستی، یک دستیار شخصی هوشمند روی Android/Termux.
- کوتاه، دقیق و فارسی پاسخ بده (مگر کاربر زبان دیگری بخواهد).
- اگر برای پاسخ نیاز به ابزار داری، فقط یک بلاک JSON بفرست:
  {"tool": "<name>", "args": {...}}
- بعد از دریافت نتیجه ابزار، پاسخ نهایی را به زبان طبیعی بده.
ابزارهای موجود:
'''

TOOL_RE = re.compile(r"\{\s*\"tool\"\s*:.*?\}\s*\}", re.S)

class Agent:
    def __init__(self, session: str = "default", provider: str | None = None, model: str | None = None):
        self.session = session
        self.memory = Memory()
        self.router = Router(provider, model)

    def _system(self) -> dict:
        specs = "\n".join(f"- {s['name']}: {s['description']} args={s['args']}" for s in tool_specs())
        facts = self.memory.all_facts()
        extra = ("\nحقایق ذخیره‌شده درباره کاربر: " + json.dumps(facts, ensure_ascii=False)) if facts else ""
        return {"role": "system", "content": SYSTEM_PROMPT + specs + extra}

    async def ask(self, user_input: str, max_tool_steps: int = 3) -> str:
        self.memory.add(self.session, "user", user_input)
        messages = [self._system()] + [m.to_dict() for m in self.memory.history(self.session)]

        for _ in range(max_tool_steps):
            result = await self.router.complete(messages)
            content = result["content"]
            call = self._extract_tool_call(content)
            if not call:
                self.memory.add(self.session, "assistant", content)
                return content
            log.info("tool call: %s", call.get("tool"))
            output = run_tool(call.get("tool", ""), call.get("args", {}) or {})
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"نتیجه ابزار {call.get('tool')}: {output}"})

        final = "به حد مجاز فراخوانی ابزار رسیدم. لطفاً درخواست را ساده‌تر بیان کنید."
        self.memory.add(self.session, "assistant", final)
        return final

    @staticmethod
    def _extract_tool_call(text: str) -> dict | None:
        m = TOOL_RE.search(text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
