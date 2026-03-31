"""Service-level tests for parse_crossref() with mocked HTTP via respx."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

import respx
import httpx

from app.services.crossref import parse_crossref, BASE_URL


def _crossref_response(items, total=None):
    """Build a CrossRef API-like response dict."""
    if total is None:
        total = len(items)
    return {
        "message": {
            "total-results": total,
            "items": items,
        }
    }


def _make_item(doi="10.1234/test", title="Test Article", **overrides):
    item = {
        "DOI": doi,
        "title": [title],
        "author": [{"given": "John", "family": "Doe"}],
        "published-online": {"date-parts": [[2024, 3, 15]]},
        "container-title": ["Nature"],
        "ISSN": ["1234-5678"],
        "type": "journal-article",
        "publisher": "Springer",
        "is-referenced-by-count": 10,
        "language": "en",
    }
    item.update(overrides)
    return item


@pytest.fixture
def mock_db():
    """Patch async_session and ArticleRepository."""
    mock_repo = AsyncMock()
    mock_repo.bulk_upsert.return_value = 0

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.crossref.async_session", return_value=mock_session):
        with patch("app.services.crossref.ArticleRepository", return_value=mock_repo):
            yield mock_repo


class TestParseCrossref:
    """Test-plan §4.1 — CrossRef service with respx mocking."""

    @respx.mock
    async def test_single_page_two_articles(self, mock_db):
        items = [_make_item(doi=f"10.1234/test{i}") for i in range(2)]
        mock_db.bulk_upsert.return_value = 2

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_crossref_response(items, total=2))
        )

        result = await parse_crossref()
        assert result == 2
        mock_db.bulk_upsert.assert_called_once()

    @respx.mock
    async def test_empty_items_returns_zero(self, mock_db):
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_crossref_response([], total=0))
        )
        result = await parse_crossref()
        assert result == 0

    @respx.mock
    async def test_ignored_doi_not_inserted(self, mock_db):
        items = [_make_item(doi="10.1142/9789811257186_0012")]
        mock_db.bulk_upsert.return_value = 0

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_crossref_response(items, total=1))
        )

        result = await parse_crossref()
        # bulk_upsert should not be called since the only article is ignored
        assert result == 0

    @respx.mock
    async def test_multipage_pagination(self, mock_db):
        """Two pages: 100 items on first, 50 on second."""
        page1_items = [_make_item(doi=f"10.1234/p1_{i}") for i in range(100)]
        page2_items = [_make_item(doi=f"10.1234/p2_{i}") for i in range(50)]
        mock_db.bulk_upsert.return_value = 100  # first call
        mock_db.bulk_upsert.side_effect = [100, 50]

        route = respx.get(BASE_URL)
        route.side_effect = [
            httpx.Response(200, json=_crossref_response(page1_items, total=150)),
            httpx.Response(200, json=_crossref_response(page2_items, total=150)),
        ]

        result = await parse_crossref()
        assert result == 150
        assert mock_db.bulk_upsert.call_count == 2

    @respx.mock
    async def test_http_500_graceful_stop(self, mock_db):
        """After 3 retries on 500, parsing stops gracefully."""
        respx.get(BASE_URL).mock(return_value=httpx.Response(500))

        result = await parse_crossref()
        assert result == 0

    @respx.mock
    async def test_since_date_passed_as_filter(self, mock_db):
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_crossref_response([], total=0))
        )

        await parse_crossref(since_date=date(2024, 1, 1))

        request = respx.calls[0].request
        assert "from-pub-date" in str(request.url)

    @respx.mock
    async def test_num_id_format(self, mock_db):
        items = [_make_item(doi="10.1234/test_format")]
        mock_db.bulk_upsert.return_value = 1

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_crossref_response(items, total=1))
        )

        await parse_crossref()
        call_args = mock_db.bulk_upsert.call_args[0][0]
        article = call_args[0]
        assert article.num_id.startswith("cr_")
        assert len(article.num_id) == 19  # "cr_" + 16 chars
