import { NextRequest, NextResponse } from "next/server";
import {
  checkSameOrigin,
  currentSessionId,
  isSignedSessionId,
  newSessionId,
  setSessionResponse,
} from "@/lib/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function issueSession() {
  try {
    return newSessionId();
  } catch {
    return null;
  }
}

export async function GET() {
  const existing = await currentSessionId();
  if (existing) {
    return NextResponse.json({ sessionId: existing }, { headers: { "Cache-Control": "no-store" } });
  }
  const sessionId = issueSession();
  if (!sessionId) {
    return NextResponse.json({ error: "session_not_configured", message: "امنیت نشست Web پیکربندی نشده است." }, { status: 503 });
  }
  return setSessionResponse({ sessionId }, sessionId);
}

export async function POST(request: NextRequest) {
  if (!checkSameOrigin(request)) {
    return NextResponse.json({ error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." }, { status: 403 });
  }
  const body = (await request.json().catch(() => ({}))) as { sessionId?: unknown };
  const requested = typeof body.sessionId === "string" ? body.sessionId : "";
  const sessionId = isSignedSessionId(requested) ? requested : issueSession();
  if (!sessionId) {
    return NextResponse.json({ error: "session_not_configured", message: "امنیت نشست Web پیکربندی نشده است." }, { status: 503 });
  }
  return setSessionResponse({ sessionId }, sessionId);
}
