import { afterEach, describe, expect, it, vi } from "vitest";
import { directNaraChat } from "../lib/nara-web";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("NaraRouter model fallback", () => {
  it("retries with the fallback model when the selected model does not exist", async () => {
    vi.stubEnv("NARA_API_KEY", "test-key");
    vi.stubEnv("NARA_MODEL", "missing-model");
    vi.stubEnv("NARA_FALLBACK_MODEL", "agnes-2.0-flash");

    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: { type: "invalid_request_error", message: "The requested model does not exist." } }), { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ choices: [{ message: { content: "ok" } }] }), { status: 200 }));
    globalThis.fetch = fetchMock as typeof fetch;

    const response = await directNaraChat([{ role: "user", content: "سلام" }]);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ reply: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string).model).toBe("missing-model");
    expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string).model).toBe("agnes-2.0-flash");
  });
});
