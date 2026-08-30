"""
Celery tasks for asynchronous job ingestion.

This module defines the Celery task for orchestrating job ingestion.
The task is thin and delegates to existing scrapers and ingestion service.

Architecture:
Celery Task -> Scraper -> NormalizedJob -> JobIngestionService -> PostgreSQL

The task is responsible for:
- Source validation via registry
- Retry classification (transient vs permanent)
- Bounded retry with exponential backoff
- HTTP 429 handling with Retry-After respect
- Returning serializable results

The task is NOT responsible for:
- HTML parsing
- JSON extraction
- Normalization rules
- Database upsert logic
- Matching logic
"""

import logging
import time
from typing import Dict, Any
from celery import shared_task
from celery.exceptions import Retry
import requests

from apps.companies.models import Company
from apps.jobs.scrapers.base import ScrapingError
from apps.jobs.scrapers.registry import get_scraper
from apps.jobs.services.ingestion import JobIngestionService


logger = logging.getLogger(__name__)


# Transient failure classification
TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}
TRANSIENT_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.RequestException,
)


class PermanentIngestionError(Exception):
    """
    Exception raised for permanent failures that should not be retried.
    
    Examples:
    - Unknown source
    - Malformed source payload
    - Missing required job identifier
    - Invalid application URL
    - Validation failure
    - Programming/configuration error
    """
    pass


def classify_failure(exception: Exception) -> bool:
    """
    Classify a failure as transient (retryable) or permanent (non-retryable).
    
    Transient failures:
    - Connection timeout
    - Temporary network failure
    - HTTP 429 (rate limit)
    - HTTP 500, 502, 503, 504 (server errors)
    - Temporary database connectivity failure
    
    Permanent failures:
    - Malformed source payload
    - Unsupported source format
    - Missing required job identifier
    - Invalid application URL
    - Invalid job data
    - Unknown configured source
    - Programming/configuration error
    
    Args:
        exception: The exception to classify
    
    Returns:
        True if the failure is transient (should retry), False if permanent
    """
    # Check for HTTP 429 with status code
    if isinstance(exception, requests.exceptions.HTTPError):
        if exception.response is not None:
            status_code = exception.response.status_code
            if status_code in TRANSIENT_HTTP_STATUS_CODES:
                return True
            # 404, 401, 403, etc. are permanent
            return False
    
    # Check for transient network exceptions
    if isinstance(exception, TRANSIENT_EXCEPTIONS):
        return True
    
    # ScrapingError may wrap various failures
    if isinstance(exception, ScrapingError):
        # Check if it wraps a transient exception
        if exception.__cause__:
            return classify_failure(exception.__cause__)
        # Default ScrapingError to permanent (malformed data, etc.)
        return False
    
    # PermanentIngestionError is explicitly permanent
    if isinstance(exception, PermanentIngestionError):
        return False
    
    # ValueError for unknown source is permanent
    if isinstance(exception, ValueError) and 'Unknown source' in str(exception):
        return False
    
    # Default: treat as permanent to avoid infinite retries
    return False


def extract_retry_after(exception: Exception) -> int:
    """
    Extract Retry-After delay from HTTP 429 response if available.
    
    Args:
        exception: The exception to check for Retry-After header
    
    Returns:
        Retry delay in seconds, or None if not available
    """
    if isinstance(exception, requests.exceptions.HTTPError):
        if exception.response is not None:
            retry_after = exception.response.headers.get('Retry-After')
            if retry_after:
                try:
                    # Retry-After may be seconds (integer) or HTTP date
                    # We only support integer seconds for simplicity
                    delay = int(retry_after)
                    # Cap at reasonable maximum (300 seconds = 5 minutes)
                    return min(delay, 300)
                except (ValueError, TypeError):
                    pass
    return None


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Start with 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Maximum 10 minutes between retries
    retry_jitter=True,
)
def ingest_jobs_task(self, source: str) -> Dict[str, Any]:
    """
    Asynchronously ingest jobs from a verified source.
    
    This task orchestrates the ingestion pipeline:
    1. Validate source identifier via registry
    2. Obtain configured scraper
    3. Execute scraper (fetch, extract, normalize)
    4. Pass normalized jobs to existing ingestion service
    5. Return serializable result
    
    The task handles retry classification:
    - Transient failures (network, 429, 5xx) trigger bounded retry
    - Permanent failures (malformed data, unknown source) do not retry
    
    The task is idempotent:
    - Same source job + same external job ID = same Job record
    - PostgreSQL uniqueness constraint prevents duplicates
    - Existing ingestion service handles upsert correctly
    
    Args:
        source: Source identifier (e.g., 'stripe', 'nexus_technologies')
    
    Returns:
        Dictionary with serializable ingestion result:
        {
            "source": "stripe",
            "fetched": 574,
            "normalized": 574,
            "created": 20,
            "updated": 554,
            "skipped": 0,
            "failed": 0
        }
    
    Raises:
        PermanentIngestionError: For permanent non-retryable failures
        Retry: For transient retryable failures
    """
    task_id = self.request.id
    retry_count = self.request.retries
    
    logger.info(
        f"Task {task_id}: Starting ingestion for source '{source}' "
        f"(attempt {retry_count + 1})"
    )
    
    try:
        # Step 1: Validate source identifier via registry
        scraper_class, company_slug = get_scraper(source)
        logger.info(f"Task {task_id}: Source '{source}' validated, company: {company_slug}")
        
        # Step 2: Resolve company
        try:
            company = Company.objects.get(slug=company_slug)
            if not company.is_active:
                raise PermanentIngestionError(f"Company {company_slug} is not active")
            logger.info(f"Task {task_id}: Company resolved: {company.name}")
        except Company.DoesNotExist:
            raise PermanentIngestionError(f"Company not found: {company_slug}")
        
        # Step 3: Initialize and execute scraper
        # This performs HTTP fetch, extraction, and normalization
        # Database transactions are NOT held during HTTP requests
        scraper = scraper_class(
            company_slug=company_slug,
            config=company.scraper_config
        )
        
        logger.info(f"Task {task_id}: Executing scraper for {source}")
        normalized_jobs = scraper.scrape()
        
        if not normalized_jobs:
            logger.warning(f"Task {task_id}: No jobs found for source {source}")
            return {
                "source": source,
                "fetched": 0,
                "normalized": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0
            }
        
        logger.info(f"Task {task_id}: Scraper returned {len(normalized_jobs)} normalized jobs")
        
        # Step 4: Ingest to database via existing service
        # This handles idempotent upsert with transaction boundaries
        ingestion_service = JobIngestionService()
        result = ingestion_service.ingest_jobs(normalized_jobs, company_slug)
        
        logger.info(
            f"Task {task_id}: Ingestion complete - "
            f"created: {result.created}, updated: {result.updated}, "
            f"skipped: {result.skipped}, failed: {result.failed}"
        )
        
        # Step 5: Return serializable result
        # Do not return Django model objects or QuerySets
        return {
            "source": source,
            "fetched": result.fetched,
            "normalized": result.normalized,
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "failed": result.failed
        }
        
    except Exception as e:
        # Classify failure as transient or permanent
        is_transient = classify_failure(e)
        
        if is_transient:
            # Check for Retry-After header on 429
            retry_after = extract_retry_after(e)
            if retry_after:
                logger.info(
                    f"Task {task_id}: Transient failure with Retry-After: {retry_after}s"
                )
                countdown = retry_after
            else:
                # Use exponential backoff
                countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
                logger.info(
                    f"Task {task_id}: Transient failure, retrying in {countdown}s "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
            
            # Check if we've exhausted retries
            if retry_count >= self.max_retries:
                logger.error(
                    f"Task {task_id}: Exhausted retries after {retry_count} attempts"
                )
                raise PermanentIngestionError(f"Retry limit exceeded: {e}")
            
            # Retry with countdown
            raise self.retry(exc=e, countdown=countdown)
        
        else:
            # Permanent failure - do not retry
            logger.error(
                f"Task {task_id}: Permanent failure, not retrying: {e}",
                exc_info=True
            )
            raise PermanentIngestionError(f"Permanent ingestion failure: {e}")
