import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";
import { checkSameOrigin, isSignedSessionId, newSessionId } from "@/lib/server";

describe("web security boundaries", () => {
  it("creates signed session ids and rejects forged ids", () => {
    vi.stubEnv("MYCHATBOT_API_TOKEN", "test-web-backend-token");
    const sessionId = newSessionId();
    expect(isSignedSessionId(sessionId)).toBe(true);
    expect(isSignedSessionId(`${sessionId.slice(0, -1)}0`)).toBe(false);
    expect(isSignedSessionId("550e8400-e29b-41d4-a716-446655440000")).toBe(false);
    vi.unstubAllEnvs();
  });

  it("fails closed when an unsafe request has no Origin", () => {
    const request = new NextRequest("https://example.test/api/chat", {
      method: "POST",
      headers: { host: "example.test" },
    });
    expect(checkSameOrigin(request)).toBe(false);
  });

  it("accepts the exact same origin", () => {
    const request = new NextRequest("https://example.test/api/chat", {
      method: "POST",
      headers: { host: "example.test", origin: "https://example.test" },
    });
    expect(checkSameOrigin(request)).toBe(true);
  });

  it("rejects a different origin", () => {
    const request = new NextRequest("https://example.test/api/chat", {
      method: "POST",
      headers: { host: "example.test", origin: "https://attacker.test" },
    });
    expect(checkSameOrigin(request)).toBe(false);
  });
});
