import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Публикационная активность | Университет Иннополис",
  description: "Мониторинг научных публикаций сотрудников Университета Иннополис",
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
