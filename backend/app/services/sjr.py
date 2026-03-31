"""
SJR Quartile mapping service.

Downloads the SJR journal ranking CSV and maps ISSN → best quartile.
CSV can be downloaded manually from https://www.scimagojr.com/journalrank.php
(click "Download data" → save as data/scimagojr.csv).

Alternatively, runs an automatic update against the database using
the CSV placed at DATA_DIR / "scimagojr.csv".
"""

import csv
import logging
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Article

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SJR_FILENAME = "scimagojr_2024.csv"


def _parse_sjr_csv(filepath: Path) -> dict[str, str]:
    """Parse SJR CSV → {issn: best_quartile}.

    SJR CSV has semicolon-separated values.
    Column "Issn" contains space-separated ISSNs (e.g. "14726483, 09628924").
    Column "SJR Best Quartile" contains Q1/Q2/Q3/Q4.
    """
    issn_to_quartile: dict[str, str] = {}

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            quartile = row.get("SJR Best Quartile", "").strip()
            if quartile not in ("Q1", "Q2", "Q3", "Q4"):
                continue

            raw_issns = row.get("Issn", "")
            for issn in raw_issns.split(","):
                issn = issn.strip()
                if len(issn) == 8:
                    issn = f"{issn[:4]}-{issn[4:]}"
                if issn:
                    issn_to_quartile[issn] = quartile

    return issn_to_quartile


async def update_quartiles_from_csv(filepath: Path | None = None) -> int:
    """Read SJR CSV and update quartile for all articles matching by ISSN."""
    filepath = filepath or DATA_DIR / SJR_FILENAME

    if not filepath.exists():
        logger.warning("SJR CSV not found at %s — skipping quartile update", filepath)
        return 0

    logger.info("Parsing SJR CSV from %s", filepath)
    issn_to_quartile = _parse_sjr_csv(filepath)
    logger.info("Loaded %d ISSN→quartile mappings", len(issn_to_quartile))

    updated = 0
    async with async_session() as session:
        for issn, quartile in issn_to_quartile.items():
            result = await session.execute(
                update(Article)
                .where(Article.issn == issn, Article.quartile.is_(None))
                .values(quartile=quartile)
            )
            updated += result.rowcount  # type: ignore[assignment]
        await session.commit()

    logger.info("Updated quartile for %d articles", updated)
    return updated
