"""
Search utility functions.

This module provides helper functions for common search operations.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


def sanitize_query(query: str) -> str:
    """
    Sanitize a search query string.

    Args:
        query: Raw query string

    Returns:
        Sanitized query string
    """
    if not query:
        return ""

    # Remove potentially dangerous characters
    # This is a basic implementation; enhance based on requirements
    query = query.strip()
    # Remove control characters
    query = "".join(char for char in query if ord(char) >= 32 or char in "\n\r\t")
    return query


def normalize_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize filter values to a consistent format.

    Args:
        filters: Raw filter dictionary

    Returns:
        Normalized filter dictionary
    """
    normalized = {}

    for key, value in filters.items():
        if value is None:
            continue

        # Handle empty strings
        if isinstance(value, str) and not value.strip():
            continue

        # Handle empty lists
        if isinstance(value, (list, tuple)) and not value:
            continue

        normalized[key] = value

    return normalized


def extract_field_boosts(query: str) -> tuple[str, Dict[str, float]]:
    """
    Extract field boost specifications from a query string.

    Args:
        query: Query string that may contain boost syntax (e.g., "title^2 content")

    Returns:
        Tuple of (cleaned_query, boosts_dict)
    """
    boosts = {}
    cleaned_parts = []

    parts = query.split()
    for part in parts:
        if "^" in part:
            field, boost_str = part.split("^", 1)
            try:
                boost = float(boost_str)
                boosts[field] = boost
            except ValueError:
                cleaned_parts.append(part)
        else:
            cleaned_parts.append(part)

    cleaned_query = " ".join(cleaned_parts)
    return cleaned_query, boosts


def calculate_score_normalization(scores: List[float]) -> List[float]:
    """
    Normalize scores to a 0-1 range.

    Args:
        scores: List of raw scores

    Returns:
        List of normalized scores
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return [0.5] * len(scores)

    normalized = []
    for score in scores:
        normalized_score = (score - min_score) / (max_score - min_score)
        normalized.append(normalized_score)

    return normalized


def merge_results(
    result_sets: List[List[Dict[str, Any]]],
    scores: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Merge multiple result sets with optional score weighting.

    Args:
        result_sets: List of result sets to merge
        scores: Optional weights for each result set

    Returns:
        Merged and deduplicated results
    """
    if not result_sets:
        return []

    if scores is None:
        scores = [1.0] * len(result_sets)

    if len(result_sets) != len(scores):
        raise ValueError("Number of result sets must match number of scores")

    # Use a dict to deduplicate by ID
    merged = {}

    for result_set, weight in zip(result_sets, scores):
        for result in result_set:
            result_id = result.get("id") or str(result)
            if result_id not in merged:
                merged[result_id] = result.copy()
                merged[result_id]["merged_score"] = result.get("score", 0) * weight
            else:
                # Add weighted score
                merged[result_id]["merged_score"] += result.get("score", 0) * weight

    # Sort by merged score
    sorted_results = sorted(
        merged.values(),
        key=lambda x: x.get("merged_score", 0),
        reverse=True,
    )

    return sorted_results


def format_highlight(
    text: str,
    highlights: List[str],
    tag: str = "em",
) -> str:
    """
    Apply highlight tags to text based on highlight fragments.

    Args:
        text: Original text
        highlights: List of highlight fragments
        tag: HTML tag to use for highlighting

    Returns:
        Text with highlight tags applied
    """
    if not highlights:
        return text

    highlighted_text = text
    for fragment in highlights:
        if fragment in highlighted_text:
            highlighted_text = highlighted_text.replace(
                fragment,
                f"<{tag}>{fragment}</{tag}>",
            )

    return highlighted_text


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length].rsplit(" ", 1)[0] + suffix


def parse_date_range(
    date_str: str,
) -> Optional[Dict[str, datetime]]:
    """
    Parse a date range string into a dictionary.

    Args:
        date_str: Date range string (e.g., "2023-01-01..2023-12-31")

    Returns:
        Dictionary with 'gte' and 'lte' datetime objects, or None
    """
    if ".." not in date_str:
        return None

    try:
        start_str, end_str = date_str.split("..", 1)
        start_date = datetime.fromisoformat(start_str.strip())
        end_date = datetime.fromisoformat(end_str.strip())
        return {"gte": start_date, "lte": end_date}
    except (ValueError, AttributeError):
        return None


def validate_pagination(
    page: int,
    page_size: int,
    max_page_size: int = 100,
) -> tuple[int, int]:
    """
    Validate and clamp pagination parameters.

    Args:
        page: Page number
        page_size: Page size
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)
    """
    validated_page = max(1, page)
    validated_page_size = max(1, min(page_size, max_page_size))
    return validated_page, validated_page_size
