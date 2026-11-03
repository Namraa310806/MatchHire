"""Job record data structure for ingestion pipeline."""

from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass
class JobRecord:
    """Normalized job record from a scraper.

    This represents a job listing after parsing but before database persistence.
    All fields are normalized (trimmed, HTML entities decoded, etc.).

    Source Identity:
        source_id: The IngestionSource database ID (foreign key)
        company_id: The Company database ID (foreign key)
        external_id: Source-specific job identifier (nullable, for deduplication)

    Core Job Fields:
        title: Job title
        description: Job description (HTML cleaned)
        requirements: Job requirements (optional, HTML cleaned)
        location: Job location
        application_url: External application URL (required, fallback identity)
        posted_date: Original posting date from source (optional)

    Job Metadata:
        remote_type: 'on-site', 'remote', 'hybrid', or None
        role_type: 'full-time', 'internship', 'contract', or None
        experience_min_years: Minimum experience required (nullable)
        experience_max_years: Maximum experience in range (nullable)
        salary_min: Minimum salary (nullable)
        salary_max: Maximum salary (nullable)
        salary_currency: Currency code (default 'INR')

    Extracted Fields:
        skills: List of skill names extracted from description
        required_yoe: Extracted years of experience requirement (nullable)
    """

    # Source identity
    source_id: int
    company_id: int
    external_id: str | None

    # Core job fields
    title: str
    description: str
    requirements: str | None
    location: str | None
    application_url: str
    posted_date: date | None

    # Job metadata
    remote_type: Literal["on-site", "remote", "hybrid"] | None
    role_type: Literal["full-time", "internship", "contract"] | None
    experience_min_years: float | None
    experience_max_years: float | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str

    # Extracted fields
    skills: list[str]
    required_yoe: float | None
