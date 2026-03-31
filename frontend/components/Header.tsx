"use client";

import type { Stats } from "@/types";

interface HeaderProps {
  stats: Stats | null;
}

export default function Header({ stats }: HeaderProps) {
  const today = new Date().toLocaleDateString("ru-RU");

  return (
    <div
      className="text-white py-7 px-10 flex flex-col md:flex-row justify-between items-center gap-3"
      style={{
        background:
          "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        boxShadow: "0 2px 12px rgba(0,0,0,.15)",
      }}
    >
      <div className="text-center md:text-left">
        <h1 className="text-[1.6rem] font-semibold">
          Публикационная активность сотрудников
        </h1>
        <div className="text-[0.78rem] opacity-60 mt-1.5">
          Данные на: {today}
        </div>
      </div>
      <div className="flex gap-8 items-center">
        <StatBox
          value={stats?.total ?? 0}
          label={stats?.first_published_date ? `публикаций с ${new Date(stats.first_published_date).toLocaleDateString("ru-RU")}` : "публикаций"}
        />
        <StatBox value={stats?.new_today ?? 0} label="новых сегодня" />
        <StatBox value={stats?.new_this_week ?? 0} label="новых за неделю" />
        <StatBox value={stats?.new_this_month ?? 0} label="новых за месяц" />
      </div>
    </div>
  );
}

function StatBox({
  value,
  label,
}: {
  value: number | string;
  label: string;
}) {
  const formatted =
    typeof value === "number" ? value.toLocaleString("ru-RU") : value;
  return (
    <div className="text-center">
      <div className="text-[1.8rem] font-bold text-accent">{formatted}</div>
      <div className="text-[0.8rem] opacity-75 mt-0.5">{label}</div>
    </div>
  );
}
