import Link from "next/link";

export default function NotFound() {
  return (
    <main className="empty-state" style={{ minHeight: "100vh", padding: "32px 20px" }}>
      <div className="hero-icon" aria-hidden="true">۴۰۴</div>
      <div className="eyebrow">صفحه پیدا نشد</div>
      <h1>این مسیر وجود ندارد.</h1>
      <p>نشانی واردشده معتبر نیست یا این صفحه جابه‌جا شده است.</p>
      <div className="suggestions">
        <Link href="/" style={{ display: "inline-block", padding: "9px 14px", border: "1px solid var(--border)", borderRadius: 11, background: "var(--panel)", color: "var(--text)", textDecoration: "none", fontSize: 12 }}>
          بازگشت به هوشمند
        </Link>
      </div>
    </main>
  );
}
