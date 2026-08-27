"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import MarkdownMessage from "@/components/markdown-message";

type Message = { role: "user" | "assistant"; content: string };
type Chat = { id: string; title: string; messages: Message[]; updatedAt: number };

const APP_NAME = "هوشمند";
const STORAGE_KEY = "hooshmand.chats.v1";
const THEME_KEY = "hooshmand.theme.v1";
const MAX_LOCAL_CHATS = 30;

function icon(name: "menu" | "dots" | "plus" | "sun" | "moon" | "send" | "stop" | "copy" | "retry" | "trash" | "spark" | "back") {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const paths: Record<string, React.ReactNode> = {
    menu: <><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></>,
    dots: <><circle cx="5" cy="12" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/><circle cx="19" cy="12" r="1.2" fill="currentColor"/></>,
    plus: <><path d="M12 5v14"/><path d="M5 12h14"/></>,
    sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/></>,
    moon: <path d="M20.6 15.6A8.5 8.5 0 0 1 8.4 3.4 8.5 8.5 0 1 0 20.6 15.6Z"/>,
    send: <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
    stop: <rect x="7" y="7" width="10" height="10" rx="1.5"/>,
    copy: <><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
    retry: <><path d="M3 12a9 9 0 0 1 15.4-6.4L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"/><path d="M3 21v-5h5"/></>,
    trash: <><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v5M14 11v5"/></>,
    spark: <><path d="m12 3-1.4 4.6L6 9l4.6 1.4L12 15l1.4-4.6L18 9l-4.6-1.4L12 3Z"/><path d="m19 14-.7 2.3L16 17l2.3.7L19 20l.7-2.3L22 17l-2.3-.7L19 14Z"/></>,
    back: <><path d="m15 18-6-6 6-6"/><path d="M9 12h11"/></>,
  };
  return <svg {...common} aria-hidden="true">{paths[name]}</svg>;
}

function makeChat(): Chat {
  return { id: crypto.randomUUID(), title: "چت جدید", messages: [], updatedAt: Date.now() };
}

function titleFrom(messages: Message[]) {
  const first = messages.find((m) => m.role === "user")?.content.trim();
  if (!first) return "چت جدید";
  return first.length > 34 ? `${first.slice(0, 34)}…` : first;
}

function readChats(): Chat[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const value = JSON.parse(raw) as unknown;
    if (!Array.isArray(value)) return [];
    return value.filter((chat): chat is Chat => !!chat && typeof chat === "object" && typeof (chat as Chat).id === "string" && Array.isArray((chat as Chat).messages));
  } catch {
    return [];
  }
}

async function apiError(response: Response) {
  const payload = (await response.json().catch(() => ({}))) as { message?: string; error?: string };
  return payload.message || payload.error || `خطای سرور (${response.status})`;
}

export default function SmartChat() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(true);
  const [copied, setCopied] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const activeChat = useMemo(() => chats.find((chat) => chat.id === activeId) ?? null, [activeId, chats]);

  const persist = useCallback((next: Chat[]) => {
    const ordered = [...next].sort((a, b) => b.updatedAt - a.updatedAt).slice(0, MAX_LOCAL_CHATS);
    setChats(ordered);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ordered));
  }, []);

  const createChat = useCallback(() => {
    abortRef.current?.abort();
    const chat = makeChat();
    const next = [chat, ...chats.filter((item) => item.id !== chat.id)];
    persist(next);
    setActiveId(chat.id);
    setInput("");
    setError(null);
    setMenuOpen(false);
    setSidebarOpen(false);
  }, [chats, persist]);

  useEffect(() => {
    const storedTheme = window.localStorage.getItem(THEME_KEY);
    const initialDark = storedTheme ? storedTheme === "dark" : true;
    setDark(initialDark);
    document.documentElement.dataset.theme = initialDark ? "dark" : "light";

    const storedChats = readChats();
    if (storedChats.length) {
      setChats(storedChats);
      setActiveId(storedChats[0].id);
    } else {
      const initial = makeChat();
      setChats([initial]);
      setActiveId(initial.id);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify([initial]));
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    window.localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    const node = endRef.current;
    if (!node || typeof node.scrollIntoView !== "function") return;
    node.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeChat?.messages.length, loading]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading || !activeChat) return;
    const userMessage: Message = { role: "user", content: text };
    const history = [...activeChat.messages, userMessage];
    const updatedChat: Chat = { ...activeChat, messages: history, title: titleFrom(history), updatedAt: Date.now() };
    persist(chats.map((chat) => chat.id === activeChat.id ? updatedChat : chat));
    setInput("");
    setError(null);
    setLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(await apiError(response));
      const payload = (await response.json()) as { reply?: string };
      const reply = (payload.reply ?? "").trim();
      if (!reply) throw new Error("هوش مصنوعی پاسخ خالی فرستاد.");
      const finalChat: Chat = {
        ...updatedChat,
        messages: [...history, { role: "assistant", content: reply }],
        updatedAt: Date.now(),
      };
      persist(chats.map((chat) => chat.id === activeChat.id ? finalChat : chat));
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      setError(cause instanceof Error ? cause.message : "ارسال پیام ناموفق بود.");
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  }, [activeChat, chats, input, loading, persist]);

  const retry = () => {
    const lastUser = [...(activeChat?.messages ?? [])].reverse().find((m) => m.role === "user");
    if (!lastUser) return;
    setInput(lastUser.content);
    setError(null);
  };

  const selectChat = (id: string) => {
    setActiveId(id);
    setError(null);
    setMenuOpen(false);
    setSidebarOpen(false);
  };

  const clearChat = () => {
    if (!activeChat || !window.confirm("این گفت‌وگو پاک شود؟")) return;
    const replacement = makeChat();
    const next = chats.map((chat) => chat.id === activeChat.id ? replacement : chat);
    persist(next);
    setActiveId(replacement.id);
    setMenuOpen(false);
    setError(null);
  };

  const copyMessage = async (index: number, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(index);
    window.setTimeout(() => setCopied(null), 1400);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  };

  return (
    <main className={`app-shell ${sidebarOpen ? "sidebar-visible" : ""}`}>
      <div className="mobile-overlay" onClick={() => setSidebarOpen(false)} aria-hidden={!sidebarOpen} />
      <aside className="sidebar" aria-label="گفت‌وگوها">
        <div className="brand-row"><div className="brand-mark">ه</div><div><strong>{APP_NAME}</strong><span>دستیار هوش مصنوعی</span></div></div>
        <button className="new-chat" onClick={createChat}>{icon("plus")}<span>چت جدید</span></button>
        <div className="conversation-label">گفت‌وگوهای اخیر</div>
        <div className="conversation-list">
          {chats.map((chat) => <button key={chat.id} className={`conversation ${chat.id === activeId ? "active" : ""}`} onClick={() => selectChat(chat.id)}><span className="conversation-dot" /><span className="conversation-title">{chat.title}</span></button>)}
        </div>
        <div className="sidebar-footer">
          <button className="side-action" onClick={() => setDark((v) => !v)}>{icon(dark ? "sun" : "moon")}<span>{dark ? "حالت روشن" : "حالت تاریک"}</span></button>
          <button className="side-action danger" onClick={clearChat}>{icon("trash")}<span>پاک‌کردن چت</span></button>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <button className="icon-btn mobile-only" onClick={() => setSidebarOpen((v) => !v)} aria-label="گفت‌وگوها">{icon("menu")}</button>
          <button className="mobile-back" onClick={() => setSidebarOpen(false)} aria-label="بازگشت">{icon("back")}</button>
          <div className="top-title"><strong>{activeChat?.title ?? APP_NAME}</strong><span>هوش مصنوعی یکپارچه</span></div>
          <div className="topbar-actions">
            <button className="icon-btn mobile-menu-button" onClick={() => setMenuOpen((v) => !v)} aria-label="گزینه‌های بیشتر" aria-expanded={menuOpen}>{icon("dots")}</button>
            <button className="icon-btn desktop-new-chat" onClick={createChat} aria-label="چت جدید">{icon("plus")}</button>
          </div>
          {menuOpen && <div className="mobile-menu" role="menu">
            <button onClick={() => { setSidebarOpen(false); setMenuOpen(false); }}>{icon("back")}<span>برگشت به چت</span></button>
            <button onClick={createChat}>{icon("plus")}<span>چت جدید</span></button>
            <button onClick={() => { setDark((v) => !v); setMenuOpen(false); }}>{icon(dark ? "sun" : "moon")}<span>{dark ? "حالت روشن" : "حالت تاریک"}</span></button>
            <button onClick={clearChat}>{icon("trash")}<span>پاک‌کردن چت</span></button>
          </div>}
        </header>

        <div className="message-scroll">
          {!activeChat || activeChat.messages.length === 0 ? (
            <div className="empty-state">
              <div className="hero-icon">{icon("spark")}</div>
              <div className="eyebrow">دستیار هوشمند</div>
              <h1>سلام! 👋</h1>
              <p>من <strong>{APP_NAME}</strong> هستم.<br />هر سؤالی داری، همین‌جا بپرس.</p>
              <div className="suggestions">
                <button onClick={() => setInput("یک موضوع جالب درباره افغانستان برایم توضیح بده.")}>یک موضوع جالب توضیح بده</button>
                <button onClick={() => setInput("در یک مسئله سخت به من کمک کن و قدم‌به‌قدم توضیح بده.")}>در یک مسئله سخت کمکم کن</button>
                <button onClick={() => setInput("خودت را کوتاه و حرفه‌ای معرفی کن.")}>خودت را معرفی کن</button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {activeChat.messages.map((message, index) => (
                <div key={`${activeChat.id}-${index}`} className={`message-row ${message.role}`}>
                  <div className="avatar">{message.role === "user" ? "ش" : "ه"}</div>
                  <article className="message-card">
                    <div className="message-meta">{message.role === "user" ? "شما" : APP_NAME}</div>
                    {message.role === "assistant" ? <MarkdownMessage content={message.content} /> : <div className="user-text">{message.content}</div>}
                    <div className="message-actions">
                      <button onClick={() => void copyMessage(index, message.content)} aria-label="کپی پیام">{icon("copy")}{copied === index && <span>کپی شد</span>}</button>
                      {message.role === "assistant" && index === activeChat.messages.length - 1 && !loading && <button onClick={retry} aria-label="تلاش دوباره">{icon("retry")}</button>}
                    </div>
                  </article>
                </div>
              ))}
              {loading && <div className="message-row assistant"><div className="avatar">ه</div><div className="message-card generating"><div className="message-meta">{APP_NAME}</div><div className="typing"><span/><span/><span/><em>در حال فکر کردن…</em></div></div></div>}
              <div ref={endRef} />
            </div>
          )}
        </div>

        {error && <div className="error-bar" role="alert"><span>{error}</span><button onClick={() => setError(null)}>×</button></div>}

        <form className="composer-wrap" onSubmit={(event: FormEvent) => { event.preventDefault(); void send(); }}>
          <div className="composer">
            <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={onKeyDown} placeholder="پیامت را اینجا بنویس…" aria-label="پیام" rows={1} />
            <div className="composer-bottom"><span>Enter ارسال · Shift+Enter خط جدید</span>{loading ? <button type="button" className="send-btn stop" onClick={() => abortRef.current?.abort()} aria-label="توقف">{icon("stop")}</button> : <button type="submit" className="send-btn" disabled={!input.trim() || !activeChat} aria-label="ارسال">{icon("send")}</button>}</div>
          </div>
          <div className="composer-note">هوشمند · سازنده: حاجی احمد صالحی</div>
        </form>
      </section>
    </main>
  );
}
