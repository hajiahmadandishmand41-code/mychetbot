import { NextResponse } from "next/server";

const MAX_MESSAGES = 40;
const MAX_MESSAGE_CHARS = 12_000;
const MAX_TOTAL_MESSAGE_CHARS = 24_000;

export type WebChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type NaraMessage = WebChatMessage | { role: "system"; content: string };

type NaraErrorDetails = {
  type: string;
  message: string;
  request_id?: string;
};

function getNaraConfig() {
  const baseUrl = (process.env.NARA_BASE_URL ?? "https://router.bynara.id/v1").replace(/\/$/, "");
  const model = (process.env.NARA_MODEL ?? process.env.DEFAULT_MODEL ?? "auto/bynara").trim() || "auto/bynara";
  const fallbackModel = (process.env.NARA_FALLBACK_MODEL ?? process.env.NARA_FALLBACK_MODELS?.split(",")[0] ?? "agnes-2.0-flash").trim() || "agnes-2.0-flash";
  return { baseUrl, model, fallbackModel };
}

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

function naraError(payload: unknown, status: number): NaraErrorDetails {
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

function isModelNotFound(status: number, details: NaraErrorDetails): boolean {
  const text = `${details.type} ${details.message}`.toLowerCase();
  return status === 404 || /model[^\n]*(not exist|not found|does not exist|unknown|unavailable)/i.test(text) || /requested model does not exist/i.test(text);
}

async function requestNara(baseUrl: string, model: string, messages: NaraMessage[], apiKey: string) {
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ model, messages, temperature: 0.7, max_tokens: 4096 }),
    cache: "no-store",
    signal: AbortSignal.timeout(60_000),
  });

  const raw = await response.text();
  let payload: unknown = {};
  try { payload = raw ? JSON.parse(raw) : {}; } catch { payload = { message: "پاسخ نامعتبر از NaraRouter دریافت شد." }; }
  return { response, payload };
}

export async function directNaraChat(messages: unknown) {
  const apiKey = (process.env.NARA_API_KEY ?? "").trim();
  const { baseUrl, model, fallbackModel } = getNaraConfig();
  if (!apiKey) return NextResponse.json({ error: "nara_not_configured", message: "کلید NaraRouter در Vercel تنظیم نشده است." }, { status: 503, headers: { "Cache-Control": "no-store" } });

  const cleaned = cleanMessages(messages);
  if (!cleaned.length) return NextResponse.json({ error: "empty_messages", message: "پیام معتبری برای ارسال وجود ندارد." }, { status: 400, headers: { "Cache-Control": "no-store" } });

  const system: NaraMessage = { role: "system", content: "تو «هوشمند» هستی؛ یک دستیار هوش مصنوعی واحد و حرفه‌ای. سازنده: حاجی احمد صالحی. تیم سازنده: تیم ربات‌های سازنده @فکر کن. درباره خودت با نام هوشمند صحبت کن و Provider یا مدل پشت‌صحنه را به‌عنوان هویت خود معرفی نکن. پاسخ‌ها را دقیق، مفید و به زبان کاربر بده. اگر برای یک کار نیاز به ابزار یا محیطی داری که در Web در دسترس نیست، صادقانه محدودیت را بگو و هرگز نتیجه جعلی نساز." };
  const conversation: NaraMessage[] = [system, ...cleaned];

  try {
    let { response, payload } = await requestNara(baseUrl, model, conversation, apiKey);
    let usedModel = model;
    let details: NaraErrorDetails | undefined;

    if (!response.ok) {
      details = naraError(payload, response.status);
      if (isModelNotFound(response.status, details) && fallbackModel !== model) {
        console.warn("NaraRouter model unavailable; retrying with fallback model", { requested_model: model, fallback_model: fallbackModel, status: response.status, type: details.type });
        ({ response, payload } = await requestNara(baseUrl, fallbackModel, conversation, apiKey));
        usedModel = fallbackModel;
        details = response.ok ? undefined : naraError(payload, response.status);
      }
    }

    if (!response.ok) {
      const errorDetails = details ?? naraError(payload, response.status);
      console.error("NaraRouter rejected request", { status: response.status, type: errorDetails.type, request_id: errorDetails.request_id, model: usedModel });
      return NextResponse.json({ error: "nara_request_failed", status: response.status, type: errorDetails.type, message: errorDetails.message, ...(errorDetails.request_id ? { request_id: errorDetails.request_id } : {}) }, { status: response.status, headers: { "Cache-Control": "no-store" } });
    }

    const content = payload && typeof payload === "object" && Array.isArray((payload as { choices?: unknown }).choices)
      ? (payload as { choices: Array<{ message?: { content?: unknown } }> }).choices[0]?.message?.content
      : null;
    if (typeof content !== "string" || !content.trim()) return NextResponse.json({ error: "empty_ai_response", message: "هوشمند پاسخ خالی از NaraRouter دریافت کرد." }, { status: 502, headers: { "Cache-Control": "no-store" } });
    return NextResponse.json({ reply: content.trim() }, { status: 200, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("Direct NaraRouter request failed", error);
    return NextResponse.json({ error: "nara_unreachable", message: "اتصال به NaraRouter برقرار نشد. لطفاً دوباره تلاش کنید." }, { status: 502, headers: { "Cache-Control": "no-store" } });
  }
}
