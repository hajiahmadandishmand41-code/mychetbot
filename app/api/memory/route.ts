import { NextRequest, NextResponse } from "next/server";
import { checkSameOrigin, currentSessionId, proxyBackend } from "@/lib/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function DELETE(request: NextRequest) {
  if (!checkSameOrigin(request)) {
    return NextResponse.json({ error: "csrf_blocked", message: "درخواست از مبدأ نامعتبر رد شد." }, { status: 403 });
  }
  const sessionId = await currentSessionId();
  if (!sessionId) return NextResponse.json({ error: "session_required" }, { status: 401 });
  return proxyBackend(`/memory/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
}
