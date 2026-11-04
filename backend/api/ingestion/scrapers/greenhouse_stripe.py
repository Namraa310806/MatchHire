"""Greenhouse ATS scraper for Stripe jobs."""

from datetime import datetime
from html import unescape
from typing import Any, Literal, cast

import requests

from ..base_scraper import BaseJobScraper
from ..record import JobRecord


class GreenhouseStripeScraper(BaseJobScraper):
    """Scraper for Stripe jobs hosted on Greenhouse ATS.

    Endpoint: https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true
    No authentication required.
    robots.txt allows access (only /embed/ is disallowed).
    """

    def __init__(self) -> None:
        """Initialize scraper with HTTP client configuration."""
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "MatchHire-Ingestion/1.0 (+https://github.com/Namraa310806/MatchHire)"
            }
        )

    def fetch(self, url: str) -> list[dict[str, Any]]:  # type: ignore[no-any-return]
        """Fetch raw job data from Greenhouse API.

        Args:
            url: The source URL (expected to be Stripe's Greenhouse endpoint)

        Returns:
            List of raw job data dictionaries

        Raises:
            requests.RequestException: Network or HTTP errors
            ValueError: Invalid JSON response
        """
        # Ensure URL has content=true parameter
        if "content=true" not in url:
            url = f"{url}?content=true" if "?" not in url else f"{url}&content=true"

        try:
            response = self.session.get(url, timeout=(10, 30))
            response.raise_for_status()

            data: dict[str, Any] = response.json()

            # Greenhouse returns {"jobs": [...], "meta": {...}}
            if "jobs" not in data:
                raise ValueError("Response missing 'jobs' field")

            return cast(list[dict[str, Any]], data["jobs"])

        except requests.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e

    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse raw Greenhouse job data into JobRecords.

        Args:
            raw: List of raw job data from fetch()

        Returns:
            List of JobRecord instances

        Note:
            HTML content is double-escaped and requires unescape() twice.
            Location may contain multiple locations separated by commas.
        """
        self._clear_parse_errors()
        records = []

        for raw_job in raw:
            try:
                # Extract and decode external_id (numeric)
                external_id = str(raw_job.get("id", ""))

                # Extract and unescape title
                title = unescape(raw_job.get("title", ""))
                if not title:
                    self._record_parse_error(raw_job, "Missing title")
                    continue

                # Extract and double-unescape HTML content
                content = raw_job.get("content", "")
                description = unescape(unescape(content)) if content else ""
                if not description:
                    self._record_parse_error(raw_job, "Missing description")
                    continue

                # Extract location (may be comma-separated)
                location = raw_job.get("location", {}).get("name")
                if location:
                    # Take first location if multiple are comma-separated
                    location = location.split(",")[0].strip()

                # Extract application URL
                application_url = raw_job.get("absolute_url")
                if not application_url:
                    self._record_parse_error(raw_job, "Missing application URL")
                    continue

                # Extract posted date (first_published or updated_at)
                posted_date = None
                for date_field in ["first_published", "updated_at"]:
                    date_str = raw_job.get(date_field)
                    if date_str:
                        try:
                            # Parse ISO 8601 format (e.g., "2026-09-09T10:50:29-04:00")
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            posted_date = dt.date()
                            break
                        except (ValueError, AttributeError):
                            continue

                # Determine remote type from location name
                remote_type: Literal["on-site", "remote", "hybrid"] | None = None
                if location:
                    location_lower = location.lower()
                    if "remote" in location_lower:
                        remote_type = "remote"
                    elif "hybrid" in location_lower:
                        remote_type = "hybrid"
                    else:
                        remote_type = "on-site"

                # Note: source_id and company_id will be set by the pipeline
                # based on the IngestionSource configuration
                records.append(
                    JobRecord(
                        source_id=0,  # Placeholder, set by pipeline
                        company_id=0,  # Placeholder, set by pipeline
                        external_id=external_id,
                        title=title,
                        description=description,
                        requirements=None,  # Greenhouse doesn't separate requirements
                        location=location,
                        application_url=application_url,
                        posted_date=posted_date,
                        remote_type=remote_type,
                        role_type=None,  # Not available in Greenhouse response
                        experience_min_years=None,
                        experience_max_years=None,
                        salary_min=None,
                        salary_max=None,
                        salary_currency="USD",  # Stripe is US-based
                        skills=[],  # Will be extracted by pipeline
                        required_yoe=None,  # Will be extracted by pipeline
                    )
                )

            except Exception as e:
                self._record_parse_error(raw_job, f"Parse error: {str(e)}")

        return records

    def validate(self, job: JobRecord) -> bool:
        """Validate a parsed JobRecord.

        Args:
            job: The JobRecord to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - pipeline will do comprehensive validation
        if not job.title or not job.title.strip():
            return False
        if not job.description or not job.description.strip():
            return False
        if not job.application_url or not job.application_url.strip():
            return False

        return True
