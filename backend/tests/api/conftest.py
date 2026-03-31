"""Fixtures for API-level tests (FastAPI TestClient with mocked DB)."""

import pytest
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import get_session
from app.repositories.article import ArticleRepository


@pytest.fixture
def mock_repo():
    """A fully-mocked ArticleRepository."""
    repo = AsyncMock(spec=ArticleRepository)
    return repo


@pytest.fixture
async def client(mock_repo):
    """Async HTTP client with dependency override for the DB session."""

    async def _override_session():
        yield AsyncMock()

    app.dependency_overrides[get_session] = _override_session

    # Also override the repo dependency used in the router
    from app.routers.articles import _get_repo
    app.dependency_overrides[_get_repo] = lambda: mock_repo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
