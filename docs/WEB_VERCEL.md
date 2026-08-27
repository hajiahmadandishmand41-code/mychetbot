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
  -> Router -> NaraProvider -> NaraRouter
  -> real assistant response
```

مسیر Web دیگر مستقیماً NaraRouter را صدا نمی‌زند. فقط آخرین پیام کاربر را به همان `/chat` اصلی می‌دهد تا Web، Telegram و API از یک Agent و یک Memory استفاده کنند. این کار از ارسال دوباره کل تاریخچه به مدل و از اجرای دو مسیر مستقل جلوگیری می‌کند.

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
DEFAULT_MODEL=auto/bynara
NARA_FALLBACK_MODELS=agnes-2.5-flash,agnes-2.0-flash
API_TOKEN=<long random secret>
```

`MYCHATBOT_API_TOKEN` باید با `API_TOKEN` Backend یکی باشد. `NARA_API_KEY` و `API_TOKEN` هرگز داخل کد، Git یا client bundle قرار نمی‌گیرند.

## Stability

Provider Nara برای خطاهای موقت شبکه، timeout، `429` و `5xx` چند Retry کوتاه و محدود با backoff دارد. خطاهای احراز هویت و درخواست نامعتبر Retry نمی‌شوند. اگر مدل انتخابی به‌دلیل نبودن alias یا محدودیت پلن قابل استفاده نباشد، Provider بدون تأخیر به یکی از `NARA_FALLBACK_MODELS` می‌رود.

NaraRouter رسماً اعلام می‌کند که `429` برای rate/concurrency و `503` برای موقتاً در دسترس نبودن سرویس استفاده می‌شود و توصیه می‌کند با backoff دوباره تلاش شود. citeturn479998search0

## Persistence

Memory فعلی پروژه SQLite-based و برای runtime پایدار مناسب است. رابط Vercel به همان API متصل می‌شود تا Agent و Memory اصلی duplicate نشوند. در Vercel به filesystem موقت/SQLite محلی برای persistence بلندمدت تکیه نشده است.

## Runtime capability boundary

Wi-Fi radio، Android/Termux APIs، local privileged filesystem و processهای مداوم روی runtime ابری Vercel وجود ندارند. Tool Registry فعلی این محدودیت را از طریق profile و runtime requirements اعمال می‌کند؛ UI هم Tool menu جداگانه‌ای نمایش نمی‌دهد. Web Research و قابلیت‌های شبکه‌ای که در Server profile مجاز باشند می‌توانند از همان Chat استفاده شوند.

## Streaming

Provider فعلی پاسخ متنی معمولی تولید می‌کند، نه stream. بنابراین Web UI یک generation state واقعی دارد اما stream جعلی نمی‌سازد.

## Identity

هویت کاربر-facing همیشه **MyChatBot** است.

سازنده: **حاجی احمد صالحی**

تیم سازنده: **تیم ربات‌های سازنده @فکر کن**
