"use client";

import type { YearCount } from "@/types";

interface BarChartProps {
  data: YearCount[];
}

export default function BarChart({ data }: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-[180px] flex items-center justify-center text-text-muted text-sm">
        Нет данных
      </div>
    );
  }

  const allSorted = [...data].sort((a, b) => a.year - b.year);
  const sorted = allSorted.slice(-10);
  const maxCount = Math.max(...sorted.map((d) => d.count), 1);
  const BAR_AREA = 130;

  return (
    <div className="flex items-end gap-1.5 mt-2" style={{ height: `${BAR_AREA + 40}px` }}>
      {sorted.map((item) => {
        const barH = Math.max(6, (item.count / maxCount) * BAR_AREA);
        return (
          <div key={item.year} className="flex-1 flex flex-col items-center justify-end h-full">
            <div className="text-[0.65rem] text-text-secondary font-semibold mb-0.5">
              {item.count}
            </div>
            <div
              className="w-full max-w-[32px] rounded-t-sm bg-primary transition-colors hover:bg-primary-light"
              style={{ height: `${barH}px` }}
              title={`${item.year}: ${item.count} публикаций`}
            />
            <div className="text-[0.6rem] text-text-muted mt-1">{item.year}</div>
          </div>
        );
      })}
    </div>
  );
}
