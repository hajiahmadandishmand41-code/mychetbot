import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChatShell from "@/components/chat-shell";

const sessionId = "550e8400e29b41d4a716446655440000";

function mockFetch() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.endsWith("/api/session") && method === "GET") return new Response(JSON.stringify({ sessionId }), { status: 200 });
    if (url.endsWith("/api/history")) return new Response(JSON.stringify({ messages: [] }), { status: 200 });
    if (url.endsWith("/api/chat") && method === "POST") {
      const body = JSON.parse(String(init?.body)) as { message: string };
      return new Response(JSON.stringify({ reply: `پاسخ واقعی: ${body.message}\n\n\`\`\`ts\nconst ok = true\n\`\`\`` }), { status: 200 });
    }
    throw new Error(`unexpected fetch ${method} ${url}`);
  });
}

describe("Sepanta web chat", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.dataset.theme = "dark";
    Object.defineProperty(window, "matchMedia", { configurable: true, value: () => ({ matches: false, media: "", onchange: null, addListener: vi.fn(), removeListener: vi.fn(), addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn() }) });
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: vi.fn() });
    vi.restoreAllMocks();
  });

  it("renders the production empty state and chat input", async () => {
    mockFetch();
    render(<ChatShell />);
    expect(await screen.findByText("سلام! 👋")).toBeTruthy();
    expect(screen.getByPlaceholderText("پیام خود را بنویسید…")).toBeTruthy();
    expect(screen.getByText(/من سپنتا هستم\./)).toBeTruthy();
  });

  it("sends a real request through /api/chat and renders markdown/code", async () => {
    mockFetch();
    render(<ChatShell />);
    const input = await screen.findByPlaceholderText("پیام خود را بنویسید…");
    fireEvent.change(input, { target: { value: "سلام سپنتا" } });
    fireEvent.submit(input.closest("form")!);
    expect(await screen.findByText("پاسخ واقعی: سلام سپنتا")).toBeTruthy();
    expect(screen.getByText("const ok = true")).toBeTruthy();
  });

  it("opens the mobile three-dot menu and exposes back/new-chat actions", async () => {
    mockFetch();
    render(<ChatShell />);
    await screen.findByText("سلام! 👋");
    fireEvent.click(screen.getByRole("button", { name: "گزینه‌های بیشتر" }));
    expect(screen.getByRole("menuitem", { name: /برگشت به چت/ })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /چت جدید/ })).toBeTruthy();
  });

  it("toggles dark/light mode from the single chat shell", async () => {
    mockFetch();
    render(<ChatShell />);
    await screen.findByText("سلام! 👋");
    expect(document.documentElement.dataset.theme).toBe("dark");
    fireEvent.click(screen.getByRole("button", { name: /حالت روشن|حالت تاریک/ }));
    await waitFor(() => expect(document.documentElement.dataset.theme).toBe("light"));
  });
});
