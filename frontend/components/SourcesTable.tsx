"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getSourcesTable } from "@/lib/api";
import type { SourceInfo } from "@/types";
import { getQuartileClass } from "@/types";

type SortKey = "journal_name" | "article_count" | "quartile" | "white_list_level";
type SortDir = "asc" | "desc";

export default function SourcesTable() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [filtered, setFiltered] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showOnly, setShowOnly] = useState<"all" | "scopus" | "white_list">("all");
  const [sortKey, setSortKey] = useState<SortKey>("article_count");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
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

  const sortData = useCallback(
    (data: SourceInfo[], key: SortKey, dir: SortDir) => {
      return [...data].sort((a, b) => {
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
    (s: string, filter: "all" | "scopus" | "white_list", sk: SortKey, sd: SortDir) => {
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
      setFiltered(sortData(result, sk, sd));
    },
    [sources, sortData]
  );

  const handleSearch = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => applyFilters(value, showOnly, sortKey, sortDir), 300);
  };

  const handleFilter = (filter: "all" | "scopus" | "white_list") => {
    setShowOnly(filter);
    applyFilters(search, filter, sortKey, sortDir);
  };

  const handleSort = (key: SortKey) => {
    const newDir = sortKey === key && sortDir === "desc" ? "asc" : "desc";
    setSortKey(key);
    setSortDir(newDir);
    applyFilters(search, showOnly, key, newDir);
  };

  const sortArrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : " \u25B2\u25BC";

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
      {/* Stats cards */}
      <div className="flex flex-wrap gap-3 mb-5">
        <div className="bg-white rounded-[10px] shadow-card flex items-center gap-3 py-3 px-4">
          <div className="text-2xl font-bold text-primary">{sources.length}</div>
          <div className="text-xs text-text-muted">{"Всего\nисточников"}</div>
        </div>
        <div className="bg-white rounded-[10px] shadow-card flex items-center gap-3 py-3 px-4">
          <div className="text-2xl font-bold text-primary">{scopusCount}</div>
          <div className="text-xs text-text-muted">В Scopus</div>
        </div>
        <div className="bg-white rounded-[10px] shadow-card flex items-center gap-3 py-3 px-4">
          <div className="text-2xl font-bold text-emerald-600">{whiteListCount}</div>
          <div className="text-xs text-text-muted">{"В Белом списке\nМОН РФ"}</div>
        </div>
        <div className="ml-auto self-center text-[0.65rem] text-text-muted italic">
          Scopus: обновлён 02.2026 &nbsp;|&nbsp; Белый список МОН: обновлён 05.04.2026
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
      <div className="overflow-x-auto rounded-lg border border-surface-border shadow-sm">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-gray-50 text-[0.65rem] text-text-muted uppercase tracking-wider">
              <th className="px-4 py-3 font-semibold text-left cursor-pointer select-none hover:text-primary" onClick={() => handleSort("journal_name")}>
                Издание<span className="text-[0.55rem] ml-1">{sortArrow("journal_name")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[100px]">ISSN</th>
              <th className="px-4 py-3 font-semibold text-center w-[80px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("article_count")}>
                Статей<span className="text-[0.55rem] ml-1">{sortArrow("article_count")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[90px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("quartile")}>
                Квартиль<span className="text-[0.55rem] ml-1">{sortArrow("quartile")}</span>
              </th>
              <th className="px-4 py-3 font-semibold text-center w-[80px]">Scopus</th>
              <th className="px-4 py-3 font-semibold text-center w-[110px] cursor-pointer select-none hover:text-primary" onClick={() => handleSort("white_list_level")}>
                Белый список<span className="text-[0.55rem] ml-1">{sortArrow("white_list_level")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((src, i) => (
              <tr key={`${src.journal_name}-${src.issn}-${i}`} className={`hover:bg-primary-50 transition-colors ${i % 2 === 1 ? "bg-gray-50/50" : ""}`}>
                <td className="px-4 py-3 font-medium text-text text-left">
                  {src.journal_name}
                </td>
                <td className="px-4 py-3 text-text-muted font-mono text-xs text-center">
                  {src.issn || "\u2014"}
                </td>
                <td className="px-4 py-3 text-center font-semibold">
                  {src.article_count}
                </td>
                <td className="px-4 py-3 text-center">
                  {src.quartile ? (
                    <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${getQuartileClass(src.quartile)}`}>
                      {src.quartile}
                    </span>
                  ) : (
                    <span className="text-text-muted">&mdash;</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {src.in_scopus ? (
                    <span className="text-primary font-bold">&#10003;</span>
                  ) : (
                    <span className="text-text-muted">&mdash;</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {src.in_white_list ? (
                    <span className="inline-block py-0.5 px-2 rounded text-xs font-bold bg-emerald-600 text-white">
                      {`БС-${src.white_list_level}`}
                    </span>
                  ) : (
                    <span className="text-text-muted">&mdash;</span>
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
