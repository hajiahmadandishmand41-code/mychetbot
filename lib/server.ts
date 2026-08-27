import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { cookies, headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { validateSessionId } from "@/lib/validation";

const SESSION_COOKIE = "mychatbot_session";
const RATE_WINDOW_MS = 60_000;
const RATE_LIMIT = 30;
const SESSION_SIGNATURE_BYTES = 12;
const hits = new Map<string, number[]>();

export function backendConfig() {
  const baseUrl = (process.env.MYCHATBOT_API_URL ?? "").trim().replace(/\/+$/, "");
  const token = (process.env.MYCHATBOT_API_TOKEN ?? "").trim();
  return { baseUrl, token };
}

function sessionSigningKey() {
  const { token } = backendConfig();
  return token ? `mychatbot-web-session:${token}` : "";
}

function signSessionId(rawSessionId: string) {
  const key = sessionSigningKey();
  if (!key) return "";
  return createHmac("sha256", key).update(rawSessionId, "utf8").digest("hex").slice(0, SESSION_SIGNATURE_BYTES * 2);
}

export function newSessionId() {
  const raw = randomUUID().replace(/-/g, "");
  const signature = signSessionId(raw);
  return signature ? `${raw}-${signature}` : raw;
}

export function isSignedSessionId(value: string | null | undefined) {
  if (!validateSessionId(value)) return false;
  const rawValue = value!;
  if (/^[a-f0-9]{32}$/i.test(rawValue)) return true;
  const separator = rawValue.lastIndexOf("-");
  if (separator <= 0) return false;
  const raw = rawValue.slice(0, separator);
  const signature = rawValue.slice(separator + 1);
  if (!/^[a-f0-9]{32}$/i.test(raw) || !/^[a-f0-9]{24}$/i.test(signature)) return false;
  const expected = signSessionId(raw);
  if (!expected || expected.length !== signature.length) return false;
  return timingSafeEqual(Buffer.from(signature, "utf8"), Buffer.from(expected, "utf8"));
}

export async function currentSessionId() {
  const store = await cookies();
  const value = store.get(SESSION_COOKIE)?.value;
  return isSignedSessionId(value) ? value : null;
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
  if (!origin) return false;
  try {
    const expectedHost = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
    if (!expectedHost) return false;
    return new URL(origin).host === expectedHost;
  } catch {
    return false;
  }
}

export async function requestRateKey(sessionId: string) {
  const requestHeaders = await headers();
  const forwarded = requestHeaders.get("x-forwarded-for")?.split(",", 1)[0]?.trim();
  const realIp = requestHeaders.get("x-real-ip")?.trim();
  const source = forwarded || realIp || "unknown";
  return `web:${source}:${sessionId}`;
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
      {
        error: "backend_not_configured",
        message: "اتصال هوش مصنوعی آماده نیست: MYCHATBOT_API_URL و MYCHATBOT_API_TOKEN باید در محیط Web تنظیم شوند.",
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  let target: URL;
  try {
    target = new URL(path, `${baseUrl}/`);
    const allowedPaths = ["/chat", "/history/", "/memory/"];
    if (!allowedPaths.some((allowed) => target.pathname === allowed || target.pathname.startsWith(allowed))) {
      return NextResponse.json(
        { error: "backend_path_not_allowed", message: "مسیر Backend موردنظر مجاز نیست." },
        { status: 400, headers: { "Cache-Control": "no-store" } },
      );
    }
  } catch {
    return NextResponse.json(
      { error: "backend_configuration_error", message: "نشانی Backend معتبر نیست." },
      { status: 500, headers: { "Cache-Control": "no-store" } },
    );
  }

  const requestHeaders = new Headers(init.headers);
  requestHeaders.set("Authorization", `Bearer ${token}`);
  requestHeaders.set("Accept", "application/json");
  if (init.body) requestHeaders.set("Content-Type", "application/json");

  try {
    const response = await fetch(target, {
      ...init,
      headers: requestHeaders,
      cache: "no-store",
      signal: AbortSignal.timeout(65_000),
    });
    const text = await response.text();
    let payload: unknown;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = { error: "invalid_backend_response", message: "Backend پاسخ JSON معتبر برنگرداند." };
    }
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
