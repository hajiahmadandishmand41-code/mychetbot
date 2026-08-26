from __future__ import annotations
import socket, subprocess

def ping(host: str, count: int = 3) -> str:
    p = subprocess.run(["ping", "-c", str(count), host], capture_output=True, text=True, timeout=30)
    return (p.stdout or p.stderr).strip()[:2000]

def dns_lookup(host: str) -> str:
    try:
        return f"{host} -> {socket.gethostbyname(host)}"
    except socket.gaierror as exc:
        return f"[dns-error] {exc}"

def port_check(host: str, port: int, timeout: float = 3.0) -> str:
    with socket.socket() as s:
        s.settimeout(timeout)
        return f"{host}:{port} " + ("باز است" if s.connect_ex((host, int(port))) == 0 else "بسته است")

def local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
