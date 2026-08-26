from __future__ import annotations
import json, shutil, subprocess

'''نیازمند termux-api روی دستگاه واقعی Android.'''

def _termux(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return f"[unavailable] {cmd[0]} نصب نیست (pkg install termux-api)"
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    return (p.stdout or p.stderr).strip()

def wifi_info() -> str:
    return _termux(["termux-wifi-connectioninfo"])

def wifi_scan() -> str:
    raw = _termux(["termux-wifi-scaninfo"])
    try:
        nets = json.loads(raw)
        return "\n".join(f"{n.get('ssid','?')}  {n.get('rssi','?')}dBm  {n.get('frequency','?')}MHz" for n in nets)
    except json.JSONDecodeError:
        return raw
