"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { Filters as FiltersType } from "@/types";
import { getJournals, getArticleTypes, getQuartiles } from "@/lib/api";

interface FiltersProps {
  filters: FiltersType;
  onChange: (filters: Partial<FiltersType>) => void;
  onSearch: () => void;
  onReset: () => void;
}

export default function Filters({
  filters,
  onChange,
  onSearch,
  onReset,
}: FiltersProps) {
  const [journals, setJournals] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [quartiles, setQuartiles] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState(filters.search);
  const [showMore, setShowMore] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getJournals().then(setJournals).catch(() => {});
    getArticleTypes().then(setTypes).catch(() => {});
    getQuartiles().then(setQuartiles).catch(() => {});
  }, []);

  useEffect(() => {
    setSearchValue(filters.search);
  }, [filters.search]);

  // Auto-expand if advanced filters are active
  useEffect(() => {
    if (filters.journal_name || filters.article_type || filters.date_from || filters.date_to) {
      setShowMore(true);
    }
  }, [filters.journal_name, filters.article_type, filters.date_from, filters.date_to]);

  const handleSearchInput = useCallback(
    (value: string) => {
      setSearchValue(value);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        onChange({ search: value });
      }, 300);
    },
    [onChange]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      onChange({ search: searchValue });
      onSearch();
    }
  };

  const activeCount = [
    filters.journal_name,
    filters.article_type,
    filters.quartile,
    filters.date_from,
    filters.date_to,
    filters.scopus_only,
  ].filter(Boolean).length;

  return (
    <div className="bg-white border-b border-surface-border">
      <div className="max-w-[1280px] mx-auto px-5 py-4">
        {/* Primary row: search + quartile + actions */}
        <div className="flex flex-wrap gap-3 items-end">
          <FilterGroup label="Поиск">
            <input
              type="text"
              className="filter-input w-[300px] max-w-full"
              placeholder="ФИО автора или название статьи..."
              value={searchValue}
              onChange={(e) => handleSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </FilterGroup>

          <FilterGroup label="Квартиль">
            <select
              className="filter-select min-w-[100px]"
              value={filters.quartile}
              onChange={(e) => onChange({ quartile: e.target.value })}
            >
              <option value="">Все</option>
              {quartiles.map((q) => (
                <option key={q} value={q}>{q}</option>
              ))}
            </select>
          </FilterGroup>

          <label className="flex items-center gap-2 self-end h-[38px] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={filters.scopus_only}
              onChange={(e) => onChange({ scopus_only: e.target.checked })}
              className="w-4 h-4 accent-primary rounded"
            />
            <span className="text-sm text-text-secondary whitespace-nowrap">Источники из Scopus</span>
          </label>

          <button
            className="h-[38px] px-5 bg-primary text-white border-none rounded-md text-sm font-medium cursor-pointer transition-colors hover:bg-primary-dark self-end"
            onClick={onSearch}
          >
            Найти
          </button>

          <button
            className={`h-[38px] px-3 bg-white border rounded-md text-sm cursor-pointer transition-all self-end ${
              showMore
                ? "border-primary text-primary"
                : "border-surface-border text-text-secondary hover:border-primary hover:text-primary"
            }`}
            onClick={() => setShowMore(!showMore)}
          >
            Фильтры{activeCount > 0 ? ` (${activeCount})` : ""}
            <span className="ml-1 text-xs">{showMore ? "\u25B2" : "\u25BC"}</span>
          </button>

          {(activeCount > 0 || filters.search) && (
            <button
              className="h-[38px] px-3 bg-white text-text-muted border border-surface-border rounded-md text-sm cursor-pointer transition-all hover:border-red-300 hover:text-red-500 self-end"
              onClick={onReset}
            >
              Сбросить
            </button>
          )}
        </div>

        {/* Active filter chips */}
        {activeCount > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {filters.journal_name && (
              <Chip label={`Издание: ${filters.journal_name}`} onRemove={() => onChange({ journal_name: "" })} />
            )}
            {filters.article_type && (
              <Chip label={`Тип: ${filters.article_type}`} onRemove={() => onChange({ article_type: "" })} />
            )}
            {filters.quartile && (
              <Chip label={filters.quartile} onRemove={() => onChange({ quartile: "" })} />
            )}
            {filters.date_from && (
              <Chip label={`С ${filters.date_from}`} onRemove={() => onChange({ date_from: "" })} />
            )}
            {filters.date_to && (
              <Chip label={`По ${filters.date_to}`} onRemove={() => onChange({ date_to: "" })} />
            )}
            {filters.scopus_only && (
              <Chip label="Scopus" onRemove={() => onChange({ scopus_only: false })} />
            )}
          </div>
        )}

        {/* Expandable advanced filters */}
        {showMore && (
          <div className="flex flex-wrap gap-3 items-end mt-3 pt-3 border-t border-surface-border">
            <FilterGroup label="Год от">
              <input
                type="number"
                className="filter-input w-[90px]"
                placeholder="2020"
                min={1900}
                max={2100}
                value={filters.date_from}
                onChange={(e) => onChange({ date_from: e.target.value })}
              />
            </FilterGroup>
            <FilterGroup label="Год до">
              <input
                type="number"
                className="filter-input w-[90px]"
                placeholder="2026"
                min={1900}
                max={2100}
                value={filters.date_to}
                onChange={(e) => onChange({ date_to: e.target.value })}
              />
            </FilterGroup>

            <FilterGroup label="Издание">
              <select
                className="filter-select min-w-[180px]"
                value={filters.journal_name}
                onChange={(e) => onChange({ journal_name: e.target.value })}
              >
                <option value="">Все издания</option>
                {journals.map((j) => (
                  <option key={j} value={j}>{j}</option>
                ))}
              </select>
            </FilterGroup>

            <FilterGroup label="Тип статьи">
              <select
                className="filter-select min-w-[150px]"
                value={filters.article_type}
                onChange={(e) => onChange({ article_type: e.target.value })}
              >
                <option value="">Все типы</option>
                {types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </FilterGroup>
          </div>
        )}
      </div>
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-text-muted font-medium uppercase tracking-wide">
        {label}
      </label>
      {children}
    </div>
  );
}

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 bg-primary-50 text-primary text-xs font-medium py-1 px-2.5 rounded-full">
      {label}
      <button
        onClick={onRemove}
        className="ml-0.5 hover:text-red-500 transition-colors cursor-pointer text-base leading-none"
        aria-label={`Удалить фильтр: ${label}`}
      >
        &times;
      </button>
    </span>
  );
}
