import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SmartChat from "@/components/smart-chat";

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, "matchMedia", { configurable: true, value: () => ({ matches: false, media: "", onchange: null, addListener: vi.fn(), removeListener: vi.fn(), addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn() }) });
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: vi.fn() });
  vi.restoreAllMocks();
});

function mockChatApi() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    expect(String(input)).toContain("/api/chat");
    expect(init?.method).toBe("POST");
    const body = JSON.parse(String(init?.body)) as { messages: Array<{ content: string }> };
    return new Response(JSON.stringify({ reply: `پاسخ هوشمند: ${body.messages.at(-1)?.content ?? ""}` }), { status: 200 });
  });
}

describe("هوشمند web chat", () => {
  it("starts without session initialization or backend dependency", async () => {
    render(<SmartChat />);
    expect(await screen.findByText("سلام! 👋")).toBeTruthy();
    expect(screen.getByText(/من هوشمند هستم/)).toBeTruthy();
    expect(screen.getByPlaceholderText("پیامت را اینجا بنویس…")).toBeTruthy();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("sends the current conversation to the real chat API", async () => {
    const fetchMock = mockChatApi();
    render(<SmartChat />);
    const input = await screen.findByPlaceholderText("پیامت را اینجا بنویس…");
    fireEvent.change(input, { target: { value: "سلام" } });
    fireEvent.submit(input.closest("form")!);
    expect(await screen.findByText("پاسخ هوشمند: سلام")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const request = fetchMock.mock.calls[0][1];
    const body = JSON.parse(String(request?.body)) as { messages: Array<{ role: string; content: string }> };
    expect(body.messages.map((m) => m.role)).toEqual(["user"]);
  });

  it("supports multiple chats through the mobile three-dot menu", async () => {
    render(<SmartChat />);
    await screen.findByText("سلام! 👋");
    fireEvent.click(screen.getByRole("button", { name: "گزینه‌های بیشتر" }));
    expect(screen.getByRole("menuitem", { name: /برگشت به چت/ })).toBeTruthy();
    fireEvent.click(screen.getByRole("menuitem", { name: /چت جدید/ }));
    expect(screen.getByText("چت جدید")).toBeTruthy();
  });

  it("persists chats and restores them after remount", async () => {
    const fetchMock = mockChatApi();
    const first = render(<SmartChat />);
    const input = await screen.findByPlaceholderText("پیامت را اینجا بنویس…");
    fireEvent.change(input, { target: { value: "حافظه" } });
    fireEvent.submit(input.closest("form")!);
    expect(await screen.findByText("پاسخ هوشمند: حافظه")).toBeTruthy();
    first.unmount();
    render(<SmartChat />);
    expect(await screen.findByText("پاسخ هوشمند: حافظه")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("toggles theme", async () => {
    render(<SmartChat />);
    await screen.findByText("سلام! 👋");
    fireEvent.click(screen.getByRole("button", { name: /حالت روشن|حالت تاریک/ }));
    await waitFor(() => expect(document.documentElement.dataset.theme).toBe("light"));
  });
});
