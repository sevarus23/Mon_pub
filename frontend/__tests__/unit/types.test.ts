/**
 * Unit tests for frontend utility functions (test-plan §1.6).
 */

import {
  getTypeLabel,
  getQuartileClass,
  isNewToday,
  formatDate,
  TYPE_LABELS,
} from "@/types/index";

describe("getTypeLabel", () => {
  test("known type returns Russian label", () => {
    expect(getTypeLabel("journal-article")).toBe("Статья");
  });

  test("another known type", () => {
    expect(getTypeLabel("proceedings-article")).toBe("Конференция");
  });

  test("unknown type returns the raw type string", () => {
    expect(getTypeLabel("some-unknown-type")).toBe("some-unknown-type");
  });

  test("null returns 'Не указан'", () => {
    expect(getTypeLabel(null)).toBe("Не указан");
  });

  test("all TYPE_LABELS values are non-empty strings", () => {
    for (const [key, value] of Object.entries(TYPE_LABELS)) {
      expect(typeof value).toBe("string");
      expect(value.length).toBeGreaterThan(0);
    }
  });
});

describe("getQuartileClass", () => {
  test("Q1 -> bg-quartile-q1", () => {
    expect(getQuartileClass("Q1")).toBe("bg-quartile-q1");
  });

  test("Q2 -> bg-quartile-q2", () => {
    expect(getQuartileClass("Q2")).toBe("bg-quartile-q2");
  });

  test("Q3 -> bg-quartile-q3", () => {
    expect(getQuartileClass("Q3")).toBe("bg-quartile-q3");
  });

  test("Q4 -> bg-quartile-q4", () => {
    expect(getQuartileClass("Q4")).toBe("bg-quartile-q4");
  });

  test("null -> empty string", () => {
    expect(getQuartileClass(null)).toBe("");
  });

  test("invalid quartile -> empty string", () => {
    expect(getQuartileClass("Q5")).toBe("");
  });
});

describe("isNewToday", () => {
  test("today's date returns true", () => {
    const today = new Date().toISOString().slice(0, 10);
    expect(isNewToday(today)).toBe(true);
  });

  test("yesterday returns false", () => {
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    expect(isNewToday(yesterday)).toBe(false);
  });

  test("null returns false", () => {
    expect(isNewToday(null)).toBe(false);
  });
});

describe("formatDate", () => {
  test("valid ISO date -> Russian locale format", () => {
    const result = formatDate("2024-03-15");
    // Russian locale: dd.mm.yyyy
    expect(result).toMatch(/15\.03\.2024/);
  });

  test("null -> dash", () => {
    expect(formatDate(null)).toBe("—");
  });

  test("empty string -> dash", () => {
    expect(formatDate("")).toBe("—");
  });
});
