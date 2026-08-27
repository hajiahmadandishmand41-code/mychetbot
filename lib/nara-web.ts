import { NextResponse } from "next/server";

const NARA_BASE_URL = (process.env.NARA_BASE_URL ?? "https://router.bynara.id/v1").replace(/\/$/, "");
const NARA_MODEL = (process.env.NARA_MODEL ?? "auto/bynara").trim() || "auto/bynara";
const MAX_MESSAGES = 40;
const MAX_MESSAGE_CHARS = 12_000;
const MAX_TOTAL_MESSAGE_CHARS = 24_000;

export type WebChatMessage = {
  role: "user" | "assistant";
  content: string;
};

function cleanMessages(messages: unknown): WebChatMessage[] {
  if (!Array.isArray(messages)) return [];

  const cleaned: WebChatMessage[] = [];
  let totalChars = 0;
  const items = messages.slice(-MAX_MESSAGES).reverse();

  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const candidate = item as { role?: unknown; content?: unknown };
    if (candidate.role !== "user" && candidate.role !== "assistant") continue;
    if (typeof candidate.content !== "string") continue;

    const content = candidate.content.trim().slice(0, MAX_MESSAGE_CHARS);
    if (!content) continue;
    if (totalChars + content.length > MAX_TOTAL_MESSAGE_CHARS) break;

    cleaned.push({ role: candidate.role, content });
    totalChars += content.length;
  }

  return cleaned.reverse();
}

function naraError(payload: unknown, status: number) {
  if (payload && typeof payload === "object" && "error" in payload) {
    const error = (payload as { error?: unknown }).error;
    if (typeof error === "string" && error.trim()) return { type: "unknown", message: error.trim() };
    if (error && typeof error === "object") {
      const item = error as { type?: unknown; message?: unknown; request_id?: unknown };
      return {
        type: typeof item.type === "string" ? item.type : `http_${status}`,
        message: typeof item.message === "string" && item.message.trim() ? item.message.trim() : "NaraRouter درخواست را رد کرد.",
        request_id: typeof item.request_id === "string" ? item.request_id : undefined,
      };
    }
  }

  if (payload && typeof payload === "object" && "message" in payload) {
    const message = (payload as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return { type: `http_${status}`, message: message.trim() };
  }

  return { type: `http_${status}`, message: "NaraRouter درخواست را رد کرد." };
}

export async function directNaraChat(messages: unknown) {
  const apiKey = (process.env.NARA_API_KEY ?? "").trim();
  if (!apiKey) {
    return NextResponse.json(
      { error: "nara_not_configured", message: "کلید NaraRouter در Vercel تنظیم نشده است." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  const cleaned = cleanMessages(messages);
  if (!cleaned.length) {
    return NextResponse.json(
      { error: "empty_messages", message: "پیام معتبری برای ارسال وجود ندارد." },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  const system = {
    role: "system" as const,
    content:
      "تو «هوشمند» هستی؛ یک دستیار هوش مصنوعی واحد و حرفه‌ای. سازنده: حاجی احمد صالحی. تیم سازنده: تیم ربات‌های سازنده @فکر کن. درباره خودت با نام هوشمند صحبت کن و Provider یا مدل پشت‌صحنه را به‌عنوان هویت خود معرفی نکن. پاسخ‌ها را دقیق، مفید و به زبان کاربر بده. اگر برای یک کار نیاز به ابزار یا محیطی داری که در Web در دسترس نیست، صادقانه محدودیت را بگو و هرگز نتیجه جعلی نساز.",
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
        messages: [system, ...cleaned],
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
      payload = { message: "پاسخ نامعتبر از NaraRouter دریافت شد." };
    }

    if (!response.ok) {
      const details = naraError(payload, response.status);
      console.error("NaraRouter rejected request", {
        status: response.status,
        type: details.type,
        request_id: "request_id" in details ? details.request_id : undefined,
        model: NARA_MODEL,
      });
      return NextResponse.json(
        {
          error: "nara_request_failed",
          status: response.status,
          type: details.type,
          message: details.message,
          ...( "request_id" in details && details.request_id ? { request_id: details.request_id } : {}),
        },
        { status: response.status, headers: { "Cache-Control": "no-store" } },
      );
    }

    const content =
      payload && typeof payload === "object" && Array.isArray((payload as { choices?: unknown }).choices)
        ? (payload as { choices: Array<{ message?: { content?: unknown } }> }).choices[0]?.message?.content
        : null;

    if (typeof content !== "string" || !content.trim()) {
      return NextResponse.json(
        { error: "empty_ai_response", message: "هوشمند پاسخ خالی از NaraRouter دریافت کرد." },
        { status: 502, headers: { "Cache-Control": "no-store" } },
      );
    }

    return NextResponse.json(
      { reply: content.trim() },
      { status: 200, headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    console.error("Direct NaraRouter request failed", error);
    return NextResponse.json(
      { error: "nara_unreachable", message: "اتصال به NaraRouter برقرار نشد. لطفاً دوباره تلاش کنید." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
