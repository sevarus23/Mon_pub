"""Unit tests for app.utils.type_mapping — normalize_type()."""

import pytest

from app.utils.type_mapping import TYPE_MAPPING, normalize_type

VALID_CATEGORIES = {
    "Articles",
    "Books & Monographs",
    "Conference materials",
    "Journal Issues & Contributions to periodicals",
    "Datasets",
    "Preprints",
    "Peer review materials",
    "Other",
}


class TestNormalizeType:
    """Test-plan §1.1 — type normalization."""

    def test_known_crossref_type(self):
        assert normalize_type("journal-article") == "Articles"

    def test_known_openalex_type(self):
        assert normalize_type("proceedings-article") == "Conference materials"

    def test_unknown_type_returns_other(self):
        assert normalize_type("grant") == "Other"

    def test_none_returns_none(self):
        assert normalize_type(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_type("") is None

    def test_all_mapping_entries_produce_valid_category(self):
        """Every value in TYPE_MAPPING must be one of the 8 known categories."""
        for raw, normalized in TYPE_MAPPING.items():
            assert normalized in VALID_CATEGORIES, (
                f"TYPE_MAPPING[{raw!r}] = {normalized!r} is not a valid category"
            )

    def test_mapping_has_26_entries(self):
        assert len(TYPE_MAPPING) == 26

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Article", "Articles"),
            ("article", "Articles"),
            ("article-journal", "Articles"),
            ("journal-article", "Articles"),
            ("Journal articles", "Articles"),
            ("book", "Books & Monographs"),
            ("book-chapter", "Books & Monographs"),
            ("monograph", "Books & Monographs"),
            ("Conference or Workshop Item", "Conference materials"),
            ("Conference papers", "Conference materials"),
            ("proceedings-article", "Conference materials"),
            ("dataset", "Datasets"),
            ("Dataset", "Datasets"),
            ("preprint", "Preprints"),
            ("workingPaper", "Preprints"),
            ("peer-review", "Peer review materials"),
            ("posted-content", "Peer review materials"),
            ("text", "Other"),
            ("other", "Other"),
        ],
    )
    def test_specific_mappings(self, raw, expected):
        assert normalize_type(raw) == expected
