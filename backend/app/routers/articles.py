import asyncio
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.article import ArticleRepository
from app.schemas.article import (
    ArticleFilters,
    ArticleOut,
    PaginatedArticles,
    ParseResponse,
    SortBy,
    SortOrder,
    StatsOut,
)
from app.services.scheduler import run_parse
from app.services.sjr import update_quartiles_from_csv

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _get_repo(session: AsyncSession = Depends(get_session)) -> ArticleRepository:
    return ArticleRepository(session)


@router.get("", response_model=PaginatedArticles)
async def list_articles(
    repo: ArticleRepository = Depends(_get_repo),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    journal_name: str | None = None,
    issn: str | None = None,
    author: str | None = None,
    title: str | None = None,
    doi: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    source: str | None = None,
    year: int | None = None,
    quartile: str | None = None,
    article_type: str | None = None,
    scopus_only: bool = False,
    sort_by: SortBy = SortBy.published_at,
    sort_order: SortOrder = SortOrder.desc,
):
    filters = ArticleFilters(
        search=search,
        journal_name=journal_name,
        issn=issn,
        author=author,
        title=title,
        doi=doi,
        date_from=date_from,
        date_to=date_to,
        source=source,
        year=year,
        quartile=quartile,
        article_type=article_type,
        scopus_only=scopus_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    return await repo.get_filtered(filters)


@router.get("/journals", response_model=list[str])
async def get_journals(
    search: str | None = None,
    repo: ArticleRepository = Depends(_get_repo),
):
    return await repo.get_journals(search=search)


@router.get("/types", response_model=list[str])
async def get_types(
    search: str | None = None,
    repo: ArticleRepository = Depends(_get_repo),
):
    return await repo.get_types(search=search)


@router.get("/authors", response_model=list[str])
async def get_authors(
    search: str | None = None,
    repo: ArticleRepository = Depends(_get_repo),
):
    return await repo.get_authors(search=search)


@router.get("/quartiles", response_model=list[str])
async def get_quartiles(repo: ArticleRepository = Depends(_get_repo)):
    return await repo.get_quartiles()


@router.get("/openalex-search")
async def openalex_search(
    search: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: SortBy = SortBy.published_at,
    sort_order: SortOrder = SortOrder.desc,
):
    from app.services.openalex import search_openalex
    try:
        return await search_openalex(
            search=search,
            page=page,
            per_page=per_page,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAlex API error: {e}")


@router.get("/stats", response_model=StatsOut)
async def get_stats(
    repo: ArticleRepository = Depends(_get_repo),
    quartile: str | None = None,
    source: str | None = None,
    article_type: str | None = None,
    year: int | None = None,
    search: str | None = None,
    scopus_only: bool = False,
):
    return await repo.get_stats(
        quartile=quartile,
        source=source,
        article_type=article_type,
        year=year,
        search=search,
        scopus_only=scopus_only,
    )


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: int, repo: ArticleRepository = Depends(_get_repo)):
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleOut.model_validate(article)


@router.post("/parse", response_model=ParseResponse)
async def trigger_parse(background_tasks: BackgroundTasks):
    background_tasks.add_task(asyncio.to_thread, lambda: asyncio.run(run_parse()))
    return ParseResponse(message="Parsing started in background")


@router.post("/update-quartiles", response_model=ParseResponse)
async def trigger_quartile_update():
    updated = await update_quartiles_from_csv()
    return ParseResponse(message=f"Updated quartile for {updated} articles")


@router.post("/normalize-types", response_model=ParseResponse)
async def trigger_normalize_types(repo: ArticleRepository = Depends(_get_repo)):
    updated = await repo.normalize_all_types()
    return ParseResponse(message=f"Normalized type for {updated} articles")
