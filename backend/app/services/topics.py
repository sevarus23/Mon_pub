import asyncio
import logging

import httpx
from sqlalchemy import select, update

from app.database import async_session
from app.models import Article

logger = logging.getLogger(__name__)

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
MAILTO = "t.bektleuov@innopolis.university"
BATCH_SIZE = 50


def _extract_topics(work: dict) -> list[str]:
    raw_topics = work.get("topics", [])
    topics = [t["display_name"] for t in raw_topics[:10] if t.get("display_name")]
    if not topics:
        concepts = work.get("concepts", [])
        topics = [c["display_name"] for c in concepts[:10]
                  if c.get("display_name") and c.get("score", 0) > 0.3]
    return topics


async def backfill_topics() -> int:
    """Fetch topics from OpenAlex for articles that have empty topics."""
    updated = 0

    async with async_session() as session:
        # Get articles with empty topics that have a DOI
        result = await session.execute(
            select(Article.id, Article.doi, Article.num_id)
            .where(Article.topics == "{}")
            .where(Article.doi.is_not(None))
            .limit(2000)
        )
        articles = result.all()

    if not articles:
        logger.info("No articles to backfill")
        return 0

    logger.info("Backfilling topics for %d articles", len(articles))

    async with httpx.AsyncClient() as client:
        for i in range(0, len(articles), BATCH_SIZE):
            batch = articles[i:i + BATCH_SIZE]
            dois = "|".join(f"https://doi.org/{a.doi}" for a in batch if a.doi)

            try:
                resp = await client.get(
                    OPENALEX_WORKS_URL,
                    params={
                        "filter": f"doi:{dois}",
                        "per_page": BATCH_SIZE,
                        "mailto": MAILTO,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                logger.exception("Failed to fetch batch %d", i)
                continue

            # Build DOI -> topics mapping
            doi_topics: dict[str, list[str]] = {}
            for work in data.get("results", []):
                doi_raw = work.get("doi")
                if doi_raw:
                    doi = doi_raw.replace("https://doi.org/", "")
                    topics = _extract_topics(work)
                    if topics:
                        doi_topics[doi.lower()] = topics

            # Update in DB
            if doi_topics:
                async with async_session() as session:
                    for article in batch:
                        if article.doi and article.doi.lower() in doi_topics:
                            await session.execute(
                                update(Article)
                                .where(Article.id == article.id)
                                .values(topics=doi_topics[article.doi.lower()])
                            )
                            updated += 1
                    await session.commit()

            logger.info("Backfill batch %d-%d: updated %d", i, i + len(batch), updated)
            await asyncio.sleep(0.5)  # Rate limiting

    logger.info("Backfill complete: %d articles updated", updated)
    return updated
