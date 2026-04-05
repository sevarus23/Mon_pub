"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getSourcesTable } from "@/lib/api";
import type { SourceInfo } from "@/types";
import { getQuartileClass } from "@/types";

export default function SourcesTable() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [filtered, setFiltered] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showOnly, setShowOnly] = useState<"all" | "scopus" | "white_list">("all");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setLoading(true);
    getSourcesTable()
      .then((data) => {
        setSources(data);
        setFiltered(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const applyFilters = useCallback(
    (s: string, filter: "all" | "scopus" | "white_list") => {
      let result = sources;
      if (s.trim()) {
        const lower = s.toLowerCase();
        result = result.filter(
          (src) =>
            src.journal_name.toLowerCase().includes(lower) ||
            (src.issn && src.issn.includes(s))
        );
      }
      if (filter === "scopus") {
        result = result.filter((src) => src.in_scopus);
      } else if (filter === "white_list") {
        result = result.filter((src) => src.in_white_list);
      }
      setFiltered(result);
    },
    [sources]
  );

  const handleSearch = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => applyFilters(value, showOnly), 300);
  };

  const handleFilter = (filter: "all" | "scopus" | "white_list") => {
    setShowOnly(filter);
    applyFilters(search, filter);
  };

  const scopusCount = sources.filter((s) => s.in_scopus).length;
  const whiteListCount = sources.filter((s) => s.in_white_list).length;

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-text-muted">
        Загрузка источников...
      </div>
    );
  }

  return (
    <div>
      {/* Header stats */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="text-sm text-text-secondary">
          Всего источников: <span className="font-semibold text-text">{sources.length}</span>
        </div>
        <div className="text-sm text-text-secondary">
          В Scopus: <span className="font-semibold text-primary">{scopusCount}</span>
        </div>
        <div className="text-sm text-text-secondary">
          В Белом списке МОН: <span className="font-semibold text-emerald-600">{whiteListCount}</span>
        </div>
      </div>

      {/* Search + filter buttons */}
      <div className="flex flex-wrap gap-3 items-center mb-4">
        <input
          type="text"
          className="filter-input w-[300px]"
          placeholder="Поиск по названию или ISSN..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
        />
        <div className="flex gap-1">
          {(["all", "scopus", "white_list"] as const).map((f) => (
            <button
              key={f}
              onClick={() => handleFilter(f)}
              className={`px-3 py-1.5 text-xs rounded-md border transition-colors cursor-pointer ${
                showOnly === f
                  ? "bg-primary text-white border-primary"
                  : "bg-white text-text-secondary border-surface-border hover:border-primary hover:text-primary"
              }`}
            >
              {f === "all" ? "Все" : f === "scopus" ? "Scopus" : "Белый список"}
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
              <th className="px-4 py-3 font-medium">Издание</th>
              <th className="px-4 py-3 font-medium w-[100px]">ISSN</th>
              <th className="px-4 py-3 font-medium w-[70px] text-center">Статей</th>
              <th className="px-4 py-3 font-medium w-[70px] text-center">Квартиль</th>
              <th className="px-4 py-3 font-medium w-[70px] text-center">Scopus</th>
              <th className="px-4 py-3 font-medium w-[90px] text-center">Белый список</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {filtered.map((src, i) => (
              <tr key={`${src.journal_name}-${src.issn}-${i}`} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-2.5 font-medium text-text">
                  {src.journal_name}
                </td>
                <td className="px-4 py-2.5 text-text-muted font-mono text-xs">
                  {src.issn || "—"}
                </td>
                <td className="px-4 py-2.5 text-center font-semibold">
                  {src.article_count}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {src.quartile ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${getQuartileClass(src.quartile)}`}>
                      {src.quartile}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {src.in_scopus ? (
                    <span className="text-primary font-bold">&#10003;</span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {src.in_white_list ? (
                    <span className="inline-block py-0.5 px-2 rounded text-xs font-bold bg-emerald-600 text-white">
                      {`БС-${src.white_list_level}`}
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-text-muted">
                  Источники не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
