# MyChatBot Android bridge

MyChatBot keeps privileged execution in the user's installed Termux instance instead of bundling a private Termux rootfs.

## Termux integration

For Android -> Termux command execution, use the official `RUN_COMMAND` intent and request `com.termux.permission.RUN_COMMAND`. On current Termux versions, third-party apps must have that permission granted by the user. Termux also documents package-visibility requirements for target SDK 30+.

Recommended runtime flow:

```text
Flutter UI
  -> MethodChannel
  -> MainActivity
  -> Termux RUN_COMMAND Intent
  -> Termux command
  -> result callback / local bridge
```

Do not expose a public HTTP listener for command execution. The Python bridge is localhost-only by default.

## Termux:API

Install Termux:API alongside the Termux app when Android APIs such as structured battery or Wi-Fi data are needed. MyChatBot detects `termux-*` commands when available and falls back to standard Android/Linux information where possible.

## Security

Android should preserve the Agent permission policy. `terminal`, `network_scan`, `wifi_scan`, `wifite_tool`, file writes/deletes and clipboard writes require confirmation. Blocked actions must never be forwarded to Termux.
