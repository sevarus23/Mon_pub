"""API-level tests for /api/articles endpoints (mocked repository)."""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock

from app.schemas.article import (
    ArticleOut,
    PaginatedArticles,
    ParseResponse,
    StatsOut,
    SourceCount,
    YearCount,
    JournalCount,
)


def _make_article(**overrides) -> ArticleOut:
    defaults = dict(
        id=1,
        num_id="cr_abc123",
        title="Test Article",
        authors="John Doe",
        doi="10.1234/test",
        published_at=date(2024, 1, 1),
        journal_name="Nature",
        issn="1234-5678",
        type="Articles",
        quartile="Q1",
        publisher="Springer",
        cited_by_count=10,
        language="en",
        source="crossref",
        topics=["AI", "Machine Learning"],
        white_list_level=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )
    defaults.update(overrides)
    return ArticleOut(**defaults)


def _make_paginated(items=None, total=1, page=1, per_page=20, pages=1):
    return PaginatedArticles(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items or [_make_article()],
    )


def _make_stats():
    return StatsOut(
        total=100,
        total_authors=50,
        new_today=2,
        new_this_week=10,
        new_this_month=30,
        first_published_date=date(2012, 1, 1),
        by_source=[SourceCount(source="crossref", count=60)],
        by_year=[YearCount(year=2024, count=20)],
        top_journals=[JournalCount(journal_name="Nature", count=5)],
    )


class TestListArticles:
    """Test-plan §3 — GET /api/articles."""

    async def test_default_params_200(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated()
        resp = await client.get("/api/articles")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body

    async def test_pagination_params(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated(
            total=25, page=2, per_page=10, pages=3,
            items=[_make_article(id=i) for i in range(10)],
        )
        resp = await client.get("/api/articles?page=2&per_page=10")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["per_page"] == 10

    async def test_page_zero_returns_422(self, client, mock_repo):
        resp = await client.get("/api/articles?page=0")
        assert resp.status_code == 422

    async def test_per_page_101_returns_422(self, client, mock_repo):
        resp = await client.get("/api/articles?per_page=101")
        assert resp.status_code == 422

    async def test_invalid_sort_by_returns_422(self, client, mock_repo):
        resp = await client.get("/api/articles?sort_by=invalid")
        assert resp.status_code == 422

    async def test_all_filters_together_200(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated(items=[], total=0, pages=0)
        resp = await client.get(
            "/api/articles"
            "?search=test&journal_name=Nature&year=2024"
            "&quartile=Q1&source=crossref&article_type=Articles"
            "&date_from=2024-01-01&date_to=2024-12-31"
        )
        assert resp.status_code == 200


class TestGetArticle:
    """Test-plan §3 — GET /api/articles/{id}."""

    async def test_existing_article(self, client, mock_repo):
        from app.models.article import Article as ArticleModel
        from unittest.mock import MagicMock

        mock_article = MagicMock(spec=ArticleModel)
        for field, val in dict(
            id=1, num_id="cr_abc", title="Test", authors="A",
            doi="10.1/x", published_at=date(2024, 1, 1),
            journal_name="J", issn="1234-5678", type="Articles",
            quartile="Q1", publisher="P", cited_by_count=5,
            language="en", source="crossref", topics=["AI"], white_list_level=1,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
        ).items():
            setattr(mock_article, field, val)

        mock_repo.get_by_id.return_value = mock_article
        resp = await client.get("/api/articles/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    async def test_nonexistent_article_404(self, client, mock_repo):
        mock_repo.get_by_id.return_value = None
        resp = await client.get("/api/articles/999")
        assert resp.status_code == 404


class TestReferenceEndpoints:
    """Test-plan §3 — journals, types, authors, quartiles."""

    async def test_journals_200(self, client, mock_repo):
        mock_repo.get_journals.return_value = ["Nature", "Science"]
        resp = await client.get("/api/articles/journals")
        assert resp.status_code == 200
        assert resp.json() == ["Nature", "Science"]

    async def test_journals_search(self, client, mock_repo):
        mock_repo.get_journals.return_value = ["Nature"]
        resp = await client.get("/api/articles/journals?search=nat")
        assert resp.status_code == 200

    async def test_types_200(self, client, mock_repo):
        mock_repo.get_types.return_value = ["Articles", "Preprints"]
        resp = await client.get("/api/articles/types")
        assert resp.status_code == 200

    async def test_authors_200(self, client, mock_repo):
        mock_repo.get_authors.return_value = ["John Doe", "Jane Smith"]
        resp = await client.get("/api/articles/authors")
        assert resp.status_code == 200

    async def test_quartiles_200(self, client, mock_repo):
        mock_repo.get_quartiles.return_value = ["Q1", "Q2", "Q3", "Q4"]
        resp = await client.get("/api/articles/quartiles")
        assert resp.status_code == 200
        assert len(resp.json()) == 4


class TestStats:
    """Test-plan §3 — GET /api/articles/stats."""

    async def test_stats_200(self, client, mock_repo):
        mock_repo.get_stats.return_value = _make_stats()
        resp = await client.get("/api/articles/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 100
        assert "by_year" in body
        assert "top_journals" in body


class TestActionEndpoints:
    """Test-plan §3 — POST parse, update-quartiles, normalize-types."""

    async def test_parse_200(self, client, mock_repo):
        from unittest.mock import patch, AsyncMock
        with patch("app.routers.articles.run_parse", new_callable=AsyncMock):
            resp = await client.post("/api/articles/parse")
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_normalize_types_200(self, client, mock_repo):
        mock_repo.normalize_all_types.return_value = 5
        resp = await client.post("/api/articles/normalize-types")
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_backfill_topics_200(self, client, mock_repo):
        from unittest.mock import patch, AsyncMock
        with patch("app.services.topics.backfill_topics", new_callable=AsyncMock):
            resp = await client.post("/api/articles/backfill-topics")
        assert resp.status_code == 200
        assert "message" in resp.json()


class TestTopicsEndpoint:
    """Tests for GET /api/articles/topics."""

    async def test_topics_200(self, client, mock_repo):
        mock_repo.get_topics.return_value = ["AI", "Machine Learning", "NLP"]
        resp = await client.get("/api/articles/topics")
        assert resp.status_code == 200
        assert resp.json() == ["AI", "Machine Learning", "NLP"]

    async def test_topics_with_search(self, client, mock_repo):
        mock_repo.get_topics.return_value = ["Artificial Intelligence"]
        resp = await client.get("/api/articles/topics?search=artif")
        assert resp.status_code == 200

    async def test_topics_empty(self, client, mock_repo):
        mock_repo.get_topics.return_value = []
        resp = await client.get("/api/articles/topics")
        assert resp.status_code == 200
        assert resp.json() == []


class TestExportEndpoint:
    """Tests for GET /api/articles/export."""

    async def test_export_xlsx_200(self, client, mock_repo):
        from app.models.article import Article as ArticleModel
        from unittest.mock import MagicMock

        mock_article = MagicMock(spec=ArticleModel)
        for field, val in dict(
            id=1, num_id="cr_abc", title="Test", authors="A",
            doi="10.1/x", published_at=date(2024, 1, 1),
            journal_name="J", issn="1234-5678", type="Articles",
            quartile="Q1", publisher="P", cited_by_count=5,
            language="en", source="crossref", topics=["AI"], white_list_level=1,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
        ).items():
            setattr(mock_article, field, val)

        mock_repo.get_all_filtered.return_value = [mock_article]
        resp = await client.get("/api/articles/export?format=xlsx")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    async def test_export_csv_200(self, client, mock_repo):
        from app.models.article import Article as ArticleModel
        from unittest.mock import MagicMock

        mock_article = MagicMock(spec=ArticleModel)
        for field, val in dict(
            id=1, num_id="cr_abc", title="Test", authors="A",
            doi="10.1/x", published_at=date(2024, 1, 1),
            journal_name="J", issn="1234-5678", type="Articles",
            quartile="Q1", publisher="P", cited_by_count=5,
            language="en", source="crossref", topics=[], white_list_level=None,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
        ).items():
            setattr(mock_article, field, val)

        mock_repo.get_all_filtered.return_value = [mock_article]
        resp = await client.get("/api/articles/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    async def test_export_invalid_format_422(self, client, mock_repo):
        resp = await client.get("/api/articles/export?format=pdf")
        assert resp.status_code == 422

    async def test_export_with_topic_filter(self, client, mock_repo):
        mock_repo.get_all_filtered.return_value = []
        resp = await client.get("/api/articles/export?topic=AI")
        assert resp.status_code == 200


class TestListArticlesWithTopic:
    """Tests for topic filter in GET /api/articles."""

    async def test_topic_filter_200(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated(items=[], total=0, pages=0)
        resp = await client.get("/api/articles?topic=AI")
        assert resp.status_code == 200

    async def test_articles_include_topics_field(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated()
        resp = await client.get("/api/articles")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert "topics" in items[0]
        assert items[0]["topics"] == ["AI", "Machine Learning"]


class TestOpenAlexSearchWithInstitution:
    """Tests for institution parameter in GET /api/articles/openalex-search."""

    async def test_institution_param_200(self, client, mock_repo):
        from unittest.mock import patch, AsyncMock
        mock_result = {
            "total": 0, "page": 1, "per_page": 20, "pages": 0, "items": []
        }
        with patch("app.services.openalex.search_openalex", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.get("/api/articles/openalex-search?institution=MIT")
        assert resp.status_code == 200

    async def test_institution_with_search(self, client, mock_repo):
        from unittest.mock import patch, AsyncMock
        mock_result = {
            "total": 0, "page": 1, "per_page": 20, "pages": 0, "items": []
        }
        with patch("app.services.openalex.search_openalex", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.get("/api/articles/openalex-search?search=AI&institution=HSE")
        assert resp.status_code == 200


class TestWhiteListFilter:
    """Tests for white_list_only filter and update endpoint."""

    async def test_white_list_filter_200(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated(items=[], total=0, pages=0)
        resp = await client.get("/api/articles?white_list_only=true")
        assert resp.status_code == 200

    async def test_articles_include_white_list_level(self, client, mock_repo):
        mock_repo.get_filtered.return_value = _make_paginated()
        resp = await client.get("/api/articles")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert "white_list_level" in items[0]
        assert items[0]["white_list_level"] == 1

    async def test_update_white_list_200(self, client, mock_repo):
        from unittest.mock import patch, AsyncMock
        with patch("app.services.white_list.update_white_list_levels", new_callable=AsyncMock):
            resp = await client.post("/api/articles/update-white-list")
        assert resp.status_code == 200
        assert "message" in resp.json()
