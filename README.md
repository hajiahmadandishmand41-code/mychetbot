# MyChatBot — Personal AI Assistant for Android + Termux

MyChatBot یک دستیار ماژولار Python با رابط CLI، FastAPI و اتصال Android/Termux است. قابلیت‌های اصلی موجود حفظ شده‌اند و اجرای واقعی، خطاهای قابل فهم و محدودیت‌های Android/Termux در اولویت هستند.

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
```

## Requirements

Python 3.10+ is supported. Python 3.13/3.14 should be tested with the same dependency set. Android functionality requires an Android build environment; Termux functionality requires Termux and, for `wifi_*`/battery/notification tools, the Termux:API application and package.

## Linux installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## Termux installation

From the repository root:

```bash
bash termux/install.sh
```

The installer detects Termux, installs the native prerequisites needed by packages such as `cryptography`, does not upgrade Termux's pip, and is safe to run again.

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

The CLI starts even when no external AI key is configured, but actual AI responses require a configured provider. Ollama is the default because it can run locally; use another provider by setting its API key and `DEFAULT_PROVIDER`.

## API

```bash
uvicorn interfaces.api_server:app --host 127.0.0.1 --port 8765
```

`/health` is public. Protected endpoints require `Authorization: Bearer <API_TOKEN>`. Set `API_TOKEN` in `.env`; never commit a real token.

## Providers

Supported implementations currently present in the repository:

- Ollama
- OpenRouter
- OpenAI
- Anthropic
- Gemini

The Router uses only configured providers and normalizes timeout, authentication, rate-limit, connection and invalid-request failures before applying fallback.

## Tools

The central registry contains shell, file, network, Wi-Fi, Termux, HTTP and notes tools. Shell execution is disabled by default, uses a whitelist, rejects shell metacharacters/chaining and runs with `shell=False`.

## Wi-Fi and Android limitations

`wifi_info` and `wifi_scan` use Termux:API when available. Without Termux:API they return an explicit unavailable message. Android Wi-Fi scanning also checks Wi-Fi state and location permission. BSSIDs are masked in public output. Root is not assumed or fabricated; low-level monitor-mode operations remain outside the supported Android/Termux path unless the device actually provides the required privileges and kernel support.

## Android ↔ Termux bridge

The Android bridge only allows the approved `cli` and `api` launch modes through `termux/run_bridge.sh`. Missing Termux and missing `RUN_COMMAND` permission are surfaced as user-facing errors.

The Android project now includes the root Gradle settings/build files required to open the module as a Gradle project.

## Security

Secrets are redacted from application-facing text, the master key is generated outside Git under `~/.mychatbot/.master.key` with restrictive permissions where supported, and the API has no insecure default token.

## Tests

```bash
pytest -q
```

Device-specific Android/Termux operations should be covered with integration tests on a real device. The pure Python tests remain runnable without Android.

## Troubleshooting

**`API provider is not configured`** — configure at least one provider (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) or run Ollama locally.

**`Termux API unavailable`** — install the Termux:API application and `pkg install termux-api`.

**Wi-Fi scan fails** — enable Wi-Fi and grant location permission on Android; Android may impose additional platform restrictions.

**`cryptography` installation fails in Termux** — re-run `bash termux/install.sh`; it installs the Rust/build prerequisites needed for a source build when a compatible wheel is unavailable.
