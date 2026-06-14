import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Price Intelligence — NVL Masterbatch",
  description: "Dashboard giá nguyên vật liệu nhựa (EUP Group)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
