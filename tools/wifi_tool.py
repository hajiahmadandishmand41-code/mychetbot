from __future__ import annotations

import json
import shutil
import subprocess


def _termux(cmd: list[str]) -> str:
    executable = shutil.which(cmd[0])
    if not executable:
        return f"[unavailable] {cmd[0]} نصب نیست؛ در Termux: pkg install termux-api"
    try:
        result = subprocess.run(
            [executable, *cmd[1:]],
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "[timeout] Termux API پاسخ نداد"
    output = (result.stdout or result.stderr).strip()
    return output or "[]"


def _mask_bssid(value: str) -> str:
    parts = value.split(":")
    if len(parts) == 6:
        return ":".join(parts[:3] + ["xx", "xx", "xx"])
    return value


def wifi_info() -> str:
    raw = _termux(["termux-wifi-connectioninfo"])
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("bssid"):
            data["bssid"] = _mask_bssid(str(data["bssid"]))
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError:
        return raw


def wifi_scan() -> str:
    raw = _termux(["termux-wifi-scaninfo"])
    try:
        networks = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(networks, list):
        return json.dumps(networks, ensure_ascii=False)
    rows = []
    for network in networks:
        ssid = str(network.get("ssid", "?"))
        bssid = _mask_bssid(str(network.get("bssid", "?")))
        rssi = network.get("rssi", "?")
        frequency = network.get("frequency", "?")
        rows.append(f"{ssid}  {bssid}  {rssi}dBm  {frequency}MHz")
    return "\n".join(rows) or "(شبکه‌ای پیدا نشد)"
