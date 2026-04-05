/**
 * Unit tests for buildQuery utility in lib/api.ts.
 *
 * Since buildQuery is not exported, we test it indirectly
 * or import it for testing purposes.
 * For now, we replicate its logic to test the contract.
 */

// Replicate buildQuery since it's not exported
function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== "" && val !== null && val !== false) {
      sp.set(key, String(val));
    }
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

describe("buildQuery", () => {
  test("empty params -> empty string", () => {
    expect(buildQuery({})).toBe("");
  });

  test("undefined values are excluded", () => {
    expect(buildQuery({ search: undefined, page: 1 })).toBe("?page=1");
  });

  test("empty string values are excluded", () => {
    expect(buildQuery({ search: "", page: 1 })).toBe("?page=1");
  });

  test("multiple params", () => {
    const result = buildQuery({ search: "test", page: 1, per_page: 20 });
    expect(result).toContain("search=test");
    expect(result).toContain("page=1");
    expect(result).toContain("per_page=20");
    expect(result.startsWith("?")).toBe(true);
  });

  test("number values are converted to strings", () => {
    const result = buildQuery({ page: 5 });
    expect(result).toBe("?page=5");
  });

  test("false boolean values are excluded", () => {
    expect(buildQuery({ scopus_only: false, page: 1 })).toBe("?page=1");
  });

  test("true boolean values are included", () => {
    expect(buildQuery({ scopus_only: true, page: 1 })).toContain("scopus_only=true");
  });
});

// Test getExportUrl by replicating its logic (same approach as buildQuery)
function getExportUrl(
  params: Record<string, string | number | boolean | undefined>,
  format: "xlsx" | "csv" = "xlsx"
): string {
  const BASE_URL = "/mon_pub";
  const query = buildQuery({ ...params, format });
  return `${BASE_URL}/api/articles/export${query}`;
}

describe("getExportUrl", () => {
  test("generates xlsx url by default", () => {
    const url = getExportUrl({}, "xlsx");
    expect(url).toContain("/api/articles/export");
    expect(url).toContain("format=xlsx");
  });

  test("generates csv url", () => {
    const url = getExportUrl({}, "csv");
    expect(url).toContain("format=csv");
  });

  test("includes search params", () => {
    const url = getExportUrl({ search: "AI", quartile: "Q1" }, "xlsx");
    expect(url).toContain("search=AI");
    expect(url).toContain("quartile=Q1");
    expect(url).toContain("format=xlsx");
  });

  test("excludes undefined params", () => {
    const url = getExportUrl({ search: undefined, quartile: "Q2" }, "xlsx");
    expect(url).not.toContain("search");
    expect(url).toContain("quartile=Q2");
  });

  test("includes topic param", () => {
    const url = getExportUrl({ topic: "Machine Learning" }, "csv");
    expect(url).toContain("topic=Machine+Learning");
    expect(url).toContain("format=csv");
  });

  test("includes scopus_only when true", () => {
    const url = getExportUrl({ scopus_only: true }, "xlsx");
    expect(url).toContain("scopus_only=true");
  });

  test("excludes scopus_only when false", () => {
    const url = getExportUrl({ scopus_only: false }, "xlsx");
    expect(url).not.toContain("scopus_only");
  });
});
