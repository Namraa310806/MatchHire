"""Utility functions for resume parsing."""

import re


def normalize_resume_text(text: str) -> str:
    """
    Normalize resume text by cleaning whitespace and formatting.

    Args:
        text: Raw text extracted from resume

    Returns:
        Normalized text with:
        - Normalized whitespace
        - Collapsed repeated blank lines
        - Trimmed leading/trailing whitespace
    """
    if not text:
        return ""

    # Normalize whitespace (tabs, multiple spaces to single space)
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse repeated blank lines (more than 2 newlines to 2 newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim leading and trailing whitespace
    text = text.strip()

    return text
