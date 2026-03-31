"""API tests for GET /health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def raw_client():
    """Client without repo mocking — for endpoints that don't need DB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    """Test-plan §3 — GET /health."""

    async def test_health_returns_200(self, raw_client):
        resp = await raw_client.get("/health")
        assert resp.status_code == 200

    async def test_health_body(self, raw_client):
        resp = await raw_client.get("/health")
        assert resp.json() == {"status": "ok"}
