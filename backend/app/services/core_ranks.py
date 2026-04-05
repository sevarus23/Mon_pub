"""Service for enriching conference articles with CORE Rankings.

Uses a pre-built JSON cache of CORE conference rankings scraped from
https://portal.core.edu.au/conf-ranks/
Matching is done by fuzzy comparison of journal_name with CORE title/acronym.
"""

import json
import logging
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article

logger = logging.getLogger(__name__)

CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "core_ranks.json"

# Only keep meaningful ranks
VALID_RANKS = {"A*", "A", "B", "C"}


def _load_core_data() -> list[dict]:
    if not CACHE_PATH.exists():
        logger.warning("CORE ranks cache not found at %s", CACHE_PATH)
        return []
    with open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _normalize(s: str) -> str:
    """Normalize string for fuzzy comparison."""
    return s.lower().strip()


def _build_lookup(core_data: list[dict]) -> dict[str, str]:
    """Build normalized title/acronym -> rank mapping."""
    lookup: dict[str, str] = {}
    for entry in core_data:
        rank = entry.get("rank", "").strip()
        if rank not in VALID_RANKS:
            continue

        title = _normalize(entry.get("title", ""))
        acronym = _normalize(entry.get("acronym", ""))

        if title:
            lookup[title] = rank
        if acronym:
            lookup[acronym] = rank

        # Also store "acronym - year" patterns and partial matches
        # e.g. "SIGCOMM" matches "ACM SIGCOMM Conference..."
        if acronym and len(acronym) >= 3:
            lookup[f"#{acronym}#"] = rank  # marker for substring match

    return lookup


def _find_rank(journal_name: str, lookup: dict[str, str]) -> str | None:
    """Find CORE rank for a journal/conference name."""
    normalized = _normalize(journal_name)

    # Exact match on title
    if normalized in lookup:
        return lookup[normalized]

    # Check if any acronym is a substring of the journal name
    for key, rank in lookup.items():
        if key.startswith("#") and key.endswith("#"):
            acronym = key[1:-1]
            # Match acronym as whole word in journal name
            words = normalized.replace("-", " ").replace("/", " ").split()
            if acronym in words or acronym.upper() in journal_name:
                return rank

    # Check if journal name contains a known conference title
    for key, rank in lookup.items():
        if key.startswith("#"):
            continue
        if len(key) > 15 and key in normalized:
            return rank

    return None


async def update_core_ranks(session: AsyncSession) -> int:
    """Update articles with CORE conference ranks from cache."""
    core_data = _load_core_data()
    if not core_data:
        return 0

    lookup = _build_lookup(core_data)
    logger.info("CORE lookup built: %d entries", len(lookup))

    # Get unique conference names (articles with type containing conference keywords)
    result = await session.execute(
        select(Article.journal_name)
        .where(Article.journal_name.is_not(None))
        .distinct()
    )
    all_names = [r[0] for r in result.all()]

    # Build name -> rank mapping
    name_ranks: dict[str, str] = {}
    for name in all_names:
        rank = _find_rank(name, lookup)
        if rank:
            name_ranks[name] = rank

    logger.info("Matched %d journal names to CORE ranks", len(name_ranks))

    # Update DB
    updated = 0
    for name, rank in name_ranks.items():
        result = await session.execute(
            update(Article)
            .where(Article.journal_name == name)
            .where(
                (Article.core_rank.is_(None))
                | (Article.core_rank != rank)
            )
            .values(core_rank=rank)
        )
        updated += result.rowcount

    await session.commit()
    logger.info("CORE ranks update complete: %d articles updated", updated)
    return updated
