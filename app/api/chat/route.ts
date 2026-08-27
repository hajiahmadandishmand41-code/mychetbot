import { NextRequest, NextResponse } from "next/server";
import {
  allowRate,
  checkSameOrigin,
  currentSessionId,
  proxyBackend,
  requestRateKey,
  validateMessage,
} from "@/lib/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!checkSameOrigin(request)) {
    return NextResponse.json({ error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." }, { status: 403 });
  }
  const sessionId = await currentSessionId();
  if (!sessionId) {
    return NextResponse.json({ error: "session_required", message: "نشست معتبر پیدا نشد؛ صفحه را تازه‌سازی کنید." }, { status: 401 });
  }
  if (!allowRate(await requestRateKey(sessionId))) {
    return NextResponse.json({ error: "rate_limit", message: "تعداد درخواست‌ها زیاد است. کمی بعد دوباره تلاش کنید." }, { status: 429 });
  }

  const body = await request.json().catch(() => null);
  const message = validateMessage(body && typeof body === "object" ? (body as { message?: unknown }).message : undefined);
  if (!message.ok) {
    return NextResponse.json({ error: "invalid_request", message: message.error }, { status: 400 });
  }

  return proxyBackend("/chat", {
    method: "POST",
    body: JSON.stringify({ message: message.value, session: sessionId }),
  });
}
