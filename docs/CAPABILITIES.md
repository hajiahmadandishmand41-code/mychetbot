# Safe Capability Detection

The Android bridge detects capabilities before attempting an operation. It must never report success when Android, Termux, or the user has not provided the required capability.

## Capability matrix

| Capability | Detection | Safe fallback |
| --- | --- | --- |
| Wi-Fi scan | Wi-Fi enabled + runtime permissions + location services | Explain the missing requirement and ask the user to enable it |
| Termux execution | Termux installed + `RUN_COMMAND` permission | Ask the user to configure Termux; do not bypass permissions |
| Accessibility | Service declared + enabled by the user in Android Settings | Open Accessibility Settings; never enable it programmatically |
| Restricted/private APIs | Explicitly unavailable | Use the nearest official Android API or report the limitation |

## Security boundary

This layer does not bypass authentication, CAPTCHA, Android security controls, Wi-Fi passwords, or permissions. Accessibility is an explicit user-controlled capability. Termux execution remains subject to the existing command allowlist and Android/Termux permissions.

Capability detection is advisory: it does not grant new authority and must not be used as a substitute for authorization checks at the operation boundary.
