"use client";

import { Suspense, useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
import Filters from "@/components/Filters";
import ArticleList from "@/components/ArticleList";
import Sidebar from "@/components/Sidebar";
import Pagination from "@/components/Pagination";
import { getArticles, getStats, searchOpenAlex, getExportUrl } from "@/lib/api";
import type { ArticlesResponse, Stats, Filters as FiltersType } from "@/types";

const DEFAULT_FILTERS: FiltersType = {
  search: "",
  date_from: "",
  date_to: "",
  journal_name: "",
  author: "",
  article_type: "",
  topic: "",
  quartile: "",
  scopus_only: false,
  white_list_only: false,
  iu_only: true,
  institution: "",
  sort_by: "published_at",
  sort_order: "desc",
  page: 1,
  per_page: 15,
};

function filtersFromParams(params: URLSearchParams): FiltersType {
  return {
    search: params.get("search") || "",
    date_from: params.get("date_from") || "",
    date_to: params.get("date_to") || "",
    journal_name: params.get("journal_name") || "",
    author: params.get("author") || "",
    article_type: params.get("article_type") || "",
    topic: params.get("topic") || "",
    quartile: params.get("quartile") || "",
    scopus_only: params.get("scopus_only") === "true",
    white_list_only: params.get("white_list_only") === "true",
    iu_only: params.get("iu_only") !== "false",
    institution: params.get("institution") || "",
    sort_by: params.get("sort_by") || "published_at",
    sort_order: params.get("sort_order") || "desc",
    page: Number(params.get("page")) || 1,
    per_page: Number(params.get("per_page")) || 15,
  };
}

function filtersToParams(f: FiltersType): string {
  const sp = new URLSearchParams();
  if (f.search) sp.set("search", f.search);
  if (f.date_from) sp.set("date_from", f.date_from);
  if (f.date_to) sp.set("date_to", f.date_to);
  if (f.journal_name) sp.set("journal_name", f.journal_name);
  if (f.author) sp.set("author", f.author);
  if (f.article_type) sp.set("article_type", f.article_type);
  if (f.topic) sp.set("topic", f.topic);
  if (f.quartile) sp.set("quartile", f.quartile);
  if (f.scopus_only) sp.set("scopus_only", "true");
  if (f.white_list_only) sp.set("white_list_only", "true");
  if (!f.iu_only) sp.set("iu_only", "false");
  if (f.institution) sp.set("institution", f.institution);
  if (f.sort_by && f.sort_by !== "published_at") sp.set("sort_by", f.sort_by);
  if (f.sort_order && f.sort_order !== "desc") sp.set("sort_order", f.sort_order);
  if (f.page > 1) sp.set("page", String(f.page));
  if (f.per_page !== 15) sp.set("per_page", String(f.per_page));
  const qs = sp.toString();
  return qs ? `?${qs}` : "/";
}

export default function HomePage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center min-h-screen text-text-muted">Загрузка...</div>}>
      <HomeContent />
    </Suspense>
  );
}

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState<FiltersType>(() => filtersFromParams(searchParams));
  const [articles, setArticles] = useState<ArticlesResponse | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const isInitial = useRef(true);

  const globalMode = !filters.iu_only;

  useEffect(() => {
    if (isInitial.current) {
      isInitial.current = false;
      return;
    }
    router.replace(filtersToParams(filters), { scroll: false });
  }, [filters, router]);

  const fetchArticles = useCallback(async (f: FiltersType) => {
    setLoading(true);
    setError(null);
    try {
      let data: ArticlesResponse;
      if (f.iu_only) {
        data = await getArticles({
          page: f.page,
          per_page: f.per_page,
          search: f.search || undefined,
          journal_name: f.journal_name || undefined,
          author: f.author || undefined,
          date_from: f.date_from ? `${f.date_from}-01-01` : undefined,
          date_to: f.date_to ? `${f.date_to}-12-31` : undefined,
          quartile: f.quartile || undefined,
          article_type: f.article_type || undefined,
          topic: f.topic || undefined,
          scopus_only: f.scopus_only || undefined,
          white_list_only: f.white_list_only || undefined,
          sort_by: f.sort_by || undefined,
          sort_order: f.sort_order || undefined,
        });
      } else {
        data = await searchOpenAlex({
          page: f.page,
          per_page: f.per_page,
          search: f.search || undefined,
          date_from: f.date_from ? `${f.date_from}-01-01` : undefined,
          date_to: f.date_to ? `${f.date_to}-12-31` : undefined,
          sort_by: f.sort_by || undefined,
          sort_order: f.sort_order || undefined,
          institution: f.institution || undefined,
        });
      }
      setArticles(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки данных");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async (f: FiltersType) => {
    if (!f.iu_only) {
      setStats(null);
      return;
    }
    try {
      const data = await getStats({
        quartile: f.quartile || undefined,
        search: f.search || undefined,
        article_type: f.article_type || undefined,
        scopus_only: f.scopus_only || undefined,
      });
      setStats(data);
    } catch {
      // Stats are non-critical
    }
  }, []);

  useEffect(() => { fetchArticles(filters); fetchStats(filters); }, [filters, fetchArticles, fetchStats]);

  const handleFiltersChange = (newFilters: Partial<FiltersType>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handleSearch = () => {
    setFilters((prev) => ({ ...prev, page: 1 }));
    fetchArticles({ ...filters, page: 1 });
  };

  const handleReset = () => setFilters({ ...DEFAULT_FILTERS, iu_only: filters.iu_only });

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    listRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleQuartileClick = (q: string) => {
    setFilters((prev) => ({
      ...prev,
      quartile: prev.quartile === q ? "" : q,
      page: 1,
    }));
  };

  return (
    <div className="min-h-screen bg-surface-secondary">
      <Header stats={stats} globalMode={globalMode} />
      <Filters
        filters={filters}
        onChange={handleFiltersChange}
        onSearch={handleSearch}
        onReset={handleReset}
      />
      <main className="max-w-[1280px] mx-auto px-5 py-6 grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
        <div ref={listRef}>
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-3">
              <p className="text-sm text-text-secondary">
                {articles
                  ? `${articles.total.toLocaleString("ru-RU")} публикаций`
                  : "Загрузка..."}
                {globalMode && <span className="ml-2 text-xs text-primary">(OpenAlex)</span>}
              </p>
              {!globalMode && articles && articles.total > 0 && (
                <div className="flex gap-1">
                  <a
                    href={getExportUrl({
                      search: filters.search || undefined,
                      journal_name: filters.journal_name || undefined,
                      author: filters.author || undefined,
                      date_from: filters.date_from ? `${filters.date_from}-01-01` : undefined,
                      date_to: filters.date_to ? `${filters.date_to}-12-31` : undefined,
                      quartile: filters.quartile || undefined,
                      article_type: filters.article_type || undefined,
                      topic: filters.topic || undefined,
                      scopus_only: filters.scopus_only || undefined,
                      white_list_only: filters.white_list_only || undefined,
                      sort_by: filters.sort_by || undefined,
                      sort_order: filters.sort_order || undefined,
                    }, "xlsx")}
                    className="text-xs px-2 py-1 border border-surface-border rounded hover:border-primary hover:text-primary transition-colors"
                    download
                  >
                    XLSX
                  </a>
                  <a
                    href={getExportUrl({
                      search: filters.search || undefined,
                      journal_name: filters.journal_name || undefined,
                      author: filters.author || undefined,
                      date_from: filters.date_from ? `${filters.date_from}-01-01` : undefined,
                      date_to: filters.date_to ? `${filters.date_to}-12-31` : undefined,
                      quartile: filters.quartile || undefined,
                      article_type: filters.article_type || undefined,
                      topic: filters.topic || undefined,
                      scopus_only: filters.scopus_only || undefined,
                      white_list_only: filters.white_list_only || undefined,
                      sort_by: filters.sort_by || undefined,
                      sort_order: filters.sort_order || undefined,
                    }, "csv")}
                    className="text-xs px-2 py-1 border border-surface-border rounded hover:border-primary hover:text-primary transition-colors"
                    download
                  >
                    CSV
                  </a>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <select
                className="filter-select text-xs"
                value={filters.sort_by}
                onChange={(e) => setFilters((prev) => ({ ...prev, sort_by: e.target.value, page: 1 }))}
              >
                <option value="published_at">По дате</option>
                <option value="title">По названию</option>
                <option value="cited_by_count">По цитированиям</option>
              </select>
              <select
                className="filter-select text-xs"
                value={filters.sort_order}
                onChange={(e) => setFilters((prev) => ({ ...prev, sort_order: e.target.value, page: 1 }))}
              >
                <option value="desc">По убыванию</option>
                <option value="asc">По возрастанию</option>
              </select>
            </div>
          </div>

          <ArticleList
            articles={articles?.items ?? []}
            loading={loading}
            error={error}
            onRetry={() => fetchArticles(filters)}
            onReset={handleReset}
          />

          {articles && articles.pages > 1 && (
            <Pagination
              currentPage={articles.page}
              totalPages={articles.pages}
              onPageChange={handlePageChange}
            />
          )}
        </div>

        <Sidebar stats={stats} onQuartileClick={handleQuartileClick} globalMode={globalMode} />
      </main>
    </div>
  );
}
