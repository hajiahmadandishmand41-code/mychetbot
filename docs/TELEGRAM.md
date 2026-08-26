# Telegram Bot

The repository already contains `interfaces/telegram_bot.py`, which uses the Telegram Bot API with long polling (`getUpdates`) and sends replies with `sendMessage`.

For the bot `@MyChetAI2026_bot`, keep the BotFather token out of Git. Set it only in the runtime environment.

## Termux

From the repository root:

```bash
export TELEGRAM_BOT_TOKEN='YOUR_BOTFATHER_TOKEN'
bash termux/start_telegram.sh
```

The launcher refuses to start when `TELEGRAM_BOT_TOKEN` is missing.

## Security

Never put the BotFather token in source files, `.env` committed to Git, issues, or chat messages. If a token is exposed, revoke it with BotFather and create a new one.
