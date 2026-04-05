export interface Article {
  id: number;
  num_id: string;
  title: string;
  authors: string;
  doi: string | null;
  published_at: string | null;
  journal_name: string | null;
  issn: string | null;
  type: string | null;
  quartile: string | null;
  publisher: string | null;
  cited_by_count: number | null;
  language: string | null;
  source: string | null;
  topics: string[];
  created_at: string;
  updated_at: string;
}

export interface ArticlesResponse {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: Article[];
}

export interface YearCount {
  year: number;
  count: number;
}

export interface SourceCount {
  source: string;
  count: number;
}

export interface JournalCount {
  journal_name: string;
  count: number;
}

export interface Stats {
  total: number;
  total_authors: number;
  new_today: number;
  new_this_week: number;
  new_this_month: number;
  first_published_date: string | null;
  by_source: SourceCount[];
  by_year: YearCount[];
  top_journals: JournalCount[];
}

export interface Filters {
  search: string;
  date_from: string;
  date_to: string;
  journal_name: string;
  author: string;
  article_type: string;
  topic: string;
  quartile: string;
  scopus_only: boolean;
  iu_only: boolean;
  institution: string;
  sort_by: string;
  sort_order: string;
  page: number;
  per_page: number;
}

export const TYPE_LABELS: Record<string, string> = {
  // CrossRef types
  "journal-article": "Статья",
  "proceedings-article": "Конференция",
  "posted-content": "Препринт",
  "book-chapter": "Глава книги",
  "book": "Книга",
  "monograph": "Монография",
  "dataset": "Датасет",
  "peer-review": "Рецензия",
  "journal-issue": "Выпуск журнала",
  "edited-book": "Ред. книга",
  "reference-entry": "Справка",
  "report": "Отчёт",
  "dissertation": "Диссертация",
  "other": "Другое",
  // OpenAlex raw_type variants
  "article": "Статья",
  "article-journal": "Статья",
  "Article": "Статья",
  "Journal articles": "Статья",
  "info:eu-repo/semantics/article": "Статья",
  "info:eu-repo/semantics/publishedVersion": "Статья",
  "preprint": "Препринт",
  "Preprints, Working Papers, ...": "Препринт",
  "workingPaper": "Препринт",
  "text": "Текст",
  "Dataset": "Датасет",
  "Software": "ПО",
  "Conference papers": "Конференция",
  "Conference or Workshop Item": "Конференция",
  "info:eu-repo/semantics/conferenceObject": "Конференция",
  "info:eu-repo/semantics/other": "Другое",
  "contributionToPeriodical": "Статья в издании",
  "review": "Обзор",
};

export function getTypeLabel(type: string | null): string {
  if (!type) return "Не указан";
  return TYPE_LABELS[type] ?? type;
}

export function getQuartileClass(q: string | null): string {
  switch (q) {
    case "Q1": return "bg-quartile-q1";
    case "Q2": return "bg-quartile-q2";
    case "Q3": return "bg-quartile-q3";
    case "Q4": return "bg-quartile-q4";
    default: return "";
  }
}

export function isNewToday(publishedAt: string | null): boolean {
  if (!publishedAt) return false;
  const today = new Date().toISOString().slice(0, 10);
  return publishedAt === today;
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("ru-RU");
}
