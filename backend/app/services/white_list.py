"""Service for enriching articles with White List (MON RF) journal levels.

Uses the official RCSI export and API to keep journal levels current.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Article

logger = logging.getLogger(__name__)

API_URL = "https://journalrank.rcsi.science/api/record-sources/{issn}/level"
EXPORT_URL = (
    "https://journalrank.rcsi.science/ru/record-sources/download/"
    "?dataType=Json"
)
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "white_list_cache.json"
VALID_LEVELS = {1, 2, 3, 4}
_refresh_lock = asyncio.Lock()
_last_refresh_success: float | None = None


def _load_cache() -> dict[str, int | None]:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, int | None]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = CACHE_PATH.with_suffix(f"{CACHE_PATH.suffix}.tmp")
    with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        f.write("\n")
    temp_path.replace(CACHE_PATH)


def _normalize_issn(value: str) -> str:
    compact = value.strip().upper().replace("-", "")
    if re.fullmatch(r"[0-9]{7}[0-9X]", compact):
        return f"{compact[:4]}-{compact[4:]}"
    return value.strip().upper()


def _extract_latest_level(data: dict[str, Any]) -> int | None:
    """Return the newest valid level, or None for an excluded journal."""
    if data.get("date_discontinued") or data.get("dateDiscontinued"):
        return None

    level_fields = sorted(
        (
            (int(key.removeprefix("level_")), value)
            for key, value in data.items()
            if key.startswith("level_") and key.removeprefix("level_").isdigit()
        ),
        reverse=True,
    )
    for _, value in level_fields:
        if type(value) is int and value in VALID_LEVELS:
            return int(value)
    return None


class WhiteListConflictError(ValueError):
    """An ISSN has conflicting active records and needs an official API lookup."""

    def __init__(self, conflicts: dict[str, set[int | None]]) -> None:
        self.conflicts = conflicts
        super().__init__(f"RCSI export contains conflicting active levels for {len(conflicts)} ISSNs")


def _build_cache(
    records: list[dict[str, Any]], *, resolutions: dict[str, int | None] | None = None,
) -> dict[str, int | None]:
    """Build a complete ISSN mapping; an active record wins over a historical one."""
    cache: dict[str, int | None] = {}
    active_issns: set[str] = set()
    active_levels: dict[str, set[int | None]] = {}

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("RCSI export contains a non-object record")
        for key, value in record.items():
            if re.fullmatch(r"level_[0-9]{4}", key) and value is not None:
                if type(value) is not int or value not in VALID_LEVELS:
                    raise ValueError("RCSI export contains an invalid journal level")
        discontinued = bool(
            record.get("date_discontinued") or record.get("dateDiscontinued")
        )
        level = _extract_latest_level(record)
        raw_issns = record.get("issns") or record.get("issn") or []
        if not isinstance(raw_issns, list):
            raise ValueError("RCSI export contains invalid ISSN data")
        if not any(re.fullmatch(r"level_[0-9]{4}", key) for key in record):
            raise ValueError("RCSI export contains a record without level fields")
        for raw_issn in raw_issns:
            if not raw_issn:
                continue
            issn = _normalize_issn(str(raw_issn))
            if not re.fullmatch(r"[0-9]{4}-[0-9]{3}[0-9X]", issn):
                raise ValueError("RCSI export contains a malformed ISSN")
            if discontinued:
                if issn not in active_issns:
                    cache[issn] = None
            else:
                cache[issn] = level
                active_issns.add(issn)
                active_levels.setdefault(issn, set()).add(level)

    conflicts = {issn: levels for issn, levels in active_levels.items() if len(levels) > 1}
    resolutions = resolutions or {}
    if any(issn not in resolutions for issn in conflicts):
        raise WhiteListConflictError(conflicts)
    for issn, levels in conflicts.items():
        if resolutions[issn] not in levels:
            raise ValueError(f"RCSI API level for {issn} does not match any export candidate")
        cache[issn] = resolutions[issn]

    return dict(sorted(cache.items()))


async def _resolve_cache(
    records: list[dict[str, Any]], client: httpx.AsyncClient,
    *, api_response_dir: Path | None = None,
) -> tuple[dict[str, int | None], dict[str, int | None]]:
    """Resolve only ambiguous ISSNs; any failed lookup leaves the cache untouched."""
    try:
        return _build_cache(records), {}
    except WhiteListConflictError as exc:
        conflicts = exc.conflicts

    resolutions: dict[str, int | None] = {}
    for issn in sorted(conflicts):
        response = await client.get(API_URL.format(issn=issn), timeout=20)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"RCSI API returned an invalid record for {issn}")
        # Reuse the strict schema and level checks. An omitted or different ISSN
        # must not be interpreted as confirmation that this journal is excluded.
        resolved = _build_cache([payload])
        if issn not in resolved or resolved[issn] not in conflicts[issn]:
            raise ValueError(f"RCSI API could not confirm a candidate level for {issn}")
        resolutions[issn] = resolved[issn]
        if api_response_dir is not None:
            api_response_dir.mkdir(parents=True, exist_ok=True)
            (api_response_dir / f"{issn}.json").write_bytes(response.content)
    return _build_cache(records, resolutions=resolutions), resolutions


async def import_white_list_records(
    records: list[dict[str, Any]], client: httpx.AsyncClient,
    *, source_bytes: bytes | None = None, api_response_dir: Path | None = None,
) -> dict[str, int | None]:
    """Validate and install official records; shared by refresh and the CLI importer."""
    if not isinstance(records, list) or len(records) < 1000:
        raise ValueError("RCSI export is unexpectedly small or has invalid format")
    cache, resolutions = await _resolve_cache(records, client, api_response_dir=api_response_dir)
    if len(cache) < 1000:
        raise ValueError("RCSI ISSN cache is unexpectedly small")
    previous = _load_cache()
    if len(previous) > 1000 and len(cache) < len(previous) * 0.9:
        raise ValueError("RCSI export lost more than 10% of known ISSNs")
    previous_active = sum(level is not None for level in previous.values())
    active = sum(level is not None for level in cache.values())
    if previous_active > 1000 and active < previous_active * 0.9:
        raise ValueError("RCSI export lost more than 10% of active ISSNs")
    _save_cache(cache)
    try:
        _save_refresh_metadata(records, cache, source_bytes=source_bytes, resolutions=resolutions)
    except Exception:
        # A metadata failure must not misreport an already installed valid cache
        # as a failed data refresh. The old visible retrieval date remains intact.
        logger.exception("White List cache updated, but freshness metadata could not be saved")
    logger.info("Refreshed White List cache: %d records, %d ISSNs, %d API resolutions",
                len(records), len(cache), len(resolutions))
    return cache


async def _fetch_level(client: httpx.AsyncClient, issn: str) -> int | None:
    """Fetch white list level for a single ISSN. Returns level (1-4) or None."""
    url = API_URL.format(issn=issn)
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code == 200:
            return _extract_latest_level(resp.json())
        # 400/404 = not in white list
        return None
    except Exception:
        logger.warning("Failed to fetch white list for ISSN %s", issn)
        return None


async def refresh_white_list_cache(
    client: httpx.AsyncClient | None = None,
) -> dict[str, int | None]:
    """Download the complete official RCSI export and atomically replace the cache."""

    async def _download(http_client: httpx.AsyncClient) -> dict[str, int | None]:
        response = await http_client.get(EXPORT_URL, timeout=120)
        response.raise_for_status()
        return await import_white_list_records(
            response.json(), http_client, source_bytes=response.content,
        )

    async with _refresh_lock:
        global _last_refresh_success
        # The unauthenticated legacy action endpoint must not download a 46 MB
        # export on every repeated request. Daily scheduled refresh is unaffected.
        if client is None and _last_refresh_success is not None:
            if time.monotonic() - _last_refresh_success < 3600:
                return _load_cache()
        if client is not None:
            return await _download(client)

        async with httpx.AsyncClient(follow_redirects=True) as http_client:
            cache = await _download(http_client)
            _last_refresh_success = time.monotonic()
            return cache


def _save_refresh_metadata(
    records: list[dict], cache: dict[str, int | None], *, source_bytes: bytes | None = None,
    resolutions: dict[str, int | None] | None = None,
) -> None:
    """Keep the visible retrieval date tied to an actual successful download."""
    metadata_path = CACHE_PATH.parent / "source_metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            metadata = {}
    except (OSError, ValueError):
        metadata = {}
    years = sorted({int(key[6:]) for record in records for key in record
                    if re.fullmatch(r"level_[0-9]{4}", key)})
    if not isinstance(metadata.get("white_list"), dict):
        metadata["white_list"] = {}
    entry = metadata["white_list"]
    entry.update({
        "title": "Белый список МОН РФ",
        "version": f"Уровни по {years[-1]} год",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://journalrank.rcsi.science/ru/record-sources/",
        "download_url": EXPORT_URL,
        "status": "current",
        "records": len(records),
        "issns": len(cache),
        "resolved_conflict_count": len(resolutions or {}),
        "resolved_conflicts": resolutions or {},
    })
    entry["data_sha256"] = hashlib.sha256(CACHE_PATH.read_bytes()).hexdigest()
    if source_bytes is not None:
        entry["download_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    else:
        entry.pop("download_sha256", None)
    dates = []
    for record in records:
        for key in ("date_accepted", "date_discontinued", "dateAccepted", "dateDiscontinued"):
            value = record.get(key)
            if not value:
                continue
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    dates.append(datetime.strptime(value, fmt).date())
                    break
                except (ValueError, TypeError):
                    continue
    if dates:
        entry["as_of"] = max(dates).isoformat()
    entry["note"] = "Используется последний утверждённый уровень; исключённые журналы не считаются включёнными."
    temp = metadata_path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temp.replace(metadata_path)


async def _apply_cache(session: AsyncSession, cache: dict[str, int | None]) -> int:
    result = await session.execute(
        select(Article.issn).where(Article.issn.is_not(None)).distinct()
    )
    article_issns = [row[0] for row in result.all() if row[0]]

    updated = 0
    for raw_issn in article_issns:
        issn = _normalize_issn(raw_issn)
        level = cache.get(issn)
        statement = update(Article).where(Article.issn == raw_issn)
        if level is None:
            statement = statement.where(Article.white_list_level.is_not(None))
        else:
            statement = statement.where(
                (Article.white_list_level.is_(None))
                | (Article.white_list_level != level)
            )
        result = await session.execute(statement.values(white_list_level=level))
        updated += result.rowcount or 0

    await session.commit()
    return updated


async def update_white_list_levels(
    session: AsyncSession | None = None,
    *,
    refresh: bool = False,
    allow_cached_fallback: bool = False,
) -> int:
    """Update articles with White List levels.

    When ``refresh`` is true, downloads the complete official export first.
    A failed explicit refresh raises; scheduled jobs may opt into cached fallback.
    """
    cache = _load_cache()
    if refresh:
        try:
            cache = await refresh_white_list_cache()
        except Exception:
            if not allow_cached_fallback:
                raise
            logger.exception(
                "Failed to refresh White List from RCSI; using last known-good cache"
            )

    if not cache:
        logger.warning("White list cache is empty or not found at %s", CACHE_PATH)
        return 0

    logger.info("Loaded cache with %d entries", len(cache))

    if session is not None:
        updated = await _apply_cache(session, cache)
    else:
        async with async_session() as own_session:
            updated = await _apply_cache(own_session, cache)

    logger.info("White list update complete: %d articles updated", updated)
    return updated
