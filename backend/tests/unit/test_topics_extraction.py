"""Unit tests for topics extraction from OpenAlex and CrossRef responses."""

import pytest


class TestOpenAlexTopicsExtraction:
    """Test topics extraction logic used in openalex.py."""

    def _extract_topics(self, work: dict) -> list[str]:
        """Replicate the extraction logic from openalex.py."""
        raw_topics = work.get("topics", [])
        topics = [t["display_name"] for t in raw_topics[:10] if t.get("display_name")]
        if not topics:
            concepts = work.get("concepts", [])
            topics = [c["display_name"] for c in concepts[:10]
                      if c.get("display_name") and c.get("score", 0) > 0.3]
        return topics

    def test_topics_from_topics_field(self):
        work = {
            "topics": [
                {"display_name": "Artificial Intelligence", "id": "t1"},
                {"display_name": "Machine Learning", "id": "t2"},
            ]
        }
        result = self._extract_topics(work)
        assert result == ["Artificial Intelligence", "Machine Learning"]

    def test_fallback_to_concepts(self):
        work = {
            "topics": [],
            "concepts": [
                {"display_name": "Computer Science", "score": 0.9},
                {"display_name": "Engineering", "score": 0.5},
            ]
        }
        result = self._extract_topics(work)
        assert result == ["Computer Science", "Engineering"]

    def test_concepts_filtered_by_score(self):
        work = {
            "topics": [],
            "concepts": [
                {"display_name": "AI", "score": 0.8},
                {"display_name": "Low Score Topic", "score": 0.2},
            ]
        }
        result = self._extract_topics(work)
        assert result == ["AI"]
        assert "Low Score Topic" not in result

    def test_max_10_topics(self):
        work = {
            "topics": [{"display_name": f"Topic {i}"} for i in range(15)]
        }
        result = self._extract_topics(work)
        assert len(result) == 10

    def test_empty_work(self):
        result = self._extract_topics({})
        assert result == []

    def test_topics_without_display_name_skipped(self):
        work = {
            "topics": [
                {"display_name": "Valid"},
                {"id": "no-name"},
                {"display_name": ""},
            ]
        }
        result = self._extract_topics(work)
        assert result == ["Valid"]

    def test_topics_preferred_over_concepts(self):
        work = {
            "topics": [{"display_name": "From Topics"}],
            "concepts": [{"display_name": "From Concepts", "score": 0.9}],
        }
        result = self._extract_topics(work)
        assert result == ["From Topics"]


class TestCrossRefTopicsExtraction:
    """Test topics extraction logic used in crossref.py."""

    def test_subject_field_extracted(self):
        item = {"subject": ["Computer Science", "Mathematics", "AI"]}
        topics = item.get("subject", [])[:10]
        assert topics == ["Computer Science", "Mathematics", "AI"]

    def test_max_10_subjects(self):
        item = {"subject": [f"Subject {i}" for i in range(15)]}
        topics = item.get("subject", [])[:10]
        assert len(topics) == 10

    def test_no_subject_field(self):
        item = {"title": ["Test"]}
        topics = item.get("subject", [])[:10]
        assert topics == []

    def test_empty_subject_list(self):
        item = {"subject": []}
        topics = item.get("subject", [])[:10]
        assert topics == []
