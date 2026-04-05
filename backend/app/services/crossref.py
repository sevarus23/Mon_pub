import hashlib
import logging
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.database import async_session
from app.repositories.article import ArticleRepository
from app.schemas.article import ArticleCreate
from app.utils.type_mapping import normalize_type

logger = logging.getLogger(__name__)

BASE_URL = "https://api.crossref.org/works"
ROWS = 100
HEADERS = {"User-Agent": f"InnoArticles/1.0 (mailto:{settings.CROSSREF_EMAIL})"}

# DOIs to skip (not Innopolis University — Korean Innopolis, Finnish Innopolis district, etc.)
IGNORED_DOIS: set[str] = {
    "10.1142/9789811257186_0012",     # Daedeok Innopolis, Korea
    "10.1142/9789812790859_0021",     # Innopolis 2 district, Espoo, Finland
    "10.1080/18752160.2024.2431418",  # Korean Innovation Cluster
}

def _is_ignored(doi: str) -> bool:
    return doi.lower() in IGNORED_DOIS


def _parse_date(item: dict) -> date | None:
    for field in ("published-online", "published-print", "created"):
        dp = item.get(field)
        if dp and "date-parts" in dp and dp["date-parts"] and dp["date-parts"][0]:
            parts = dp["date-parts"][0]
            try:
                year = parts[0]
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                return date(year, month, day)
            except (ValueError, TypeError):
                continue
    return None


def _parse_authors(item: dict) -> str:
    authors = item.get("author", [])
    names = []
    for a in authors:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            names.append(name)
    return ", ".join(names) if names else "Unknown"


def _doi_hash(doi: str) -> str:
    return hashlib.md5(doi.encode()).hexdigest()[:16]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
async def _fetch_page(client: httpx.AsyncClient, offset: int, since_date: date | None) -> dict:
    params = {
        "query.affiliation": "Innopolis",
        "rows": ROWS,
        "offset": offset,
    }
    if since_date:
        params["filter"] = f"from-pub-date:{since_date.isoformat()}"
    resp = await client.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


async def parse_crossref(since_date: date | None = None) -> int:
    logger.info("Starting CrossRef parsing (since=%s)", since_date)
    inserted = 0
    offset = 0

    async with httpx.AsyncClient() as client:
        while True:
            try:
                data = await _fetch_page(client, offset, since_date)
            except Exception:
                logger.exception("CrossRef fetch failed at offset %d", offset)
                break

            items = data.get("message", {}).get("items", [])
            if not items:
                break

            articles: list[ArticleCreate] = []
            for item in items:
                doi = item.get("DOI")
                if not doi:
                    continue

                if _is_ignored(doi):
                    continue

                pub_date = _parse_date(item)

                title_list = item.get("title", [])
                title = title_list[0] if title_list else "Untitled"

                container = item.get("container-title", [])
                journal = container[0] if container else None

                issn_list = item.get("ISSN", [])
                issn = issn_list[0] if issn_list else None

                topics = item.get("subject", [])[:10]

                articles.append(ArticleCreate(
                    num_id=f"cr_{_doi_hash(doi)}",
                    title=title,
                    authors=_parse_authors(item),
                    doi=doi,
                    published_at=pub_date,
                    journal_name=journal,
                    issn=issn,
                    type=normalize_type(item.get("type")),
                    publisher=item.get("publisher"),
                    cited_by_count=item.get("is-referenced-by-count"),
                    language=item.get("language"),
                    source="crossref",
                    topics=topics,
                ))

            if articles:
                async with async_session() as session:
                    repo = ArticleRepository(session)
                    inserted += await repo.bulk_upsert(articles)

            total = data.get("message", {}).get("total-results", 0)
            offset += ROWS
            logger.info("CrossRef: fetched %d/%d, inserted so far: %d", offset, total, inserted)

            if offset >= total:
                break

    logger.info("CrossRef parsing complete: %d new articles", inserted)
    return inserted
