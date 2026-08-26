from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from typing import Any

BLOCKED_OPERATIONS = [
    "password guessing/cracking",
    "handshake/PMKID capture",
    "WPS PIN attacks",
    "deauthentication",
    "packet injection",
    "permission/root bypass",
    "authentication/CAPTCHA bypass",
]


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    executable = shutil.which(cmd[0])
    if not executable:
        return 127, f"{cmd[0]} not installed"
    try:
        result = subprocess.run(
            [executable, *cmd[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    output = (result.stdout or result.stderr).strip()
    return result.returncode, output


def _termux(command: str, timeout: int = 15) -> tuple[bool, str]:
    code, output = _run([command], timeout=timeout)
    return code == 0, output


def _termux_json(command: str) -> tuple[bool, Any, str | None]:
    ok, raw = _termux(command)
    if not ok:
        return False, None, raw
    try:
        return True, json.loads(raw), None
    except json.JSONDecodeError:
        return False, None, raw or "invalid JSON"


def _mask_bssid(value: str) -> str:
    parts = value.split(":")
    if len(parts) == 6:
        return ":".join(parts[:3] + ["xx", "xx", "xx"])
    return value


def _channel(frequency: int) -> int:
    if 2412 <= frequency <= 2472:
        return (frequency - 2407) // 5
    if frequency == 2484:
        return 14
    if 5000 <= frequency <= 5895:
        return (frequency - 5000) // 5
    if 5955 <= frequency <= 7115:
        return (frequency - 5950) // 5
    return -1


def _security(capabilities: str) -> str:
    caps = capabilities.upper()
    if not caps:
        return "Unknown"
    if "OWE" in caps:
        return "OWE"
    if "SAE" in caps or "WPA3" in caps:
        return "WPA3-Personal"
    if "EAP" in caps:
        return "WPA/WPA2-Enterprise"
    if "WEP" in caps:
        return "WEP"
    if "WPA2" in caps:
        return "WPA2"
    if "WPA" in caps:
        return "WPA"
    return "Open-or-Unknown"


def _wps(capabilities: str) -> str:
    caps = capabilities.upper()
    if "WPS" in caps:
        return "advertised"
    return "unknown" if not caps else "not-advertised"


def _band(frequency: int) -> str:
    if 2400 <= frequency < 2500:
        return "2.4 GHz"
    if 4900 <= frequency < 5925:
        return "5 GHz"
    if 5925 <= frequency < 7200:
        return "6 GHz"
    return "unknown"


def capability_detection() -> str:
    termux_info = {
        "termux_wifi_connectioninfo": bool(shutil.which("termux-wifi-connectioninfo")),
        "termux_wifi_scaninfo": bool(shutil.which("termux-wifi-scaninfo")),
        "termux_api_helper": bool(shutil.which("termux-api")),
        "ip": bool(shutil.which("ip")),
        "ping": bool(shutil.which("ping")),
    }
    return json.dumps(
        {
            "mode": "legal_security_audit",
            "termux_api": termux_info,
            "root": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
            "root_required_for_audit": False,
            "supported": [
                "capability detection",
                "wifi scan",
                "encryption/security classification",
                "WPS advertised status",
                "signal strength",
                "network diagnostics",
                "security report",
            ],
            "unsupported_or_intentionally_blocked": BLOCKED_OPERATIONS,
            "limitations": [
                "termux-wifi-scaninfo can return cached OS scan results; this tool does not force monitor mode or packet capture.",
                "WPS is reported as advertised/not-advertised/unknown from OS-exposed capability data; unknown is not treated as disabled.",
                "Missing Termux:API, Android permissions, Wi-Fi off, or disabled location services can prevent scan results.",
            ],
        },
        ensure_ascii=False,
    )


def wifi_scan() -> str:
    ok, payload, error = _termux_json("termux-wifi-scaninfo")
    if not ok:
        return json.dumps(
            {
                "status": "unavailable",
                "error": error,
                "fallback": "Install/enable Termux:API and grant its location permission; no root fallback is attempted.",
            },
            ensure_ascii=False,
        )
    if not isinstance(payload, list):
        return json.dumps({"status": "error", "data": payload}, ensure_ascii=False)

    rows: list[dict[str, Any]] = []
    for network in payload:
        if not isinstance(network, dict):
            continue
        ssid = str(network.get("ssid", ""))
        bssid = _mask_bssid(str(network.get("bssid", "")))
        try:
            frequency = int(network.get("frequency_mhz", network.get("frequency", 0)))
        except (TypeError, ValueError):
            frequency = 0
        try:
            rssi = int(network.get("rssi", 0))
        except (TypeError, ValueError):
            rssi = 0
        capabilities = str(network.get("capabilities", ""))
        rows.append(
            {
                "ssid": ssid,
                "bssid": bssid,
                "rssi_dbm": rssi,
                "frequency_mhz": frequency,
                "channel": _channel(frequency),
                "band": _band(frequency),
                "capabilities": capabilities,
                "security": _security(capabilities),
                "wps_status": _wps(capabilities),
            }
        )
    rows.sort(key=lambda item: item["rssi_dbm"], reverse=True)
    return json.dumps({"status": "ok", "count": len(rows), "networks": rows}, ensure_ascii=False)


def wifi_info() -> str:
    ok, data, error = _termux_json("termux-wifi-connectioninfo")
    if not ok:
        return json.dumps(
            {"status": "unavailable", "error": error, "hint": "Check Termux:API and Android Wi-Fi/location permissions."},
            ensure_ascii=False,
        )
    if not isinstance(data, dict):
        return json.dumps({"status": "error", "data": data}, ensure_ascii=False)
    if data.get("bssid"):
        data["bssid"] = _mask_bssid(str(data["bssid"]))
    data["status"] = "ok"
    return json.dumps(data, ensure_ascii=False)


def network_diagnostics() -> str:
    info_ok, info, info_error = _termux_json("termux-wifi-connectioninfo")
    route_code, route = _run(["ip", "route", "get", "1.1.1.1"], timeout=5)
    dns_servers: list[str] = []
    try:
        with open("/system/etc/resolv.conf", "r", encoding="utf-8") as handle:
            dns_servers = [line.split()[1] for line in handle if line.startswith("nameserver ")]
    except (FileNotFoundError, PermissionError, IndexError):
        pass

    ping_host = "1.1.1.1"
    ping_code, _ = _run(["ping", "-c", "1", "-W", "2", ping_host], timeout=5)
    dns_ok = False
    try:
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        dns_ok = True
    except OSError:
        dns_ok = False

    return json.dumps(
        {
            "wifi": info if info_ok else {"status": "unavailable", "error": info_error},
            "default_route": route if route_code == 0 else {"status": "unavailable", "error": route},
            "dns_servers": dns_servers,
            "dns_resolution": "ok" if dns_ok else "failed",
            "internet_reachability": "ok" if ping_code == 0 else "failed",
            "ping_target": ping_host,
            "notes": [
                "Diagnostics are passive/read-only; no port scanning, packet injection, or traffic interception is performed.",
                "A failed ICMP ping alone does not prove that Internet access is unavailable because some networks block ICMP.",
            ],
        },
        ensure_ascii=False,
    )


def security_report() -> str:
    info_ok, info, info_error = _termux_json("termux-wifi-connectioninfo")
    scan_ok, networks, scan_error = _termux_json("termux-wifi-scaninfo")

    current_ssid = str(info.get("ssid", "")) if info_ok and isinstance(info, dict) else ""
    current_bssid = _mask_bssid(str(info.get("bssid", ""))) if info_ok and isinstance(info, dict) else ""
    current = None
    if scan_ok and isinstance(networks, list) and current_ssid:
        for network in networks:
            if not isinstance(network, dict):
                continue
            network_ssid = str(network.get("ssid", ""))
            network_bssid = _mask_bssid(str(network.get("bssid", "")))
            if current_bssid and network_bssid == current_bssid:
                current = network
                break
            if current is None and network_ssid == current_ssid:
                current = network

    capabilities = str((current or {}).get("capabilities", ""))
    security = _security(capabilities)
    wps_status = _wps(capabilities)
    findings: list[dict[str, str]] = []

    if security == "WEP":
        findings.append({"severity": "critical", "finding": "WEP encryption advertised", "recommendation": "Migrate to WPA3-Personal or WPA2-AES immediately."})
    elif security in {"Open-or-Unknown", "Unknown"}:
        findings.append({"severity": "high", "finding": "Network security could not be confirmed as encrypted", "recommendation": "Verify the access point uses WPA3 or WPA2-AES; do not assume Unknown means Open."})
    elif security == "WPA":
        findings.append({"severity": "high", "finding": "Legacy WPA security advertised", "recommendation": "Upgrade the AP to WPA2-AES or WPA3."})
    elif security == "WPA2":
        findings.append({"severity": "info", "finding": "WPA2 security advertised", "recommendation": "Prefer WPA3-Personal when supported and keep AES/CCMP enabled."})
    elif security == "WPA3-Personal":
        findings.append({"severity": "good", "finding": "WPA3-Personal advertised", "recommendation": "Keep firmware current and use a strong unique passphrase."})

    if "TKIP" in capabilities.upper():
        findings.append({"severity": "high", "finding": "TKIP cipher advertised", "recommendation": "Disable TKIP and use AES/CCMP-only configuration."})

    if wps_status == "advertised":
        findings.append({"severity": "medium", "finding": "WPS advertised by the AP", "recommendation": "Disable WPS on the router when it is not required."})
    elif wps_status == "unknown":
        findings.append({"severity": "info", "finding": "WPS status unknown", "recommendation": "Check the router configuration directly; the OS did not expose enough data to prove WPS state."})

    return json.dumps(
        {
            "mode": "security_audit",
            "current_ssid": current_ssid or "unknown",
            "security": security,
            "wps_status": wps_status,
            "capabilities": capabilities,
            "findings": findings,
            "data_quality": "direct_bssid_match" if current is not None and current_bssid else ("direct_ssid_match" if current is not None else "connection_info_only"),
            "limitations": {
                "wifi_scan": None if scan_ok else scan_error,
                "wifi_connectioninfo": None if info_ok else info_error,
                "explicitly_not_supported": BLOCKED_OPERATIONS,
            },
        },
        ensure_ascii=False,
    )
