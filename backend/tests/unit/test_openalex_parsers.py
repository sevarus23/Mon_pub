"""Unit tests for pure functions in app.services.openalex."""

import pytest
from datetime import date

from app.services.openalex import (
    _has_innopolis_affiliation,
    _parse_authors,
    _parse_date,
    _extract_openalex_id,
)


class TestHasInnopolisAffiliation:
    """Test-plan §1.3 — _has_innopolis_affiliation()."""

    def test_match_in_raw_affiliation(self):
        authorships = [
            {"raw_affiliation_strings": ["Innopolis University, Russia"]}
        ]
        assert _has_innopolis_affiliation(authorships) is True

    def test_case_insensitive(self):
        authorships = [
            {"raw_affiliation_strings": ["INNOPOLIS UNIVERSITY"]}
        ]
        assert _has_innopolis_affiliation(authorships) is True

    def test_no_match(self):
        authorships = [
            {"raw_affiliation_strings": ["MIT, USA"]}
        ]
        assert _has_innopolis_affiliation(authorships) is False

    def test_empty_list(self):
        assert _has_innopolis_affiliation([]) is False

    def test_missing_raw_affiliation_key(self):
        authorships = [{"author": {"display_name": "Test"}}]
        assert _has_innopolis_affiliation(authorships) is False

    def test_multiple_authors_one_match(self):
        authorships = [
            {"raw_affiliation_strings": ["MIT, USA"]},
            {"raw_affiliation_strings": ["Innopolis University"]},
        ]
        assert _has_innopolis_affiliation(authorships) is True


class TestParseDate:
    """Test-plan §1.3 — _parse_date()."""

    def test_valid_iso_date(self):
        assert _parse_date("2024-03-15") == date(2024, 3, 15)

    def test_none(self):
        assert _parse_date(None) is None

    def test_invalid_string(self):
        assert _parse_date("not-a-date") is None

    def test_empty_string(self):
        assert _parse_date("") is None


class TestParseAuthors:
    """Test-plan §1.3 — _parse_authors()."""

    def test_standard_list(self):
        authorships = [
            {"author": {"display_name": "Alice Smith"}},
            {"author": {"display_name": "Bob Jones"}},
        ]
        assert _parse_authors(authorships) == "Alice Smith, Bob Jones"

    def test_empty_list(self):
        assert _parse_authors([]) == "Unknown"

    def test_missing_display_name(self):
        authorships = [{"author": {}}]
        assert _parse_authors(authorships) == "Unknown"


class TestExtractOpenalexId:
    """Test-plan §1.3 — _extract_openalex_id()."""

    def test_url_to_id(self):
        assert _extract_openalex_id("https://openalex.org/W12345") == "W12345"

    def test_empty_string(self):
        assert _extract_openalex_id("") == ""

    def test_id_without_url(self):
        assert _extract_openalex_id("W99999") == "W99999"
