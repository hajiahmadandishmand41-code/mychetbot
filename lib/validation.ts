const MAX_MESSAGE_CHARS = 12_000;
const SESSION_RE = /^[a-f0-9-]{16,64}$/i;

export function validateSessionId(value: string | null | undefined): value is string {
  return typeof value === "string" && SESSION_RE.test(value);
}

export function validateMessage(message: unknown) {
  if (typeof message !== "string") return { ok: false as const, error: "message must be a string" };
  const value = message.trim();
  if (!value) return { ok: false as const, error: "message must not be empty" };
  if (value.length > MAX_MESSAGE_CHARS) return { ok: false as const, error: "message is too long" };
  return { ok: true as const, value };
}
