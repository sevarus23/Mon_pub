"""Unit tests for Pydantic schemas in app.schemas.article."""

import pytest
from pydantic import ValidationError

from app.schemas.article import ArticleCreate, ArticleFilters, SortBy


class TestArticleFilters:
    """Test-plan §1.5 — ArticleFilters validation."""

    def test_defaults(self):
        f = ArticleFilters()
        assert f.page == 1
        assert f.per_page == 20
        assert f.sort_by == SortBy.published_at
        assert f.search is None

    def test_page_zero_rejected(self):
        with pytest.raises(ValidationError):
            ArticleFilters(page=0)

    def test_page_negative_rejected(self):
        with pytest.raises(ValidationError):
            ArticleFilters(page=-1)

    def test_per_page_101_rejected(self):
        with pytest.raises(ValidationError):
            ArticleFilters(per_page=101)

    def test_per_page_zero_rejected(self):
        with pytest.raises(ValidationError):
            ArticleFilters(per_page=0)

    def test_per_page_100_accepted(self):
        f = ArticleFilters(per_page=100)
        assert f.per_page == 100

    def test_per_page_1_accepted(self):
        f = ArticleFilters(per_page=1)
        assert f.per_page == 1


class TestArticleCreate:
    """Test-plan §1.5 — ArticleCreate required fields."""

    def test_valid_minimal(self):
        a = ArticleCreate(
            num_id="cr_abc123",
            title="Test Article",
            authors="John Doe",
            source="crossref",
        )
        assert a.num_id == "cr_abc123"
        assert a.doi is None

    def test_missing_num_id(self):
        with pytest.raises(ValidationError):
            ArticleCreate(title="Test", authors="X", source="crossref")

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            ArticleCreate(num_id="cr_1", authors="X", source="crossref")

    def test_missing_authors(self):
        with pytest.raises(ValidationError):
            ArticleCreate(num_id="cr_1", title="Test", source="crossref")

    def test_missing_source(self):
        with pytest.raises(ValidationError):
            ArticleCreate(num_id="cr_1", title="Test", authors="X")


class TestSortByEnum:
    """Test-plan §1.5 — SortBy enum validation."""

    def test_valid_values(self):
        assert SortBy("published_at") == SortBy.published_at
        assert SortBy("cited_by_count") == SortBy.cited_by_count

    def test_invalid_value_rejected(self):
        with pytest.raises(ValueError):
            SortBy("invalid_field")
