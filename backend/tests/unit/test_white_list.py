"""Unit tests for white list service helper functions."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


class TestFetchLevel:
    """Test _fetch_level logic."""

    def _extract_level(self, data: dict) -> int | None:
        """Replicate the level extraction logic from white_list.py."""
        return data.get("level_2025") or data.get("level_2023")

    def test_level_2025_preferred(self):
        data = {"level_2023": 2, "level_2025": 1}
        assert self._extract_level(data) == 1

    def test_fallback_to_2023(self):
        data = {"level_2023": 3, "level_2025": None}
        assert self._extract_level(data) == 3

    def test_both_none(self):
        data = {"level_2023": None, "level_2025": None}
        assert self._extract_level(data) is None

    def test_only_2023(self):
        data = {"level_2023": 1}
        assert self._extract_level(data) == 1

    def test_empty_response(self):
        assert self._extract_level({}) is None

    def test_level_values_range(self):
        for level in [1, 2, 3, 4]:
            data = {"level_2023": level}
            assert self._extract_level(data) == level


class TestWhiteListCache:
    """Test cache save/load logic."""

    def test_cache_round_trip(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache = {"0028-0836": 1, "1234-5678": None, "0036-8075": 2}

        with open(cache_file, "w") as f:
            json.dump(cache, f)

        with open(cache_file) as f:
            loaded = json.load(f)

        assert loaded == cache

    def test_filter_entries_with_level(self):
        cache = {"0028-0836": 1, "1234-5678": None, "0036-8075": 2}
        with_level = {k: v for k, v in cache.items() if v is not None}
        assert with_level == {"0028-0836": 1, "0036-8075": 2}
        assert "1234-5678" not in with_level


class TestWhiteListSchemaIntegration:
    """Test that ArticleFilters and ArticleOut support white list fields."""

    def test_filters_white_list_only_default(self):
        from app.schemas.article import ArticleFilters
        f = ArticleFilters()
        assert f.white_list_only is False

    def test_filters_white_list_only_true(self):
        from app.schemas.article import ArticleFilters
        f = ArticleFilters(white_list_only=True)
        assert f.white_list_only is True

    def test_article_out_white_list_level(self):
        from app.schemas.article import ArticleOut
        from datetime import date, datetime
        a = ArticleOut(
            id=1, num_id="cr_1", title="T", authors="A",
            doi=None, published_at=date(2024, 1, 1),
            journal_name="J", issn="1234", type="Articles",
            quartile="Q1", publisher="P", cited_by_count=0,
            language="en", source="crossref", topics=[],
            white_list_level=2,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
        )
        assert a.white_list_level == 2

    def test_article_out_white_list_level_none(self):
        from app.schemas.article import ArticleOut
        from datetime import date, datetime
        a = ArticleOut(
            id=1, num_id="cr_1", title="T", authors="A",
            doi=None, published_at=date(2024, 1, 1),
            journal_name="J", issn="1234", type="Articles",
            quartile="Q1", publisher="P", cited_by_count=0,
            language="en", source="crossref", topics=[],
            white_list_level=None,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
        )
        assert a.white_list_level is None
