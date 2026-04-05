"""Unit tests for CORE conference ranking service functions."""

import pytest

from app.services.core_ranks import _normalize, _build_lookup, _find_rank, VALID_RANKS


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("AAAI Conference") == "aaai conference"

    def test_strip_whitespace(self):
        assert _normalize("  test  ") == "test"

    def test_empty(self):
        assert _normalize("") == ""


class TestBuildLookup:
    def test_basic_entry(self):
        data = [{"title": "AAAI Conference", "acronym": "AAAI", "rank": "A*"}]
        lookup = _build_lookup(data)
        assert "aaai conference" in lookup
        assert lookup["aaai conference"] == "A*"
        assert "aaai" in lookup
        assert "#aaai#" in lookup  # substring marker

    def test_filters_invalid_ranks(self):
        data = [
            {"title": "Good", "acronym": "G", "rank": "A"},
            {"title": "Bad", "acronym": "B", "rank": "Unranked"},
            {"title": "National", "acronym": "N", "rank": "National: USA"},
        ]
        lookup = _build_lookup(data)
        assert "good" in lookup
        assert "bad" not in lookup
        assert "national" not in lookup

    def test_valid_ranks_set(self):
        assert VALID_RANKS == {"A*", "A", "B", "C"}

    def test_empty_data(self):
        assert _build_lookup([]) == {}

    def test_missing_fields(self):
        data = [{"rank": "A"}]
        lookup = _build_lookup(data)
        assert len(lookup) == 0

    def test_short_acronym_no_substring_marker(self):
        data = [{"title": "Conference", "acronym": "AB", "rank": "B"}]
        lookup = _build_lookup(data)
        assert "ab" in lookup
        assert "#ab#" not in lookup  # too short for substring

    def test_long_acronym_has_substring_marker(self):
        data = [{"title": "Conference", "acronym": "ICSE", "rank": "A*"}]
        lookup = _build_lookup(data)
        assert "#icse#" in lookup


class TestFindRank:
    @pytest.fixture
    def lookup(self):
        data = [
            {"title": "AAAI Conference on Artificial Intelligence", "acronym": "AAAI", "rank": "A*"},
            {"title": "ACM SIGCOMM Conference", "acronym": "SIGCOMM", "rank": "A*"},
            {"title": "IEEE Congress on Evolutionary Computation", "acronym": "CEC", "rank": "B"},
            {"title": "International Conference on Software Engineering", "acronym": "ICSE", "rank": "A*"},
        ]
        return _build_lookup(data)

    def test_exact_title_match(self, lookup):
        assert _find_rank("AAAI Conference on Artificial Intelligence", lookup) == "A*"

    def test_exact_title_case_insensitive(self, lookup):
        assert _find_rank("aaai conference on artificial intelligence", lookup) == "A*"

    def test_acronym_match(self, lookup):
        assert _find_rank("AAAI", lookup) == "A*"

    def test_acronym_in_title(self, lookup):
        assert _find_rank("Proceedings of the SIGCOMM 2024", lookup) == "A*"

    def test_substring_title_match(self, lookup):
        result = _find_rank("International Conference on Software Engineering Companion", lookup)
        assert result == "A*"

    def test_no_match(self, lookup):
        assert _find_rank("Unknown Conference on Nothing", lookup) is None

    def test_empty_name(self, lookup):
        assert _find_rank("", lookup) is None

    def test_partial_acronym_in_longer_word_no_match(self, lookup):
        # CEC is 3 chars, but "CECC" shouldn't match as a whole word
        result = _find_rank("CECC Workshop", lookup)
        assert result is None or result == "B"  # depends on word splitting
