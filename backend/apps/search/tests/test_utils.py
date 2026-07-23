"""
Tests for search utility functions.
"""

import pytest
from datetime import datetime

from apps.search.utils.helpers import (
    sanitize_query,
    normalize_filters,
    extract_field_boosts,
    calculate_score_normalization,
    merge_results,
    format_highlight,
    truncate_text,
    parse_date_range,
    validate_pagination,
)


class TestSanitizeQuery:
    """Test query sanitization."""

    def test_basic_query(self):
        """Test basic query sanitization."""
        query = "software engineer"
        result = sanitize_query(query)
        assert result == "software engineer"

    def test_query_with_leading_trailing_spaces(self):
        """Test query with leading/trailing spaces."""
        query = "  software engineer  "
        result = sanitize_query(query)
        assert result == "software engineer"

    def test_empty_query(self):
        """Test empty query."""
        query = ""
        result = sanitize_query(query)
        assert result == ""

    def test_none_query(self):
        """Test None query."""
        query = None
        result = sanitize_query(query)
        assert result == ""


class TestNormalizeFilters:
    """Test filter normalization."""

    def test_basic_filters(self):
        """Test basic filter normalization."""
        filters = {"status": "active", "salary": 50000}
        result = normalize_filters(filters)
        assert result == filters

    def test_remove_none_values(self):
        """Test removing None values."""
        filters = {"status": "active", "salary": None}
        result = normalize_filters(filters)
        assert result == {"status": "active"}

    def test_remove_empty_strings(self):
        """Test removing empty strings."""
        filters = {"status": "active", "title": ""}
        result = normalize_filters(filters)
        assert result == {"status": "active"}

    def test_remove_empty_lists(self):
        """Test removing empty lists."""
        filters = {"status": "active", "skills": []}
        result = normalize_filters(filters)
        assert result == {"status": "active"}


class TestExtractFieldBoosts:
    """Test field boost extraction."""

    def test_extract_boosts(self):
        """Test extracting field boosts."""
        query = "title^2 content^1.5 description"
        cleaned, boosts = extract_field_boosts(query)
        assert cleaned == "title content description"
        assert boosts == {"title": 2.0, "content": 1.5}

    def test_no_boosts(self):
        """Test query without boosts."""
        query = "software engineer"
        cleaned, boosts = extract_field_boosts(query)
        assert cleaned == "software engineer"
        assert boosts == {}

    def test_invalid_boost(self):
        """Test query with invalid boost syntax."""
        query = "title^invalid content"
        cleaned, boosts = extract_field_boosts(query)
        assert "title^invalid" in cleaned
        assert boosts == {}


class TestCalculateScoreNormalization:
    """Test score normalization."""

    def test_basic_normalization(self):
        """Test basic score normalization."""
        scores = [0.5, 0.75, 1.0]
        result = calculate_score_normalization(scores)
        assert len(result) == 3
        assert result[0] == 0.0
        assert result[-1] == 1.0

    def test_empty_scores(self):
        """Test empty scores."""
        scores = []
        result = calculate_score_normalization(scores)
        assert result == []

    def test_identical_scores(self):
        """Test identical scores."""
        scores = [0.5, 0.5, 0.5]
        result = calculate_score_normalization(scores)
        assert all(s == 0.5 for s in result)


class TestMergeResults:
    """Test result merging."""

    def test_basic_merge(self):
        """Test basic result merging."""
        result_sets = [
            [{"id": "1", "score": 0.8}, {"id": "2", "score": 0.6}],
            [{"id": "3", "score": 0.7}],
        ]
        result = merge_results(result_sets)
        assert len(result) == 3

    def test_merge_with_weights(self):
        """Test merging with weights."""
        result_sets = [
            [{"id": "1", "score": 0.8}],
            [{"id": "1", "score": 0.6}],
        ]
        scores = [0.7, 0.3]
        result = merge_results(result_sets, scores)
        assert len(result) == 1
        assert "merged_score" in result[0]

    def test_deduplication(self):
        """Test result deduplication."""
        result_sets = [
            [{"id": "1", "score": 0.8}],
            [{"id": "1", "score": 0.6}],
        ]
        result = merge_results(result_sets)
        assert len(result) == 1

    def test_empty_merge(self):
        """Test merging empty result sets."""
        result = merge_results([])
        assert result == []

    def test_mismatched_scores_length(self):
        """Test mismatched scores and result sets length."""
        result_sets = [[{"id": "1", "score": 0.8}]]
        scores = [0.5, 0.5]
        with pytest.raises(ValueError):
            merge_results(result_sets, scores)


class TestFormatHighlight:
    """Test highlight formatting."""

    def test_basic_highlight(self):
        """Test basic highlight formatting."""
        text = "software engineer position"
        highlights = ["engineer"]
        result = format_highlight(text, highlights)
        assert "<em>engineer</em>" in result

    def test_multiple_highlights(self):
        """Test multiple highlights."""
        text = "software engineer position"
        highlights = ["software", "engineer"]
        result = format_highlight(text, highlights)
        assert "<em>software</em>" in result
        assert "<em>engineer</em>" in result

    def test_no_highlights(self):
        """Test no highlights."""
        text = "software engineer"
        highlights = []
        result = format_highlight(text, highlights)
        assert result == text

    def test_custom_tag(self):
        """Test custom highlight tag."""
        text = "software engineer"
        highlights = ["engineer"]
        result = format_highlight(text, highlights, tag="strong")
        assert "<strong>engineer</strong>" in result


class TestTruncateText:
    """Test text truncation."""

    def test_basic_truncation(self):
        """Test basic text truncation."""
        text = "This is a long text that should be truncated"
        result = truncate_text(text, max_length=20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_short_text(self):
        """Test text shorter than max length."""
        text = "Short text"
        result = truncate_text(text, max_length=50)
        assert result == "Short text"

    def test_empty_text(self):
        """Test empty text."""
        text = ""
        result = truncate_text(text, max_length=20)
        assert result == ""

    def test_custom_suffix(self):
        """Test custom suffix."""
        text = "This is a long text that should be truncated"
        result = truncate_text(text, max_length=20, suffix=" [more]")
        assert result.endswith(" [more]")


class TestParseDateRange:
    """Test date range parsing."""

    def test_valid_range(self):
        """Test valid date range."""
        date_str = "2023-01-01..2023-12-31"
        result = parse_date_range(date_str)
        assert result is not None
        assert "gte" in result
        assert "lte" in result
        assert isinstance(result["gte"], datetime)
        assert isinstance(result["lte"], datetime)

    def test_invalid_range(self):
        """Test invalid date range."""
        date_str = "invalid"
        result = parse_date_range(date_str)
        assert result is None

    def test_no_separator(self):
        """Test date range without separator."""
        date_str = "2023-01-01"
        result = parse_date_range(date_str)
        assert result is None


class TestValidatePagination:
    """Test pagination validation."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        page, page_size = validate_pagination(2, 20)
        assert page == 2
        assert page_size == 20

    def test_invalid_page(self):
        """Test invalid page number."""
        page, page_size = validate_pagination(0, 20)
        assert page == 1  # Clamped to 1

    def test_invalid_page_size(self):
        """Test invalid page size."""
        page, page_size = validate_pagination(2, 0)
        assert page_size == 1  # Clamped to 1

    def test_page_size_exceeds_max(self):
        """Test page size exceeding maximum."""
        page, page_size = validate_pagination(2, 150, max_page_size=100)
        assert page_size == 100  # Clamped to max

    def test_custom_max_page_size(self):
        """Test custom max page size."""
        page, page_size = validate_pagination(2, 50, max_page_size=30)
        assert page_size == 30
