"""Unit tests for white list service — cache and API logic."""

import json
import hashlib
import httpx
import pytest
from unittest.mock import patch, mock_open, AsyncMock, MagicMock

from app.services.white_list import (
    _build_cache,
    _extract_latest_level,
    _fetch_level,
    _load_cache,
    _save_cache,
    _save_refresh_metadata,
    _apply_cache,
    WhiteListConflictError,
    refresh_white_list_cache,
    update_white_list_levels,
)


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
    async def test_success_level_2026_preferred(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "level_2023": 3,
            "level_2025": 2,
            "level_2026": 1,
        }
        client = AsyncMock()
        client.get.return_value = mock_resp
        result = await _fetch_level(client, "0028-0836")
        assert result == 1

    @pytest.mark.asyncio
    async def test_discontinued_journal_has_no_level(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "level_2026": 1,
            "dateDiscontinued": "2026-03-25",
        }
        client = AsyncMock()
        client.get.return_value = mock_resp
        result = await _fetch_level(client, "0028-0836")
        assert result is None

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


class TestLevelExtraction:
    def test_uses_newest_year_without_hardcoding_it(self):
        assert _extract_latest_level(
            {"level_2023": 3, "level_2025": 2, "level_2027": 1}
        ) == 1

    def test_falls_back_to_previous_non_null_year(self):
        assert _extract_latest_level(
            {"level_2023": 3, "level_2025": 2, "level_2026": None}
        ) == 2

    def test_discontinued_snake_case_record_is_excluded(self):
        assert _extract_latest_level(
            {"level_2026": 1, "date_discontinued": "25.03.2026"}
        ) is None

    def test_ignores_invalid_level(self):
        assert _extract_latest_level({"level_2026": 5, "level_2025": 2}) == 2


class TestBuildCache:
    def test_conflicting_active_levels_require_official_resolution(self):
        records = [
            {"issns": ["2709-8036"], "level_2023": 4},
            {"issns": ["2709-8036"], "level_2023": 1},
        ]
        for ordered in (records, list(reversed(records))):
            with pytest.raises(WhiteListConflictError) as exc:
                _build_cache(ordered)
            assert exc.value.conflicts == {"2709-8036": {1, 4}}
            assert _build_cache(ordered, resolutions={"2709-8036": 4}) == {"2709-8036": 4}

    @pytest.mark.parametrize("level", ["2", True, 0, 5, {}, []])
    def test_invalid_non_null_level_rejects_export(self, level):
        with pytest.raises(ValueError, match="invalid journal level"):
            _build_cache([{"issns": ["0028-0836"], "level_2026": level}])

    def test_active_record_wins_over_discontinued_history(self):
        records = [
            {
                "issns": ["12345678"],
                "level_2025": 2,
                "date_discontinued": "11.07.2024",
            },
            {"issns": ["1234-5678"], "level_2026": 1},
        ]
        assert _build_cache(records) == {"1234-5678": 1}

    def test_discontinued_record_is_kept_as_null_for_database_cleanup(self):
        records = [
            {
                "issns": ["1063-7850"],
                "level_2025": 2,
                "date_discontinued": "29.10.2025",
            }
        ]
        assert _build_cache(records) == {"1063-7850": None}

    def test_discontinued_history_cannot_override_active_record(self):
        records = [
            {"issns": ["1234-5678"], "level_2026": 1},
            {"issns": ["1234-5678"], "level_2023": 3,
             "date_discontinued": "11.07.2024"},
        ]
        assert _build_cache(records) == {"1234-5678": 1}

    def test_schema_drift_does_not_turn_all_journals_into_exclusions(self):
        with pytest.raises(ValueError, match="level fields"):
            _build_cache([{"issns": ["1234-5678"], "new_level_field": 1}])


class TestRefresh:
    @staticmethod
    def _complete_records():
        return [{"issns": [f"1234-{index:04d}"], "level_2026": 2}
                for index in range(1000)]

    @pytest.mark.parametrize("reverse", [False, True])
    async def test_full_refresh_resolves_conflict_and_saves_metadata(self, tmp_path, reverse):
        records = self._complete_records() + [{"issns": ["1234-0000"], "level_2026": 3}]
        if reverse:
            records.reverse()
        requested = []

        def respond(request):
            requested.append(str(request.url))
            if request.url.path.endswith("/download/"):
                return httpx.Response(200, json=records)
            return httpx.Response(200, json={"issn": ["1234-0000"], "level_2026": 2})

        cache_file = tmp_path / "cache.json"
        metadata_file = tmp_path / "source_metadata.json"
        metadata_file.write_text('{"scopus":{"version":"retained"}}', encoding="utf-8")
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with patch("app.services.white_list.CACHE_PATH", cache_file):
                cache = await refresh_white_list_cache(client)
        assert len(requested) == 2
        assert requested[1].endswith("/1234-0000/level")
        assert len(cache) == 1000
        assert cache["1234-0000"] == 2
        assert json.loads(cache_file.read_text()) == cache
        assert b"\r\n" not in cache_file.read_bytes()
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        assert metadata["scopus"] == {"version": "retained"}
        assert metadata["white_list"]["resolved_conflicts"] == {"1234-0000": 2}
        assert metadata["white_list"]["resolved_conflict_count"] == 1
        assert metadata["white_list"]["data_sha256"] == hashlib.sha256(cache_file.read_bytes()).hexdigest()

    @pytest.mark.parametrize("failure", ["http", "wrong_issn", "invalid_level", "unconfirmed_level"])
    async def test_conflict_lookup_failure_preserves_old_cache_and_metadata(self, tmp_path, failure):
        records = self._complete_records() + [{"issns": ["1234-0000"], "level_2026": 3}]

        def respond(request):
            if request.url.path.endswith("/download/"):
                return httpx.Response(200, json=records)
            if failure == "http":
                return httpx.Response(503)
            payload = {"issn": ["1234-0000"], "level_2026": 2}
            if failure == "wrong_issn":
                payload["issn"] = ["9999-9999"]
            elif failure == "invalid_level":
                payload["level_2026"] = "2"
            elif failure == "unconfirmed_level":
                payload["level_2026"] = 1
            return httpx.Response(200, json=payload)

        cache_file = tmp_path / "cache.json"
        metadata_file = tmp_path / "source_metadata.json"
        cache_file.write_text('{"0028-0836": 1}', encoding="utf-8")
        metadata_file.write_text('{"white_list":{"retrieved_at":"old"}}', encoding="utf-8")
        original_cache = cache_file.read_bytes()
        original_metadata = metadata_file.read_bytes()
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with patch("app.services.white_list.CACHE_PATH", cache_file):
                with pytest.raises((ValueError, httpx.HTTPStatusError)):
                    await refresh_white_list_cache(client)
        assert cache_file.read_bytes() == original_cache
        assert metadata_file.read_bytes() == original_metadata

    async def test_metadata_write_failure_still_returns_installed_data(self, tmp_path, caplog):
        records = self._complete_records()
        cache_file = tmp_path / "cache.json"
        metadata_file = tmp_path / "source_metadata.json"
        metadata_file.write_text('{"white_list":{"retrieved_at":"old"}}', encoding="utf-8")
        original_metadata = metadata_file.read_bytes()
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=records)
        )) as client:
            with patch("app.services.white_list.CACHE_PATH", cache_file), \
                 patch("app.services.white_list._save_refresh_metadata", side_effect=PermissionError("read-only")):
                cache = await refresh_white_list_cache(client)
        assert len(cache) == 1000
        assert json.loads(cache_file.read_text()) == cache
        assert metadata_file.read_bytes() == original_metadata
        assert "cache updated, but freshness metadata could not be saved" in caplog.text

    def test_metadata_updates_hashes_and_retains_other_sources(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        metadata_file = tmp_path / "source_metadata.json"
        metadata_file.write_text(json.dumps({
            "white_list": {"download_sha256": "old", "data_sha256": "old"},
            "scopus": {"version": "Август 2026"},
        }), encoding="utf-8")
        records = [{"issns": ["0028-0836"], "level_2026": 1}]
        cache = {"0028-0836": 1}
        source = json.dumps(records).encode()
        with patch("app.services.white_list.CACHE_PATH", cache_file):
            _save_cache(cache)
            _save_refresh_metadata(records, cache, source_bytes=source)
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        assert metadata["white_list"]["download_sha256"] == hashlib.sha256(source).hexdigest()
        assert metadata["white_list"]["data_sha256"] == hashlib.sha256(cache_file.read_bytes()).hexdigest()
        assert metadata["scopus"]["version"] == "Август 2026"

    async def test_truncated_export_does_not_overwrite_cache(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text('{"0028-0836": 1}', encoding="utf-8")
        client = AsyncMock()
        response = MagicMock()
        response.json.return_value = [{"issns": ["0028-0836"], "level_2026": 2}]
        client.get.return_value = response
        with patch("app.services.white_list.CACHE_PATH", cache_file):
            with pytest.raises(ValueError, match="unexpectedly small"):
                await refresh_white_list_cache(client)
        assert json.loads(cache_file.read_text()) == {"0028-0836": 1}

    async def test_explicit_refresh_failure_is_not_reported_as_success(self):
        session = AsyncMock()
        with patch("app.services.white_list._load_cache", return_value={"0028-0836": 1}), \
             patch("app.services.white_list.refresh_white_list_cache", side_effect=RuntimeError("unavailable")):
            with pytest.raises(RuntimeError, match="unavailable"):
                await update_white_list_levels(session, refresh=True)
        session.execute.assert_not_awaited()

    async def test_scheduled_network_failure_keeps_last_good_levels(self):
        session = AsyncMock()
        cache = {"0028-0836": 1}
        with patch("app.services.white_list._load_cache", return_value=cache), \
             patch("app.services.white_list.refresh_white_list_cache", side_effect=RuntimeError("unavailable")), \
             patch("app.services.white_list._apply_cache", new_callable=AsyncMock, return_value=0) as apply:
            await update_white_list_levels(session, refresh=True, allow_cached_fallback=True)
        apply.assert_awaited_once_with(session, cache)

    async def test_applies_to_new_issns_and_clears_excluded_or_missing(self):
        session = AsyncMock()
        select_result = MagicMock()
        select_result.all.return_value = [("00280836",), ("1063-7850",), ("9999-9999",)]
        session.execute.side_effect = [select_result] + [MagicMock(rowcount=1) for _ in range(3)]
        changed = await _apply_cache(session, {"0028-0836": 1, "1063-7850": None})
        assert changed == 3
        params = [call.args[0].compile().params for call in session.execute.await_args_list[1:]]
        assert [p["white_list_level"] for p in params] == [1, None, None]
        session.commit.assert_awaited_once()
