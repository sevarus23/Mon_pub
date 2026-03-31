"""Service-level tests for parse_openalex() with mocked HTTP via respx."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

import respx
import httpx

from app.services.openalex import parse_openalex, BASE_URL, INNOPOLIS_ROR


def _openalex_response(results, next_cursor=None, count=None):
    return {
        "results": results,
        "meta": {
            "next_cursor": next_cursor,
            "count": count or len(results),
        },
    }


def _make_work(
    openalex_id="W12345",
    doi="https://doi.org/10.1234/test",
    title="Test Article",
    pub_date="2024-03-15",
    has_innopolis=True,
    **overrides,
):
    raw_aff = ["Innopolis University, Russia"] if has_innopolis else ["MIT, USA"]
    work = {
        "id": f"https://openalex.org/{openalex_id}",
        "doi": doi,
        "title": title,
        "publication_date": pub_date,
        "authorships": [
            {
                "author": {"display_name": "Alice Smith"},
                "raw_affiliation_strings": raw_aff,
            }
        ],
        "primary_location": {
            "source": {
                "display_name": "Nature",
                "issn_l": "1234-5678",
                "host_organization_name": "Springer",
            },
            "raw_type": "journal-article",
        },
        "cited_by_count": 5,
        "language": "en",
    }
    work.update(overrides)
    return work


@pytest.fixture
def mock_db():
    mock_repo = AsyncMock()
    mock_repo.bulk_upsert.return_value = 0

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.openalex.async_session", return_value=mock_session):
        with patch("app.services.openalex.ArticleRepository", return_value=mock_repo):
            yield mock_repo


class TestParseOpenalex:
    """Test-plan §4.2 — OpenAlex service with respx mocking."""

    @respx.mock
    async def test_cursor_pagination(self, mock_db):
        """Two pages via cursor."""
        mock_db.bulk_upsert.side_effect = [1, 1]

        route = respx.get(BASE_URL)
        route.side_effect = [
            httpx.Response(200, json=_openalex_response(
                [_make_work(openalex_id="W1")], next_cursor="abc123", count=2,
            )),
            httpx.Response(200, json=_openalex_response(
                [_make_work(openalex_id="W2", doi="https://doi.org/10.1234/test2")],
                next_cursor=None, count=2,
            )),
        ]

        result = await parse_openalex()
        assert result == 2

    @respx.mock
    async def test_no_innopolis_affiliation_skipped(self, mock_db):
        works = [_make_work(has_innopolis=False)]

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response(works))
        )

        result = await parse_openalex()
        assert result == 0

    @respx.mock
    async def test_year_before_2012_skipped(self, mock_db):
        works = [_make_work(pub_date="2011-06-15")]

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response(works))
        )

        result = await parse_openalex()
        assert result == 0

    @respx.mock
    async def test_doi_url_cleaned(self, mock_db):
        works = [_make_work(doi="https://doi.org/10.1234/cleaned")]
        mock_db.bulk_upsert.return_value = 1

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response(works))
        )

        await parse_openalex()
        call_args = mock_db.bulk_upsert.call_args[0][0]
        assert call_args[0].doi == "10.1234/cleaned"

    @respx.mock
    async def test_num_id_format(self, mock_db):
        works = [_make_work(openalex_id="W99999")]
        mock_db.bulk_upsert.return_value = 1

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response(works))
        )

        await parse_openalex()
        call_args = mock_db.bulk_upsert.call_args[0][0]
        assert call_args[0].num_id == "oa_W99999"

    @respx.mock
    async def test_issn_fallback(self, mock_db):
        """When issn_l is missing, falls back to issn[0]."""
        work = _make_work()
        work["primary_location"]["source"]["issn_l"] = None
        work["primary_location"]["source"]["issn"] = ["9999-0000"]
        mock_db.bulk_upsert.return_value = 1

        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response([work]))
        )

        await parse_openalex()
        call_args = mock_db.bulk_upsert.call_args[0][0]
        assert call_args[0].issn == "9999-0000"

    @respx.mock
    async def test_ror_in_request(self, mock_db):
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=_openalex_response([]))
        )

        await parse_openalex()
        request = respx.calls[0].request
        # URL is percent-encoded, so check the decoded version
        from urllib.parse import unquote
        assert INNOPOLIS_ROR in unquote(str(request.url))
