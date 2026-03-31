"use client";

import type { Article } from "@/types";
import { getTypeLabel, getQuartileClass, isNewToday, formatDate } from "@/types";

interface ArticleCardProps {
  article: Article;
}

export default function ArticleCard({ article }: ArticleCardProps) {
  const isNew = isNewToday(article.published_at);
  const qClass = getQuartileClass(article.quartile);
  const typeLabel = getTypeLabel(article.type);

  return (
    <div
      className={`bg-white rounded-[10px] py-5 px-6 shadow-[0_1px_4px_rgba(0,0,0,0.06)] border-l-4 transition-all relative hover:shadow-[0_4px_16px_rgba(0,0,0,0.1)] hover:border-l-primary ${
        isNew ? "border-l-accent" : "border-l-transparent"
      }`}
    >
      {/* NEW badge */}
      {isNew && (
        <span className="absolute top-3 right-4 bg-accent text-white text-[0.7rem] font-bold py-0.5 px-2.5 rounded-[10px] uppercase tracking-wider">
          new
        </span>
      )}

      {/* Title */}
      <div className="text-[1.05rem] font-semibold mb-2 leading-[1.4] pr-[60px]">
        {article.doi ? (
          <a
            href={`https://doi.org/${article.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary no-underline hover:underline hover:text-accent"
          >
            {article.title}
          </a>
        ) : (
          <span className="text-primary">{article.title}</span>
        )}
      </div>

      {/* Authors */}
      <div className="text-[0.88rem] text-[#444] mb-1.5 leading-[1.5]">
        {article.authors}
      </div>

      {/* Meta */}
      <div className="flex flex-wrap gap-4 items-center text-[0.82rem] text-[#777] mt-2">
        {/* Journal */}
        {article.journal_name && (
          <span className="italic text-[#555]">
            {article.journal_name}
            {article.publisher ? ` (${article.publisher})` : ""}
          </span>
        )}

        {/* Date */}
        <span>{formatDate(article.published_at)}</span>

        {/* Quartile badge */}
        {article.quartile && (
          <span
            className={`inline-block py-0.5 px-2 rounded text-[0.75rem] font-bold text-white ${qClass}`}
          >
            {article.quartile}
          </span>
        )}

        {/* Type badge */}
        <span className="text-[0.72rem] py-0.5 px-2 rounded bg-type-bg text-type-text font-medium">
          {typeLabel}
        </span>

        {/* DOI link */}
        {article.doi && (
          <a
            href={`https://doi.org/${article.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary no-underline hover:underline"
          >
            DOI: {article.doi}
          </a>
        )}

        {/* Citations */}
        {article.cited_by_count != null && (
          <span className="inline-flex items-center gap-1 bg-surface py-0.5 px-2 rounded text-[0.78rem] text-[#555]">
            &#128218; {article.cited_by_count} цит.
          </span>
        )}
      </div>
    </div>
  );
}
