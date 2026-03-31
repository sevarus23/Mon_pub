"""Service-level tests for run_parse() scheduler logic."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch


class TestRunParse:
    """Test-plan §4.3 — Scheduler run_parse()."""

    async def test_since_date_is_last_minus_7_days(self):
        last_date = date(2024, 3, 15)
        expected_since = date(2024, 3, 8)

        mock_repo = AsyncMock()
        mock_repo.get_last_published_date.return_value = last_date
        mock_repo.normalize_all_types.return_value = 0

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.scheduler.async_session", return_value=mock_session), \
             patch("app.services.scheduler.ArticleRepository", return_value=mock_repo), \
             patch("app.services.scheduler.parse_crossref", new_callable=AsyncMock, return_value=0) as mock_cr, \
             patch("app.services.scheduler.parse_openalex", new_callable=AsyncMock, return_value=0) as mock_oa, \
             patch("app.services.scheduler.update_quartiles_from_csv", new_callable=AsyncMock, return_value=0):
            from app.services.scheduler import run_parse
            await run_parse()

            mock_cr.assert_called_once_with(expected_since)
            mock_oa.assert_called_once_with(expected_since)

    async def test_last_date_none_since_date_none(self):
        mock_repo = AsyncMock()
        mock_repo.get_last_published_date.return_value = None
        mock_repo.normalize_all_types.return_value = 0

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.scheduler.async_session", return_value=mock_session), \
             patch("app.services.scheduler.ArticleRepository", return_value=mock_repo), \
             patch("app.services.scheduler.parse_crossref", new_callable=AsyncMock, return_value=0) as mock_cr, \
             patch("app.services.scheduler.parse_openalex", new_callable=AsyncMock, return_value=0) as mock_oa, \
             patch("app.services.scheduler.update_quartiles_from_csv", new_callable=AsyncMock, return_value=0):
            from app.services.scheduler import run_parse
            await run_parse()

            mock_cr.assert_called_once_with(None)
            mock_oa.assert_called_once_with(None)

    async def test_sequence_parse_then_quartiles_then_types(self):
        """Verify call order: parse → quartiles → normalize_types."""
        call_order = []

        mock_repo = AsyncMock()
        mock_repo.get_last_published_date.return_value = None
        mock_repo.normalize_all_types.side_effect = lambda: call_order.append("types") or 0

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        async def mock_cr(since):
            call_order.append("crossref")
            return 0

        async def mock_oa(since):
            call_order.append("openalex")
            return 0

        async def mock_q():
            call_order.append("quartiles")
            return 0

        with patch("app.services.scheduler.async_session", return_value=mock_session), \
             patch("app.services.scheduler.ArticleRepository", return_value=mock_repo), \
             patch("app.services.scheduler.parse_crossref", side_effect=mock_cr), \
             patch("app.services.scheduler.parse_openalex", side_effect=mock_oa), \
             patch("app.services.scheduler.update_quartiles_from_csv", side_effect=mock_q):
            from app.services.scheduler import run_parse
            await run_parse()

        # crossref and openalex run in parallel via gather, so both before quartiles
        assert "quartiles" in call_order
        assert "types" in call_order
        quartile_idx = call_order.index("quartiles")
        types_idx = call_order.index("types")
        assert quartile_idx < types_idx
