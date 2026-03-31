import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Публикационная активность сотрудников",
  description: "Система мониторинга публикационной активности сотрудников",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
