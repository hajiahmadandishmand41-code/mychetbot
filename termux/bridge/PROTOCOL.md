# Android ↔ Termux bridge protocol

## Local HTTP

The Python Agent bridge listens on `127.0.0.1:18923` only.

- `GET /health` — process/provider health
- `GET /tools` — registered tool catalog
- `GET /permissions/{tool}` — current permission level
- `POST /chat` — natural-language agent request
- `POST /confirm` — approve/cancel a pending sensitive operation

## Android native command path

For command execution from the Android layer, prefer Termux's official `RUN_COMMAND` intent with the mandatory `com.termux.permission.RUN_COMMAND` permission. Avoid spawning arbitrary Android shell commands directly when the action is intended for the user's Termux environment.

## Confirmation contract

A sensitive tool returns:

```json
{
  "confirmation_required": true,
  "id": "opaque-token",
  "name": "terminal",
  "arguments": {"command": "..."},
  "reason": "..."
}
```

The Android client must display the exact operation and side effects, then call `/confirm` with the token and the user's approval. Tokens are single-use and kept in process memory.
