import { describe, expect, it } from "vitest";
import { validateMessage, validateSessionId } from "@/lib/validation";

describe("web validation", () => {
  it("accepts generated-looking session ids and rejects arbitrary input", () => {
    expect(validateSessionId("550e8400-e29b-41d4-a716-446655440000")).toBe(true);
    expect(validateSessionId("../../other-session")).toBe(false);
    expect(validateSessionId("short")).toBe(false);
  });

  it("trims valid messages and rejects malformed payloads", () => {
    expect(validateMessage("  سلام  ")).toEqual({ ok: true, value: "سلام" });
    expect(validateMessage(123)).toEqual({ ok: false, error: "message must be a string" });
    expect(validateMessage("   ")).toEqual({ ok: false, error: "message must not be empty" });
    expect(validateMessage("x".repeat(12_001))).toEqual({ ok: false, error: "message is too long" });
  });
});
