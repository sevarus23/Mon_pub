import logging
import math
from datetime import date, datetime

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

                # Extract topics from OpenAlex
                raw_topics = work.get("topics", [])
                topics = [t["display_name"] for t in raw_topics[:10] if t.get("display_name")]
                if not topics:
                    concepts = work.get("concepts", [])
                    topics = [c["display_name"] for c in concepts[:10]
                              if c.get("display_name") and c.get("score", 0) > 0.3]

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
                    topics=topics,
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


# --- Real-time OpenAlex search (global mode) ---

SORT_MAP = {
    "published_at": "publication_date",
    "cited_by_count": "cited_by_count",
    "title": "display_name",
}

MAILTO = "t.bektleuov@innopolis.university"


async def search_openalex(
    search: str = "",
    page: int = 1,
    per_page: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    institution: str | None = None,
) -> dict:
    """Query OpenAlex API in real-time and return PaginatedArticles-shaped dict."""
    params: dict[str, str | int] = {
        "page": page,
        "per_page": per_page,
        "mailto": MAILTO,
    }

    if search:
        params["search"] = search

    filter_parts: list[str] = []
    if institution:
        filter_parts.append(f"authorships.institutions.search:{institution}")
    if date_from:
        filter_parts.append(f"from_publication_date:{date_from.isoformat()}")
    if date_to:
        filter_parts.append(f"to_publication_date:{date_to.isoformat()}")
    if filter_parts:
        params["filter"] = ",".join(filter_parts)

    oa_sort = SORT_MAP.get(sort_by, "publication_date")
    params["sort"] = f"{oa_sort}:{'desc' if sort_order == 'desc' else 'asc'}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    meta = data.get("meta", {})
    total = min(meta.get("count", 0), 10000)  # OpenAlex caps at 10k for page-based
    now = datetime.utcnow().isoformat()

    items = []
    for work in results:
        authorships = work.get("authorships", [])
        doi_raw = work.get("doi")
        doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None

        primary_loc = work.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        journal = source.get("display_name")
        issn = source.get("issn_l")

        openalex_id = _extract_openalex_id(work.get("id", ""))

        raw_topics = work.get("topics", [])
        topics = [t["display_name"] for t in raw_topics[:10] if t.get("display_name")]
        if not topics:
            concepts = work.get("concepts", [])
            topics = [c["display_name"] for c in concepts[:10]
                      if c.get("display_name") and c.get("score", 0) > 0.3]

        items.append({
            "id": abs(hash(openalex_id)) % (2**31),
            "num_id": f"oa_{openalex_id}",
            "title": work.get("title") or "Untitled",
            "authors": _parse_authors(authorships),
            "doi": doi,
            "published_at": work.get("publication_date"),
            "journal_name": journal,
            "issn": issn,
            "type": normalize_type(primary_loc.get("raw_type")),
            "quartile": None,
            "publisher": source.get("host_organization_name"),
            "cited_by_count": work.get("cited_by_count"),
            "language": work.get("language"),
            "source": "openalex",
            "topics": topics,
            "created_at": now,
            "updated_at": now,
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 0,
        "items": items,
    }
