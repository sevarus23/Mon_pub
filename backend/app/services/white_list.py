"""Service for enriching articles with White List (MON RF) journal levels.

Uses the open API at https://journalrank.rcsi.science/api
to look up journal levels by ISSN.
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx
from sqlalchemy import select, update, func

from app.database import async_session
from app.models import Article

logger = logging.getLogger(__name__)

API_URL = "https://journalrank.rcsi.science/api/record-sources/{issn}/level"
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "white_list_cache.json"


def _load_cache() -> dict[str, int | None]:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, int | None]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


async def _fetch_level(client: httpx.AsyncClient, issn: str) -> int | None:
    """Fetch white list level for a single ISSN. Returns level (1-4) or None."""
    url = API_URL.format(issn=issn)
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Prefer 2025 level, fall back to 2023
            level = data.get("level_2025") or data.get("level_2023")
            return level
        # 400/404 = not in white list
        return None
    except Exception:
        logger.warning("Failed to fetch white list for ISSN %s", issn)
        return None


async def update_white_list_levels() -> int:
    """Update articles with white list levels from cache and API.

    First applies levels from existing cache, then fetches uncached ISSNs
    from the RCSI API.
    """
    # Get all unique ISSNs from DB
    async with async_session() as session:
        result = await session.execute(
            select(Article.issn)
            .where(Article.issn.is_not(None))
            .where(Article.issn != "")
            .distinct()
        )
        all_issns = [r[0] for r in result.all()]

    if not all_issns:
        logger.info("No ISSNs to check")
        return 0

    logger.info("Checking %d unique ISSNs against White List", len(all_issns))

    # Load cache
    cache = _load_cache()
    logger.info("Cache has %d entries", len(cache))

    # Try to fetch uncached ISSNs from API
    issns_to_fetch = [issn for issn in all_issns if issn not in cache]
    if issns_to_fetch:
        logger.info("Fetching %d new ISSNs from RCSI API", len(issns_to_fetch))
        try:
            async with httpx.AsyncClient(verify=True) as client:
                for i, issn in enumerate(issns_to_fetch):
                    level = await _fetch_level(client, issn)
                    cache[issn] = level
                    if (i + 1) % 50 == 0:
                        logger.info("Fetched %d/%d ISSNs", i + 1, len(issns_to_fetch))
                    await asyncio.sleep(0.15)
            _save_cache(cache)
        except Exception:
            logger.exception("API fetch failed, using cache only")

    # Build ISSN -> level mapping (only entries that have a level)
    issn_levels: dict[str, int] = {k: v for k, v in cache.items() if v is not None}
    logger.info("Found %d ISSNs in White List", len(issn_levels))

    # Update articles in DB
    updated = 0
    async with async_session() as session:
        # Set level for matching ISSNs
        for issn, level in issn_levels.items():
            result = await session.execute(
                update(Article)
                .where(Article.issn == issn)
                .where(
                    (Article.white_list_level.is_(None))
                    | (Article.white_list_level != level)
                )
                .values(white_list_level=level)
            )
            updated += result.rowcount

        # Clear level for ISSNs not in white list
        known_issns = set(cache.keys())
        not_in_list_issns = [issn for issn in all_issns if issn in known_issns and cache.get(issn) is None]
        if not_in_list_issns:
            result = await session.execute(
                update(Article)
                .where(Article.issn.in_(not_in_list_issns))
                .where(Article.white_list_level.is_not(None))
                .values(white_list_level=None)
            )
            updated += result.rowcount

        await session.commit()

    logger.info("White list update complete: %d articles updated", updated)
    return updated
