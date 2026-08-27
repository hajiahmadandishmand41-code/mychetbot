# Vercel deployment verification

The Web Chat uses the server-side NaraRouter path in `app/api/chat/route.ts`.
Required Web secret: `NARA_API_KEY`.

This file intentionally contains no secrets and exists to trigger a fresh Vercel deployment after the Web Chat architecture update.
