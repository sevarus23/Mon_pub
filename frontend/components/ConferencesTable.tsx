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

type SortKey = "journal_name" | "article_count" | "core_rank" | "quartile" | "white_list_level";
type SortDir = "asc" | "desc";

const RANK_ORDER: Record<string, number> = { "A*": 1, A: 2, B: 3, C: 4 };

export default function ConferencesTable() {
  const [conferences, setConferences] = useState<ConferenceInfo[]>([]);
  const [filtered, setFiltered] = useState<ConferenceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [rankFilter, setRankFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("article_count");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
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

  const sortData = useCallback(
    (data: ConferenceInfo[], key: SortKey, dir: SortDir) => {
      return [...data].sort((a, b) => {
        if (key === "core_rank") {
          const av = RANK_ORDER[a.core_rank || ""] ?? 99;
          const bv = RANK_ORDER[b.core_rank || ""] ?? 99;
          return dir === "asc" ? av - bv : bv - av;
        }
        const av = a[key] ?? "";
        const bv = b[key] ?? "";
        if (typeof av === "number" && typeof bv === "number") {
          return dir === "asc" ? av - bv : bv - av;
        }
        const cmp = String(av).localeCompare(String(bv));
        return dir === "asc" ? cmp : -cmp;
      });
    },
    []
  );

  const applyFilters = useCallback(
    (s: string, rank: string, sk: SortKey, sd: SortDir) => {
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
      setFiltered(sortData(result, sk, sd));
    },
    [conferences, sortData]
  );

  const handleSearch = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => applyFilters(value, rankFilter, sortKey, sortDir), 300);
  };

  const handleRankFilter = (rank: string) => {
    setRankFilter(rank);
    applyFilters(search, rank, sortKey, sortDir);
  };

  const handleSort = (key: SortKey) => {
    const newDir = sortKey === key && sortDir === "desc" ? "asc" : "desc";
    setSortKey(key);
    setSortDir(newDir);
    applyFilters(search, rankFilter, key, newDir);
  };

  const sortArrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : " \u25B2\u25BC";

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
      {/* Stats cards (same style as Sources) */}
      <div className="flex flex-wrap gap-3 mb-5">
        <div className="bg-white rounded-[10px] shadow-card flex items-center gap-3 py-3 px-4">
          <div className="text-2xl font-bold text-primary">{conferences.length}</div>
          <div className="text-xs text-text-muted">{"Всего\nконференций"}</div>
        </div>
        {["A*", "A", "B", "C"].map((r) => (
          <div key={r} className="bg-white rounded-[10px] shadow-card flex items-center gap-3 py-3 px-4">
            <div className="text-2xl font-bold text-primary">{rankCounts[r] || 0}</div>
            <div className="text-xs text-text-muted">{r}</div>
          </div>
        ))}
        <div className="ml-auto self-center text-[0.65rem] text-text-muted italic">
          CORE Rankings: ICORE2026 &nbsp;|&nbsp; обновлён 05.04.2026
        </div>
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
                  ? "bg-primary text-white border-primary"
                  : "bg-white text-text-secondary border-surface-border hover:border-primary hover:text-primary"
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
      <div className="overflow-x-auto rounded-lg border border-surface-border shadow-sm">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-gray-50 text-[0.65rem] text-text-muted uppercase tracking-wider">
              <th className="px-4 py-3 font-semibold text-left cursor-pointer select-none hover:text-primary" onClick={() => handleSort("journal_name")}>
                Конференция<span className="text-[0.55rem] ml-1">{sortArrow("journal_name")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[80px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("article_count")}>
                Статей<span className="text-[0.55rem] ml-1">{sortArrow("article_count")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[100px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("core_rank")}>
                CORE Rank<span className="text-[0.55rem] ml-1">{sortArrow("core_rank")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[90px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("quartile")}>
                Квартиль<span className="text-[0.55rem] ml-1">{sortArrow("quartile")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[110px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("white_list_level")}>
                Белый список<span className="text-[0.55rem] ml-1">{sortArrow("white_list_level")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((conf, i) => (
              <tr key={`${conf.journal_name}-${i}`} className={`hover:bg-primary-50 transition-colors ${i % 2 === 1 ? "bg-gray-50/50" : ""}`}>
                <td className="px-4 py-3 font-medium text-text text-left">
                  {conf.journal_name}
                </td>
                <td className="px-4 py-3 text-center font-semibold">
                  {conf.article_count}
                </td>
                <td className="px-4 py-3 text-center">
                  {conf.core_rank ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${CORE_COLORS[conf.core_rank] || "bg-violet-400"}`}>
                      {conf.core_rank}
                    </span>
                  ) : (
                    <span className="text-text-muted">{"\u2014"}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {conf.quartile ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${getQuartileClass(conf.quartile)}`}>
                      {conf.quartile}
                    </span>
                  ) : (
                    <span className="text-text-muted">{"\u2014"}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {conf.white_list_level ? (
                    <span className="inline-block py-0.5 px-2 rounded text-xs font-bold bg-emerald-600 text-white">
                      {`\u0411\u0421-${conf.white_list_level}`}
                    </span>
                  ) : (
                    <span className="text-text-muted">{"\u2014"}</span>
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
