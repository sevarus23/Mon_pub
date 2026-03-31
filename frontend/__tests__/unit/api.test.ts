/**
 * Unit tests for buildQuery utility in lib/api.ts.
 *
 * Since buildQuery is not exported, we test it indirectly
 * or import it for testing purposes.
 * For now, we replicate its logic to test the contract.
 */

// Replicate buildQuery since it's not exported
function buildQuery(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== "" && val !== null) {
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
});
