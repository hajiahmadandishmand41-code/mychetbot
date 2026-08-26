from __future__ import annotations

import re
import time

from core.config import config
from core.logger import get_logger
from core.memory import Memory
from core.router import Router

log = get_logger("agent")

SYSTEM_PROMPT = """تو MyChatBot هستی؛ یک دستیار هوشمند گفت‌وگویی حرفه‌ای.
سازنده MyChatBot: حاجی احمد صالحی

قواعد اصلی:
- هویت تو فقط MyChatBot است. نام مدل، Provider، Router یا زیرساخت را به‌عنوان هویت خود مطرح نکن.
- زبان و لحن کاربر را تشخیص بده و همان سبک را با لحن طبیعی و حرفه‌ای دنبال کن؛ فارسی را عالی پشتیبانی کن.
- برای سؤال ساده، مستقیم و کوتاه پاسخ بده. برای موضوع پیچیده، ساختاریافته و عمیق پاسخ بده.
- Context و حافظه ذخیره‌شده را فقط وقتی مرتبط است به کار ببر. هرگز چیزی را که در حافظه نیست حدس نزن.
- درباره دسترسی به اینترنت، فایل‌ها، دستگاه یا اطلاعات خصوصی ادعای ساختگی نکن.
- اطلاعات نادرست یا ساختگی تولید نکن و در صورت نبود داده کافی، شفاف بگو چه چیزی نامشخص است.
- از عبارت‌های کلیشه‌ای و تکراری بیش از حد استفاده نکن.
- این سیستم یک Chatbot است؛ هیچ ابزار دستگاه، Wi‑Fi، شبکه، Shell، Termux یا automation در مسیر پاسخ‌گویی ندارد.
- Memory به معنی افزایش دانش شخصی و Context است، نه آموزش یا تغییر وزن‌های مدل.

یادداشت درباره حافظه:
- facts حافظه بلندمدت هستند و از Session جدا نگهداری می‌شوند.
- تاریخچه گفتگو فقط برای Context مرتبط استفاده می‌شود.
- ممکن است برخی اطلاعات عمداً ذخیره نشده باشند؛ در چنین مواردی حدس نزن.
"""

_NAME_PATTERNS = (
    re.compile(r"(?:اسم|نام)\s*(?:من\s*)?(?:=|:|،)?\s*([\u0600-\u06FFA-Za-z][\u0600-\u06FFA-Za-z .'-]{0,60}?)\s*(?:است|هست|هستم|می‌باشد|میباشد)$", re.I),
    re.compile(r"(?:من\s+|my name is\s+)([\u0600-\u06FFA-Za-z][\u0600-\u06FFA-Za-z .'-]{0,60})$", re.I),
)
_PREFERENCE_PATTERNS = (
    ("response_preference", re.compile(r"(?:دوست دارم|ترجیح می‌دهم|ترجیح میدم|می‌خواهم|میخوام).*?(?:جواب|پاسخ).*?(کوتاه|مختصر|طولانی|کامل|رسمی|خودمانی)", re.I)),
    ("language_preference", re.compile(r"(?:از این به بعد|لطفاً|لطفا).*?(?:به فارسی|به انگلیسی|به دری|به پشتو).*?(?:جواب|پاسخ|صحبت)", re.I)),
)
_EXPLICIT_REMEMBER = re.compile(r"(?:یادت باشد|یادت باشه|به خاطر بسپار|به خاطر داشته باش|remember this|remember)\s*[:：]?\s*(.+)$", re.I)
_FORGET = re.compile(r"(?:فراموش کن|یادت نباشه|پاک کن|forget)\s+(.+)$", re.I)
_IDENTITY = re.compile(r"(?:تو\s+)?(?:چه\s+مدلی|چه\s+ai|کدام\s+مدل|کدوم\s+مدل|از\s+چه\s+مدلی|چه\s+هوش|چه\s+سیستمی)|(?:deepseek|chatgpt|claude|gemini|gpt|nara)\s*(?:هستی|استی|ی|هستید|هستی؟|ی؟)", re.I)
_CREATOR = re.compile(r"(?:سازنده|خالق|توسعه\s*دهنده|developer|creator|who\s+made)\b", re.I)


def _clean_fact(value: str) -> str:
    return " ".join(value.strip().split())[:200]


class Agent:
    """Memory-first chat orchestrator. No tool execution is part of the chat path."""

    def __init__(self, session: str = "default"):
        if not session or len(session) > 100:
            raise ValueError("session must be between 1 and 100 characters")
        self.session = session
        self.memory = Memory()
        self.router = Router()

    def _remember_from_message(self, user_input: str) -> None:
        text = user_input.strip()
        explicit = _EXPLICIT_REMEMBER.search(text)
        if explicit:
            self.memory.remember(f"note:{int(time.time() * 1000)}", _clean_fact(explicit.group(1)), self.session)

        for pattern in _NAME_PATTERNS:
            match = pattern.search(text)
            if match:
                name = _clean_fact(match.group(1))
                if name and len(name) <= 60:
                    self.memory.remember("name", name, self.session)
                break

        for key, pattern in _PREFERENCE_PATTERNS:
            match = pattern.search(text)
            if match:
                self.memory.remember(key, _clean_fact(match.group(1)), self.session)

    def _identity_response(self, text: str) -> str | None:
        if _CREATOR.search(text):
            return "سازنده MyChatBot حاجی احمد صالحی است."
        if _IDENTITY.search(text):
            return "من MyChatBot هستم؛ یک دستیار هوشمند گفت‌وگویی که برای پاسخ‌گویی حرفه‌ای، حفظ Context و استفاده از حافظه طراحی شده‌ام."
        return None

    def _forget_from_message(self, user_input: str) -> bool:
        match = _FORGET.search(user_input.strip())
        if not match:
            return False
        target = match.group(1).strip().lower()
        aliases = {
            "اسمم": "name",
            "اسم من": "name",
            "نام": "name",
            "نام من": "name",
            "name": "name",
            "اسم": "name",
            "ترجیحم": "response_preference",
            "پاسخ": "response_preference",
            "response_preference": "response_preference",
        }
        key = aliases.get(target)
        if key:
            self.memory.forget(key, self.session)
            return True
        if target in {"همه", "همه چیز", "all", "all memory", "حافظه"}:
            self.memory.clear(self.session)
            return True
        return False

    def _system(self, user_input: str) -> dict[str, str]:
        context = self.memory.relevant_context(self.session, user_input, max_messages=config.memory_context_messages)
        facts = self.memory.relevant_facts(self.session, user_input, max_facts=config.memory_context_facts)
        blocks = [SYSTEM_PROMPT]
        if facts:
            blocks.append("Facts مرتبط و تأییدشده:\n" + "\n".join(f"- {k}: {v}" for k, v in facts.items()))
        if context:
            blocks.append("بخش مرتبط از گفت‌وگوی قبلی:\n" + "\n".join(f"{m['role']}: {m['content']}" for m in context))
        return {"role": "system", "content": "\n\n".join(blocks)}

    async def ask(self, user_input: str) -> str:
        text = user_input.strip()
        if not text:
            raise ValueError("user_input must not be empty")
        if len(text) > config.max_input_chars:
            raise ValueError("user_input is too long")

        self._remember_from_message(text)
        identity = self._identity_response(text)
        if identity is not None:
            self.memory.add(self.session, "user", text)
            self.memory.add(self.session, "assistant", identity)
            return identity

        if self._forget_from_message(text):
            self.memory.add(self.session, "user", text)
            reply = "انجام شد. اطلاعات موردنظر از حافظه پاک شد."
            self.memory.add(self.session, "assistant", reply)
            return reply

        self.memory.add(self.session, "user", text)
        messages = [self._system(text)] + self.memory.recent_history(self.session, limit=config.recent_history_messages)

        try:
            result = await self.router.complete(messages)
            answer = str(result.get("content", "")).strip()
        except Exception:
            log.exception("chat completion failed")
            raise

        if not answer:
            answer = "متأسفم، پاسخی از سرویس دریافت نشد. لطفاً دوباره تلاش کنید."
        self.memory.add(self.session, "assistant", answer)
        return answer
