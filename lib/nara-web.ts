import { NextResponse } from "next/server";

const NARA_BASE_URL = "https://router.bynara.id/v1";
const NARA_MODEL = "auto/bynara";
const MAX_MESSAGES = 40;
const MAX_MESSAGE_CHARS = 12_000;

export type WebChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

function cleanMessages(messages: unknown): WebChatMessage[] {
  if (!Array.isArray(messages)) return [];
  return messages
    .filter((item): item is { role: unknown; content: unknown } => !!item && typeof item === "object")
    .map((item) => ({
      role: item.role === "assistant" ? "assistant" : "user",
      content: typeof item.content === "string" ? item.content.trim().slice(0, MAX_MESSAGE_CHARS) : "",
    }))
    .filter((item) => item.content)
    .slice(-MAX_MESSAGES);
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

  const system: WebChatMessage = {
    role: "system",
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
      const message =
        payload && typeof payload === "object" && "error" in payload
          ? typeof (payload as { error?: unknown }).error === "string"
            ? (payload as { error: string }).error
            : "NaraRouter درخواست را رد کرد."
          : "NaraRouter درخواست را رد کرد.";
      return NextResponse.json(
        { error: "nara_request_failed", message },
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
      { reply: content.trim(), model: NARA_MODEL },
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
