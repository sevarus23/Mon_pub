"""Unit tests for SJR CSV parsing logic in app.services.sjr."""

import csv
import pytest
from pathlib import Path

from app.services.sjr import _parse_sjr_csv


@pytest.fixture
def sjr_csv(tmp_path: Path) -> Path:
    """Create a minimal SJR CSV file for testing."""
    filepath = tmp_path / "sjr_test.csv"
    rows = [
        {"Issn": "14726483, 09628924", "SJR Best Quartile": "Q1"},
        {"Issn": "12345678", "SJR Best Quartile": "Q2"},
        {"Issn": "1111-2222", "SJR Best Quartile": "Q3"},
        {"Issn": "99998888", "SJR Best Quartile": "Q5"},  # invalid quartile
        {"Issn": "77776666", "SJR Best Quartile": ""},     # empty quartile
        {"Issn": "55554444", "SJR Best Quartile": "Q4"},
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Issn", "SJR Best Quartile"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return filepath


class TestParseSjrCsv:
    """Test-plan §1.4 — SJR CSV parsing."""

    def test_issn_8chars_gets_dash(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        assert "1472-6483" in result
        assert result["1472-6483"] == "Q1"

    def test_multiple_issns_per_row(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        assert "1472-6483" in result
        assert "0962-8924" in result
        assert result["0962-8924"] == "Q1"

    def test_invalid_quartile_skipped(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        # Q5 and empty should not be in the result
        assert "9999-8888" not in result
        assert "7777-6666" not in result

    def test_only_q1_to_q4_accepted(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        for v in result.values():
            assert v in ("Q1", "Q2", "Q3", "Q4")

    def test_semicolon_delimiter(self, sjr_csv):
        """Verifies the CSV was parsed correctly (semicolon-separated)."""
        result = _parse_sjr_csv(sjr_csv)
        assert len(result) >= 4  # at least the valid entries

    def test_already_formatted_issn(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        assert "1111-2222" in result
        assert result["1111-2222"] == "Q3"

    def test_single_8char_issn(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        assert "1234-5678" in result
        assert result["1234-5678"] == "Q2"
