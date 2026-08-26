# Wi-Fi Security Audit

The Android Wi-Fi module performs **passive security posture analysis** of networks visible to the device through the official Android Wi-Fi scan APIs.

## Reports

For each visible network it can report:

- SSID and masked BSSID
- RSSI and frequency
- driver-reported security capabilities
- WEP / WPA / WPA2 / WPA3-SAE / Enterprise / Open classification
- whether WPS is advertised
- a defensive security score and remediation findings

## Explicit limits

This module does not perform monitor-mode capture, packet injection, deauthentication, handshake collection, PMKID collection, WPS PIN attacks, password guessing, cracking, or credential extraction.

Android may restrict Wi-Fi scanning depending on OS version, runtime permissions, location services, device policy, and hardware. When a capability is unavailable, the application must report the exact limitation and use the safest available fallback.

The output is intended for networks the user is authorized to assess.
