"""Unit tests for app.services.export — XLSX/CSV generation."""

import csv
import io
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.export import export_xlsx, export_csv, _cell_value, COLUMNS


def _mock_article(**overrides):
    defaults = dict(
        title="Test Article",
        authors="John Doe, Jane Smith",
        doi="10.1234/test",
        published_at=date(2024, 3, 15),
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
        core_rank=None,
        in_scopus=False,
    )
    defaults.update(overrides)
    article = MagicMock()
    for k, v in defaults.items():
        setattr(article, k, v)
    return article


class TestCellValue:
    def test_none_returns_empty(self):
        article = _mock_article(doi=None)
        assert _cell_value(article, "doi") == ""

    def test_date_returns_isoformat(self):
        article = _mock_article()
        assert _cell_value(article, "published_at") == "2024-03-15"

    def test_string_returned_as_is(self):
        article = _mock_article()
        assert _cell_value(article, "title") == "Test Article"

    def test_int_returned_as_is(self):
        article = _mock_article()
        assert _cell_value(article, "cited_by_count") == 10

    def test_list_joined_with_comma(self):
        article = _mock_article()
        assert _cell_value(article, "topics") == "AI, Machine Learning"

    def test_empty_list_returns_empty(self):
        article = _mock_article(topics=[])
        assert _cell_value(article, "topics") == ""


class TestExportXlsx:
    def test_returns_bytes_io(self):
        articles = [_mock_article()]
        result = export_xlsx(articles)
        assert isinstance(result, io.BytesIO)
        assert len(result.getvalue()) > 0

    def test_empty_list_produces_header_only(self):
        result = export_xlsx([])
        assert isinstance(result, io.BytesIO)
        assert len(result.getvalue()) > 0

    def test_multiple_articles(self):
        articles = [_mock_article(title=f"Article {i}") for i in range(5)]
        result = export_xlsx(articles)
        assert len(result.getvalue()) > 0


class TestExportCsv:
    def test_returns_string_io(self):
        articles = [_mock_article()]
        result = export_csv(articles)
        assert isinstance(result, io.StringIO)

    def test_csv_has_header_and_data(self):
        articles = [_mock_article()]
        result = export_csv(articles)
        reader = csv.reader(io.StringIO(result.getvalue()))
        rows = list(reader)
        assert len(rows) == 2  # header + 1 data row
        assert rows[0] == [c[0] for c in COLUMNS]

    def test_csv_data_values(self):
        articles = [_mock_article()]
        result = export_csv(articles)
        reader = csv.reader(io.StringIO(result.getvalue()))
        rows = list(reader)
        data = rows[1]
        assert data[0] == "Test Article"
        assert data[1] == "John Doe, Jane Smith"
        assert data[2] == "10.1234/test"

    def test_empty_list_produces_header_only(self):
        result = export_csv([])
        reader = csv.reader(io.StringIO(result.getvalue()))
        rows = list(reader)
        assert len(rows) == 1  # header only

    def test_topics_in_csv(self):
        articles = [_mock_article(topics=["AI", "NLP"])]
        result = export_csv(articles)
        content = result.getvalue()
        assert "AI, NLP" in content
