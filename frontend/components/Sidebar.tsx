"use client";

import { useState, useEffect } from "react";
import type { Stats } from "@/types";
import BarChart from "./BarChart";
import { getArticles } from "@/lib/api";

interface SidebarProps {
  stats: Stats | null;
  onQuartileClick?: (q: string) => void;
  globalMode?: boolean;
}

const Q_COLORS: Record<string, string> = {
  Q1: "text-quartile-q1 border-quartile-q1",
  Q2: "text-quartile-q2 border-quartile-q2",
  Q3: "text-quartile-q3 border-quartile-q3",
  Q4: "text-quartile-q4 border-quartile-q4",
};

export default function Sidebar({ stats, onQuartileClick, globalMode }: SidebarProps) {
  const [qCounts, setQCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    for (const q of ["Q1", "Q2", "Q3", "Q4"]) {
      getArticles({ quartile: q, per_page: 1, page: 1 })
        .then((res) => setQCounts((prev) => ({ ...prev, [q]: res.total })))
        .catch(() => {});
    }
  }, []);

  if (globalMode) {
    return (
      <aside className="space-y-4">
        <div className="bg-white rounded-card p-5 shadow-card text-center">
          <p className="text-sm text-text-muted">
            Статистика и графики доступны только для публикаций Innopolis University
          </p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="space-y-4">
      {/* Year distribution chart */}
      <div className="bg-white rounded-[10px] p-5 shadow-card">
        <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <span className="w-1 h-4 bg-primary rounded-full"></span>
          Распределение по годам
        </h3>
        {stats ? (
          <BarChart data={stats.by_year} />
        ) : (
          <div className="h-[180px] flex items-center justify-center">
            <div className="animate-pulse text-text-muted text-sm">
              Загрузка...
            </div>
          </div>
        )}
      </div>

      {/* Quartile cards */}
      <div className="bg-white rounded-[10px] p-5 shadow-card">
        <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <span className="w-1 h-4 bg-quartile-q1 rounded-full"></span>
          Квартили
        </h3>
        <div className="grid grid-cols-2 gap-2.5">
        {(["Q1", "Q2", "Q3", "Q4"] as const).map((q) => (
          <button
            key={q}
            onClick={() => onQuartileClick?.(q)}
            className={`bg-surface-secondary rounded-lg py-3 px-4 border-l-[3px] ${Q_COLORS[q]} flex flex-col items-center transition-all hover:shadow-md cursor-pointer`}
          >
            <span className="text-lg font-bold">{qCounts[q] ?? 0}</span>
            <span className="text-xs text-text-muted">{q}</span>
          </button>
        ))}
        </div>
      </div>

      {/* Top journals */}
      {stats && stats.top_journals.length > 0 && (
        <div className="bg-white rounded-[10px] p-5 shadow-card">
          <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <span className="w-1 h-4 bg-accent rounded-full"></span>
            Топ журналов
          </h3>
          <ul className="space-y-2">
            {stats.top_journals.slice(0, 5).map((j) => (
              <li key={j.journal_name} className="flex justify-between items-baseline text-xs">
                <span className="text-text-secondary truncate mr-2">{j.journal_name}</span>
                <span className="font-semibold text-primary shrink-0">{j.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
