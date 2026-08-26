#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
python -m uvicorn termux.server:app --host "${BRIDGE_HOST:-127.0.0.1}" --port "${BRIDGE_PORT:-18923}"
