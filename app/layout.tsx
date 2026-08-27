import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MyChatBot",
  description: "Unified conversational AI by Haj Ahmad Salehi",
  applicationName: "MyChatBot",
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
