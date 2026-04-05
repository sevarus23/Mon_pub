"""Unit tests for Scopus ISSN utility."""

import json
import pytest
from unittest.mock import patch, mock_open

from app.utils.scopus import get_scopus_issns


class TestGetScopusIssns:
    def setup_method(self):
        """Reset global cache before each test."""
        import app.utils.scopus as mod
        mod._scopus_issns = None

    def test_returns_set(self):
        with patch("app.utils.scopus.SCOPUS_FILE") as mock_path:
            mock_path.exists.return_value = True
            data = json.dumps(["0028-0836", "0036-8075", "1234-5678"])
            with patch("builtins.open", mock_open(read_data=data)):
                result = get_scopus_issns()
        assert isinstance(result, set)
        assert len(result) == 3
        assert "0028-0836" in result

    def test_caches_result(self):
        with patch("app.utils.scopus.SCOPUS_FILE") as mock_path:
            mock_path.exists.return_value = True
            data = json.dumps(["0028-0836"])
            with patch("builtins.open", mock_open(read_data=data)):
                result1 = get_scopus_issns()
                result2 = get_scopus_issns()
        assert result1 is result2

    def test_missing_file_returns_empty(self):
        with patch("app.utils.scopus.SCOPUS_FILE") as mock_path:
            mock_path.exists.return_value = False
            result = get_scopus_issns()
        assert result == set()
