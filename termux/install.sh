#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
echo "==> نصب پیش‌نیازهای MyChatBot روی Termux"
pkg update -y
pkg install -y python git openssh termux-api clang libffi openssl
pip install --upgrade pip
pip install -r requirements.txt
termux-setup-storage || true
mkdir -p "$HOME/.mychatbot"
[ -f .env ] || cp .env.example .env
echo "==> نصب تمام شد. فایل .env را ویرایش کنید سپس: bash termux/start.sh"
