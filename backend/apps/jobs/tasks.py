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
from apps.jobs.models import IngestionRun
from apps.jobs.scrapers.base import ScrapingError
from apps.jobs.scrapers.registry import get_scraper
from apps.jobs.services.ingestion import JobIngestionService


logger = logging.getLogger(__name__)


# Transient failure classification
TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}
TRANSIENT_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
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
    - Connection timeout (requests.exceptions.Timeout)
    - Connection error (requests.exceptions.ConnectionError)
    - HTTP 429 (rate limit)
    - HTTP 500, 502, 503, 504 (server errors)
    
    Permanent failures:
    - HTTP 400 (bad request)
    - HTTP 401 (unauthorized)
    - HTTP 403 (forbidden)
    - HTTP 404 (not found)
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
    retry_backoff=True,
    retry_backoff_max=600,  # Maximum 10 minutes between retries
    retry_jitter=True,
)
def ingest_jobs_task(self, source: str, ingestion_run_id: int = None) -> Dict[str, Any]:
    """
    Asynchronously ingest jobs from a verified source.
    
    This task orchestrates the ingestion pipeline:
    1. Validate source identifier via registry
    2. Obtain configured scraper
    3. Create or reuse IngestionRun record
    4. Execute scraper (fetch, extract, normalize)
    5. Pass normalized jobs to existing ingestion service
    6. Update IngestionRun with result
    7. Return serializable result
    
    The task handles retry classification:
    - Transient failures (network, 429, 5xx) trigger bounded retry
    - Permanent failures (malformed data, unknown source) do not retry
    
    The task is idempotent:
    - Same source job + same external job ID = same Job record
    - PostgreSQL uniqueness constraint prevents duplicates
    - Existing ingestion service handles upsert correctly
    
    IngestionRun semantics:
    - One logical IngestionRun per ingestion operation
    - Retries reuse the same logical IngestionRun
    - Status transitions: PENDING -> RUNNING -> (RETRYING -> RUNNING)* -> SUCCEEDED/PARTIAL/FAILED
    - retry_count tracks the number of retry attempts
    
    Args:
        source: Source identifier (e.g., 'stripe', 'nexus_technologies')
        ingestion_run_id: Optional existing IngestionRun ID for retry reuse
    
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
    
    # Resolve company to get company slug
    try:
        scraper_class, company_slug = get_scraper(source)
        company = Company.objects.get(slug=company_slug)
    except (ValueError, Company.DoesNotExist) as e:
        # Permanent failure - cannot even resolve source
        logger.error(f"Task {task_id}: Failed to resolve source: {e}")
        raise PermanentIngestionError(f"Failed to resolve source: {e}")
    
    # Create or reuse IngestionRun record
    if ingestion_run_id:
        # Retry: reuse existing logical IngestionRun
        try:
            ingestion_run = IngestionRun.objects.get(id=ingestion_run_id)
            # Verify it belongs to the correct source
            if ingestion_run.source != source:
                logger.error(
                    f"Task {task_id}: IngestionRun {ingestion_run_id} source mismatch "
                    f"(expected {source}, got {ingestion_run.source})"
                )
                raise PermanentIngestionError("IngestionRun source mismatch")
            
            # Update task_id to current retry task
            ingestion_run.task_id = task_id
            ingestion_run.save()
            
            logger.info(f"Task {task_id}: Reusing IngestionRun {ingestion_run.id}")
        except IngestionRun.DoesNotExist:
            logger.error(f"Task {task_id}: IngestionRun {ingestion_run_id} not found")
            raise PermanentIngestionError(f"IngestionRun {ingestion_run_id} not found")
    else:
        # First attempt: create new IngestionRun
        ingestion_run = IngestionRun.objects.create(
            company=company,
            source=source,
            status=IngestionRun.RunStatus.PENDING,
            task_id=task_id,
            retry_count=0
        )
        logger.info(f"Task {task_id}: Created IngestionRun {ingestion_run.id}")
    
    try:
        # Mark run as RUNNING (or back to RUNNING if retrying)
        if ingestion_run.status == IngestionRun.RunStatus.RETRYING:
            # Coming back from RETRYING state
            ingestion_run.increment_retry()
        ingestion_run.mark_running(task_id=task_id)
        logger.info(f"Task {task_id}: IngestionRun {ingestion_run.id} marked RUNNING")
        
        # Step 1: Validate source identifier via registry (already done above)
        logger.info(f"Task {task_id}: Source '{source}' validated, company: {company_slug}")
        
        # Step 2: Resolve company (already done above)
        if not company.is_active:
            raise PermanentIngestionError(f"Company {company_slug} is not active")
        logger.info(f"Task {task_id}: Company resolved: {company.name}")
        
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
            # Mark as SUCCEEDED with zero counts
            result = {
                "source": source,
                "fetched": 0,
                "normalized": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0
            }
            ingestion_run.mark_succeeded(result)
            return result
        
        logger.info(f"Task {task_id}: Scraper returned {len(normalized_jobs)} normalized jobs")
        
        # Step 4: Ingest to database via existing service
        # This handles idempotent upsert with transaction boundaries
        ingestion_service = JobIngestionService()
        service_result = ingestion_service.ingest_jobs(normalized_jobs, company_slug)
        
        logger.info(
            f"Task {task_id}: Ingestion complete - "
            f"created: {service_result.created}, updated: {service_result.updated}, "
            f"skipped: {service_result.skipped}, failed: {service_result.failed}"
        )
        
        # Step 5: Determine final status and update run
        result = {
            "source": source,
            "fetched": service_result.fetched,
            "normalized": service_result.normalized,
            "created": service_result.created,
            "updated": service_result.updated,
            "skipped": service_result.skipped,
            "failed": service_result.failed
        }
        
        # Determine status based on result
        if service_result.failed > 0 or service_result.skipped > 0:
            # Some jobs failed or were skipped - PARTIAL
            if service_result.created + service_result.updated > 0:
                # At least some jobs succeeded
                ingestion_run.mark_partial(result)
                logger.info(f"Task {task_id}: IngestionRun {ingestion_run.id} marked PARTIAL")
            else:
                # All jobs failed or skipped
                ingestion_run.mark_failed(
                    error_type="IngestionError",
                    error_message=f"All jobs failed or skipped: {service_result.failed} failed, {service_result.skipped} skipped"
                )
                logger.warning(f"Task {task_id}: IngestionRun {ingestion_run.id} marked FAILED")
        else:
            # All jobs processed successfully
            ingestion_run.mark_succeeded(result)
            logger.info(f"Task {task_id}: IngestionRun {ingestion_run.id} marked SUCCEEDED")
        
        # Step 6: Return serializable result
        # Do not return Django model objects or QuerySets
        return result
        
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
                # Mark current run as FAILED (terminal state)
                ingestion_run.mark_failed(
                    error_type=type(e).__name__,
                    error_message=str(e)[:1000]
                )
                raise PermanentIngestionError(f"Retry limit exceeded: {e}")
            
            # Mark run as RETRYING (in-progress, not terminal)
            ingestion_run.mark_retrying()
            logger.info(f"Task {task_id}: IngestionRun {ingestion_run.id} marked RETRYING")
            
            # Retry with countdown, passing ingestion_run_id to reuse the same logical run
            raise self.retry(exc=e, countdown=countdown, args=(source, ingestion_run.id))
        
        else:
            # Permanent failure - do not retry
            logger.error(
                f"Task {task_id}: Permanent failure, not retrying: {e}",
                exc_info=True
            )
            # Mark run as FAILED
            ingestion_run.mark_failed(
                error_type=type(e).__name__,
                error_message=str(e)[:1000]
            )
            raise PermanentIngestionError(f"Permanent ingestion failure: {e}")
