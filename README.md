# MyChatBot

Personal AI Agent for Android + Termux. This project uses Hermes Mobile as an architectural reference, but is a clean-room redesign for MyChatBot rather than a full copy.

## Architecture

```text
Flutter Android UI
      |
      | HTTP localhost
      v
Termux FastAPI Bridge
      |
      v
Central Agent -> Provider Adapter -> OpenAI / Claude / Gemini / OpenRouter
      |
      +-> Permission Policy -> Tools -> Termux / Files / Memory / Skills
```

## Why this differs from Hermes

Hermes Mobile contains useful patterns: a Python agent loop, tool registry, persistent memory, skills, a Flutter chat layer, and a native Android/Termux bridge. Its current implementation also has tight Hermes/Nous naming and executes shell/file operations directly. MyChatBot therefore keeps the architectural ideas but separates provider adapters, agent policy, tool registry, and Termux transport. Sensitive tools require confirmation instead of executing immediately.

## Current repository status

Implemented in this first foundation:
- Provider abstraction for OpenAI, OpenRouter, Claude/Anthropic and Gemini.
- Central agent loop with bounded tool iterations.
- Persistent JSONL memory.
- Extensible tool registry.
- Baseline file and Termux tools.
- Conservative confirmation policy for terminal/write/delete operations.
- FastAPI localhost bridge.
- Initial Flutter chat client with provider switching.
- `.env.example` and secret-safe `.gitignore`.
- Initial security tests.

Not yet complete:
- Android native MethodChannel/Termux RUN_COMMAND integration.
- Android notifications and clipboard adapters.
- Secure Android Keystore-backed secret storage.
- Full streaming UI.
- PDF/DOCX conversion tools.
- Skills lifecycle and sandboxing.
- Confirmation UI/token flow.
- Comprehensive provider-specific tool-call normalization (Claude/Gemini tool calling needs dedicated adapters).
- Release build configuration and device verification.

## Termux development

Install Python dependencies in Termux:

```bash
pkg update
pkg install python
cd ~/mychetbot
python -m pip install -r termux/requirements.txt
cp .env.example .env
# edit .env and add exactly the provider key you intend to use
bash termux/start.sh
```

The bridge listens only on `127.0.0.1` by default. The Flutter app uses `http://127.0.0.1:18923`.

## Provider examples

Set `AI_PROVIDER` to one of `openai`, `claude`, `gemini`, or `openrouter`, and set the corresponding API key. `AI_MODEL` selects the model. OpenRouter and OpenAI use OpenAI-compatible chat-completions; Claude and Gemini are isolated behind their own adapters so future provider changes do not leak into the Agent core.

## Security rules

Never commit `.env`, API keys, OAuth tokens, or device credentials. Read-only tools can run automatically. State-changing or sensitive tools are returned as confirmation-required actions. Future Android integrations must preserve this rule and must not expose arbitrary shell execution to an untrusted network interface.

## Hermes Mobile review

Reference repository: https://github.com/sinonchum/hermes-mobile

The full repository tree was inspected before writing the foundation. Hermes is a small Flutter + Kotlin + Python project with its agent/LLM/tools/memory/session code under `android/app/src/main/assets/bridge`, Flutter UI/services under `lib`, and Android bridge/bootstrap under `android/app/src/main/kotlin`. The key reusable concepts are the bounded agent loop, persistent memory/session model, centralized platform service, and bridge separation. Hermes-specific Nous OAuth, package names, branding, and bundled bootstrap implementation are intentionally not copied into MyChatBot.
