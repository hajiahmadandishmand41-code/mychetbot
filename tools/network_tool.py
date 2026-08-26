from __future__ import annotations

import re
import socket
import subprocess

_HOST_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,253}$")


def _validate_host(host: str) -> str:
    value = host.strip()
    if not value or not _HOST_RE.fullmatch(value):
        raise ValueError("invalid host")
    return value


def ping(host: str, count: int = 3, timeout: int = 10) -> str:
    target = _validate_host(host)
    safe_count = max(1, min(int(count), 4))
    safe_timeout = max(1, min(int(timeout), 30))
    try:
        p = subprocess.run(
            ["ping", "-c", str(safe_count), "-W", str(safe_timeout), target],
            capture_output=True,
            text=True,
            timeout=safe_timeout * safe_count + 5,
            check=False,
        )
    except FileNotFoundError:
        return "[error] ping command is not installed"
    except subprocess.TimeoutExpired:
        return "[timeout] ping timed out"
    return (p.stdout or p.stderr).strip()[:2000]


def dns_lookup(host: str) -> str:
    target = _validate_host(host)
    try:
        addresses = sorted({str(item[4][0]) for item in socket.getaddrinfo(target, None)})
        return f"{target} -> {', '.join(addresses)}"
    except socket.gaierror as exc:
        return f"[dns-error] {exc}"


def port_check(host: str, port: int, timeout: float = 3.0) -> str:
    target = _validate_host(host)
    safe_port = int(port)
    if not 1 <= safe_port <= 65535:
        return "[arg-error] port must be between 1 and 65535"
    safe_timeout = max(0.5, min(float(timeout), 10.0))
    try:
        with socket.socket() as sock:
            sock.settimeout(safe_timeout)
            return f"{target}:{safe_port} " + ("باز است" if sock.connect_ex((target, safe_port)) == 0 else "بسته است")
    except OSError as exc:
        return f"[network-error] {exc}"


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
