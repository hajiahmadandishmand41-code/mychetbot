"use client";

import { useEffect } from "react";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("MyChatBot route error", error);
  }, [error]);

  return (
    <main className="empty-state" style={{ minHeight: "100vh", padding: "32px 20px" }}>
      <div className="hero-icon" aria-hidden="true">!</div>
      <div className="eyebrow">خطای موقت</div>
      <h1>این بخش نتوانست بارگذاری شود.</h1>
      <p>مشکل ثبت شده است. دوباره تلاش کنید؛ گفت‌وگوها و ظاهر برنامه حفظ می‌شوند.</p>
      <div className="suggestions">
        <button type="button" onClick={() => reset()}>تلاش دوباره</button>
      </div>
    </main>
  );
}
