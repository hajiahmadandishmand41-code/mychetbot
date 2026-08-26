#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "[error] TELEGRAM_BOT_TOKEN is not set." >&2
  echo "Set it in the Termux environment before starting the bot." >&2
  exit 1
fi

exec python -m interfaces.telegram_bot
