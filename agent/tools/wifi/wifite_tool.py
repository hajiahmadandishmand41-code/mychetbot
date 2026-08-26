"""Wifite capability detection and guarded launcher metadata.

The launcher is intentionally not exposed as an unrestricted shell command.
Actual Wifite runs require the CONFIRM permission and should only be used on
networks the user owns or is explicitly authorized to test.
"""
import shutil


def wifite_detect(_args: dict) -> dict:
    path = shutil.which("wifite") or shutil.which("wifite.py")
    return {
        "installed": bool(path),
        "path": path,
        "message": "Wifite is available." if path else "Wifite is not installed",
        "root": _root_status(),
    }


def _root_status() -> dict:
    su = shutil.which("su")
    if not su:
        return {"available": False, "message": "This operation may require Root/extra permissions."}
    try:
        import subprocess
        p = subprocess.run([su, "-c", "id"], capture_output=True, text=True, timeout=3)
        value = (p.stdout or p.stderr).strip()
        return {"available": p.returncode == 0 and "uid=0" in value, "message": value[:200]}
    except Exception as exc:
        return {"available": False, "message": str(exc)}


def wifite_tool(args: dict) -> str:
    """Return a guarded execution plan; server permission controls execution."""
    action = str(args.get("action", "audit")).lower()
    if action != "audit":
        return "Only the authorized audit mode is supported by the MyChatBot Wifite adapter."
    detected = wifite_detect({})
    if not detected["installed"]:
        return "Wifite is not installed"
    if not detected["root"]["available"]:
        return "This operation may require Root/extra permissions."
    return (
        "Wifite is installed and root appears available. Confirm that you own the target network "
        "or have written authorization before launching the audit from Termux."
    )


def build_wifite_tools():
    return {"wifite_detect": wifite_detect, "wifite_tool": wifite_tool}
