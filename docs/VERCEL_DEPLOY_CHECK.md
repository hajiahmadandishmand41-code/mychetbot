# Vercel deployment verification

The Web Chat uses the server-side Backend path in `app/api/chat/route.ts`.

## Current Backend

The Python/FastAPI backend is deployed separately from the Web UI. The Web runtime must use:

```text
MYCHATBOT_API_URL=https://mychatbot-backend-lred.onrender.com
MYCHATBOT_API_TOKEN=<same value as Backend API_TOKEN>
```

The Backend uses these provider settings:

```text
NARA_API_KEY=<secret kept only on Backend>
NARA_BASE_URL=https://router.bynara.id/v1
DEFAULT_MODEL=laguna-s-2.1
NARA_FALLBACK_MODELS=<comma-separated IDs returned by authenticated GET /v1/models>
```

Never expose `NARA_API_KEY` to the Vercel client bundle.
