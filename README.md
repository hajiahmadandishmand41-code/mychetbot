# MyChatBot — Personal AI Assistant for Android + Termux

MyChatBot یک دستیار ماژولار Python با رابط CLI، FastAPI و اتصال Android/Termux است. تمرکز پروژه روی اجرای واقعی، خطاهای قابل فهم، session isolation و محدودیت‌های واقعی هر محیط است.

## Architecture

```text
core/       config, logger, memory, security, router, agent
providers/  OpenAI, Anthropic, Gemini, OpenRouter, Ollama
 tools/     shell, files, network, wifi, termux, http, notes
interfaces/ CLI, FastAPI, Telegram
termux/     install/start/API/bridge launchers
android/    Kotlin Termux bridge, Wi-Fi scanner, notifications
flutter_app/ mobile client
 tests/     pytest unit/integration-ready tests
docs/       architecture, security, roadmap, report
Dockerfile  non-root API image
docker-compose.yml  hardened local/VPS API service
```

## Requirements

Python 3.10+ is supported. CI validates Python 3.10, 3.13 and 3.14. Android functionality requires an Android build environment; Termux functionality requires Termux and, for `wifi_*`/battery/notification tools, Termux:API and its Android permissions.

## Linux installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `API_TOKEN` for protected API access. Never commit `.env`, API keys, Telegram tokens or the generated master key.

## Termux installation

From the repository root:

```bash
bash termux/install.sh
```

Then configure `.env` and run:

```bash
bash termux/start.sh
```

API server:

```bash
bash termux/start_api.sh
```

## CLI

```bash
python -m interfaces.cli
python -m mychatbot
```

The CLI can start without an external AI key, but actual AI responses require a configured provider or a reachable local Ollama instance.

## API

```bash
uvicorn interfaces.api_server:app --host 127.0.0.1 --port 8765
```

`/health` is intentionally public for health checks. `/tools`, `/chat` and `/history/*` require `Authorization: Bearer <API_TOKEN>`. The API validates session identifiers, enforces an in-process request rate limit and bounds the number of cached Agent sessions.

## Telegram

Set `TELEGRAM_BOT_TOKEN`. Optionally set `TELEGRAM_ALLOWED_CHAT_IDS` to a comma-separated allow-list. The bot uses long polling with timeouts/retries, per-chat locks, per-chat Agent sessions and Telegram message-size handling.

```bash
bash termux/start_telegram.sh
```

## Providers

Supported implementations currently present in the repository:

- Ollama
- OpenRouter
- OpenAI
- Anthropic
- Gemini

The Router uses only configured providers and normalizes timeout, authentication, rate-limit, connection and invalid-request failures before fallback.

## Tools and security

Shell execution is disabled by default, uses a command whitelist, rejects shell chaining/redirection and runs with `shell=False`. The HTTP tool validates DNS-resolved destinations, blocks private/loopback/link-local/metadata networks, disables automatic redirects and limits response size.

## Legal Wi-Fi Security Audit

The Wi-Fi feature is intentionally limited to lawful, read-only / OS-managed audit functions:

- capability detection and environment limitations
- Wi-Fi scan results exposed by Android/Termux
- security/encryption classification
- WPS advertised status when exposed by the OS
- signal strength and radio/channel information
- network diagnostics (route, DNS and Internet reachability)
- security report with remediation guidance

The project does **not** implement password guessing/cracking, handshake/PMKID capture, WPS PIN attacks, deauthentication, packet injection, privilege/root bypass, authentication bypass or CAPTCHA bypass.

Android/Termux restrictions are real: missing Wi-Fi/location permissions, disabled location services, API throttling and missing Termux:API can make scan data unavailable. The code reports `unavailable`/`unknown` instead of fabricating results. No VPS/Vercel deployment is allowed to claim access to the phone's Wi-Fi radio; Wi-Fi audit requires the Android/Termux device-side components.

## Android ↔ Termux bridge

The Android bridge only supports the approved application/bridge paths already present in the repository. Wi-Fi scanning uses Android's official Wi-Fi APIs; no monitor mode or packet injection is required or attempted.

## Docker / VPS

Build and run the API container:

```bash
docker compose up -d --build
```

The image runs as a non-root user. Compose enables `no-new-privileges`, drops Linux capabilities and keeps the data directory on a named volume. Bind the service to localhost and put it behind a reverse proxy/VPN/firewall when exposing it from a VPS.

Docker/VPS can run the Python API and AI providers, but cannot access the Android device's Wi-Fi interface merely because the chatbot is remote.

## Vercel

Vercel can host a web/API workload, but this repository's Android/Termux Wi-Fi capabilities are device-local and must not be proxied as if they were available on Vercel. Deploy the API remotely only when the requested functionality does not depend on the phone's Wi-Fi/Termux environment.

## Tests and CI

```bash
pytest -q
python -m compileall -q core providers tools interfaces mychatbot
```

GitHub Actions runs the Python suite on Python 3.10, 3.13 and 3.14. Android/Termux runtime behavior remains device-dependent and should be validated on a real Android device with the required permissions.

## Troubleshooting

**`API provider is not configured`** — configure at least one provider or run Ollama locally.

**`TELEGRAM_BOT_TOKEN تنظیم نشده است`** — set the token in `.env`; for production, also consider `TELEGRAM_ALLOWED_CHAT_IDS`.

**`Termux API unavailable`** — install the Termux:API Android application and `pkg install termux-api` in Termux.

**Wi-Fi scan unavailable** — enable Wi-Fi, grant the relevant Android Wi-Fi/location permissions, enable location services when required by Android, and ensure Termux:API is installed for the Termux path.

**`cryptography` installation fails in Termux** — re-run `bash termux/install.sh` so the native build prerequisites are installed when a compatible wheel is unavailable.
