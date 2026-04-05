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
      className={`bg-white rounded-card py-4 px-5 shadow-card border-l-[3px] transition-all relative hover:shadow-card-hover ${
        isNew ? "border-l-accent" : "border-l-transparent hover:border-l-primary"
      }`}
    >
      {isNew && (
        <span className="absolute top-3 right-4 bg-accent text-white text-[0.7rem] font-bold py-0.5 px-2 rounded-full uppercase tracking-wide">
          new
        </span>
      )}

      {/* Title */}
      <h3 className="text-[0.95rem] font-semibold mb-1.5 leading-snug pr-14">
        {article.doi ? (
          <a
            href={`https://doi.org/${article.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-700 no-underline hover:text-primary hover:underline"
          >
            {article.title}
          </a>
        ) : (
          <span className="text-primary-700">{article.title}</span>
        )}
      </h3>

      {/* Authors */}
      <p className="text-sm text-text-secondary mb-2 leading-relaxed">
        {article.authors}
      </p>

      {/* Meta row */}
      <div className="flex flex-wrap gap-3 items-center text-xs text-text-muted">
        {article.journal_name && (
          <span className="italic text-text-secondary">
            {article.journal_name}
          </span>
        )}

        <span>{formatDate(article.published_at)}</span>

        {article.quartile && (
          <span className={`inline-block py-0.5 px-2 rounded text-xs font-bold text-white ${qClass}`}>
            {article.quartile}
          </span>
        )}

        <span className="py-0.5 px-2 rounded bg-type-bg text-type-text text-xs font-medium">
          {typeLabel}
        </span>

        {article.doi && (
          <a
            href={`https://doi.org/${article.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            DOI
          </a>
        )}

        {article.cited_by_count != null && (
          <span className="inline-flex items-center gap-1 bg-surface-secondary py-0.5 px-2 rounded text-text-secondary">
            {article.cited_by_count} цит.
          </span>
        )}
      </div>

      {/* Topics */}
      {article.topics && article.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {article.topics.slice(0, 5).map((topic) => (
            <span
              key={topic}
              className="inline-block py-0.5 px-2 rounded-full bg-blue-50 text-blue-700 text-[0.65rem] font-medium"
            >
              {topic}
            </span>
          ))}
          {article.topics.length > 5 && (
            <span className="text-[0.65rem] text-text-muted self-center">
              +{article.topics.length - 5}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
