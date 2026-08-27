"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import MarkdownMessage from "@/components/markdown-message";

type Message = { role: "user" | "assistant" | "system" | "tool"; content: string };
type Conversation = { id: string; title: string; updatedAt: number };

const APP_NAME = "سپنتا";
const STORAGE_KEY = "sepanta.conversations.v1";
const THEME_KEY = "sepanta.theme.v1";

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

function makeTitle(messages: Message[]) {
  const first = messages.find((message) => message.role === "user")?.content.trim();
  if (!first) return "گفت‌وگوی جدید";
  return first.length > 36 ? `${first.slice(0, 36)}…` : first;
}

async function apiError(response: Response, fallback: string) {
  const payload = (await response.json().catch(() => ({}))) as { message?: string; detail?: string | { message?: string } };
  if (typeof payload.message === "string" && payload.message.trim()) return payload.message;
  if (typeof payload.detail === "string" && payload.detail.trim()) return payload.detail;
  if (payload.detail && typeof payload.detail === "object" && typeof payload.detail.message === "string") return payload.detail.message;
  return fallback;
}

export default function ChatShell() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dark, setDark] = useState(true);
  const [copied, setCopied] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const currentConversation = useMemo(() => conversations.find((conversation) => conversation.id === sessionId), [conversations, sessionId]);

  const saveConversations = useCallback((next: Conversation[]) => {
    setConversations(next);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next.slice(0, 30)));
  }, []);

  const ensureSession = useCallback(async () => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try { setConversations(JSON.parse(stored) as Conversation[]); } catch { window.localStorage.removeItem(STORAGE_KEY); }
    }
    const response = await fetch("/api/session", { cache: "no-store" });
    if (!response.ok) throw new Error(await apiError(response, "نشست جدید ساخته نشد. صفحه را تازه‌سازی کنید."));
    const data = (await response.json()) as { sessionId?: string };
    if (!data.sessionId) throw new Error("شناسه نشست از Web دریافت نشد.");
    setSessionId(data.sessionId);
    setConversations((current) => {
      if (current.some((item) => item.id === data.sessionId)) return current;
      const next = [{ id: data.sessionId!, title: "گفت‌وگوی جدید", updatedAt: Date.now() }, ...current];
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

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; window.localStorage.setItem(THEME_KEY, dark ? "dark" : "light"); }, [dark]);

  useEffect(() => {
    const node = endRef.current;
    if (!node || typeof node.scrollIntoView !== "function") return;
    node.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const loadSession = useCallback(async (id: string) => {
    setError(null); abortRef.current?.abort();
    const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId: id }) });
    if (!response.ok) { setError(await apiError(response, "تغییر گفت‌وگو انجام نشد.")); return; }
    setSessionId(id);
    const history = await fetch("/api/history", { cache: "no-store" });
    if (!history.ok) { setError(await apiError(history, "تاریخچه گفت‌وگو بارگذاری نشد.")); return; }
    const payload = (await history.json()) as { messages?: Message[] };
    setMessages((payload.messages ?? []).filter((item) => item.role === "user" || item.role === "assistant"));
    setSidebarOpen(false); setMobileMenuOpen(false);
  }, []);

  const newChat = useCallback(async () => {
    const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!response.ok) { setError(await apiError(response, "چت جدید ساخته نشد.")); return; }
    const data = (await response.json()) as { sessionId?: string };
    if (!data.sessionId) { setError("چت جدید شناسه نشست دریافت نکرد."); return; }
    setSessionId(data.sessionId); setMessages([]); setError(null);
    saveConversations([{ id: data.sessionId, title: "گفت‌وگوی جدید", updatedAt: Date.now() }, ...conversations.filter((item) => item.id !== data.sessionId)]);
    setSidebarOpen(false); setMobileMenuOpen(false);
  }, [conversations, saveConversations]);

  const send = useCallback(async () => {
    const message = input.trim();
    if (!message || loading || !sessionId) return;
    setInput(""); setError(null); setMessages((current) => [...current, { role: "user", content: message }]); setLoading(true);
    const controller = new AbortController(); abortRef.current = controller;
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message }), signal: controller.signal });
      if (!response.ok) throw new Error(await apiError(response, "هوش مصنوعی پاسخ نداد."));
      const payload = (await response.json()) as { reply?: string };
      const reply = (payload.reply ?? "").trim();
      if (!reply) throw new Error("هوش مصنوعی پاسخ خالی برگرداند.");
      setMessages((current) => [...current, { role: "assistant", content: reply }]);
      const next = conversations.map((item) => item.id === sessionId ? { ...item, title: makeTitle([...messages, { role: "user", content: message }]), updatedAt: Date.now() } : item);
      if (!next.some((item) => item.id === sessionId)) next.unshift({ id: sessionId, title: makeTitle([{ role: "user", content: message }]), updatedAt: Date.now() });
      saveConversations(next.sort((a, b) => b.updatedAt - a.updatedAt));
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      setError(cause instanceof Error ? cause.message : "خطای غیرمنتظره");
    } finally { abortRef.current = null; setLoading(false); }
  }, [conversations, input, loading, messages, saveConversations, sessionId]);

  const onInputKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); }
  };
  const stop = () => abortRef.current?.abort();
  const retryLast = () => {
    const lastUser = [...messages].reverse().find((message) => message.role === "user");
    if (!lastUser) return;
    setMessages((current) => { const index = current.map((item) => item.role).lastIndexOf("user"); return index >= 0 ? current.slice(0, index + 1) : current; });
    setInput(lastUser.content);
  };
  const clearMemory = async () => {
    if (!sessionId || !window.confirm("حافظه و تاریخچه این گفت‌وگو پاک شود؟")) return;
    const response = await fetch("/api/memory", { method: "DELETE" });
    if (!response.ok) { setError(await apiError(response, "پاک‌سازی حافظه انجام نشد.")); return; }
    setMessages([]);
  };

  return (
    <main className={`app-shell ${sidebarOpen ? "sidebar-visible" : ""}`}>
      <aside className="sidebar" aria-label="فهرست گفت‌وگوها">
        <div className="brand-row"><div className="brand-mark">س</div><div><strong>{APP_NAME}</strong><span>دستیار هوش مصنوعی</span></div></div>
        <button className="new-chat" onClick={() => void newChat()}>{icon("plus")} <span>چت جدید</span></button>
        <div className="conversation-label">گفت‌وگوها</div>
        <div className="conversation-list">
          {conversations.length === 0 && <div className="sidebar-empty">هنوز گفت‌وگویی ندارید.</div>}
          {conversations.map((conversation) => <button key={conversation.id} className={`conversation ${conversation.id === sessionId ? "active" : ""}`} onClick={() => void loadSession(conversation.id)}><span className="conversation-dot" /><span className="conversation-title">{conversation.title}</span></button>)}
        </div>
        <div className="sidebar-footer">
          <button className="side-action" onClick={() => setDark((value) => !value)}>{icon(dark ? "sun" : "moon")} <span>{dark ? "حالت روشن" : "حالت تاریک"}</span></button>
          <button className="side-action danger" onClick={() => void clearMemory()}>{icon("trash")} <span>پاک‌کردن گفت‌وگوی فعلی</span></button>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <button className="icon-btn mobile-only" onClick={() => setSidebarOpen((value) => !value)} aria-label="باز کردن گفت‌وگوها">{icon("menu")}</button>
          <div className="top-title"><strong>{currentConversation?.title ?? APP_NAME}</strong><span>دستیار هوش مصنوعی یکپارچه</span></div>
          <div className="topbar-actions">
            <button className="icon-btn mobile-menu-button" onClick={() => setMobileMenuOpen((value) => !value)} aria-label="گزینه‌های بیشتر" aria-expanded={mobileMenuOpen}>{icon("dots")}</button>
            <button className="icon-btn desktop-new-chat" onClick={() => void newChat()} aria-label="چت جدید">{icon("plus")}</button>
          </div>
        </header>

        {mobileMenuOpen && <><button className="menu-backdrop" aria-label="بستن منو" onClick={() => setMobileMenuOpen(false)} /><div className="mobile-menu" role="menu" aria-label="گزینه‌های چت"><button role="menuitem" onClick={() => { setMobileMenuOpen(false); setSidebarOpen(false); }}>{icon("back")} <span>برگشت به چت</span></button><button role="menuitem" onClick={() => void newChat()}>{icon("plus")} <span>چت جدید</span></button><button role="menuitem" onClick={() => { setDark((value) => !value); setMobileMenuOpen(false); }}>{icon(dark ? "sun" : "moon")} <span>{dark ? "حالت روشن" : "حالت تاریک"}</span></button><button role="menuitem" onClick={() => { setMobileMenuOpen(false); void clearMemory(); }}>{icon("trash")} <span>پاک‌کردن چت</span></button></div></>}

        <div className="message-scroll">
          {messages.length === 0 ? <div className="empty-state"><div className="hero-icon">{icon("spark")}</div><h1>سلام! 👋</h1><p>من {APP_NAME} هستم.<br />دستیار هوش مصنوعی شما. چطور کمکتان کنم؟</p><div className="suggestions"><button onClick={() => setInput("درباره هوش مصنوعی برایم تحقیق کن.")}>درباره یک موضوع تحقیق کن</button><button onClick={() => setInput("آخرین اطلاعات مهم امروز را برایم پیدا کن.")}>اطلاعات جدید را پیدا کن</button><button onClick={() => setInput("سلام، خودت را معرفی کن.")}>خودت را معرفی کن</button></div></div> : <div className="messages">{messages.map((message, index) => <div key={`${index}-${message.role}`} className={`message-row ${message.role}`}><div className="avatar">{message.role === "user" ? "ش" : "س"}</div><article className="message-card"><div className="message-meta">{message.role === "user" ? "شما" : APP_NAME}</div>{message.role === "assistant" ? <MarkdownMessage content={message.content} /> : <div className="user-text">{message.content}</div>}<div className="message-actions"><button onClick={() => void navigator.clipboard.writeText(message.content).then(() => { setCopied(index); window.setTimeout(() => setCopied(null), 1500); })} aria-label="کپی پیام">{icon("copy")} {copied === index && <span>کپی شد</span>}</button>{index === messages.length - 1 && message.role === "assistant" && !loading && <button onClick={retryLast} aria-label="تلاش دوباره">{icon("retry")}</button>}</div></article></div>)}{loading && <div className="message-row assistant"><div className="avatar">س</div><div className="message-card generating"><div className="message-meta">{APP_NAME}</div><div className="typing"><span /><span /><span /><em>در حال فکر کردن…</em></div></div></div>}<div ref={endRef} /></div>}
        </div>
        {error && <div className="error-bar" role="alert"><span>{error}</span><button onClick={() => setError(null)} aria-label="بستن خطا">×</button></div>}
        <form className="composer-wrap" onSubmit={(event: FormEvent) => { event.preventDefault(); void send(); }}><div className="composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={onInputKeyDown} placeholder="پیام خود را بنویسید…" aria-label="پیام" rows={1} /><div className="composer-bottom"><span>Enter برای ارسال · Shift+Enter برای خط جدید</span>{loading ? <button type="button" className="send-btn stop" onClick={stop} aria-label="توقف تولید">{icon("stop")}</button> : <button type="submit" className="send-btn" disabled={!input.trim() || !sessionId} aria-label="ارسال پیام">{icon("send")}</button>}</div></div><div className="composer-note">{APP_NAME} · دستیار هوش مصنوعی شخصی شما</div></form>
      </section>
    </main>
  );
}
