"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import MarkdownMessage from "@/components/markdown-message";

type Message = { role: "user" | "assistant" | "system" | "tool"; content: string };
type Conversation = { id: string; title: string; updatedAt: number };

const STORAGE_KEY = "mychatbot.conversations.v1";
const THEME_KEY = "mychatbot.theme.v1";

function icon(name: "menu" | "plus" | "sun" | "moon" | "send" | "stop" | "copy" | "retry" | "trash" | "spark") {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const paths: Record<string, React.ReactNode> = {
    menu: <><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></>,
    plus: <><path d="M12 5v14"/><path d="M5 12h14"/></>,
    sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/></>,
    moon: <path d="M20.6 15.6A8.5 8.5 0 0 1 8.4 3.4 8.5 8.5 0 1 0 20.6 15.6Z"/>,
    send: <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
    stop: <rect x="7" y="7" width="10" height="10" rx="1.5"/>,
    copy: <><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
    retry: <><path d="M3 12a9 9 0 0 1 15.4-6.4L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"/><path d="M3 21v-5h5"/></>,
    trash: <><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v5M14 11v5"/></>,
    spark: <><path d="m12 3-1.4 4.6L6 9l4.6 1.4L12 15l1.4-4.6L18 9l-4.6-1.4L12 3Z"/><path d="m19 14-.7 2.3L16 17l2.3.7L19 20l.7-2.3L22 17l-2.3-.7L19 14Z"/></>,
  };
  return <svg {...common} aria-hidden="true">{paths[name]}</svg>;
}

function makeTitle(messages: Message[]) {
  const first = messages.find((message) => message.role === "user")?.content.trim();
  if (!first) return "گفت‌وگوی جدید";
  return first.length > 36 ? `${first.slice(0, 36)}…` : first;
}

export default function ChatShell() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(true);
  const [copied, setCopied] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const currentConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === sessionId),
    [conversations, sessionId],
  );

  const saveConversations = useCallback((next: Conversation[]) => {
    setConversations(next);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next.slice(0, 30)));
  }, []);

  const ensureSession = useCallback(async () => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setConversations(JSON.parse(stored) as Conversation[]);
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    const response = await fetch("/api/session", { cache: "no-store" });
    if (!response.ok) throw new Error("session initialization failed");
    const data = (await response.json()) as { sessionId: string };
    setSessionId(data.sessionId);
    setConversations((current) => {
      if (current.some((item) => item.id === data.sessionId)) return current;
      const next = [{ id: data.sessionId, title: "گفت‌وگوی جدید", updatedAt: Date.now() }, ...current];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next.slice(0, 30)));
      return next;
    });
    const history = await fetch("/api/history", { cache: "no-store" });
    if (history.ok) {
      const payload = (await history.json()) as { messages?: Message[] };
      setMessages((payload.messages ?? []).filter((item) => item.role === "user" || item.role === "assistant"));
    }
  }, []);

  useEffect(() => {
    const storedTheme = window.localStorage.getItem(THEME_KEY);
    const initialDark = storedTheme ? storedTheme === "dark" : !window.matchMedia("(prefers-color-scheme: light)").matches;
    setDark(initialDark);
    document.documentElement.dataset.theme = initialDark ? "dark" : "light";
    ensureSession().catch((cause) => setError(cause instanceof Error ? cause.message : "خطا در آغاز نشست"));
  }, [ensureSession]);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    window.localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const loadSession = useCallback(async (id: string) => {
    setError(null);
    setLoading(false);
    abortRef.current?.abort();
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: id }),
    });
    if (!response.ok) throw new Error("session switch failed");
    setSessionId(id);
    const history = await fetch("/api/history", { cache: "no-store" });
    if (!history.ok) throw new Error("history load failed");
    const payload = (await history.json()) as { messages?: Message[] };
    setMessages((payload.messages ?? []).filter((item) => item.role === "user" || item.role === "assistant"));
    setSidebarOpen(false);
  }, []);

  const newChat = useCallback(async () => {
    const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!response.ok) throw new Error("new session failed");
    const data = (await response.json()) as { sessionId: string };
    setSessionId(data.sessionId);
    setMessages([]);
    setError(null);
    saveConversations([{ id: data.sessionId, title: "گفت‌وگوی جدید", updatedAt: Date.now() }, ...conversations.filter((item) => item.id !== data.sessionId)]);
    setSidebarOpen(false);
  }, [conversations, saveConversations]);

  const copyMessage = useCallback(async (index: number, content: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(index);
    window.setTimeout(() => setCopied(null), 1500);
  }, []);

  const send = useCallback(async () => {
    const message = input.trim();
    if (!message || loading || !sessionId) return;
    setInput("");
    setError(null);
    setMessages((current) => [...current, { role: "user", content: message }]);
    setLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
      const payload = (await response.json().catch(() => ({}))) as { reply?: string; message?: string };
      if (!response.ok) throw new Error(payload.message || "پاسخی از Unified Agent دریافت نشد.");
      const reply = (payload.reply ?? "").trim();
      if (!reply) throw new Error("پاسخ خالی از Backend دریافت شد.");
      setMessages((current) => [...current, { role: "assistant", content: reply }]);
      const next = conversations.map((item) => item.id === sessionId ? { ...item, title: makeTitle([...messages, { role: "user", content: message }]), updatedAt: Date.now() } : item);
      if (!next.some((item) => item.id === sessionId)) next.unshift({ id: sessionId, title: message.slice(0, 36), updatedAt: Date.now() });
      saveConversations(next.sort((a, b) => b.updatedAt - a.updatedAt));
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      setError(cause instanceof Error ? cause.message : "خطای غیرمنتظره");
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  }, [conversations, input, loading, messages, saveConversations, sessionId]);

  const onInputKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  };

  const stop = () => abortRef.current?.abort();

  const retryLast = () => {
    const lastUser = [...messages].reverse().find((message) => message.role === "user");
    if (!lastUser) return;
    setMessages((current) => {
      const index = current.map((item) => item.role).lastIndexOf("user");
      return index >= 0 ? current.slice(0, index + 1) : current;
    });
    setInput(lastUser.content);
  };

  const clearMemory = async () => {
    if (!sessionId || !window.confirm("حافظه و تاریخچه این گفت‌وگو پاک شود؟")) return;
    const response = await fetch("/api/memory", { method: "DELETE" });
    if (!response.ok) {
      setError("پاک‌سازی حافظه انجام نشد.");
      return;
    }
    setMessages([]);
  };

  return (
    <main className={`app-shell ${sidebarOpen ? "sidebar-visible" : ""}`}>
      <aside className="sidebar" aria-label="فهرست گفت‌وگوها">
        <div className="brand-row">
          <div className="brand-mark">M</div>
          <div><strong>MyChatBot</strong><span>Unified AI</span></div>
        </div>
        <button className="new-chat" onClick={() => void newChat()}>{icon("plus")} <span>گفت‌وگوی جدید</span></button>
        <div className="conversation-label">گفت‌وگوها</div>
        <div className="conversation-list">
          {conversations.length === 0 && <div className="sidebar-empty">هنوز گفت‌وگویی ندارید.</div>}
          {conversations.map((conversation) => (
            <button key={conversation.id} className={`conversation ${conversation.id === sessionId ? "active" : ""}`} onClick={() => void loadSession(conversation.id)}>
              <span className="conversation-dot" />
              <span className="conversation-title">{conversation.title}</span>
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          <button className="side-action" onClick={() => setDark((value) => !value)}>{icon(dark ? "sun" : "moon")} <span>{dark ? "حالت روشن" : "حالت تاریک"}</span></button>
          <button className="side-action danger" onClick={() => void clearMemory()}>{icon("trash")} <span>پاک‌کردن گفت‌وگوی فعلی</span></button>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <button className="icon-btn mobile-only" onClick={() => setSidebarOpen((value) => !value)} aria-label="باز کردن منو">{icon("menu")}</button>
          <div className="top-title">
            <strong>{currentConversation?.title ?? "MyChatBot"}</strong>
            <span>دستیار گفت‌وگویی یکپارچه</span>
          </div>
          <button className="icon-btn" onClick={() => void newChat()} aria-label="گفت‌وگوی جدید">{icon("plus")}</button>
        </header>

        <div className="message-scroll">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="hero-icon">{icon("spark")}</div>
              <h1>سلام! 👋</h1>
              <p>من MyChatBot هستم.<br />چطور می‌توانم کمکت کنم؟</p>
              <div className="suggestions">
                <button onClick={() => setInput("درباره هوش مصنوعی برایم تحقیق کن.")}>درباره یک موضوع تحقیق کن</button>
                <button onClick={() => setInput("وضعیت محیط فعلی را بررسی کن.")}>وضعیت محیط را بررسی کن</button>
                <button onClick={() => setInput("سلام، خودت را معرفی کن.")}>خودت را معرفی کن</button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div key={`${index}-${message.role}`} className={`message-row ${message.role}`}>
                  <div className="avatar">{message.role === "user" ? "ش" : "M"}</div>
                  <article className="message-card">
                    <div className="message-meta">{message.role === "user" ? "شما" : "MyChatBot"}</div>
                    {message.role === "assistant" ? <MarkdownMessage content={message.content} /> : <div className="user-text">{message.content}</div>}
                    <div className="message-actions">
                      <button onClick={() => void copyMessage(index, message.content)} aria-label="کپی پیام">{icon("copy")} {copied === index && <span>کپی شد</span>}</button>
                      {index === messages.length - 1 && message.role === "assistant" && !loading && <button onClick={retryLast} aria-label="تلاش دوباره">{icon("retry")}</button>}
                    </div>
                  </article>
                </div>
              ))}
              {loading && (
                <div className="message-row assistant">
                  <div className="avatar">M</div>
                  <div className="message-card generating"><div className="message-meta">MyChatBot</div><div className="typing"><span /><span /><span /><em>در حال فکر کردن…</em></div></div>
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        {error && <div className="error-bar" role="alert"><span>{error}</span><button onClick={() => setError(null)}>×</button></div>}

        <form className="composer-wrap" onSubmit={(event: FormEvent) => { event.preventDefault(); void send(); }}>
          <div className="composer">
            <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={onInputKeyDown} placeholder="پیام خود را بنویسید…" aria-label="پیام" rows={1} />
            <div className="composer-bottom"><span>Enter برای ارسال · Shift+Enter برای خط جدید</span>{loading ? <button type="button" className="send-btn stop" onClick={stop} aria-label="توقف تولید">{icon("stop")}</button> : <button type="submit" className="send-btn" disabled={!input.trim() || !sessionId} aria-label="ارسال پیام">{icon("send")}</button>}</div>
          </div>
          <div className="composer-note">MyChatBot · سازنده: حاجی احمد صالحی</div>
        </form>
      </section>
    </main>
  );
}
