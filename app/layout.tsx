import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./mobile.css";

export const metadata: Metadata = {
  title: "سپنتا",
  description: "دستیار هوش مصنوعی یکپارچه سپنتا",
  applicationName: "سپنتا",
};

export const viewport: Viewport = {
  colorScheme: "dark light",
  themeColor: "#0b0d10",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
