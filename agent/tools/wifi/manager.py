"""Read-only Wi-Fi and connectivity helpers for Android/Termux."""
import shutil
import socket
import subprocess
import urllib.request


def _run(command: str, timeout: int = 8) -> str:
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout + p.stderr).strip()
        return out[:8000] if out else f"exit_code={p.returncode}"
    except FileNotFoundError:
        return "command_not_found"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception as exc:
        return f"error: {exc}"


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _getprop(name: str) -> str:
    if not _command_exists("getprop"):
        return "unknown"
    value = _run(f"getprop {name}")
    return value or "unknown"


def wifi_manager(_args: dict) -> dict:
    ssid = _getprop("gsm.wifi.ssid")
    if ssid in ("", "unknown"):
        ssid = _getprop("dhcp.wlan0.hostname")
    ip = _run("ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | head -1")
    gateway = _run("ip route 2>/dev/null | awk '/default/{print $3; exit}'")
    dns = _run("getprop | grep -E '\\[net\\.(dns[0-9]*)\\]' | head -4")
    iface = _run("ip route 2>/dev/null | awk '/default/{print $5; exit}'")
    return {
        "connected": bool(gateway and gateway not in {"command_not_found", "timeout"}),
        "ssid": ssid,
        "ip": ip or "unknown",
        "gateway": gateway or "unknown",
        "dns": dns or "unknown",
        "interface": iface or "unknown",
        "signal": "not_available_without_platform_adapter",
    }


def network_info(_args: dict) -> dict:
    return {
        "interfaces": _run("ip -brief addr 2>/dev/null || ip addr").splitlines()[:40],
        "routes": _run("ip route 2>/dev/null").splitlines()[:40],
        "dns": _run("getprop | grep -E '\\[net\\.(dns[0-9]*)\\]'").splitlines()[:10],
    }


def connectivity(_args: dict) -> dict:
    checks = {}
    for host in ("1.1.1.1", "8.8.8.8"):
        checks[host] = _run(f"ping -c 1 -W 2 {host} 2>&1 | tail -3")
    try:
        with urllib.request.urlopen("https://example.com", timeout=5) as response:
            checks["https"] = {"ok": True, "status": response.status}
    except Exception as exc:
        checks["https"] = {"ok": False, "error": str(exc)}
    return checks


def ping(args: dict) -> str:
    host = str(args.get("host", "1.1.1.1")).strip()
    if not host or any(ch in host for ch in ";&|`$()<>\n\r"):
        return "invalid_host"
    return _run(f"ping -c {min(max(int(args.get('count', 1)), 1), 4)} -W 2 {host}")


def dns_lookup(args: dict) -> str:
    host = str(args.get("host", "example.com")).strip()
    if not host:
        return "invalid_host"
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        return sorted({x[4][0] for x in infos})
    except Exception as exc:
        return f"dns_error: {exc}"


def wifi_interface_info(_args: dict) -> dict:
    return {
        "wlan0": _run("ip -details link show wlan0 2>/dev/null"),
        "wireless_tools": {name: _command_exists(name) for name in ("iw", "nmcli")},
    }


def wifi_scan(_args: dict) -> str:
    if _command_exists("nmcli"):
        return _run("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list", timeout=15)
    if _command_exists("termux-wifi-scaninfo"):
        return _run("termux-wifi-scaninfo", timeout=15)
    return "Wi-Fi scan is unavailable. Install/configure nmcli or Termux:API."


def network_scan(args: dict) -> str:
    cidr = str(args.get("cidr", "")).strip()
    if not cidr:
        cidr = _run("ip route 2>/dev/null | awk '/proto kernel/ && /src/{print $1; exit}'")
    if _command_exists("nmap"):
        return _run(f"nmap -sn --max-rate 50 {cidr}", timeout=60)
    return "nmap is not installed. Install it in Termux to enable authorized local-network discovery."


def build_wifi_tools():
    return {
        "wifi_manager": wifi_manager,
        "network_info": network_info,
        "connectivity": connectivity,
        "ping": ping,
        "dns_lookup": dns_lookup,
        "wifi_interface_info": wifi_interface_info,
        "wifi_scan": wifi_scan,
        "network_scan": network_scan,
    }
