"""Map ISSNs to SJR best quartiles from a versioned, bundled CSV snapshot.

This service does not download data or fall back to an older edition. Snapshot
provenance and attribution are recorded in data/source_metadata.json.
"""

import csv
import hashlib
import json
import logging
import re
from pathlib import Path

from sqlalchemy import select, update

from app.database import async_session
from app.models import Article

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SJR_FILENAME = "scimagojr_2025.csv"
SJR_YEAR = 2025
LEGACY_SJR_FILENAME = "scimagojr_2024.csv"


def _parse_sjr_csv(
    filepath: Path, *, expected_year: int | None = None,
    exclude_ambiguous: bool = False,
) -> dict[str, str | None]:
    """Parse SJR CSV → {issn: best_quartile}.

    SJR CSV has semicolon-separated values.
    Column "Issn" contains comma-separated ISSNs (e.g. "14726483, 09628924").
    A '-' quartile explicitly means unranked; absence from the file does not.
    Unexpected schema, values or conflicting duplicate ISSNs fail closed before
    the caller opens a database transaction.
    """
    issn_to_quartile: dict[str, str | None] = {}
    ambiguous_issns: set[str] = set()

    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        required = {"Issn", "SJR Best Quartile"}
        if expected_year is not None:
            required.add(f"Total Docs. ({expected_year})")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("SJR CSV has missing columns or an unexpected edition")
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(row.get(key) is None for key in required):
                raise ValueError(f"Malformed SJR CSV row {row_number}")
            raw_quartile = row["SJR Best Quartile"].strip()
            if raw_quartile not in ("Q1", "Q2", "Q3", "Q4", "-"):
                raise ValueError(f"Invalid SJR quartile at row {row_number}")
            quartile = None if raw_quartile == "-" else raw_quartile

            raw_issns = row.get("Issn", "")
            for issn in raw_issns.split(","):
                issn = issn.strip().upper()
                if issn in ("", "-"):
                    continue
                compact = issn.replace("-", "")
                if not re.fullmatch(r"[0-9]{7}[0-9X]", compact):
                    raise ValueError(f"Invalid SJR ISSN at row {row_number}")
                issn = f"{compact[:4]}-{compact[4:]}"
                if issn in ambiguous_issns:
                    continue
                if issn in issn_to_quartile and issn_to_quartile[issn] != quartile:
                    if exclude_ambiguous:
                        ambiguous_issns.add(issn)
                        del issn_to_quartile[issn]
                        continue
                    raise ValueError(f"Conflicting SJR quartiles for ISSN {issn}")
                issn_to_quartile[issn] = quartile

    if not issn_to_quartile or not any(issn_to_quartile.values()):
        raise ValueError("SJR CSV has no ranked ISSNs")
    if ambiguous_issns:
        logger.warning("Excluded %d ambiguous legacy SJR ISSNs from cleanup", len(ambiguous_issns))

    return issn_to_quartile


async def update_quartiles_from_csv(
    filepath: Path | None = None, *, baseline_filepath: Path | None = None,
) -> int:
    """Apply current ranks and remove only matching, known legacy values.

    The DB has no quartile provenance. An unranked or missing current ISSN is
    cleared only when its value exactly matches the legacy snapshot. Unknown or
    differing values are preserved. A manual value equal to the legacy rank is
    indistinguishable; this limitation is documented in DATA_SOURCES.md.
    """
    is_default = filepath is None
    filepath = filepath or DATA_DIR / SJR_FILENAME

    if not filepath.exists():
        logger.warning("SJR CSV not found at %s — skipping quartile update", filepath)
        return 0

    logger.info("Parsing SJR CSV from %s", filepath)
    issn_to_quartile = _parse_sjr_csv(
        filepath, expected_year=SJR_YEAR if is_default else None,
    )
    if is_default and len(issn_to_quartile) < 1000:
        raise ValueError("Bundled SJR CSV is unexpectedly small")
    if is_default:
        metadata = json.loads((DATA_DIR / "source_metadata.json").read_text(encoding="utf-8"))
        snapshot = metadata.get("sjr", {})
        if (
            snapshot.get("filename") != SJR_FILENAME
            or snapshot.get("data_sha256") != hashlib.sha256(filepath.read_bytes()).hexdigest()
        ):
            raise ValueError("Bundled SJR CSV does not match its provenance checksum")
    logger.info("Loaded %d ISSN→quartile mappings", len(issn_to_quartile))

    legacy_quartiles: dict[str, str | None] = {}
    if baseline_filepath is None and is_default:
        baseline_filepath = DATA_DIR / LEGACY_SJR_FILENAME
    if baseline_filepath is not None:
        if not baseline_filepath.exists():
            logger.warning("SJR legacy snapshot missing; legacy cleanup skipped")
        else:
            legacy_quartiles = _parse_sjr_csv(
                baseline_filepath, expected_year=2024 if is_default else None,
                exclude_ambiguous=True,
            )

    updated = 0
    async with async_session() as session:
        rows = (await session.execute(
            select(Article.issn, Article.quartile)
            .where(Article.issn.is_not(None))
            .distinct()
        )).all()
        for raw_issn, existing_quartile in rows:
            compact = raw_issn.strip().upper().replace("-", "")
            if not re.fullmatch(r"[0-9]{7}[0-9X]", compact):
                continue
            issn = f"{compact[:4]}-{compact[4:]}"
            quartile = issn_to_quartile.get(issn)
            if quartile is None:
                legacy_quartile = legacy_quartiles.get(issn)
                if legacy_quartile is None or existing_quartile != legacy_quartile:
                    continue
            if existing_quartile == quartile:
                continue
            # Compare-and-set avoids overwriting a concurrent change after SELECT.
            existing_condition = (
                Article.quartile.is_(None) if existing_quartile is None
                else Article.quartile == existing_quartile
            )
            result = await session.execute(
                update(Article)
                .where(Article.issn == raw_issn)
                .where(existing_condition)
                .values(quartile=quartile)
            )
            updated += result.rowcount  # type: ignore[assignment]
        await session.commit()

    logger.info("Updated quartile for %d articles", updated)
    return updated
