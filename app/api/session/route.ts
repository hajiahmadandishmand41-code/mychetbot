import { NextRequest, NextResponse } from "next/server";
import {
  currentSessionId,
  newSessionId,
  setSessionResponse,
  validateSessionId,
} from "@/lib/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const existing = await currentSessionId();
  const sessionId = existing ?? newSessionId();
  if (existing) return NextResponse.json({ sessionId }, { headers: { "Cache-Control": "no-store" } });
  return setSessionResponse({ sessionId }, sessionId);
}

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => ({}))) as { sessionId?: unknown };
  const requested = typeof body.sessionId === "string" ? body.sessionId : "";
  const sessionId = validateSessionId(requested) ? requested : newSessionId();
  return setSessionResponse({ sessionId }, sessionId);
}
