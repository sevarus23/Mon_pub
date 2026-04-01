"""Scopus ISSN index — used to filter articles by Scopus-indexed sources."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SCOPUS_FILE = DATA_DIR / "scopus_issns.json"

_scopus_issns: set[str] | None = None


def get_scopus_issns() -> set[str]:
    """Load and cache Scopus ISSN set."""
    global _scopus_issns
    if _scopus_issns is None:
        if not SCOPUS_FILE.exists():
            logger.warning("Scopus ISSN file not found at %s", SCOPUS_FILE)
            _scopus_issns = set()
        else:
            with open(SCOPUS_FILE, encoding="utf-8") as f:
                _scopus_issns = set(json.load(f))
            logger.info("Loaded %d Scopus ISSNs", len(_scopus_issns))
    return _scopus_issns
