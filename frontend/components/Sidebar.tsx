"use client";

import { useState, useEffect } from "react";
import type { Stats } from "@/types";
import BarChart from "./BarChart";
import { getArticles } from "@/lib/api";

interface SidebarProps {
  stats: Stats | null;
}

export default function Sidebar({ stats }: SidebarProps) {
  const [qCounts, setQCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    for (const q of ["Q1", "Q2", "Q3", "Q4"]) {
      getArticles({ quartile: q, per_page: 1, page: 1 })
        .then((res) => setQCounts((prev) => ({ ...prev, [q]: res.total })))
        .catch(() => {});
    }
  }, []);

  return (
    <div>
      {/* Year distribution chart */}
      <div className="bg-white rounded-[10px] p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)] mb-5">
        <h3 className="text-[1rem] text-[#333] mb-3">
          Распределение по годам
        </h3>
        {stats ? (
          <BarChart data={stats.by_year} />
        ) : (
          <div className="h-[180px] flex items-center justify-center">
            <div className="animate-pulse text-[#999] text-sm">
              Загрузка...
            </div>
          </div>
        )}
      </div>

      {/* Stat cards */}
      <div className="flex flex-col gap-2.5">
        <StatCard label="Статей в Q1" value={String(qCounts.Q1 ?? 0)} />
        <StatCard label="Статей в Q2" value={String(qCounts.Q2 ?? 0)} />
        <StatCard label="Статей в Q3" value={String(qCounts.Q3 ?? 0)} />
        <StatCard label="Статей в Q4" value={String(qCounts.Q4 ?? 0)} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-[10px] py-4 px-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)] flex justify-between items-center">
      <span className="text-[0.85rem] text-[#666]">{label}</span>
      <span className="text-[1.2rem] font-bold text-primary">{value}</span>
    </div>
  );
}
