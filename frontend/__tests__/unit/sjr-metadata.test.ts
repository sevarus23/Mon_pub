import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { SjrMetadata } from "@/components/SourcesTable";
import type { ReferenceDataItem } from "@/types";

function render(metadata?: ReferenceDataItem | null) {
  return renderToStaticMarkup(createElement(SjrMetadata, { metadata }));
}

describe("SJR provenance", () => {
  test("current snapshot shows the actual date, attribution and both source links", () => {
    const html = render({
      version: "SJR 2025",
      latest_version: "SJR 2025",
      retrieved_at: "2026-09-19T10:00:00Z",
      status: "current",
      url: "https://www.scimagojr.com/journalrank.php?year=2025",
      source_kind: "public_mirror",
      source_url: "https://github.com/barais/hal-irisa-scripts/blob/commit/data/scimagojr_2025.csv",
      attribution: "SCImago, SJR — SCImago Journal & Country Rank",
    });
    expect(html).toContain("Квартили: SJR 2025; получены 19.09.2026");
    expect(html).toContain('href="https://www.scimagojr.com/journalrank.php?year=2025"');
    expect(html).toContain('href="https://github.com/barais/hal-irisa-scripts/blob/commit/data/scimagojr_2025.csv"');
    expect(html).toContain("SCImago — SCImago Journal &amp; Country Rank");
    expect(html).toContain("публичный снимок");
    expect(html).not.toContain("опубликован SJR 2025");
    expect(html).not.toContain("устаревшими");
    expect(html).not.toContain("text-amber-700");
  });

  test("a newer published edition preserves the stale-data warning", () => {
    const html = render({ version: "SJR 2025", latest_version: "SJR 2026", status: "outdated" });
    expect(html).toContain("опубликован SJR 2026");
    expect(html).toContain("данные могут быть устаревшими");
    expect(html).toContain("text-amber-700");
  });

  test("absent metadata is clearly labelled without inventing a date or source", () => {
    const html = render(null);
    expect(html).toContain("Квартили: дата не определена");
    expect(html).not.toContain("href=");
    expect(html).not.toContain("получены");
  });

  test("malformed dates and non-web URLs cannot create misleading links", () => {
    const html = render({
      retrieved_at: "unknown",
      url: "javascript:alert(1)",
      source_kind: "public_mirror",
      source_url: "data:text/html,unsafe",
    });
    expect(html).not.toContain("href=");
    expect(html).not.toContain("получены");
    expect(html).not.toContain("публичный снимок");
  });
});
