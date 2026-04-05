"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getConferencesTable } from "@/lib/api";
import type { ConferenceInfo } from "@/types";
import { getQuartileClass } from "@/types";

const CORE_COLORS: Record<string, string> = {
  "A*": "bg-violet-700",
  A: "bg-violet-600",
  B: "bg-violet-400",
  C: "bg-violet-300 text-violet-900",
};

export default function ConferencesTable() {
  const [conferences, setConferences] = useState<ConferenceInfo[]>([]);
  const [filtered, setFiltered] = useState<ConferenceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [rankFilter, setRankFilter] = useState<string>("all");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setLoading(true);
    getConferencesTable()
      .then((data) => {
        setConferences(data);
        setFiltered(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const applyFilters = useCallback(
    (s: string, rank: string) => {
      let result = conferences;
      if (s.trim()) {
        const lower = s.toLowerCase();
        result = result.filter((c) =>
          c.journal_name.toLowerCase().includes(lower)
        );
      }
      if (rank !== "all") {
        result = result.filter((c) => c.core_rank === rank);
      }
      setFiltered(result);
    },
    [conferences]
  );

  const handleSearch = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => applyFilters(value, rankFilter), 300);
  };

  const handleRankFilter = (rank: string) => {
    setRankFilter(rank);
    applyFilters(search, rank);
  };

  const rankCounts: Record<string, number> = {};
  for (const c of conferences) {
    const r = c.core_rank || "Other";
    rankCounts[r] = (rankCounts[r] || 0) + 1;
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-text-muted">
        Загрузка конференций...
      </div>
    );
  }

  return (
    <div>
      {/* Stats */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="text-sm text-text-secondary">
          Всего конференций: <span className="font-semibold text-text">{conferences.length}</span>
        </div>
        {["A*", "A", "B", "C"].map((r) => (
          <div key={r} className="text-sm text-text-secondary">
            {r}: <span className="font-semibold text-violet-600">{rankCounts[r] || 0}</span>
          </div>
        ))}
      </div>

      {/* Search + rank filter */}
      <div className="flex flex-wrap gap-3 items-center mb-4">
        <input
          type="text"
          className="filter-input w-[300px]"
          placeholder="Поиск по названию конференции..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
        />
        <div className="flex gap-1">
          {["all", "A*", "A", "B", "C"].map((r) => (
            <button
              key={r}
              onClick={() => handleRankFilter(r)}
              className={`px-3 py-1.5 text-xs rounded-md border transition-colors cursor-pointer ${
                rankFilter === r
                  ? "bg-violet-600 text-white border-violet-600"
                  : "bg-white text-text-secondary border-surface-border hover:border-violet-400 hover:text-violet-600"
              }`}
            >
              {r === "all" ? "Все" : r}
            </button>
          ))}
        </div>
        <span className="text-xs text-text-muted">
          Показано: {filtered.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs text-text-muted uppercase tracking-wide">
              <th className="px-4 py-3 font-medium">Конференция</th>
              <th className="px-4 py-3 font-medium w-[70px] text-center">Статей</th>
              <th className="px-4 py-3 font-medium w-[90px] text-center">CORE Rank</th>
              <th className="px-4 py-3 font-medium w-[70px] text-center">Квартиль</th>
              <th className="px-4 py-3 font-medium w-[90px] text-center">Белый список</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {filtered.map((conf, i) => (
              <tr key={`${conf.journal_name}-${i}`} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-2.5 font-medium text-text">
                  {conf.journal_name}
                </td>
                <td className="px-4 py-2.5 text-center font-semibold">
                  {conf.article_count}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {conf.core_rank ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${CORE_COLORS[conf.core_rank] || "bg-violet-400"}`}>
                      {conf.core_rank}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {conf.quartile ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${getQuartileClass(conf.quartile)}`}>
                      {conf.quartile}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {conf.white_list_level ? (
                    <span className="inline-block py-0.5 px-2 rounded text-xs font-bold bg-emerald-600 text-white">
                      {`БС-${conf.white_list_level}`}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-text-muted">
                  Конференции не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
