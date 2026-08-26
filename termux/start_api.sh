#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"
termux-wake-lock 2>/dev/null || true
exec python -m uvicorn interfaces.api_server:app --host "${API_HOST:-127.0.0.1}" --port "${API_PORT:-8765}"
