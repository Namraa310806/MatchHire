"""Base scraper abstraction for job ingestion."""

from abc import ABC, abstractmethod
from typing import Any

from .record import JobRecord


class BaseJobScraper(ABC):
    """Abstract base class for job scrapers.

    Scrapers implement fetch, parse, and validate operations for specific
    job sources (company career pages, ATS, APIs, etc.).

    Scrapers must:
    - Never perform real network requests in tests (use FakeScraper)
    - Return normalized JobRecord instances from parse()
    - Implement validation in validate()
    - Handle errors gracefully and return clear error messages

    Parsing error reporting:
    - Scrapers should use record_parse_error() to report parsing failures
    - Each parse() invocation should start with _clear_parse_errors()
    - The pipeline consumes parse_errors after each batch
    - Errors include the original raw record for attribution
    """

    def __init__(self) -> None:
        """Initialize scraper with empty parse errors collection."""
        self.parse_errors: list[tuple[dict[str, Any], str]] = []

    def _clear_parse_errors(self) -> None:
        """Clear previous parse errors before a new parse invocation."""
        self.parse_errors = []

    def _record_parse_error(self, raw_record: dict[str, Any], error_msg: str) -> None:
        """Record a parsing error with attribution to the raw record.

        Args:
            raw_record: The raw job data that failed to parse
            error_msg: Description of the parsing error
        """
        self.parse_errors.append((raw_record, error_msg))

    @abstractmethod
    def fetch(self, url: str) -> list[dict[str, Any]]:
        """Fetch raw job data from a source URL.

        Args:
            url: The source URL to fetch from

        Returns:
            List of raw job data dictionaries (source-specific format)

        Raises:
            Exception: Network errors, parsing errors, or source errors
        """

    @abstractmethod
    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse raw job data into normalized JobRecords.

        Args:
            raw: List of raw job data dictionaries from fetch()

        Returns:
            List of normalized JobRecord instances

        Raises:
            ValueError: If required fields are missing or invalid

        Note:
            Implementations should call _clear_parse_errors() at the start
            and use _record_parse_error() for individual record failures.
        """

    @abstractmethod
    def validate(self, job: JobRecord) -> bool:
        """Validate a parsed JobRecord.

        Args:
            job: The JobRecord to validate

        Returns:
            True if valid, False otherwise

        Note:
            Validation should check business rules, not just data types.
            The ingestion pipeline will handle validation error reporting.
        """
