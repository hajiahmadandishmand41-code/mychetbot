# Render Telegram and NaraRouter operations

## Render Telegram webhook

The Render web service runs `uvicorn interfaces.api_server:app` and receives Telegram updates through a webhook.

Required:
- `TELEGRAM_BOT_TOKEN`: current token created by BotFather.
- `TELEGRAM_WEBHOOK_URL`: public Render service origin, such as `https://example.onrender.com`, without the `/telegram/webhook` suffix. If empty, the service uses Render's `RENDER_EXTERNAL_URL`.

Optional:
- `TELEGRAM_WEBHOOK_SECRET`: secret used by Telegram's webhook header validation.
- `TELEGRAM_REQUIRE_ALLOWLIST=true` and `TELEGRAM_ALLOWLIST=123456789,987654321`: numeric Telegram user IDs allowed to use the webhook.

The Termux long-polling interface is separate. It uses `TELEGRAM_ALLOWED_CHAT_IDS`; that variable does not configure the Render webhook allow-list.

The startup path verifies the bot and registers the webhook. It does not rewrite the bot's display name, descriptions, or command list on every restart. Those profile settings are intentionally managed separately to avoid needless Telegram API rate limits.

A failed `sendChatAction` is non-fatal. The assistant still processes the user's message. If `sendMessage` returns HTTP 403, the target chat is rejecting delivery (for example, the user blocked the bot, has not started it, or the bot lacks permission in a group). The bot cannot force delivery to that chat; the user must unblock/start it or an administrator must restore the bot's permissions.

Telegram API exceptions must never be logged with their raw HTTP request URL because Telegram bot tokens are embedded in that URL.

## NaraRouter

Base URL:
`https://router.bynara.id/v1`

Chat endpoint:
`POST /chat/completions`

Use `GET /v1/models` with the same server-side Bearer API key to retrieve the model aliases available to that specific key and plan. Do not assume that a model shown in a public catalog is enabled for every account.

Common response meanings:
- `401`: missing or invalid API key.
- `402`: payment or available-credit requirement; changing model names does not repair an account balance.
- `403`: the account or plan is not allowed to use the selected model.
- `404`: model alias or endpoint was not found.
- `429`: request, concurrency, or model-tier daily quota was reached.

Do not retry billing failures or account-wide rate limits against multiple models. Model fallback is reserved for model/request rejection and transient upstream server errors. Do not log the Authorization header or full provider request details.

Official documentation: https://router.bynara.id/docs
