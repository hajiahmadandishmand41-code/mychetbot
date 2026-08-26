#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
termux-wake-lock || true
exec uvicorn interfaces.api_server:app --host 0.0.0.0 --port "${API_PORT:-8765}"
