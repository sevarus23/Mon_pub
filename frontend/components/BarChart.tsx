"use client";

import type { YearCount } from "@/types";

interface BarChartProps {
  data: YearCount[];
}

export default function BarChart({ data }: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-[180px] flex items-center justify-center text-[#999] text-sm">
        Нет данных
      </div>
    );
  }

  const allSorted = [...data].sort((a, b) => a.year - b.year);
  const sorted = allSorted.slice(-10);
  const maxCount = Math.max(...sorted.map((d) => d.count), 1);

  return (
    <div className="flex items-end gap-1.5 h-[210px] mt-3">
      {sorted.map((item) => {
        const height = Math.max(8, (item.count / maxCount) * 160);
        return (
          <div
            key={item.year}
            className="flex-1 flex flex-col items-center gap-1"
          >
            <div className="text-[0.7rem] text-[#333] font-semibold">
              {item.count}
            </div>
            <div
              className="w-full max-w-[36px] rounded-t bar-hover"
              style={{
                height: `${height}px`,
                background: "linear-gradient(180deg, #0f3460, #1a1a2e)",
              }}
              title={`${item.year}: ${item.count} публикаций`}
            />
            <div className="text-[0.68rem] text-[#888]">{item.year}</div>
          </div>
        );
      })}
    </div>
  );
}
