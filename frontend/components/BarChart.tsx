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

  return (
    <div className="flex items-end gap-1.5 h-[200px] mt-3">
      {sorted.map((item) => {
        const height = Math.max(8, (item.count / maxCount) * 155);
        return (
          <div key={item.year} className="flex-1 flex flex-col items-center gap-1">
            <div className="text-[0.7rem] text-text font-semibold">
              {item.count}
            </div>
            <div
              className="w-full max-w-[36px] rounded-t-sm bg-primary transition-colors hover:bg-primary-light"
              style={{ height: `${height}px` }}
              title={`${item.year}: ${item.count} публикаций`}
            />
            <div className="text-[0.68rem] text-text-muted">{item.year}</div>
          </div>
        );
      })}
    </div>
  );
}
