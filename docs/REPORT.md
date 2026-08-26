# گزارش پیاده‌سازی MyChatBot

## چه چیزهایی ساخته شد
- **core/**: `config`, `logger` (با redaction), `security` (Fernet + whitelist), `memory` (SQLite: messages/facts), `router` (fallback), `agent` (حلقه tool-use).
- **providers/**: OpenAI, OpenRouter, Anthropic, Gemini, Ollama + registry.
- **tools/**: shell, files (sandbox), network (ping/dns/port/ip), wifi (termux-api), termux (battery/notify/toast/tts/clipboard/location), http_get, notes (remember/recall/facts) — مجموعاً ۲۱ ابزار ثبت‌شده.
- **interfaces/**: CLI با rich، FastAPI با احراز هویت Bearer، ربات تلگرام.
- **termux/**: `install.sh`, `start.sh`, `start_api.sh`.
- **android/**: `MainActivity`, `TermuxBridge` (RUN_COMMAND), `WifiScanner`, `Notifier`, Manifest, Gradle.
- **flutter_app/**: مدل، ApiClient، ChatScreen، MessageBubble، main.
- **tests/**: memory, security, tools, agent, router.

## Providerهای فعال
هر کدام که کلیدشان در `.env` باشد؛ `ollama` همیشه در دسترس است (محلی).

## وضعیت Wi-Fi و Termux
ابزارهای Wi-Fi/Termux به `termux-api` وابسته‌اند و فقط روی دستگاه واقعی Android خروجی واقعی می‌دهند؛ در غیر این صورت پیام `[unavailable]` برمی‌گردانند (بدون crash).

## آنچه هنوز به Android واقعی نیاز دارد
اسکن Wi-Fi، نوتیفیکیشن، TTS، موقعیت مکانی، اجرای Termux RUN_COMMAND، و بیلد APK/Flutter.

## Dependencyهای اضافه‌شده
httpx, pydantic, python-dotenv, fastapi, uvicorn, cryptography, rich, pytest, pytest-asyncio | Dart: http, shared_preferences | Kotlin: core-ktx, appcompat.
