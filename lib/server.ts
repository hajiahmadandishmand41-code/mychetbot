import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { validateMessage, validateSessionId } from "@/lib/validation";

const SESSION_COOKIE = "mychatbot_session";
const RATE_WINDOW_MS = 60_000;
const RATE_LIMIT = 30;
const hits = new Map<string, number[]>();

export function backendConfig() {
  const baseUrl = (process.env.MYCHATBOT_API_URL ?? "").trim().replace(/\/+$/, "");
  const token = (process.env.MYCHATBOT_API_TOKEN ?? "").trim();
  return { baseUrl, token };
}

export function newSessionId() {
  return crypto.randomUUID();
}

export async function currentSessionId() {
  const store = await cookies();
  const value = store.get(SESSION_COOKIE)?.value;
  return validateSessionId(value) ? value : null;
}

export function sessionCookieHeader(sessionId: string) {
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  return `${SESSION_COOKIE}=${encodeURIComponent(sessionId)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000${secure}`;
}

export function setSessionResponse(body: unknown, sessionId: string, status = 200) {
  const response = NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });
  response.headers.set("Set-Cookie", sessionCookieHeader(sessionId));
  return response;
}

export function checkSameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    const expectedHost = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
    return new URL(origin).host === expectedHost;
  } catch {
    return false;
  }
}

export function allowRate(key: string) {
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((timestamp) => now - timestamp < RATE_WINDOW_MS);
  if (recent.length >= RATE_LIMIT) {
    hits.set(key, recent);
    return false;
  }
  recent.push(now);
  hits.set(key, recent);
  if (hits.size > 4096) {
    for (const [entry, timestamps] of hits) {
      if (!timestamps.some((timestamp) => now - timestamp < RATE_WINDOW_MS)) hits.delete(entry);
    }
  }
  return true;
}

export async function proxyBackend(path: string, init: RequestInit = {}) {
  const { baseUrl, token } = backendConfig();
  if (!baseUrl || !token) {
    return NextResponse.json(
      { error: "backend_not_configured", message: "MyChatBot Web نیازمند MYCHATBOT_API_URL و MYCHATBOT_API_TOKEN برای اتصال به Unified Agent است." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(65_000),
    });
    const text = await response.text();
    let payload: unknown;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { error: "invalid_backend_response", message: "Backend returned invalid JSON." }; }
    return NextResponse.json(payload, {
      status: response.status,
      headers: { "Cache-Control": "no-store", "X-MyChatBot-Streaming": "false" },
    });
  } catch (error) {
    console.error("Unified Agent backend proxy failed", error);
    return NextResponse.json(
      { error: "backend_unreachable", message: "اتصال به Unified Agent برقرار نشد. پیکربندی Backend و دسترسی شبکه را بررسی کنید." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export { validateMessage, validateSessionId } from "@/lib/validation";
