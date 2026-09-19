"""Unit tests for SJR CSV parsing logic in app.services.sjr."""

import csv
import hashlib
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sjr import DATA_DIR, SJR_FILENAME, SJR_YEAR, _parse_sjr_csv, update_quartiles_from_csv


@pytest.fixture
def sjr_csv(tmp_path: Path) -> Path:
    """Create a minimal SJR CSV file for testing."""
    filepath = tmp_path / "sjr_test.csv"
    rows = [
        {"Issn": "14726483, 09628924", "SJR Best Quartile": "Q1"},
        {"Issn": "12345678", "SJR Best Quartile": "Q2"},
        {"Issn": "1111-2222", "SJR Best Quartile": "Q3"},
        {"Issn": "77776666", "SJR Best Quartile": "-"},
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

    def test_unranked_is_distinct_from_absent(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        assert "9999-8888" not in result
        assert "7777-6666" in result
        assert result["7777-6666"] is None

    def test_only_q1_to_q4_accepted(self, sjr_csv):
        result = _parse_sjr_csv(sjr_csv)
        for v in result.values():
            assert v in (None, "Q1", "Q2", "Q3", "Q4")

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


async def test_quartile_update_corrects_existing_values(sjr_csv):
    session = AsyncMock()
    records = MagicMock()
    records.all.return_value = [
        ("1472-6483", "Q4"), ("09628924", None),
        ("1234-5678", "Q2"), ("7777-6666", "Q3"),
    ]
    session.execute.side_effect = [records, MagicMock(rowcount=1), MagicMock(rowcount=1)]
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    with patch("app.services.sjr.async_session", return_value=context):
        changed = await update_quartiles_from_csv(sjr_csv)
    assert changed == 2
    statements = [call.args[0].compile() for call in session.execute.await_args_list[1:]]
    assert statements[0].params == {"quartile": "Q1", "issn_1": "1472-6483", "quartile_1": "Q4"}
    assert statements[1].params == {"quartile": "Q1", "issn_1": "09628924"}
    assert "quartile IS NULL" in str(statements[1])
    session.commit.assert_awaited_once()


@pytest.mark.parametrize("content", [
    "<html>Cloudflare</html>",
    "Issn,SJR Best Quartile\n14726483,Q1\n",
    "Issn;SJR Best Quartile\n14726483\n",
    "Issn;SJR Best Quartile\n14726483;Q1;extra\n",
    "Issn;SJR Best Quartile\n14726483;Q5\n",
    "Issn;SJR Best Quartile\n14726483;\n",
    "Issn;SJR Best Quartile\nnot-an-issn;Q1\n",
    "Issn;SJR Best Quartile\n14726483;Q1\n1472-6483;Q2\n",
    "Issn;SJR Best Quartile\n14726483;Q1\n1472-6483;-\n",
    "Issn;SJR Best Quartile\n",
])
def test_malformed_snapshot_fails_closed(tmp_path, content):
    filepath = tmp_path / "invalid.csv"
    filepath.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        _parse_sjr_csv(filepath)


def test_identical_duplicate_and_missing_issn(tmp_path):
    filepath = tmp_path / "valid.csv"
    filepath.write_text(
        "\ufeffIssn;SJR Best Quartile\n14726483;Q1\n1472-6483;Q1\n-;Q2\n;Q2\n",
        encoding="utf-8",
    )
    assert _parse_sjr_csv(filepath) == {"1472-6483": "Q1"}


def test_ambiguous_legacy_issns_excluded_even_after_third_occurrence(tmp_path):
    filepath = tmp_path / "legacy.csv"
    filepath.write_text(
        "Issn;SJR Best Quartile\n14726483;Q1\n77776666;Q1\n77776666;Q2\n77776666;Q1\n",
        encoding="utf-8",
    )
    assert _parse_sjr_csv(filepath, exclude_ambiguous=True) == {"1472-6483": "Q1"}


def test_bundled_2025_snapshot():
    assert SJR_FILENAME == "scimagojr_2025.csv"
    assert SJR_YEAR == 2025
    filepath = DATA_DIR / SJR_FILENAME
    metadata = json.loads((DATA_DIR / "source_metadata.json").read_text(encoding="utf-8"))["sjr"]
    assert metadata["filename"] == SJR_FILENAME
    assert str(SJR_YEAR) in metadata["version"]
    assert hashlib.sha256(filepath.read_bytes()).hexdigest() == metadata["data_sha256"]
    with filepath.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter=";"))
    assert len(rows) == 32193
    result = _parse_sjr_csv(filepath, expected_year=2025)
    assert result["0007-9235"] == "Q1"
    assert "-" not in result
    assert None in result.values()


async def test_legacy_cleanup_only_removes_matching_known_values(tmp_path):
    current = tmp_path / "current.csv"
    current.write_text(
        "Issn;SJR Best Quartile\n14726483;Q1\n77776666;-\n", encoding="utf-8",
    )
    baseline = tmp_path / "legacy.csv"
    baseline.write_text(
        "Issn;SJR Best Quartile\n14726483;Q2\n77776666;Q3\n55554444;Q4\n",
        encoding="utf-8",
    )
    records = MagicMock()
    records.all.return_value = [
        ("1472-6483", "Q2"),   # current rank supersedes old rank
        ("7777-6666", "Q3"),   # explicit unranked, matches legacy: clear
        ("7777-6666", "Q1"),   # differing / manual-like: preserve
        ("5555-4444", "Q4"),   # absent now, matches legacy: clear
        ("5555-4444", "Q2"),   # absent now but differs: preserve
        ("1234-5678", "Q1"),   # unknown to both editions: preserve
        ("7777-6666", None),   # already empty: no action
    ]
    session = AsyncMock()
    session.execute.side_effect = [records] + [MagicMock(rowcount=1) for _ in range(3)]
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    with patch("app.services.sjr.async_session", return_value=context):
        assert await update_quartiles_from_csv(current, baseline_filepath=baseline) == 3
    params = [call.args[0].compile().params for call in session.execute.await_args_list[1:]]
    assert params == [
        {"quartile": "Q1", "issn_1": "1472-6483", "quartile_1": "Q2"},
        {"quartile": None, "issn_1": "7777-6666", "quartile_1": "Q3"},
        {"quartile": None, "issn_1": "5555-4444", "quartile_1": "Q4"},
    ]
    session.commit.assert_awaited_once()


def test_wrong_edition_is_rejected(sjr_csv):
    with pytest.raises(ValueError, match="unexpected edition"):
        _parse_sjr_csv(sjr_csv, expected_year=2025)


async def test_invalid_snapshot_never_opens_database(tmp_path):
    filepath = tmp_path / "invalid.csv"
    filepath.write_text("Cloudflare challenge", encoding="utf-8")
    with patch("app.services.sjr.async_session") as session_factory:
        with pytest.raises(ValueError):
            await update_quartiles_from_csv(filepath)
    session_factory.assert_not_called()


async def test_default_does_not_fall_back_to_2024(tmp_path):
    (tmp_path / "scimagojr_2024.csv").write_text(
        "Issn;SJR Best Quartile\n14726483;Q1\n", encoding="utf-8",
    )
    with patch("app.services.sjr.DATA_DIR", tmp_path), patch(
        "app.services.sjr.async_session",
    ) as session_factory:
        assert await update_quartiles_from_csv() == 0
    session_factory.assert_not_called()


async def test_default_requires_expected_edition_before_database(tmp_path):
    (tmp_path / SJR_FILENAME).write_text(
        "Issn;SJR Best Quartile;Total Docs. (2024)\n14726483;Q1;1\n", encoding="utf-8",
    )
    with patch("app.services.sjr.DATA_DIR", tmp_path), patch(
        "app.services.sjr.async_session",
    ) as session_factory:
        with pytest.raises(ValueError, match="unexpected edition"):
            await update_quartiles_from_csv()
    session_factory.assert_not_called()


async def test_default_rejects_truncated_snapshot_before_database(tmp_path):
    (tmp_path / SJR_FILENAME).write_text(
        "Issn;SJR Best Quartile;Total Docs. (2025)\n14726483;Q1;1\n", encoding="utf-8",
    )
    with patch("app.services.sjr.DATA_DIR", tmp_path), patch(
        "app.services.sjr.async_session",
    ) as session_factory:
        with pytest.raises(ValueError, match="unexpectedly small"):
            await update_quartiles_from_csv()
    session_factory.assert_not_called()


@pytest.mark.parametrize("manifest", [None, {"sjr": {"filename": SJR_FILENAME, "data_sha256": "wrong"}}])
async def test_bundled_missing_or_mismatched_checksum_never_opens_database(tmp_path, manifest):
    (tmp_path / SJR_FILENAME).write_bytes((DATA_DIR / SJR_FILENAME).read_bytes())
    if manifest is not None:
        (tmp_path / "source_metadata.json").write_text(json.dumps(manifest), encoding="utf-8")
    with patch("app.services.sjr.DATA_DIR", tmp_path), patch(
        "app.services.sjr.async_session",
    ) as session_factory:
        with pytest.raises((ValueError, FileNotFoundError)):
            await update_quartiles_from_csv()
    session_factory.assert_not_called()


async def test_real_default_snapshot_and_legacy_update_path():
    records = MagicMock()
    records.all.return_value = [("0007-9235", "Q4")]
    session = AsyncMock()
    session.execute.side_effect = [records, MagicMock(rowcount=1)]
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    with patch("app.services.sjr.async_session", return_value=context):
        assert await update_quartiles_from_csv() == 1
    statement = session.execute.await_args_list[1].args[0].compile()
    assert statement.params == {"quartile": "Q1", "issn_1": "0007-9235", "quartile_1": "Q4"}
    session.commit.assert_awaited_once()
