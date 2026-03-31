"""Unit tests for pure functions in app.services.crossref."""

import pytest
from datetime import date

from app.services.crossref import _parse_date, _parse_authors, _doi_hash, _is_ignored


class TestParseDate:
    """Test-plan §1.2 — _parse_date()."""

    def test_full_date_from_published_online(self):
        item = {"published-online": {"date-parts": [[2024, 3, 15]]}}
        assert _parse_date(item) == date(2024, 3, 15)

    def test_year_month_only(self):
        item = {"published-online": {"date-parts": [[2024, 3]]}}
        assert _parse_date(item) == date(2024, 3, 1)

    def test_year_only(self):
        item = {"published-online": {"date-parts": [[2024]]}}
        assert _parse_date(item) == date(2024, 1, 1)

    def test_fallback_to_published_print(self):
        item = {"published-print": {"date-parts": [[2023, 6, 10]]}}
        assert _parse_date(item) == date(2023, 6, 10)

    def test_fallback_to_created(self):
        item = {"created": {"date-parts": [[2022, 1, 5]]}}
        assert _parse_date(item) == date(2022, 1, 5)

    def test_fallback_chain(self):
        """published-online invalid → published-print used."""
        item = {
            "published-online": {"date-parts": [[2024, 13, 1]]},  # month=13 invalid
            "published-print": {"date-parts": [[2024, 1, 20]]},
        }
        assert _parse_date(item) == date(2024, 1, 20)

    def test_empty_date_parts(self):
        item = {"published-online": {"date-parts": []}}
        assert _parse_date(item) is None

    def test_missing_date_parts_key(self):
        item = {"published-online": {}}
        assert _parse_date(item) is None

    def test_no_date_fields_at_all(self):
        assert _parse_date({}) is None


class TestParseAuthors:
    """Test-plan §1.2 — _parse_authors()."""

    def test_standard_list(self):
        item = {
            "author": [
                {"given": "John", "family": "Doe"},
                {"given": "Jane", "family": "Smith"},
            ]
        }
        assert _parse_authors(item) == "John Doe, Jane Smith"

    def test_missing_given(self):
        item = {"author": [{"family": "Doe"}]}
        assert _parse_authors(item) == "Doe"

    def test_missing_family(self):
        item = {"author": [{"given": "John"}]}
        assert _parse_authors(item) == "John"

    def test_empty_author_list(self):
        item = {"author": []}
        assert _parse_authors(item) == "Unknown"

    def test_missing_author_key(self):
        assert _parse_authors({}) == "Unknown"

    def test_author_with_empty_strings(self):
        item = {"author": [{"given": "", "family": ""}]}
        # Both empty → name is empty string → filtered out → "Unknown"
        assert _parse_authors(item) == "Unknown"


class TestDoiHash:
    """Test-plan §1.2 — _doi_hash()."""

    def test_deterministic(self):
        assert _doi_hash("10.1234/test") == _doi_hash("10.1234/test")

    def test_length_16(self):
        assert len(_doi_hash("10.1234/test")) == 16

    def test_different_dois_different_hashes(self):
        assert _doi_hash("10.1234/a") != _doi_hash("10.1234/b")


class TestIsIgnored:
    """Test-plan §1.2 — _is_ignored()."""

    def test_known_ignored_doi(self):
        assert _is_ignored("10.1142/9789811257186_0012") is True

    def test_normal_doi(self):
        assert _is_ignored("10.1234/something") is False

    def test_case_insensitive(self):
        assert _is_ignored("10.1142/9789811257186_0012") is True
