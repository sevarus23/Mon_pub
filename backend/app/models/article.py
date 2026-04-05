from datetime import date, datetime

from sqlalchemy import Column, Date, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    num_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    journal_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    issn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str | None] = mapped_column("type", String(50), nullable=True)
    quartile: Mapped[str | None] = mapped_column(String(2), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cited_by_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), server_default="{}", nullable=False)
    white_list_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    core_rank: Mapped[str | None] = mapped_column(String(10), nullable=True)
    search_vector = Column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_articles_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
        Index("idx_articles_authors_trgm", "authors", postgresql_using="gin", postgresql_ops={"authors": "gin_trgm_ops"}),
        Index("idx_articles_journal_trgm", "journal_name", postgresql_using="gin", postgresql_ops={"journal_name": "gin_trgm_ops"}),
        Index("idx_articles_doi", "doi"),
        Index("idx_articles_issn", "issn"),
        Index("idx_articles_published_at", "published_at"),
        Index("idx_articles_topics", "topics", postgresql_using="gin"),
        Index("idx_articles_white_list_level", "white_list_level"),
        Index("idx_articles_core_rank", "core_rank"),
        Index("idx_articles_fts", "search_vector", postgresql_using="gin"),
    )
