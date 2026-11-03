"""Fake scraper for testing ingestion pipeline."""

from datetime import date
from typing import Any

from .base_scraper import BaseJobScraper
from .record import JobRecord


class FakeScraper(BaseJobScraper):
    """Fake scraper for testing with in-memory fixtures.

    This scraper uses pre-defined fixtures and never performs real network requests.
    It is registered only for tests and should not be used in production.

    The scraper accepts a list of fixture job dictionaries and returns them
    from fetch(), then parses them into JobRecord instances.
    """

    def __init__(self, fixtures: list[dict[str, Any]] | None = None) -> None:
        """Initialize with optional fixtures.

        Args:
            fixtures: List of job data dictionaries to return from fetch()
        """
        super().__init__()
        self.fixtures = fixtures or []

    def fetch(self, url: str) -> list[dict[str, Any]]:
        """Return fixtures (ignores URL)."""
        return self.fixtures

    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse raw fixture data into JobRecords.

        Expected raw format for each record:
        {
            "source_id": int,
            "company_id": int,
            "external_id": str | None,
            "title": str,
            "description": str,
            "requirements": str | None,
            "location": str | None,
            "application_url": str,
            "posted_date": str | None (YYYY-MM-DD),
            "remote_type": str | None,
            "role_type": str | None,
            "experience_min_years": float | None,
            "experience_max_years": float | None,
            "salary_min": float | None,
            "salary_max": float | None,
            "salary_currency": str,
            "skills": list[str],
            "required_yoe": float | None,
        }

        Returns:
            List of JobRecord instances, one per successfully parsed input dictionary.
            Malformed records are skipped and errors are stored in self.parse_errors.
        """
        self._clear_parse_errors()
        records = []

        for raw_record in raw:
            try:
                posted_date = None
                if raw_record.get("posted_date"):
                    posted_date = date.fromisoformat(raw_record["posted_date"])

                records.append(
                    JobRecord(
                        source_id=raw_record["source_id"],
                        company_id=raw_record["company_id"],
                        external_id=raw_record.get("external_id"),
                        title=raw_record["title"],
                        description=raw_record["description"],
                        requirements=raw_record.get("requirements"),
                        location=raw_record.get("location"),
                        application_url=raw_record["application_url"],
                        posted_date=posted_date,
                        remote_type=raw_record.get("remote_type"),
                        role_type=raw_record.get("role_type"),
                        experience_min_years=raw_record.get("experience_min_years"),
                        experience_max_years=raw_record.get("experience_max_years"),
                        salary_min=raw_record.get("salary_min"),
                        salary_max=raw_record.get("salary_max"),
                        salary_currency=raw_record.get("salary_currency", "INR"),
                        skills=raw_record.get("skills", []),
                        required_yoe=raw_record.get("required_yoe"),
                    )
                )
            except Exception as e:
                # Store error with raw record for attribution
                self._record_parse_error(raw_record, str(e))

        return records

    def validate(self, job: JobRecord) -> bool:
        """Validate JobRecord.

        Checks:
        - Title is not empty
        - Description is not empty
        - Application URL is not empty
        - Source ID and company ID are positive

        Returns:
            True if valid, False otherwise
        """
        if not job.title or not job.title.strip():
            return False
        if not job.description or not job.description.strip():
            return False
        if not job.application_url or not job.application_url.strip():
            return False
        if job.source_id <= 0:
            return False
        if job.company_id <= 0:
            return False

        return True
