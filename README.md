# MyChatBot

**Personal AI Assistant for Android + Termux** built by **Haji Ahmad**.

MyChatBot is a modular personal assistant: the Flutter UI talks to a localhost-only FastAPI Agent in Termux; the Agent selects AI providers and tools, checks permissions, executes authorized operations, stores memory, and returns results.

## Architecture

```text
User
  ↓
Flutter Android UI
  ↓ localhost:18923
Termux FastAPI Bridge
  ↓
Central Agent
  ├─ Memory
  ├─ Provider Adapter
  ├─ Tool Registry
  └─ Permission Policy
       ↓
   SAFE / CONFIRM / BLOCKED
       ↓
Files / Termux / Phone / Wi-Fi / Network
```

## AI providers

- OpenAI
- OpenRouter
- Claude / Anthropic
- Gemini

The Agent uses a normalized internal tool-call format. Gemini is configured through Google's OpenAI-compatible endpoint; Google documents function calling on that compatibility layer. https://ai.google.dev/gemini-api/docs/openai

## Tool families

```text
agent/tools/
├── filesystem/
│   └── archive.py
├── phone/
│   └── system.py
├── wifi/
│   ├── manager.py
│   └── wifite_tool.py
├── builtin.py
└── registry.py
```

Implemented tools include:

- `list_files`, `read_file`, `write_file`, `delete_file`
- `terminal`
- `memory_search`, `memory_save`
- `zip_info`, `zip_extract`
- `system_info`, `battery`, `storage_info`
- `wifi_manager`, `network_info`, `wifi_interface_info`
- `connectivity`, `ping`, `dns_lookup`
- `wifi_scan`, `network_scan`
- `wifite_detect`, `wifite_tool`

## Permission model

| Level | Examples | Behavior |
|---|---|---|
| SAFE | Wi-Fi status, ping, DNS, battery, storage, file listing/reading | Runs automatically |
| CONFIRM | terminal, file write/delete, network scan, Wi-Fi scan, Wifite adapter, clipboard write | Requires explicit user confirmation |
| BLOCKED | credential theft, unauthorized access, deauthentication/third-party attacks | Never executed |

Wifite is intentionally separated from generic shell execution. The current adapter detects installation/root requirements and returns an authorized-audit plan; it does not expose unrestricted attack flags to the Agent.

## Wi-Fi and network safety

Network discovery is restricted by policy to authorized networks. `network_scan` requires confirmation. The Agent must never be used to break Wi-Fi passwords, collect credentials, deauthenticate other networks, or attack third-party systems.

## Android + Termux

The project does **not** bundle a private Termux root filesystem. It uses the installed Termux app. Android integration is documented under `android/` and the protocol under `termux/bridge/PROTOCOL.md`.

Current Termux documentation states that third-party apps can use `RUN_COMMAND` when the required `com.termux.permission.RUN_COMMAND` permission is granted; current target-SDK package-visibility requirements also apply. The project keeps this path behind the same Agent permission policy. https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent

For Android APIs such as structured battery information, notifications and other device APIs, the official Termux:API project provides command-line access to Android APIs. https://github.com/termux/termux-api

## Running in Termux

```bash
pkg update
pkg install python
cd ~/mychetbot
python -m pip install -r termux/requirements.txt
cp .env.example .env
# edit .env and set exactly the provider key you need
bash termux/start.sh
```

The bridge defaults to `127.0.0.1:18923` and should not be exposed to the LAN.

## Flutter

The Flutter client contains tabs for:

- Chat
- Tools
- Wi-Fi
- Memory
- Settings

The Chat screen displays confirmation dialogs for sensitive tool calls instead of executing them silently.

## Testing

Python tests cover:

- permission levels
- memory persistence
- tool registration
- Wifite detection when installed or missing
- ZIP extraction

Run:

```bash
pytest -q
```

Flutter/Android build verification still needs a machine with Flutter + Android SDK installed; this environment cannot execute that toolchain.

## Hermes Mobile reference

Reference: https://github.com/sinonchum/hermes-mobile

Hermes was inspected before implementation. Useful architectural ideas retained or redesigned include the bounded Agent loop, persistent memory/session approach, tool registry, Flutter-to-native separation, and the local bridge concept. Hermes-specific Nous branding/OAuth, package names, and bundled Termux bootstrap were deliberately not copied.

## Security rules

Never commit `.env`, API keys, OAuth tokens, passwords, or device credentials. Logs must not print secrets. The localhost bridge must remain local. Sensitive tools must pass the centralized permission policy, and blocked tool names cannot be registered as executable functionality without changing the policy deliberately.
