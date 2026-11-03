"""Normalization functions for job records."""

import re
from html import unescape

from .record import JobRecord

# Maximum description length (from schema considerations)
MAX_DESCRIPTION_LENGTH = 50000


def normalize_job_record(record: JobRecord) -> JobRecord:
    """Normalize a JobRecord.

    Performs:
    - HTML entity decoding
    - HTML tag removal (basic)
    - Leading/trailing whitespace trimming
    - Empty field handling
    - Case normalization for titles and locations
    - URL validation
    - Description length check

    Args:
        record: The JobRecord to normalize

    Returns:
        A new JobRecord with normalized fields

    Raises:
        ValueError: If record fails validation (e.g., URL too long, description too large)
    """
    # Normalize title
    title = _normalize_text(record.title)
    if not title:
        raise ValueError("Title cannot be empty after normalization")

    # Normalize description
    description = _normalize_text(record.description)
    if not description:
        raise ValueError("Description cannot be empty after normalization")

    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Description too long: {len(description)} characters "
            f"(max {MAX_DESCRIPTION_LENGTH})"
        )

    # Normalize requirements (optional)
    requirements = None
    if record.requirements:
        requirements = _normalize_text(record.requirements)

    # Normalize location (optional)
    location = None
    if record.location:
        location = _normalize_text(record.location)
        # Title case for location (e.g., "bangalore" -> "Bangalore")
        if location:
            location = location.title()

    # Validate and normalize URL
    application_url = _normalize_url(record.application_url)
    if not application_url:
        raise ValueError("Application URL cannot be empty")

    # Normalize external_id (optional)
    external_id = None
    if record.external_id:
        external_id = _normalize_text(record.external_id)

    # Normalize skills (trim each, remove duplicates)
    skills = [_normalize_text(skill) for skill in record.skills if skill]
    skills = list(dict.fromkeys(skills))  # Remove duplicates while preserving order

    return JobRecord(
        source_id=record.source_id,
        company_id=record.company_id,
        external_id=external_id,
        title=title,
        description=description,
        requirements=requirements,
        location=location,
        application_url=application_url,
        posted_date=record.posted_date,
        remote_type=record.remote_type,
        role_type=record.role_type,
        experience_min_years=record.experience_min_years,
        experience_max_years=record.experience_max_years,
        salary_min=record.salary_min,
        salary_max=record.salary_max,
        salary_currency=record.salary_currency,
        skills=skills,
        required_yoe=record.required_yoe,
    )


def _normalize_text(text: str) -> str:
    """Normalize text field.

    Performs:
    - HTML entity decoding
    - Basic HTML tag removal
    - Leading/trailing whitespace trimming
    - Collapse multiple whitespace

    Args:
        text: The text to normalize

    Returns:
        Normalized text
    """
    # Decode HTML entities
    text = unescape(text)

    # Remove HTML tags (basic - not a full parser)
    text = re.sub(r"<[^>]+>", " ", text)

    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text)

    # Trim
    text = text.strip()

    return text


def _normalize_url(url: str) -> str:
    """Normalize and validate URL.

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL

    Raises:
        ValueError: If URL is malformed
    """
    url = url.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url} (must start with http:// or https://)")

    # Length check (from schema: max_length=1000)
    if len(url) > 1000:
        raise ValueError(f"URL too long: {len(url)} characters (max 1000)")

    return url
