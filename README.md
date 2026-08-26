# MyChatBot — Personal AI Assistant for Android + Termux

MyChatBot یک دستیار ماژولار Python با رابط CLI، FastAPI و اتصال Android/Termux است. تمرکز پروژه روی اجرای واقعی، خطاهای قابل فهم، session isolation و محدودیت‌های واقعی هر محیط است.

## Architecture

```text
core/       config, logger, memory, security, router, agent
providers/  OpenAI, Anthropic, Gemini, OpenRouter, Ollama
tools/      shell, files, network, wifi, termux, http, notes
interfaces/ CLI, FastAPI, Telegram
termux/     install/start/API/bridge launchers
android/    Kotlin Termux bridge, Wi-Fi scanner, notifications
flutter_app/ mobile client
tests/      pytest unit/integration-ready tests
docs/       architecture, security, roadmap, report
Dockerfile  non-root production API image
compose.yaml hardened local/VPS API service
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

`/health` is intentionally public for health checks. `/tools`, `/chat` and `/history/*` require `Authorization: Bearer <API_TOKEN>`. The API validates session identifiers, enforces an in-process request rate limit, serializes concurrent requests per Agent session, and bounds the number of cached Agent sessions.

For a reverse proxy such as Caddy, set `TRUST_PROXY=true` only when the application is reachable exclusively through that trusted proxy. It is `false` by default so clients cannot spoof `X-Forwarded-For` for rate-limit bypass.

The API always uses `API_TOOL_PROFILE=server` in the production deployment, exposing only server-safe tools. Android/Termux/local tools are rejected as `capability_unavailable` rather than executed remotely.

## Telegram

Set `TELEGRAM_BOT_TOKEN`. For production, configure `TELEGRAM_ALLOWED_CHAT_IDS` and set `TELEGRAM_REQUIRE_ALLOWLIST=true`. The bot uses long polling with timeouts/retries, respects Telegram `Retry-After` on rate limits, per-chat locks, per-chat Agent sessions and Telegram message-size handling.

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

Shell execution is disabled by default, uses a command whitelist, rejects shell chaining/redirection and runs with `shell=False`. The default whitelist intentionally excludes `curl`. The file tool is sandboxed and blocks reading/writing environment files, master keys and credential directories. The HTTP tool validates DNS-resolved destinations, blocks private/loopback/link-local/metadata networks, disables automatic redirects and limits response size.

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

The production image installs only runtime dependencies and runs as UID/GID 10001. Compose enables `no-new-privileges`, drops Linux capabilities, uses a read-only container filesystem with a small `/tmp`, and keeps persistent application data under `./data`. Caddy is the public HTTPS entry point while the API port remains internal to the Compose network.

Docker/VPS can run the Python API and AI providers, but cannot access the Android device's Wi-Fi interface merely because the chatbot is remote.

## Vercel

Vercel can host a web/API workload, but this repository's Android/Termux Wi-Fi capabilities are device-local and must not be proxied as if they were available on Vercel. Deploy the API remotely only when the requested functionality does not depend on the phone's Wi-Fi/Termux environment.

## Tests and CI

```bash
pytest -q
python -m compileall -q core providers tools interfaces mychatbot
```

GitHub Actions workflow `CI` runs Python 3.10/3.13/3.14 with compile checks, Ruff, mypy, dependency audit, imports, pytest and shell syntax checks. A separate Docker workflow builds and health-checks the production image on pull requests and pushes to `main`. Android CI builds the debug APK on every main/PR change.

Android/Termux runtime behavior remains device-dependent and should be validated on a real Android device with the required permissions.

## Troubleshooting

**`API provider is not configured`** — configure at least one provider or run Ollama locally.

**`TELEGRAM_BOT_TOKEN تنظیم نشده است`** — set the token in `.env`; production also requires the configured Telegram allow-list when `TELEGRAM_REQUIRE_ALLOWLIST=true`.

**`Termux API unavailable`** — install the Termux:API Android application and `pkg install termux-api` in Termux.

**Wi-Fi scan unavailable** — enable Wi-Fi, grant the relevant Android Wi-Fi/location permissions, enable location services when required by Android, and ensure Termux:API is installed for the Termux path.

**`cryptography` installation fails in Termux** — re-run `bash termux/install.sh` so the native build prerequisites are installed when a compatible wheel is unavailable.
