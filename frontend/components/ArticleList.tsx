"use client";

import type { Article } from "@/types";
import ArticleCard from "./ArticleCard";

interface ArticleListProps {
  articles: Article[];
  loading: boolean;
  error: string | null;
}

export default function ArticleList({
  articles,
  loading,
  error,
}: ArticleListProps) {
  if (error) {
    return (
      <div className="text-center py-10 text-[#999]">
        <p className="text-accent mb-2">Ошибка загрузки</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-3.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-[10px] p-5 px-6 shadow-[0_1px_4px_rgba(0,0,0,0.06)] border-l-4 border-transparent animate-pulse"
          >
            <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="flex gap-4 mt-3">
              <div className="h-3 bg-gray-200 rounded w-32" />
              <div className="h-3 bg-gray-200 rounded w-20" />
              <div className="h-3 bg-gray-200 rounded w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="text-center py-10 text-[#999]">
        Публикации не найдены
      </div>
    );
  }

  return (
    <div className="space-y-3.5">
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
