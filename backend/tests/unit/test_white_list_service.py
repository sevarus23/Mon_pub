"""Unit tests for white list service — cache and API logic."""

import json
import pytest
from unittest.mock import patch, mock_open, AsyncMock, MagicMock

from app.services.white_list import _load_cache, _save_cache, _fetch_level


class TestLoadCache:
    def test_existing_file(self):
        data = json.dumps({"0028-0836": 1, "1234-5678": None})
        with patch("app.services.white_list.CACHE_PATH") as mock_path:
            mock_path.exists.return_value = True
            with patch("builtins.open", mock_open(read_data=data)):
                result = _load_cache()
        assert result == {"0028-0836": 1, "1234-5678": None}

    def test_missing_file(self):
        with patch("app.services.white_list.CACHE_PATH") as mock_path:
            mock_path.exists.return_value = False
            result = _load_cache()
        assert result == {}


class TestSaveCache:
    def test_writes_json(self, tmp_path):
        cache_file = tmp_path / "data" / "cache.json"
        with patch("app.services.white_list.CACHE_PATH", cache_file):
            _save_cache({"0028-0836": 1})
        assert cache_file.exists()
        with open(cache_file) as f:
            data = json.load(f)
        assert data == {"0028-0836": 1}


class TestFetchLevel:
    @pytest.mark.asyncio
    async def test_success_level_2023(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"level_2023": 2, "level_2025": None}
        client = AsyncMock()
        client.get.return_value = mock_resp
        result = await _fetch_level(client, "0028-0836")
        assert result == 2

    @pytest.mark.asyncio
    async def test_success_level_2025_preferred(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"level_2023": 3, "level_2025": 1}
        client = AsyncMock()
        client.get.return_value = mock_resp
        result = await _fetch_level(client, "0028-0836")
        assert result == 1

    @pytest.mark.asyncio
    async def test_not_found(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        client = AsyncMock()
        client.get.return_value = mock_resp
        result = await _fetch_level(client, "9999-9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        client = AsyncMock()
        client.get.side_effect = Exception("connection error")
        result = await _fetch_level(client, "0028-0836")
        assert result is None
