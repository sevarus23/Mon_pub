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
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch dropdown data
  useEffect(() => {
    getJournals().then(setJournals).catch(() => {});
    getArticleTypes().then(setTypes).catch(() => {});
    getQuartiles().then(setQuartiles).catch(() => {});
  }, []);

  // Sync searchValue from parent (e.g. on reset)
  useEffect(() => {
    setSearchValue(filters.search);
  }, [filters.search]);

  // Debounced search
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

  return (
    <div className="bg-white py-5 px-5 md:px-10 flex flex-wrap gap-3 items-end border-b border-[#e0e0e0]">
      {/* Search */}
      <FilterGroup label="Поиск">
        <input
          type="text"
          className="filter-input w-[260px] max-w-full"
          placeholder="ФИО автора или название статьи..."
          value={searchValue}
          onChange={(e) => handleSearchInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </FilterGroup>

      {/* Year range */}
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

      {/* Journal */}
      <FilterGroup label="Издание">
        <select
          className="filter-select min-w-[150px]"
          value={filters.journal_name}
          onChange={(e) => onChange({ journal_name: e.target.value })}
        >
          <option value="">Все издания</option>
          {journals.map((j) => (
            <option key={j} value={j}>
              {j}
            </option>
          ))}
        </select>
      </FilterGroup>

      {/* Type */}
      <FilterGroup label="Тип статьи">
        <select
          className="filter-select min-w-[150px]"
          value={filters.article_type}
          onChange={(e) => onChange({ article_type: e.target.value })}
        >
          <option value="">Все типы</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </FilterGroup>

      {/* Quartile */}
      <FilterGroup label="Квартиль">
        <select
          className="filter-select min-w-[100px]"
          value={filters.quartile}
          onChange={(e) => onChange({ quartile: e.target.value })}
        >
          <option value="">Все</option>
          {quartiles.map((q) => (
            <option key={q} value={q}>
              {q}
            </option>
          ))}
        </select>
      </FilterGroup>

      {/* Buttons */}
      <button
        className="py-2 px-6 bg-primary text-white border-none rounded-md text-[0.9rem] cursor-pointer transition-colors hover:bg-accent self-end"
        onClick={onSearch}
      >
        Найти
      </button>
      <button
        className="py-2 px-4 bg-transparent text-[#666] border border-[#ccc] rounded-md text-[0.9rem] cursor-pointer transition-all hover:border-accent hover:text-accent self-end"
        onClick={onReset}
      >
        Сбросить
      </button>
    </div>
  );
}

function FilterGroup({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[0.75rem] text-[#666] font-medium uppercase tracking-wide">
        {label}
      </label>
      {children}
    </div>
  );
}
