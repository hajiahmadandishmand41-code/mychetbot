# MyChatBot Web on Vercel

این رابط وب یک Interface واحد برای همان Unified Agent پایتونی موجود در مخزن است و Agent/Memory/Tool Registry جدیدی ایجاد نمی‌کند.

## معماری

```text
Browser
  -> Next.js Web Chat
  -> /api/chat (same-origin server proxy)
  -> Existing FastAPI /chat
  -> core.agent.Agent
  -> Memory + Intent/Tool Planner + Tool Registry
  -> Router -> NaraRouter
  -> real assistant response
```

رابط وب فقط session cookie را مدیریت می‌کند، ورودی را اعتبارسنجی می‌کند، درخواست را rate-limit می‌کند و secret مربوط به Backend را در سمت Server نگه می‌دارد. هیچ API key در Browser ارسال نمی‌شود.

## Vercel Environment Variables

برای پروژه Vercel:

```text
MYCHATBOT_API_URL=https://YOUR-UNIFIED-AGENT-HOST
MYCHATBOT_API_TOKEN=<same API_TOKEN configured on the FastAPI backend>
```

روی Backend موجود:

```text
NARA_API_KEY=<secret>
NARA_BASE_URL=https://router.bynara.id/v1
DEFAULT_MODEL=<approved model name>
API_TOKEN=<long random secret>
```

`MYCHATBOT_API_TOKEN` باید با `API_TOKEN` Backend یکی باشد. `NARA_API_KEY` و `API_TOKEN` هرگز داخل کد، Git یا client bundle قرار نمی‌گیرند.

## Persistence

Memory فعلی پروژه SQLite-based و برای runtime پایدار مناسب است. رابط Vercel به همان API متصل می‌شود تا Agent و Memory اصلی duplicate نشوند. در Vercel به filesystem موقت/SQLite محلی برای persistence بلندمدت تکیه نشده است.

## Runtime capability boundary

Wi-Fi radio، Android/Termux APIs، local privileged filesystem و processهای مداوم روی runtime ابری Vercel وجود ندارند. Tool Registry فعلی این محدودیت را از طریق profile و runtime requirements اعمال می‌کند؛ UI هم Tool menu جداگانه‌ای نمایش نمی‌دهد. Web Research و قابلیت‌های شبکه‌ای که در Server profile مجاز باشند می‌توانند از همان Chat استفاده شوند.

## Streaming

Provider فعلی Nara در `providers/nara_provider.py` پاسخ متنی معمولی تولید می‌کند، نه stream. بنابراین Web UI یک generation state واقعی دارد اما stream جعلی نمی‌سازد. پاسخ به‌صورت یک response معتبر از `/api/chat` دریافت می‌شود.

## Identity

هویت کاربر-facing همیشه **MyChatBot** است.

سازنده: **حاجی احمد صالحی**

تیم سازنده: **تیم ربات‌های سازنده @فکر کن**
