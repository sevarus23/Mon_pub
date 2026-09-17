import asyncio
import logging
from datetime import timedelta

from app.database import async_session
from app.repositories.article import ArticleRepository
from app.services.crossref import parse_crossref
from app.services.openalex import parse_openalex
from app.services.sjr import update_quartiles_from_csv
from app.services.white_list import update_white_list_levels
from app.services.core_ranks import update_core_ranks

logger = logging.getLogger(__name__)


async def run_parse() -> dict:
    logger.info("Starting parse job")

    async with async_session() as session:
        repo = ArticleRepository(session)
        last_date = await repo.get_last_published_date()

    since_date = last_date - timedelta(days=7) if last_date else None

    crossref_count, openalex_count = await asyncio.gather(
        parse_crossref(since_date),
        parse_openalex(since_date),
    )

    logger.info("Parse complete: crossref=%d, openalex=%d", crossref_count, openalex_count)

    quartile_count = await update_quartiles_from_csv()
    logger.info("Quartile update: %d articles updated", quartile_count)

    white_list_count = await update_white_list_levels(refresh=True, allow_cached_fallback=True)
    logger.info("White List update: %d articles updated", white_list_count)

    # Normalize article types
    async with async_session() as session:
        repo = ArticleRepository(session)
        types_count = await repo.normalize_all_types()
        core_count = await update_core_ranks(session)
    logger.info("Type normalization: %d articles updated", types_count)

    return {"crossref": crossref_count, "openalex": openalex_count,
            "quartiles_updated": quartile_count, "white_list_updated": white_list_count,
            "core_ranks_updated": core_count}
