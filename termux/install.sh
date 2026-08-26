#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

is_termux=false
if [[ "${TERMUX_VERSION:-}" != "" || "${PREFIX:-}" == "/data/data/com.termux/files/usr" || -d "/data/data/com.termux/files/usr" ]]; then
  is_termux=true
fi

if [[ "$is_termux" != true ]]; then
  echo "[error] این installer فقط برای Termux است. برای Linux از pip/venv استاندارد استفاده کنید." >&2
  exit 1
fi

echo "==> MyChatBot / Termux"
pkg update -y
pkg install -y python git openssh termux-api clang rust pkg-config libffi openssl

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> .env ایجاد شد؛ کلیدهای provider و API_TOKEN را تنظیم کنید."
fi

python -m pip install -r requirements.txt
termux-setup-storage || true
mkdir -p "$HOME/.mychatbot"
chmod 700 "$HOME/.mychatbot" 2>/dev/null || true

echo "==> نصب تمام شد. اجرا: bash termux/start.sh"
echo "==> API: bash termux/start_api.sh"
