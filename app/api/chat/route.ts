import { NextRequest, NextResponse } from "next/server";
import { directNaraChat } from "@/lib/nara-web";
import { allowRate, checkSameOrigin } from "@/lib/server";

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
  const messages = Array.isArray(body?.messages)
    ? body.messages
    : fallback
      ? [{ role: "user", content: fallback }]
      : [];

  return directNaraChat(messages);
}
