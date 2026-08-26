# MyChatBot — Personal AI Assistant (Android + Termux)

معماری ماژولار، امن و قابل توسعه؛ الهام‌گرفته از ساختار Hermes Mobile.

```
mychatbot/
├── core/          # هسته: config, logger, memory, security, router, agent
├── providers/     # OpenAI, Anthropic, Gemini, OpenRouter, Ollama (local)
├── tools/         # shell, files, network, wifi, termux, http, notes
├── interfaces/    # cli, fastapi server, telegram bot
├── termux/        # اسکریپت‌های نصب و اجرا روی Termux
├── android/       # Kotlin bridge (Termux + Wi-Fi + Notification)
├── flutter_app/   # کلاینت موبایل (Dart)
├── tests/         # pytest
└── docs/          # ARCHITECTURE, SECURITY, ROADMAP, REPORT
```

## نصب سریع (Termux)
```bash
pkg update -y && pkg install -y python git openssh termux-api
git clone https://github.com/hajiahmadandishmand41-code/mychetbot
cd mychetbot && bash termux/install.sh
cp .env.example .env   # کلیدها را وارد کنید
python -m interfaces.cli
```

## اجرای سرور API
```bash
uvicorn interfaces.api_server:app --host 127.0.0.1 --port 8765
```

## تست
```bash
pytest -q
```

جزئیات کامل در `docs/REPORT.md`.
