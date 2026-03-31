"use client";

import type { Article } from "@/types";
import ArticleCard from "./ArticleCard";

interface ArticleListProps {
  articles: Article[];
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
  onReset?: () => void;
}

export default function ArticleList({
  articles,
  loading,
  error,
  onRetry,
  onReset,
}: ArticleListProps) {
  if (error) {
    return (
      <div className="bg-white rounded-card shadow-card text-center py-12 px-6">
        <div className="text-4xl mb-3">&#9888;</div>
        <p className="text-base font-semibold text-text mb-1">Не удалось загрузить данные</p>
        <p className="text-sm text-text-muted mb-4">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-5 py-2 bg-primary text-white rounded-md text-sm font-medium cursor-pointer hover:bg-primary-dark transition-colors"
          >
            Попробовать снова
          </button>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-card p-5 shadow-card border-l-[3px] border-transparent animate-pulse"
          >
            <div className="h-4 bg-primary-50 rounded w-3/4 mb-3" />
            <div className="h-3.5 bg-primary-50 rounded w-1/2 mb-2" />
            <div className="flex gap-4 mt-3">
              <div className="h-3 bg-primary-50 rounded w-32" />
              <div className="h-3 bg-primary-50 rounded w-20" />
              <div className="h-3 bg-primary-50 rounded w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="bg-white rounded-card shadow-card text-center py-12 px-6">
        <div className="text-4xl mb-3">&#128269;</div>
        <p className="text-base font-semibold text-text mb-1">Публикации не найдены</p>
        <p className="text-sm text-text-muted mb-4">
          Попробуйте изменить параметры поиска или сбросить фильтры
        </p>
        {onReset && (
          <button
            onClick={onReset}
            className="px-5 py-2 border border-surface-border text-text-secondary rounded-md text-sm font-medium cursor-pointer hover:border-primary hover:text-primary transition-all"
          >
            Сбросить фильтры
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
