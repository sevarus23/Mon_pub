from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SortBy(str, Enum):
    published_at = "published_at"
    title = "title"
    journal_name = "journal_name"
    cited_by_count = "cited_by_count"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class ArticleFilters(BaseModel):
    search: str | None = None
    journal_name: str | None = None
    issn: str | None = None
    author: str | None = None
    title: str | None = None
    doi: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    source: str | None = None
    year: int | None = None
    quartile: str | None = None
    article_type: str | None = None
    topic: str | None = None
    scopus_only: bool = False
    white_list_only: bool = False
    core_rank: str | None = None
    sort_by: SortBy = SortBy.published_at
    sort_order: SortOrder = SortOrder.desc
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class ArticleCreate(BaseModel):
    num_id: str
    title: str
    authors: str
    doi: str | None = None
    published_at: date | None = None
    journal_name: str | None = None
    issn: str | None = None
    type: str | None = None
    publisher: str | None = None
    cited_by_count: int | None = None
    language: str | None = None
    source: str
    topics: list[str] = []


class ArticleOut(BaseModel):
    id: int
    num_id: str
    title: str
    authors: str
    doi: str | None
    published_at: date | None
    journal_name: str | None
    issn: str | None
    type: str | None
    quartile: str | None
    publisher: str | None
    cited_by_count: int | None
    language: str | None
    source: str
    topics: list[str] = []
    white_list_level: int | None = None
    core_rank: str | None = None
    in_scopus: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedArticles(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[ArticleOut]


class YearCount(BaseModel):
    year: int
    count: int


class JournalCount(BaseModel):
    journal_name: str
    count: int


class SourceCount(BaseModel):
    source: str
    count: int


class StatsOut(BaseModel):
    total: int
    total_authors: int
    new_today: int
    new_this_week: int
    new_this_month: int
    first_published_date: date | None
    by_source: list[SourceCount]
    by_year: list[YearCount]
    top_journals: list[JournalCount]


class SourceInfo(BaseModel):
    journal_name: str
    issn: str | None
    article_count: int
    quartile: str | None
    white_list_level: int | None
    in_scopus: bool
    in_white_list: bool


class ConferenceInfo(BaseModel):
    journal_name: str
    article_count: int
    core_rank: str | None
    quartile: str | None
    white_list_level: int | None


class ParseResponse(BaseModel):
    message: str


class ScopusImportResponse(BaseModel):
    total_in_file: int
    matched_by_doi: int
    matched_by_title: int
    created_new: int
    total_scopus: int
