from __future__ import annotations
import httpx

BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal"}

def http_get(url: str, max_chars: int = 4000) -> str:
    if any(h in url for h in BLOCKED_HOSTS):
        return "[blocked] دسترسی به metadata ممنوع است"
    if not url.startswith(("http://", "https://")):
        return "[error] فقط http/https"
    r = httpx.get(url, timeout=20, follow_redirects=True)
    return f"HTTP {r.status_code}\n{r.text[:max_chars]}"
