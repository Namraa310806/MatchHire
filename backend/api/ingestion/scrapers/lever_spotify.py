"""Lever ATS scraper for Spotify jobs."""

from datetime import datetime
from typing import Any, Literal

import requests

from ..base_scraper import BaseJobScraper
from ..record import JobRecord


class LeverSpotifyScraper(BaseJobScraper):
    """Scraper for Spotify jobs hosted on Lever ATS.

    Endpoint: https://api.lever.co/v0/postings/spotify?mode=json
    No authentication required.
    robots.txt allows access with crawl-delay: 1

    Note: Response is a bare JSON array, not an object with 'jobs' key.
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

    def fetch(self, url: str) -> list[dict[str, Any]]:
        """Fetch raw job data from Lever API.

        Args:
            url: The source URL (expected to be Spotify's Lever endpoint)

        Returns:
            List of raw job data dictionaries

        Raises:
            requests.RequestException: Network or HTTP errors
            ValueError: Invalid JSON response
        """
        # Ensure URL has mode=json parameter
        if "mode=json" not in url:
            url = f"{url}?mode=json" if "?" not in url else f"{url}&mode=json"

        try:
            response = self.session.get(url, timeout=(10, 30))
            response.raise_for_status()

            data = response.json()

            # Lever returns a bare JSON array, not an object
            if not isinstance(data, list):
                raise ValueError("Response is not a JSON array")

            return data

        except requests.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e

    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse raw Lever job data into JobRecords.

        Args:
            raw: List of raw job data from fetch()

        Returns:
            List of JobRecord instances

        Note:
            createdAt is Unix timestamp in milliseconds.
            descriptionPlain contains plain-text description.
            categories object contains location, commitment, team, department.
        """
        self._clear_parse_errors()
        records = []

        for raw_job in raw:
            try:
                # Extract external_id (UUID string)
                external_id = raw_job.get("id")
                if not external_id:
                    self._record_parse_error(raw_job, "Missing id")
                    continue

                # Extract title
                title = raw_job.get("text", "")
                if not title:
                    self._record_parse_error(raw_job, "Missing title")
                    continue

                # Extract description (prefer descriptionPlain)
                description = raw_job.get("descriptionPlain", "")
                if not description:
                    # Fallback to descriptionBodyPlain or description
                    description = raw_job.get("descriptionBodyPlain", "")
                    if not description:
                        description = raw_job.get("description", "")
                        if not description:
                            self._record_parse_error(raw_job, "Missing description")
                            continue

                # Extract location from categories
                categories = raw_job.get("categories", {})
                location = categories.get("location")

                # Extract application URL
                application_url = raw_job.get("applyUrl")
                if not application_url:
                    self._record_parse_error(raw_job, "Missing application URL")
                    continue

                # Extract posted date (createdAt is Unix timestamp in milliseconds)
                posted_date = None
                created_at = raw_job.get("createdAt")
                if created_at:
                    try:
                        # Convert milliseconds to seconds
                        dt = datetime.fromtimestamp(created_at / 1000)
                        posted_date = dt.date()
                    except (ValueError, TypeError, OSError):
                        pass

                # Extract remote type from workplaceType
                workplace_type = raw_job.get("workplaceType", "").lower()
                remote_type: Literal["on-site", "remote", "hybrid"] | None = None
                if workplace_type == "remote":
                    remote_type = "remote"
                elif workplace_type == "hybrid":
                    remote_type = "hybrid"
                elif workplace_type == "onsite":
                    remote_type = "on-site"

                # Extract role type from commitment
                commitment = categories.get("commitment", "").lower()
                role_type: Literal["full-time", "internship", "contract"] | None = None
                if "permanent" in commitment or "full-time" in commitment:
                    role_type = "full-time"
                elif "contract" in commitment:
                    role_type = "contract"
                elif "intern" in commitment:
                    role_type = "internship"

                # Extract salary if available (salaryRange is optional)
                salary_min = None
                salary_max = None
                salary_currency = None
                salary_range = raw_job.get("salaryRange")
                if salary_range:
                    salary_min = salary_range.get("min")
                    salary_max = salary_range.get("max")
                    salary_currency = salary_range.get("currency", "USD")

                # Note: source_id and company_id will be set by the pipeline
                # based on the IngestionSource configuration
                records.append(
                    JobRecord(
                        source_id=0,  # Placeholder, set by pipeline
                        company_id=0,  # Placeholder, set by pipeline
                        external_id=external_id,
                        title=title,
                        description=description,
                        requirements=None,  # Lever doesn't separate requirements
                        location=location,
                        application_url=application_url,
                        posted_date=posted_date,
                        remote_type=remote_type,
                        role_type=role_type,
                        experience_min_years=None,
                        experience_max_years=None,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        salary_currency=salary_currency or "USD",
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
