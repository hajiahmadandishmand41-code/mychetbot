import { NextRequest, NextResponse } from "next/server";
import {
  allowRate,
  checkSameOrigin,
  currentSessionId,
  newSessionId,
  proxyBackend,
  setSessionResponse,
} from "@/lib/server";

const MAX_MESSAGE_CHARS = 12_000;

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function clientAddress(request: NextRequest) {
  return request.headers.get("x-forwarded-for")?.split(",", 1)[0]?.trim() || request.headers.get("x-real-ip") || "unknown";
}

export async function POST(request: NextRequest) {
  if (!checkSameOrigin(request)) {
    return NextResponse.json(
      { error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." },
      { status: 403, headers: { "Cache-Control": "no-store" } },
    );
  }

  if (!allowRate(`web-chat:${clientAddress(request)}`)) {
    return NextResponse.json(
      { error: "rate_limit", message: "تعداد درخواست‌ها زیاد است. کمی بعد دوباره تلاش کنید." },
      { status: 429, headers: { "Cache-Control": "no-store" } },
    );
  }

  const body = await request.json().catch(() => null) as { messages?: unknown; message?: unknown } | null;
  const fallback = typeof body?.message === "string" ? body.message.trim().slice(0, MAX_MESSAGE_CHARS) : "";
  const candidateMessages = Array.isArray(body?.messages) ? body.messages : [];
  const lastUser = [...candidateMessages].reverse().find((item) => {
    return !!item && typeof item === "object" && (item as { role?: unknown }).role === "user" && typeof (item as { content?: unknown }).content === "string";
  }) as { role: "user"; content: string } | undefined;
  const message = (lastUser?.content ?? fallback).trim().slice(0, MAX_MESSAGE_CHARS);
  if (!message) {
    return NextResponse.json(
      { error: "empty_messages", message: "پیام معتبری برای ارسال وجود ندارد." },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  let sessionId = await currentSessionId();
  if (!sessionId) sessionId = newSessionId();

  const backendResponse = await proxyBackend("/chat", {
    method: "POST",
    body: JSON.stringify({ message, session: sessionId }),
  });

  if (backendResponse.status >= 500 && backendResponse.status !== 503) {
    backendResponse.headers.set("Cache-Control", "no-store");
  }

  if (backendResponse.status === 200) {
    const payload = await backendResponse.json().catch(() => ({ error: "invalid_backend_response", message: "پاسخ نامعتبر از Backend دریافت شد." }));
    return setSessionResponse(payload, sessionId);
  }

  const payload = await backendResponse.json().catch(() => ({ error: "backend_request_failed", message: "درخواست هوش مصنوعی ناموفق بود." }));
  return setSessionResponse(payload, sessionId, backendResponse.status);
}
