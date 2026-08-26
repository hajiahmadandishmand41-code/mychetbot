"""Read-only Android/Termux device status tools."""
import shutil
import subprocess


def _run(command: str) -> str:
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return (p.stdout + p.stderr).strip()[:6000]
    except Exception as exc:
        return f"error: {exc}"


def system_info(_args: dict) -> dict:
    mem = _run("cat /proc/meminfo | head -8")
    load = _run("cat /proc/loadavg")
    return {
        "os": _run("getprop ro.build.version.release 2>/dev/null") or _run("uname -o"),
        "device": _run("getprop ro.product.model 2>/dev/null"),
        "kernel": _run("uname -srmo"),
        "cpu": _run("getprop ro.product.cpu.abi 2>/dev/null"),
        "load": load,
        "memory": mem,
    }


def battery(_args: dict) -> dict:
    dumpsys = shutil.which("termux-battery-status")
    if dumpsys:
        return {"status": _run("termux-battery-status")}
    raw = _run("dumpsys battery 2>/dev/null")
    return {"status": raw or "Battery information is unavailable. Install Termux:API for structured battery data."}


def storage_info(_args: dict) -> dict:
    return {"df": _run("df -h 2>/dev/null | head -20"), "shared_storage": _run("df -h $HOME/storage 2>/dev/null | tail -1")}


def build_phone_tools():
    return {"system_info": system_info, "battery": battery, "storage_info": storage_info}
