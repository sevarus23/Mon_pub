import math
from datetime import date, timedelta

from sqlalchemy import String, desc, func, select, text
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article
from app.utils.type_mapping import TYPE_MAPPING
from app.schemas.article import (
    ArticleCreate,
    ArticleFilters,
    ArticleOut,
    JournalCount,
    PaginatedArticles,
    SortOrder,
    SourceCount,
    StatsOut,
    YearCount,
)

SIMILARITY_THRESHOLD = 0.3


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, article_id: int) -> Article | None:
        result = await self._session.execute(
            select(Article).where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_last_published_date(self) -> date | None:
        result = await self._session.execute(
            select(func.max(Article.published_at))
        )
        return result.scalar()

    async def bulk_upsert(self, articles: list[ArticleCreate]) -> int:
        if not articles:
            return 0

        total_inserted = 0
        # Split into articles with DOI and without DOI
        with_doi = [a for a in articles if a.doi]
        without_doi = [a for a in articles if not a.doi]

        if with_doi:
            values = [a.model_dump() for a in with_doi]
            stmt = (
                insert(Article)
                .values(values)
                .on_conflict_do_nothing(index_elements=["doi"])
            )
            result = await self._session.execute(stmt)
            total_inserted += result.rowcount  # type: ignore[assignment]

        if without_doi:
            values = [a.model_dump() for a in without_doi]
            stmt = (
                insert(Article)
                .values(values)
                .on_conflict_do_nothing(index_elements=["num_id"])
            )
            result = await self._session.execute(stmt)
            total_inserted += result.rowcount  # type: ignore[assignment]

        await self._session.commit()
        return total_inserted

    async def get_filtered(self, filters: ArticleFilters) -> PaginatedArticles:
        query = select(Article)
        count_query = select(func.count(Article.id))

        has_fuzzy = any([filters.search, filters.journal_name, filters.author, filters.title])
        if has_fuzzy:
            await self._session.execute(
                text(f"SET pg_trgm.similarity_threshold = {SIMILARITY_THRESHOLD}")
            )

        query, count_query = self._apply_filters(query, count_query, filters)

        # Sorting
        sort_column = getattr(Article, filters.sort_by.value)
        if filters.search:
            relevance = self._search_relevance(filters.search)
            if filters.sort_order == SortOrder.desc:
                query = query.order_by(desc(relevance), sort_column.desc().nullslast())
            else:
                query = query.order_by(desc(relevance), sort_column.asc().nullsfirst())
        else:
            if filters.sort_order == SortOrder.desc:
                query = query.order_by(sort_column.desc().nullslast())
            else:
                query = query.order_by(sort_column.asc().nullsfirst())

        # Count
        total = (await self._session.execute(count_query)).scalar() or 0

        # Pagination
        offset = (filters.page - 1) * filters.per_page
        query = query.offset(offset).limit(filters.per_page)
        result = await self._session.execute(query)
        articles = result.scalars().all()

        return PaginatedArticles(
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            pages=math.ceil(total / filters.per_page) if filters.per_page else 0,
            items=[ArticleOut.model_validate(a) for a in articles],
        )

    async def get_stats(
        self,
        quartile: str | None = None,
        source: str | None = None,
        article_type: str | None = None,
        year: int | None = None,
        search: str | None = None,
        scopus_only: bool = False,
    ) -> StatsOut:
        # Build optional WHERE conditions
        conditions = []
        if quartile:
            conditions.append(Article.quartile == quartile)
        if source:
            conditions.append(Article.source == source)
        if article_type:
            conditions.append(Article.type == article_type)
        if year:
            conditions.append(func.extract("year", Article.published_at) == year)
        if scopus_only:
            from app.utils.scopus import get_scopus_issns
            scopus_issns = list(get_scopus_issns())
            conditions.append(Article.issn == func.any_(func.cast(scopus_issns, ARRAY(String))))
        if search:
            like_pat = f"%{search}%"
            conditions.append(
                Article.title.ilike(like_pat) | Article.authors.ilike(like_pat)
            )

        def _where(stmt):
            for c in conditions:
                stmt = stmt.where(c)
            return stmt

        total = (
            await self._session.execute(_where(select(func.count(Article.id))))
        ).scalar() or 0

        # Unique authors count via subquery
        author_base = select(Article.authors).where(Article.authors.is_not(None))
        for c in conditions:
            author_base = author_base.where(c)
        author_subq = (
            select(
                func.distinct(func.trim(func.unnest(func.string_to_array(author_base.subquery().c.authors, ","))))
            ).subquery()
        )
        total_authors = (
            await self._session.execute(select(func.count()).select_from(author_subq))
        ).scalar() or 0

        # New today / this week by published_at
        today = date.today()
        week_ago = today - timedelta(days=7)

        new_today = (
            await self._session.execute(
                _where(select(func.count(Article.id)).where(Article.published_at == today))
            )
        ).scalar() or 0

        new_this_week = (
            await self._session.execute(
                _where(select(func.count(Article.id)).where(Article.published_at >= week_ago))
            )
        ).scalar() or 0

        month_ago = today - timedelta(days=30)
        new_this_month = (
            await self._session.execute(
                _where(select(func.count(Article.id)).where(Article.published_at >= month_ago))
            )
        ).scalar() or 0

        # First published date
        first_published_date = (
            await self._session.execute(
                _where(select(func.min(Article.published_at))
                .where(Article.published_at.is_not(None)))
            )
        ).scalar()

        # By source
        source_q = select(Article.source, func.count(Article.id)).group_by(Article.source)
        source_rows = (await self._session.execute(_where(source_q))).all()
        by_source = [SourceCount(source=r[0], count=r[1]) for r in source_rows]

        # By year
        year_expr = func.extract("year", Article.published_at).label("year")
        year_q = (
            select(year_expr, func.count(Article.id))
            .where(Article.published_at.is_not(None))
            .group_by(year_expr)
            .order_by(year_expr.desc())
        )
        year_rows = (await self._session.execute(_where(year_q))).all()
        by_year = [YearCount(year=int(r[0]), count=r[1]) for r in year_rows]

        # Top journals
        journal_q = (
            select(Article.journal_name, func.count(Article.id))
            .where(Article.journal_name.is_not(None))
            .group_by(Article.journal_name)
            .order_by(func.count(Article.id).desc())
            .limit(10)
        )
        journal_rows = (await self._session.execute(_where(journal_q))).all()
        top_journals = [JournalCount(journal_name=r[0], count=r[1]) for r in journal_rows]

        return StatsOut(
            total=total,
            total_authors=total_authors,
            new_today=new_today,
            new_this_week=new_this_week,
            new_this_month=new_this_month,
            first_published_date=first_published_date,
            by_source=by_source,
            by_year=by_year,
            top_journals=top_journals,
        )

    async def get_journals(self, search: str | None = None) -> list[str]:
        query = (
            select(Article.journal_name)
            .where(Article.journal_name.is_not(None))
            .distinct()
        )
        if search:
            ws = func.word_similarity(search, Article.journal_name).label("ws")
            query = (
                select(Article.journal_name, ws)
                .where(Article.journal_name.is_not(None))
                .where(ws > 0.2)
                .distinct()
                .order_by(ws.desc())
            )
        else:
            query = query.order_by(Article.journal_name)
        rows = (await self._session.execute(query)).all()
        return [r[0] for r in rows]

    async def get_types(self, search: str | None = None) -> list[str]:
        not_empty = (Article.type.is_not(None)) & (Article.type != "")
        query = (
            select(Article.type)
            .where(not_empty)
            .distinct()
        )
        if search:
            ws = func.word_similarity(search, Article.type).label("ws")
            query = (
                select(Article.type, ws)
                .where(not_empty)
                .where(ws > 0.2)
                .distinct()
                .order_by(ws.desc())
            )
        else:
            query = query.order_by(Article.type)
        rows = (await self._session.execute(query)).all()
        return [r[0] for r in rows]

    async def get_authors(self, search: str | None = None) -> list[str]:
        author_expr = func.trim(func.unnest(func.string_to_array(Article.authors, ",")))
        subq = (
            select(author_expr.label("author"))
            .where(Article.authors.is_not(None))
            .subquery()
        )
        col = subq.c.author
        if search:
            ws = func.word_similarity(search, col).label("ws")
            query = (
                select(col, ws)
                .where(col != "Unknown")
                .where(col != "")
                .where(ws > 0.2)
                .distinct()
                .order_by(ws.desc())
                .limit(50)
            )
        else:
            query = (
                select(col)
                .where(col != "Unknown")
                .where(col != "")
                .distinct()
                .order_by(col)
                .limit(50)
            )
        rows = (await self._session.execute(query)).all()
        return [r[0] for r in rows]

    async def get_quartiles(self) -> list[str]:
        result = await self._session.execute(
            select(Article.quartile)
            .where(Article.quartile.is_not(None))
            .distinct()
            .order_by(Article.quartile)
        )
        return list(result.scalars().all())

    async def get_topics(self, search: str | None = None) -> list[str]:
        topic_expr = func.unnest(Article.topics).label("topic")
        subq = (
            select(topic_expr)
            .where(func.array_length(Article.topics, 1) > 0)
            .subquery()
        )
        col = subq.c.topic

        if search:
            await self._session.execute(
                text(f"SET pg_trgm.similarity_threshold = {SIMILARITY_THRESHOLD}")
            )
            ws = func.word_similarity(search, col).label("ws")
            query = (
                select(col, ws)
                .where(col != "")
                .where(ws > 0.2)
                .distinct()
                .order_by(ws.desc())
                .limit(50)
            )
        else:
            query = (
                select(col)
                .where(col != "")
                .distinct()
                .order_by(col)
                .limit(50)
            )
        rows = (await self._session.execute(query)).all()
        return [r[0] for r in rows]

    async def normalize_all_types(self) -> int:
        """Update existing articles with normalized type mapping."""
        updated = 0
        for old_type, new_type in TYPE_MAPPING.items():
            if old_type == new_type:
                continue
            result = await self._session.execute(
                text("UPDATE articles SET type = :new WHERE type = :old"),
                {"old": old_type, "new": new_type},
            )
            updated += result.rowcount
        await self._session.commit()
        return updated

    async def get_all_filtered(self, filters: ArticleFilters, limit: int = 10000) -> list[Article]:
        query = select(Article)
        count_query = select(func.count(Article.id))

        has_fuzzy = any([filters.search, filters.journal_name, filters.author, filters.title])
        if has_fuzzy:
            await self._session.execute(
                text(f"SET pg_trgm.similarity_threshold = {SIMILARITY_THRESHOLD}")
            )

        query, _ = self._apply_filters(query, count_query, filters)

        sort_column = getattr(Article, filters.sort_by.value)
        if filters.sort_order == SortOrder.desc:
            query = query.order_by(sort_column.desc().nullslast())
        else:
            query = query.order_by(sort_column.asc().nullsfirst())

        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    # ---- private ----

    def _author_fuzzy_cond(self, search_term: str):
        """Fuzzy match against individual authors (split by comma)."""
        return text(
            "EXISTS (SELECT 1 FROM unnest(string_to_array(articles.authors, ',')) AS a "
            "WHERE word_similarity(:term, trim(a)) > 0.6 OR trim(a) ILIKE :pat)"
        ).bindparams(term=search_term, pat=f"%{search_term}%")

    def _search_relevance(self, search_term: str):
        """Relevance score: exact ILIKE match = top, then fuzzy matches below."""
        return text(
            "CASE WHEN articles.authors ILIKE :pat THEN 2"
            " WHEN articles.title ILIKE :pat THEN 1"
            " ELSE 0 END"
        ).bindparams(pat=f"%{search_term}%")

    def _apply_filters(self, query, count_query, filters: ArticleFilters):
        if filters.search:
            like_pat = f"%{filters.search}%"
            author_cond = self._author_fuzzy_cond(filters.search)
            # FTS: stemming via plainto_tsquery
            fts_cond = Article.search_vector.op("@@")(
                func.plainto_tsquery("english", filters.search)
            )
            cond = (
                Article.title.ilike(like_pat)
                | (func.word_similarity(filters.search, Article.title) > 0.6)
                | author_cond
                | fts_cond
            )
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.journal_name:
            cond = Article.journal_name == filters.journal_name
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.author:
            cond = self._author_fuzzy_cond(filters.author)
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.title:
            cond = func.similarity(Article.title, filters.title) > SIMILARITY_THRESHOLD
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.issn:
            query = query.where(Article.issn == filters.issn)
            count_query = count_query.where(Article.issn == filters.issn)

        if filters.doi:
            query = query.where(Article.doi == filters.doi)
            count_query = count_query.where(Article.doi == filters.doi)

        if filters.date_from:
            query = query.where(Article.published_at >= filters.date_from)
            count_query = count_query.where(Article.published_at >= filters.date_from)

        if filters.date_to:
            query = query.where(Article.published_at <= filters.date_to)
            count_query = count_query.where(Article.published_at <= filters.date_to)

        if filters.source:
            query = query.where(Article.source == filters.source)
            count_query = count_query.where(Article.source == filters.source)

        if filters.year:
            year_expr = func.extract("year", Article.published_at)
            query = query.where(year_expr == filters.year)
            count_query = count_query.where(year_expr == filters.year)

        if filters.quartile:
            query = query.where(Article.quartile == filters.quartile)
            count_query = count_query.where(Article.quartile == filters.quartile)

        if filters.article_type:
            query = query.where(Article.type == filters.article_type)
            count_query = count_query.where(Article.type == filters.article_type)

        if filters.topic:
            # Search in topics array OR fall back to FTS on title
            topic_in_array = Article.topics.any(filters.topic)
            fts_fallback = Article.search_vector.op("@@")(
                func.plainto_tsquery("english", filters.topic)
            )
            cond = topic_in_array | fts_fallback
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.scopus_only:
            from app.utils.scopus import get_scopus_issns
            scopus_issns = list(get_scopus_issns())
            cond = Article.issn == func.any_(func.cast(scopus_issns, ARRAY(String)))
            query = query.where(cond)
            count_query = count_query.where(cond)

        return query, count_query
