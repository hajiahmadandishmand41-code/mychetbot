from __future__ import annotations
import asyncio, os
import httpx
from core.agent import Agent

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

async def main() -> None:
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN تنظیم نشده است")
    offset = 0
    async with httpx.AsyncClient(timeout=70) as client:
        while True:
            r = await client.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 60})
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text, chat = msg.get("text"), msg.get("chat", {}).get("id")
                if not text or chat is None:
                    continue
                agent = Agent(session=f"tg:{chat}")
                reply = await agent.ask(text)
                await client.post(f"{API}/sendMessage", json={"chat_id": chat, "text": reply})

if __name__ == "__main__":
    asyncio.run(main())
