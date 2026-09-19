import json
from pathlib import Path
from unittest.mock import patch

from app.services.reference_data import load_reference_data


def test_load_reference_data():
    payload = json.dumps(
        {
            "white_list": {
                "title": "Белый список МОН РФ",
                "version": "ДС/39-пр",
                "as_of": "2026-03-25",
                "status": "current",
            },
            "scopus": {"version": "August 2026"},
            "unknown": {"version": "ignored"},
        }
    )

    with patch.object(Path, "read_text", return_value=payload):
        result = load_reference_data()

    assert result["white_list"]["as_of"] == "2026-03-25"
    assert result["scopus"]["version"] == "August 2026"
    assert "unknown" not in result


def test_load_reference_data_returns_empty_for_missing_file():
    with patch.object(Path, "read_text", side_effect=FileNotFoundError):
        assert load_reference_data() == {}


def test_load_reference_data_returns_empty_for_invalid_json():
    with patch.object(Path, "read_text", return_value="not-json"):
        assert load_reference_data() == {}


def test_load_reference_data_skips_malformed_entries():
    payload = json.dumps({"white_list": "invalid", "core": {"version": "ICORE2026"}})
    with patch.object(Path, "read_text", return_value=payload):
        assert load_reference_data() == {"core": {"version": "ICORE2026"}}


def test_load_reference_data_drops_malformed_fields_without_losing_source():
    payload = json.dumps(
        {
            "sjr": {
                "version": 2024,
                "latest_version": "SJR 2025",
                "status": ["outdated"],
                "source_kind": 7,
                "source_url": {"url": "invalid"},
                "attribution": ["invalid"],
            }
        }
    )
    with patch.object(Path, "read_text", return_value=payload):
        assert load_reference_data() == {"sjr": {"latest_version": "SJR 2025"}}


def test_load_reference_data_preserves_mirror_provenance():
    metadata = {
        "version": "SJR 2025",
        "retrieved_at": "2026-09-19",
        "source_kind": "public_mirror",
        "source_url": "https://github.com/example/snapshot",
        "attribution": "SCImago — SCImago Journal & Country Rank",
        "url": "https://www.scimagojr.com/journalrank.php?year=2025",
        "status": "current",
    }
    with patch.object(Path, "read_text", return_value=json.dumps({"sjr": metadata})):
        assert load_reference_data() == {"sjr": metadata}
