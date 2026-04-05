"use client";

import type { Stats } from "@/types";

interface HeaderProps {
  stats: Stats | null;
  globalMode?: boolean;
}

export default function Header({ stats, globalMode }: HeaderProps) {
  const today = new Date().toLocaleDateString("ru-RU");

  return (
    <header className="bg-gradient-to-r from-primary-800 to-primary text-white shadow-lg">
      <div className="max-w-[1280px] mx-auto px-6 py-5 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-center md:text-left">
          <h1 className="text-xl font-bold tracking-tight">
            Публикационная активность сотрудников
          </h1>
          <p className="text-xs text-primary-100 mt-1">
            Данные на {today}
          </p>
        </div>
        {globalMode ? (
          <div className="text-xs text-white bg-white/20 px-3 py-1.5 rounded-full font-medium">
            Глобальный поиск OpenAlex
          </div>
        ) : (
          <div className="flex gap-3 items-center">
            <StatBox
              value={stats?.total ?? 0}
              label={
                stats?.first_published_date
                  ? `с ${new Date(stats.first_published_date).toLocaleDateString("ru-RU")}`
                  : "всего"
              }
            />
            <StatBox value={stats?.new_today ?? 0} label="сегодня" />
            <StatBox value={stats?.new_this_week ?? 0} label="за неделю" />
            <StatBox value={stats?.new_this_month ?? 0} label="за месяц" />
          </div>
        )}
      </div>
    </header>
  );
}

function StatBox({ value, label }: { value: number | string; label: string }) {
  const formatted =
    typeof value === "number" ? value.toLocaleString("ru-RU") : value;
  return (
    <div className="bg-white rounded-[10px] shadow-card px-5 py-3 text-center min-w-[90px]">
      <div className="text-2xl font-bold text-primary">{formatted}</div>
      <div className="text-[0.65rem] text-text-muted">{label}</div>
    </div>
  );
}
