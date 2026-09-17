"""Read provenance and freshness metadata for bundled reference datasets."""

import json
from pathlib import Path
from typing import Any


REFERENCE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "source_metadata.json"
REFERENCE_DATA_KEYS = ("white_list", "scopus", "sjr", "core")
REFERENCE_DATA_FIELDS = (
    "title",
    "version",
    "latest_version",
    "as_of",
    "retrieved_at",
    "url",
    "status",
)


def load_reference_data(path: Path = REFERENCE_DATA_PATH) -> dict[str, dict[str, Any]]:
    """Return valid per-source metadata, or an empty object for unavailable data.

    Metadata is informational and must never make the main articles API unavailable.
    A malformed entry is skipped while well-formed entries remain visible.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    result: dict[str, dict[str, Any]] = {}
    for key in REFERENCE_DATA_KEYS:
        value = payload.get(key)
        if not isinstance(value, dict):
            continue
        # Keep the endpoint tolerant even when a hand-edited metadata field has
        # an unexpected type. FastAPI must not turn an informational issue into 500.
        result[key] = {
            field: field_value
            for field in REFERENCE_DATA_FIELDS
            if isinstance((field_value := value.get(field)), str)
        }
    return result
