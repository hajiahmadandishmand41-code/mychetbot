import { NextResponse } from "next/server";
import { currentSessionId, proxyBackend } from "@/lib/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const sessionId = await currentSessionId();
  if (!sessionId) return NextResponse.json({ error: "session_required" }, { status: 401 });
  return proxyBackend(`/history/${encodeURIComponent(sessionId)}`);
}
