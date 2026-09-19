"""Import an official RCSI JSON export into the bundled White List snapshot.

Run from backend: python scripts/import_white_list.py <official-export.json>
The input is downloaded from the URL advertised on the RCSI journal list.
"""

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.white_list import (  # noqa: E402
    CACHE_PATH,
    _load_cache,
    import_white_list_records,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--api-response-dir", type=Path,
                        help="Optional audit directory for official conflict-resolution API responses")
    args = parser.parse_args()
    content = args.export.read_bytes()
    records = json.loads(content.decode("utf-8-sig"))
    previous = _load_cache()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        cache = await import_white_list_records(
            records, client, source_bytes=content, api_response_dir=args.api_response_dir,
        )
    print(json.dumps({
        "records": len(records), "issns": len(cache),
        "active_issns": sum(level is not None for level in cache.values()),
        "changed_previous_issns": sum(cache.get(issn) != level for issn, level in previous.items()),
        "download_sha256": hashlib.sha256(content).hexdigest(),
        "data_sha256": hashlib.sha256(CACHE_PATH.read_bytes()).hexdigest(),
    }, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
