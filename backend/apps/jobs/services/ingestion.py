"""
Job ingestion service.

This service handles the persistence boundary between scrapers and the database.
It is responsible for:
- Validating normalized jobs
- Resolving companies
- Upserting jobs with deduplication
- Transaction management
- Observability/statistics

The service does NOT:
- Perform HTTP requests
- Implement scraping logic
- Handle user authentication
- Calculate match scores
"""

import logging
from typing import List, Dict, Any
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from apps.companies.models import Company
from apps.jobs.models import Job
from apps.jobs.scrapers.base import NormalizedJob, ScrapingError


logger = logging.getLogger(__name__)


class IngestionResult:
    """
    Result of a job ingestion run.
    
    Tracks statistics and outcomes for observability.
    """
    def __init__(self):
        self.fetched: int = 0
        self.normalized: int = 0
        self.created: int = 0
        self.updated: int = 0
        self.skipped: int = 0
        self.failed: int = 0
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for logging/serialization."""
        return {
            'fetched': self.fetched,
            'normalized': self.normalized,
            'created': self.created,
            'updated': self.updated,
            'skipped': self.skipped,
            'failed': self.failed,
            'errors': self.errors
        }
    
    def __str__(self):
        return (
            f"IngestionResult(fetched={self.fetched}, normalized={self.normalized}, "
            f"created={self.created}, updated={self.updated}, skipped={self.skipped}, "
            f"failed={self.failed})"
        )


class JobIngestionService:
    """
    Service for ingesting normalized jobs into the database.
    
    This service provides a clean boundary between scraping and persistence.
    It handles company resolution, job upserts, and transaction management.
    """
    
    def __init__(self):
        """Initialize the ingestion service."""
        self.result = IngestionResult()
    
    def ingest_jobs(
        self,
        normalized_jobs: List[NormalizedJob],
        company_slug: str
    ) -> IngestionResult:
        """
        Ingest a list of normalized jobs into the database.
        
        This method:
        1. Resolves the company by slug
        2. Validates each normalized job
        3. Upserts jobs with deduplication
        4. Tracks statistics
        
        Args:
            normalized_jobs: List of NormalizedJob objects from a scraper
            company_slug: The company slug for job association
        
        Returns:
            IngestionResult with statistics
        """
        self.result = IngestionResult()
        self.result.fetched = len(normalized_jobs)
        
        logger.info(f"Starting ingestion for company: {company_slug}")
        logger.info(f"Jobs to process: {len(normalized_jobs)}")
        
        try:
            # Resolve company
            company = self._resolve_company(company_slug)
            if not company:
                error_msg = f"Company not found: {company_slug}"
                logger.error(error_msg)
                self.result.errors.append(error_msg)
                self.result.failed = len(normalized_jobs)
                return self.result
            
            # Process each job
            for normalized_job in normalized_jobs:
                try:
                    self._ingest_single_job(normalized_job, company)
                    self.result.normalized += 1
                except ValidationError as e:
                    logger.warning(f"Validation failed for job {normalized_job.external_id}: {e}")
                    self.result.skipped += 1
                    self.result.errors.append(f"Validation error for {normalized_job.external_id}: {e}")
                except IntegrityError as e:
                    logger.warning(f"Integrity error for job {normalized_job.external_id}: {e}")
                    self.result.skipped += 1
                    self.result.errors.append(f"Integrity error for {normalized_job.external_id}: {e}")
                except Exception as e:
                    logger.error(f"Failed to ingest job {normalized_job.external_id}: {e}", exc_info=True)
                    self.result.failed += 1
                    self.result.errors.append(f"Failed to ingest {normalized_job.external_id}: {e}")
            
            logger.info(f"Ingestion complete: {self.result}")
            return self.result
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            self.result.errors.append(f"Ingestion failed: {e}")
            self.result.failed = len(normalized_jobs)
            return self.result
    
    def _resolve_company(self, company_slug: str) -> Company:
        """
        Resolve a company by slug.
        
        Args:
            company_slug: The company slug
        
        Returns:
            Company object or None if not found
        """
        try:
            company = Company.objects.get(slug=company_slug)
            if not company.is_active:
                logger.warning(f"Company {company_slug} is not active")
                return None
            return company
        except Company.DoesNotExist:
            logger.error(f"Company not found: {company_slug}")
            return None
    
    def _ingest_single_job(self, normalized_job: NormalizedJob, company: Company):
        """
        Ingest a single normalized job.
        
        This method performs an upsert:
        - If job exists (by company + external_job_id): update
        - If job does not exist: create
        
        Args:
            normalized_job: The normalized job to ingest
            company: The resolved Company object
        """
        with transaction.atomic():
            # Generate deduplication hash
            deduplication_hash = normalized_job.generate_deduplication_hash()
            
            # Validate normalized job
            validation_errors = normalized_job.validate()
            if validation_errors:
                raise ValidationError(f"Validation failed: {validation_errors}")
            
            # Try to get existing job
            try:
                existing_job = Job.objects.get(
                    company=company,
                    external_job_id=normalized_job.external_id
                )
                
                # Update existing job
                existing_job.title = normalized_job.title
                existing_job.description = normalized_job.description
                existing_job.location = normalized_job.location or ''
                existing_job.employment_type = normalized_job.employment_type or ''
                existing_job.experience_required = normalized_job.experience_required or ''
                existing_job.minimum_experience_years = normalized_job.minimum_experience_years
                existing_job.maximum_experience_years = normalized_job.maximum_experience_years
                existing_job.skills = normalized_job.skills or []
                existing_job.keywords = normalized_job.keywords or []
                existing_job.application_url = normalized_job.application_url
                existing_job.source_url = normalized_job.source_url or ''
                existing_job.job_metadata = normalized_job.raw_data or {}
                existing_job.save()
                
                self.result.updated += 1
                logger.debug(f"Updated job: {normalized_job.external_id}")
                
            except Job.DoesNotExist:
                # Create new job
                Job.objects.create(
                    company=company,
                    external_job_id=normalized_job.external_id,
                    title=normalized_job.title,
                    description=normalized_job.description,
                    location=normalized_job.location or '',
                    employment_type=normalized_job.employment_type or '',
                    experience_required=normalized_job.experience_required or '',
                    minimum_experience_years=normalized_job.minimum_experience_years,
                    maximum_experience_years=normalized_job.maximum_experience_years,
                    skills=normalized_job.skills or [],
                    keywords=normalized_job.keywords or [],
                    application_url=normalized_job.application_url,
                    source_url=normalized_job.source_url or '',
                    deduplication_hash=deduplication_hash,
                    job_metadata=normalized_job.raw_data or {},
                    status=Job.JobStatus.ACTIVE
                )
                
                self.result.created += 1
                logger.debug(f"Created job: {normalized_job.external_id}")
