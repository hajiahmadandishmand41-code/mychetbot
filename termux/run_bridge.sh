#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

case "${1:-}" in
  cli) exec bash "$SCRIPT_DIR/start.sh" ;;
  api) exec bash "$SCRIPT_DIR/start_api.sh" ;;
  *) echo "usage: bash termux/run_bridge.sh {cli|api}" >&2; exit 2 ;;
esac
