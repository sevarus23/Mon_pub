import logging
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.database import async_session
from app.repositories.article import ArticleRepository
from app.schemas.article import ArticleCreate
from app.utils.type_mapping import normalize_type

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org/works"
INNOPOLIS_ROR = "https://ror.org/02b7jh107"
PER_PAGE = 200

# DOIs to skip (misattributed to Innopolis University)
IGNORED_DOIS: set[str] = {
    "10.1158/0008-5472.can-11-0760",
    "10.5762/kais.2012.13.6.2528",
    "10.1007/978-1-4471-5508-9_24",  # International Innopolis Research Center, Korea
}


def _has_innopolis_affiliation(authorships: list) -> bool:
    """Check that at least one author has 'Innopolis' in raw affiliation string."""
    for a in authorships:
        for raw in a.get("raw_affiliation_strings", []):
            if "innopolis" in raw.lower():
                return True
    return False


def _parse_authors(authorships: list) -> str:
    names = []
    for a in authorships:
        name = a.get("author", {}).get("display_name")
        if name:
            names.append(name)
    return ", ".join(names) if names else "Unknown"


def _extract_openalex_id(openalex_url: str) -> str:
    return openalex_url.rsplit("/", 1)[-1] if openalex_url else ""


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
async def _fetch_page(client: httpx.AsyncClient, cursor: str, since_date: date | None) -> dict:
    filter_parts = [f"authorships.institutions.ror:{INNOPOLIS_ROR}"]
    if since_date:
        filter_parts.append(f"from_publication_date:{since_date.isoformat()}")

    params = {
        "filter": ",".join(filter_parts),
        "per_page": PER_PAGE,
        "cursor": cursor,
    }
    resp = await client.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


async def parse_openalex(since_date: date | None = None) -> int:
    logger.info("Starting OpenAlex parsing (since=%s)", since_date)
    inserted = 0
    cursor = "*"

    async with httpx.AsyncClient() as client:
        while cursor:
            try:
                data = await _fetch_page(client, cursor, since_date)
            except Exception:
                logger.exception("OpenAlex fetch failed at cursor %s", cursor)
                break

            results = data.get("results", [])
            if not results:
                break

            articles: list[ArticleCreate] = []
            for work in results:
                authorships = work.get("authorships", [])

                # Filter out misattributed articles
                if not _has_innopolis_affiliation(authorships):
                    continue

                pub_date = _parse_date(work.get("publication_date"))
                if pub_date and pub_date.year < 2012:
                    continue

                openalex_id = _extract_openalex_id(work.get("id", ""))
                doi_raw = work.get("doi")
                doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None

                if doi and doi.lower() in IGNORED_DOIS:
                    continue

                title = work.get("title") or "Untitled"

                primary_loc = work.get("primary_location") or {}
                source = primary_loc.get("source") or {}
                journal = source.get("display_name")
                issn = source.get("issn_l")
                if not issn:
                    issn_list = source.get("issn")
                    issn = issn_list[0] if issn_list else None

                articles.append(ArticleCreate(
                    num_id=f"oa_{openalex_id}",
                    title=title,
                    authors=_parse_authors(authorships),
                    doi=doi,
                    published_at=_parse_date(work.get("publication_date")),
                    journal_name=journal,
                    issn=issn,
                    type=normalize_type(primary_loc.get("raw_type")),
                    publisher=source.get("host_organization_name"),
                    cited_by_count=work.get("cited_by_count"),
                    language=work.get("language"),
                    source="openalex",
                ))

            if articles:
                async with async_session() as session:
                    repo = ArticleRepository(session)
                    inserted += await repo.bulk_upsert(articles)

            cursor = data.get("meta", {}).get("next_cursor")
            count = data.get("meta", {}).get("count", 0)
            logger.info("OpenAlex: page done, total=%d, inserted so far: %d", count, inserted)

    logger.info("OpenAlex parsing complete: %d new articles", inserted)
    return inserted
