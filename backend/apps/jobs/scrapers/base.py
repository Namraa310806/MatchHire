"""
Base job scraper abstraction.

This module defines the contract and shared functionality for all company-specific scrapers.
Scrapers are responsible for:
- Fetching raw job data from official company sources
- Extracting job information from source-specific formats
- Normalizing to a common representation
- Preserving source identity for deduplication

Scrapers are NOT responsible for:
- Database persistence (handled by ingestion service)
- User authentication
- Matching logic
- Analytics
- Frontend behavior
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json


logger = logging.getLogger(__name__)


@dataclass
class NormalizedJob:
    """
    Common normalized job representation.
    
    This is the canonical output format for all scrapers.
    All company-specific scrapers must transform their source data
    into this format before passing to the ingestion service.
    
    Fields map directly to the Job model where possible.
    """
    # Source identity
    source: str  # Source identifier (e.g., 'nexus_technologies')
    external_id: str  # External job ID from the source system
    
    # Core job information
    title: str
    description: str
    
    # Optional fields (use None if not available from source)
    location: Optional[str] = None
    employment_type: Optional[str] = None  # Must match Job.EmploymentType choices
    experience_required: Optional[str] = None  # Text description
    
    # Structured experience for matching
    minimum_experience_years: Optional[Decimal] = None
    maximum_experience_years: Optional[Decimal] = None
    
    # Skills and keywords
    skills: List[str] = None  # List of normalized concrete skills
    keywords: List[str] = None  # List of normalized broader terms
    
    # URLs
    application_url: str = None  # Official application URL (required)
    source_url: Optional[str] = None  # Source listing URL if distinct
    
    # Raw data preservation
    raw_data: Dict[str, Any] = None  # Original source data for debugging
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.skills is None:
            self.skills = []
        if self.keywords is None:
            self.keywords = []
        if self.raw_data is None:
            self.raw_data = {}
    
    def generate_deduplication_hash(self) -> str:
        """
        Generate a deterministic hash for deduplication.
        
        The hash is based on the stable identity of the job:
        - source
        - external_id
        - title
        - application_url
        
        Volatile fields (timestamps, fetch order) are NOT included.
        """
        hash_input = f"{self.source}:{self.external_id}:{self.title}:{self.application_url}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def validate(self) -> List[str]:
        """
        Validate the normalized job.
        
        Returns a list of validation error messages.
        Empty list means valid.
        """
        errors = []
        
        if not self.title or not self.title.strip():
            errors.append("Title is required")
        
        if not self.description or not self.description.strip():
            errors.append("Description is required")
        
        if not self.external_id or not self.external_id.strip():
            errors.append("External ID is required")
        
        if not self.application_url or not self.application_url.strip():
            errors.append("Application URL is required")
        
        if not self.source or not self.source.strip():
            errors.append("Source is required")
        
        # Validate experience range if both values are provided
        if (self.minimum_experience_years is not None and 
            self.maximum_experience_years is not None):
            if self.minimum_experience_years > self.maximum_experience_years:
                errors.append("Minimum experience years cannot exceed maximum experience years")
        
        return errors


class BaseJobScraper(ABC):
    """
    Abstract base class for company-specific job scrapers.
    
    Each concrete scraper must implement:
    - get_source_identifier(): Return a unique source identifier
    - fetch(): Retrieve raw data from the source
    - extract(): Parse raw data into structured job records
    - normalize(): Transform structured records into NormalizedJob objects
    
    The scraper should NOT:
    - Hold database transactions during HTTP requests
    - Perform database persistence
    - Implement matching logic
    - Handle user authentication
    """
    
    def __init__(self, company_slug: str, config: Dict[str, Any] = None):
        """
        Initialize the scraper.
        
        Args:
            company_slug: The company slug for resolution
            config: Optional scraper configuration from Company.scraper_config
        """
        self.company_slug = company_slug
        self.config = config or {}
        self.source_identifier = self.get_source_identifier()
    
    @abstractmethod
    def get_source_identifier(self) -> str:
        """
        Return a unique identifier for this source.
        
        This identifier is used in deduplication and logging.
        It should be stable across scraper runs.
        
        Example: 'nexus_technologies', 'company_a'
        """
        pass
    
    @abstractmethod
    def fetch(self) -> Any:
        """
        Fetch raw data from the official source.
        
        This method performs the actual HTTP request or data retrieval.
        It should handle:
        - Timeouts
        - HTTP errors
        - Malformed responses
        - Empty responses
        
        Returns:
            Raw data in the source's native format (JSON, HTML, etc.)
        
        Raises:
            ScrapingError: If fetching fails for any reason
        """
        pass
    
    @abstractmethod
    def extract(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Extract structured job records from raw source data.
        
        This method parses the source-specific format and extracts
        individual job records into a structured dictionary format.
        
        Args:
            raw_data: The raw data returned by fetch()
        
        Returns:
            List of structured job records (dictionaries)
        
        Raises:
            ScrapingError: If extraction fails
        """
        pass
    
    @abstractmethod
    def normalize(self, extracted_job: Dict[str, Any]) -> NormalizedJob:
        """
        Normalize a single extracted job into the common representation.
        
        This method transforms source-specific fields into the NormalizedJob format.
        It should handle:
        - Field mapping
        - Type conversion
        - Whitespace normalization
        - Employment type mapping to Job.EmploymentType choices
        - Experience parsing into numeric values
        - Skill/keyword list normalization
        
        Args:
            extracted_job: A single structured job record from extract()
        
        Returns:
            NormalizedJob object
        
        Raises:
            ScrapingError: If normalization fails
        """
        pass
    
    def scrape(self) -> List[NormalizedJob]:
        """
        Execute the full scraping pipeline.
        
        This orchestrates: fetch -> extract -> normalize for all jobs.
        
        Returns:
            List of NormalizedJob objects
        
        Raises:
            ScrapingError: If any step fails
        """
        logger.info(f"Starting scrape for source: {self.source_identifier}")
        
        try:
            # Step 1: Fetch raw data
            raw_data = self.fetch()
            logger.info(f"Fetched raw data from {self.source_identifier}")
            
            # Step 2: Extract structured records
            extracted_jobs = self.extract(raw_data)
            logger.info(f"Extracted {len(extracted_jobs)} job records")
            
            # Step 3: Normalize to common representation
            normalized_jobs = []
            for extracted_job in extracted_jobs:
                try:
                    normalized_job = self.normalize(extracted_job)
                    validation_errors = normalized_job.validate()
                    if validation_errors:
                        logger.warning(
                            f"Validation errors for job {normalized_job.external_id}: "
                            f"{validation_errors}"
                        )
                        continue
                    normalized_jobs.append(normalized_job)
                except Exception as e:
                    logger.error(
                        f"Failed to normalize job: {e}",
                        exc_info=True
                    )
                    continue
            
            logger.info(f"Normalized {len(normalized_jobs)} valid jobs")
            return normalized_jobs
            
        except Exception as e:
            logger.error(
                f"Scraping failed for {self.source_identifier}: {e}",
                exc_info=True
            )
            raise ScrapingError(f"Scraping failed: {e}") from e


class ScrapingError(Exception):
    """
    Exception raised when scraping fails.
    
    This wraps various scraping-specific errors (HTTP, parsing, etc.)
    into a single exception type for the ingestion service to handle.
    """
    pass
