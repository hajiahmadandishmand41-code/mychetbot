import { NextRequest, NextResponse } from "next/server";
import {
  checkSameOrigin,
  currentSessionId,
  newSessionId,
  setSessionResponse,
  validateSessionId,
} from "@/lib/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const existing = await currentSessionId();
  const sessionId = existing ?? newSessionId();
  if (existing) {
    return NextResponse.json(
      { sessionId },
      { headers: { "Cache-Control": "no-store" } },
    );
  }
  return setSessionResponse({ sessionId }, sessionId);
}

export async function POST(request: NextRequest) {
  if (!checkSameOrigin(request)) {
    return NextResponse.json(
      { error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." },
      { status: 403 },
    );
  }
  const body = (await request.json().catch(() => ({}))) as { sessionId?: unknown };
  const requested = typeof body.sessionId === "string" ? body.sessionId : "";
  const sessionId = validateSessionId(requested) ? requested : newSessionId();
  return setSessionResponse({ sessionId }, sessionId);
}
