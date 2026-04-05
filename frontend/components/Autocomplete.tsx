"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface AutocompleteProps {
  value: string;
  onSearch: (query: string) => Promise<string[]>;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function Autocomplete({
  value,
  onSearch,
  onChange,
  placeholder = "",
  className = "",
}: AutocompleteProps) {
  const [input, setInput] = useState(value);
  const [options, setOptions] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setInput(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const doSearch = useCallback(
    (query: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(async () => {
        if (!query.trim()) {
          setOptions([]);
          setOpen(false);
          return;
        }
        try {
          const results = await onSearch(query);
          setOptions(results.slice(0, 10));
          setOpen(results.length > 0);
          setHighlighted(-1);
        } catch {
          setOptions([]);
        }
      }, 300);
    },
    [onSearch],
  );

  const handleInput = (val: string) => {
    setInput(val);
    doSearch(val);
  };

  const handleSelect = (option: string) => {
    setInput(option);
    onChange(option);
    setOpen(false);
  };

  const handleClear = () => {
    setInput("");
    onChange("");
    setOptions([]);
    setOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, options.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter" && highlighted >= 0) {
      e.preventDefault();
      handleSelect(options[highlighted]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          className="filter-input w-full pr-7"
          placeholder={placeholder}
          value={input}
          onChange={(e) => handleInput(e.target.value)}
          onFocus={() => options.length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
        />
        {input && (
          <button
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-red-500 transition-colors cursor-pointer text-sm leading-none"
            aria-label="Очистить"
          >
            &times;
          </button>
        )}
      </div>
      {open && options.length > 0 && (
        <ul className="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-surface-border rounded-md shadow-lg max-h-[240px] overflow-y-auto">
          {options.map((option, i) => (
            <li
              key={option}
              className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                i === highlighted
                  ? "bg-primary-50 text-primary"
                  : "hover:bg-gray-50"
              }`}
              onMouseDown={() => handleSelect(option)}
              onMouseEnter={() => setHighlighted(i)}
            >
              {option}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
