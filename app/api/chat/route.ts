import { NextRequest, NextResponse } from "next/server";

const NARA_BASE_URL = "https://router.bynara.id/v1";
const NARA_MODEL = "auto/bynara";
const MAX_MESSAGES = 40;
const MAX_CHARS = 12_000;
const RATE_LIMIT = 30;
const RATE_WINDOW_MS = 60_000;
const rateHits = new Map<string, number[]>();

type ChatMessage = { role: "user" | "assistant"; content: string };

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function sameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

function clientAddress(request: NextRequest) {
  return request.headers.get("x-forwarded-for")?.split(",", 1)[0]?.trim() || request.headers.get("x-real-ip") || "unknown";
}

function allowRequest(key: string) {
  const now = Date.now();
  const current = (rateHits.get(key) ?? []).filter((time) => now - time < RATE_WINDOW_MS);
  if (current.length >= RATE_LIMIT) {
    rateHits.set(key, current);
    return false;
  }
  current.push(now);
  rateHits.set(key, current);
  if (rateHits.size > 4096) {
    for (const [entry, times] of rateHits) {
      if (!times.some((time) => now - time < RATE_WINDOW_MS)) rateHits.delete(entry);
    }
  }
  return true;
}

function sanitizeMessages(value: unknown): ChatMessage[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is { role?: unknown; content?: unknown } => !!item && typeof item === "object")
    .map((item) => ({
      role: item.role === "assistant" ? "assistant" as const : "user" as const,
      content: typeof item.content === "string" ? item.content.trim().slice(0, MAX_CHARS) : "",
    }))
    .filter((item) => item.content)
    .slice(-MAX_MESSAGES);
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." }, { status: 403 });
  }

  if (!allowRequest(`web:${clientAddress(request)}`)) {
    return NextResponse.json({ error: "rate_limit", message: "تعداد درخواست‌ها زیاد است. کمی بعد دوباره تلاش کنید." }, { status: 429 });
  }

  const apiKey = (process.env.NARA_API_KEY ?? "").trim();
  if (!apiKey) {
    return NextResponse.json({ error: "nara_not_configured", message: "کلید NaraRouter در Vercel تنظیم نشده است." }, { status: 503 });
  }

  const body = await request.json().catch(() => null) as { messages?: unknown; message?: unknown } | null;
  const messages = sanitizeMessages(body?.messages);
  const fallbackMessage = typeof body?.message === "string" ? body.message.trim().slice(0, MAX_CHARS) : "";
  const conversation = messages.length ? messages : fallbackMessage ? [{ role: "user" as const, content: fallbackMessage }] : [];

  if (!conversation.length) {
    return NextResponse.json({ error: "empty_message", message: "پیامی برای ارسال وجود ندارد." }, { status: 400 });
  }

  const system: ChatMessage = {
    role: "user",
    content: "تو «هوشمند» هستی؛ یک دستیار هوش مصنوعی فارسی و چندزبانه، سریع، دقیق و حرفه‌ای. سازنده: حاجی احمد صالحی. تیم سازنده: تیم ربات‌های سازنده @فکر کن. هرگز Provider، مدل یا API پشت‌صحنه را هویت خود معرفی نکن. پاسخ را با زبان کاربر بده و توانایی یا نتیجه‌ای را جعل نکن.",
  };

  try {
    const response = await fetch(`${NARA_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        model: NARA_MODEL,
        messages: [
          { role: "system", content: system.content },
          ...conversation,
        ],
        temperature: 0.7,
        max_tokens: 4096,
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });

    const raw = await response.text();
    let payload: unknown = {};
    try {
      payload = raw ? JSON.parse(raw) : {};
    } catch {
      payload = {};
    }

    if (!response.ok) {
      const providerError = payload && typeof payload === "object" && "error" in payload ? (payload as { error?: unknown }).error : null;
      const message = typeof providerError === "string" ? providerError : "NaraRouter درخواست را نپذیرفت.";
      return NextResponse.json({ error: "nara_request_failed", message }, { status: response.status });
    }

    const reply = payload && typeof payload === "object" && Array.isArray((payload as { choices?: unknown }).choices)
      ? (payload as { choices: Array<{ message?: { content?: unknown } }> }).choices[0]?.message?.content
      : null;

    if (typeof reply !== "string" || !reply.trim()) {
      return NextResponse.json({ error: "empty_ai_response", message: "NaraRouter پاسخ معتبری برنگرداند." }, { status: 502 });
    }

    return NextResponse.json({ reply: reply.trim() }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("Direct NaraRouter chat failed", error);
    return NextResponse.json({ error: "nara_unreachable", message: "ارتباط با NaraRouter برقرار نشد. دوباره تلاش کنید." }, { status: 502 });
  }
}
