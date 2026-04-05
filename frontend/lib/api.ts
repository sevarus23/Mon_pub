import type { ArticlesResponse, Stats, SourceInfo, ConferenceInfo } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/mon_pub";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

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

export async function getArticles(params: {
  page?: number;
  per_page?: number;
  search?: string;
  journal_name?: string;
  author?: string;
  date_from?: string;
  date_to?: string;
  quartile?: string;
  article_type?: string;
  topic?: string;
  scopus_only?: boolean;
  white_list_only?: boolean;
  sort_by?: string;
  sort_order?: string;
}): Promise<ArticlesResponse> {
  const query = buildQuery(params);
  return fetchJSON<ArticlesResponse>(`${BASE_URL}/api/articles${query}`);
}

export async function getStats(params?: {
  quartile?: string;
  source?: string;
  article_type?: string;
  year?: number;
  search?: string;
  scopus_only?: boolean;
}): Promise<Stats> {
  const query = params ? buildQuery(params) : "";
  return fetchJSON<Stats>(`${BASE_URL}/api/articles/stats${query}`);
}

export async function getJournals(search?: string): Promise<string[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<string[]>(`${BASE_URL}/api/articles/journals${query}`);
}

export async function getArticleTypes(search?: string): Promise<string[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<string[]>(`${BASE_URL}/api/articles/types${query}`);
}

export async function getAuthors(search?: string): Promise<string[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<string[]>(`${BASE_URL}/api/articles/authors${query}`);
}

export async function getQuartiles(): Promise<string[]> {
  return fetchJSON<string[]>(`${BASE_URL}/api/articles/quartiles`);
}

export async function getTopics(search?: string): Promise<string[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<string[]>(`${BASE_URL}/api/articles/topics${query}`);
}

export async function getConferencesTable(search?: string): Promise<ConferenceInfo[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<ConferenceInfo[]>(`${BASE_URL}/api/articles/conferences-table${query}`);
}

export async function getSourcesTable(search?: string): Promise<SourceInfo[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return fetchJSON<SourceInfo[]>(`${BASE_URL}/api/articles/sources-table${query}`);
}

export function getExportUrl(params: {
  search?: string;
  journal_name?: string;
  author?: string;
  date_from?: string;
  date_to?: string;
  quartile?: string;
  article_type?: string;
  topic?: string;
  scopus_only?: boolean;
  white_list_only?: boolean;
  sort_by?: string;
  sort_order?: string;
}, format: "xlsx" | "csv" = "xlsx"): string {
  const query = buildQuery({ ...params, format });
  return `${BASE_URL}/api/articles/export${query}`;
}

export async function searchOpenAlex(params: {
  page?: number;
  per_page?: number;
  search?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  institution?: string;
}): Promise<ArticlesResponse> {
  const query = buildQuery(params);
  return fetchJSON<ArticlesResponse>(`${BASE_URL}/api/articles/openalex-search${query}`);
}
