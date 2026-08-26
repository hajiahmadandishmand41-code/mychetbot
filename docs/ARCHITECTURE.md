# معماری MyChatBot

```
Flutter App ──HTTP──> FastAPI (interfaces/api_server.py)
CLI (rich)  ─────────> Agent (core/agent.py)
Telegram    ─────────>   │
                         ├── Router (fallback بین providerها)
                         │      └── providers/*  (OpenAI, OpenRouter, Anthropic, Gemini, Ollama)
                         ├── Memory (SQLite: messages + facts)
                         ├── Security (Fernet, whitelist, redaction)
                         └── Tools registry (shell, files, network, wifi, termux, http, notes)

Android (Kotlin) ── RUN_COMMAND ──> Termux ──> uvicorn/CLI
```

## اصول
1. هر لایه فقط از لایه پایین‌تر import می‌کند (بدون وابستگی حلقوی).
2. افزودن provider = یک فایل در `providers/` + یک خط در `registry.py`.
3. افزودن tool = یک تابع + یک `register(Tool(...))`.
4. همه I/O شبکه‌ای async است؛ ابزارهای سیستمی sync و timeout-دار.
