"""Celery tasks for automated job ingestion."""

import logging
import time
import uuid
from typing import Any, cast

import requests
from celery import shared_task
from celery.exceptions import Ignore
from django.conf import settings
from django.utils import timezone
from redis import Redis
from redis.exceptions import RedisError

from api.ingestion.pipeline import process_batch
from api.ingestion.scraper_registry import load_scraper
from api.models import FetchRun, IngestionSource

logger = logging.getLogger(__name__)


# Lua script for safe lock release (compare-and-delete)
RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class SourceLockError(Exception):
    """Raised when unable to acquire lock for a source."""

    pass


def acquire_source_lock(source_id: int, redis_client: Redis, timeout: int = 3600) -> str | None:
    """Acquire a distributed lock for a source with unique ownership token.

    Args:
        source_id: The IngestionSource ID
        redis_client: Redis client instance
        timeout: Lock lifetime in seconds (default 1 hour)

    Returns:
        Lock token if acquired, None otherwise

    Raises:
        SourceLockError: If Redis operation fails
    """
    lock_key = f"ingestion_lock:source:{source_id}"
    lock_token = str(uuid.uuid4())

    try:
        # Use SET with NX (only set if not exists) and EX (expiration)
        # Store unique token to verify ownership on release
        acquired = redis_client.set(lock_key, lock_token, nx=True, ex=timeout)
        if acquired:
            return lock_token
        return None
    except RedisError as e:
        logger.error(f"Redis error acquiring lock for source {source_id}: {e}")
        raise SourceLockError(f"Redis error acquiring lock: {e}") from None


def release_source_lock(source_id: int, redis_client: Redis, lock_token: str) -> bool:
    """Release a distributed lock for a source using compare-and-delete.

    Only releases the lock if the stored token matches the provided token.
    This prevents deleting a lock acquired by another task after expiry.

    Args:
        source_id: The IngestionSource ID
        redis_client: Redis client instance
        lock_token: The token returned by acquire_source_lock

    Returns:
        True if lock was released, False if lock not owned by this token
    """
    lock_key = f"ingestion_lock:source:{source_id}"

    try:
        # Use Lua script for atomic compare-and-delete
        result = redis_client.eval(RELEASE_LOCK_SCRIPT, 1, lock_key, lock_token)
        return bool(result)
    except RedisError as e:
        logger.error(f"Redis error releasing lock for source {source_id}: {e}")
        return False


def is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient (retryable).

    Transient errors:
    - Network timeouts
    - Connection errors
    - HTTP 429 (rate limit)
    - HTTP 5xx (server errors)

    Non-transient errors:
    - HTTP 4xx (client errors, except 429)
    - Invalid scraper configuration
    - Malformed data
    - ValueError with invalid configuration

    Args:
        error: The exception to evaluate

    Returns:
        True if error is transient, False otherwise
    """
    if isinstance(error, requests.Timeout):
        return True
    if isinstance(error, requests.ConnectionError):
        return True
    if isinstance(error, requests.HTTPError):
        if error.response is not None:
            status_code = error.response.status_code
            # Retry on 429 (rate limit) and 5xx (server errors)
            if status_code == 429 or status_code >= 500:
                return True
    if isinstance(error, RedisError):
        return True
    return False


def get_retry_after_seconds(error: Exception) -> int | None:
    """Extract Retry-After header from HTTP 429 response.

    Args:
        error: The exception to check

    Returns:
        Seconds to wait before retry, or None if not available
    """
    if isinstance(error, requests.HTTPError) and error.response is not None:
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
    return None


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(requests.Timeout, requests.ConnectionError, RedisError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def ingest_source_task(self, source_id: int) -> dict[str, Any]:
    """Orchestrate ingestion for a single source.

    This task:
    - Resolves the IngestionSource
    - Validates source is active
    - Acquires distributed lock
    - Executes ingestion pipeline
    - Updates FetchRun state and counters
    - Handles retries for transient failures
    - Releases lock

    Args:
        source_id: The IngestionSource ID to ingest from

    Returns:
        Dict with task result including fetch_run_id and status

    Raises:
        Ignore: If source is inactive or lock cannot be acquired
        Retry: If error is transient and retries remain
    """
    logger.info(f"Task received: ingest_source_task for source_id={source_id}")

    # Initialize Redis client before lock acquisition
    redis_url = getattr(settings, "REDIS_LOCK_URL", settings.CELERY_BROKER_URL)
    redis_client = Redis.from_url(redis_url)

    # Resolve source
    try:
        source = IngestionSource.objects.get(id=source_id)
    except IngestionSource.DoesNotExist:
        logger.error(f"Source {source_id} does not exist")
        raise Ignore(f"Source {source_id} does not exist") from None

    logger.info(f"Source selected: {source.company.name} - {source.name}")

    # Validate source is active
    if not source.is_active:
        logger.warning(f"Source {source_id} is inactive, skipping")
        raise Ignore(f"Source {source_id} is inactive")

    # Validate scraper class
    if not source.scraper_class:
        logger.error(f"Source {source_id} has no scraper_class configured")
        # Mark as failed without retry (configuration error)
        fetch_run = _create_fetch_run(source, self.request.id)
        _mark_fetch_run_failed(fetch_run, "No scraper_class configured")
        raise Ignore(f"Source {source_id} has no scraper_class")

    # Load scraper (will raise ValueError if not in registry)
    try:
        scraper = load_scraper(source.scraper_class)
    except ValueError as e:
        logger.error(f"Failed to load scraper for source {source_id}: {e}")
        # Mark as failed without retry (configuration error)
        fetch_run = _create_fetch_run(source, self.request.id)
        _mark_fetch_run_failed(fetch_run, f"Invalid scraper configuration: {e}")
        raise Ignore(f"Invalid scraper configuration: {e}") from None

    # Acquire distributed lock
    lock_token = acquire_source_lock(source_id, redis_client)
    if not lock_token:
        logger.warning(f"Could not acquire lock for source {source_id}, skipping")
        raise Ignore(f"Could not acquire lock for source {source_id}")

    logger.info(f"Lock acquired for source {source_id}")

    # Create or reuse FetchRun (check if already exists for this task)
    task_id = self.request.id
    fetch_run = _create_fetch_run(source, task_id)

    if fetch_run.retry_count > 0:
        logger.info(f"Retry: fetch_run_id={fetch_run.id}, retry_count={fetch_run.retry_count}")
    else:
        logger.info(f"Fetch created: fetch_run_id={fetch_run.id}, source_id={source_id}")

    try:
        # Check for Spotify-specific crawl-delay
        if "spotify" in source.name.lower() or "lever" in source.scraper_class.lower():
            logger.info("Spotify (Lever) source detected, applying 1-second crawl-delay")
            time.sleep(1)

        # Fetch jobs
        logger.info(f"Fetching jobs from {source.base_url}")
        raw_records = scraper.fetch(source.base_url)
        fetch_run.jobs_fetched = len(raw_records)
        fetch_run.save(update_fields=["jobs_fetched"])

        logger.info(f"Fetch completed: {len(raw_records)} jobs fetched")

        if not raw_records:
            logger.info(f"No jobs found for source {source_id}")
            _mark_fetch_run_succeeded(fetch_run, jobs_parsed=0)
            return {"fetch_run_id": fetch_run.id, "status": "succeeded", "jobs_fetched": 0}

        # Add source_id and company_id to records
        for raw_record in raw_records:
            raw_record["_source_id"] = source.id
            raw_record["_company_id"] = source.company_id

        # Process through pipeline
        logger.info(f"Processing {len(raw_records)} jobs through pipeline")
        result = process_batch(raw_records, source.scraper_class, dry_run=False)

        # Update FetchRun with results
        fetch_run.jobs_parsed = result.jobs_processed
        fetch_run.jobs_created = result.jobs_created
        fetch_run.jobs_updated = result.jobs_updated
        fetch_run.jobs_skipped = result.jobs_skipped
        fetch_run.jobs_invalid = len(result.validation_errors)

        # Determine final status
        if result.validation_errors:
            # Partial success if some jobs succeeded
            if result.jobs_created > 0 or result.jobs_updated > 0:
                _mark_fetch_run_partially_succeeded(
                    fetch_run,
                    f"{len(result.validation_errors)} validation errors",
                )
            else:
                # All failed
                _mark_fetch_run_failed(fetch_run, "All records failed validation")
        else:
            _mark_fetch_run_succeeded(fetch_run, result.jobs_processed)

        logger.info(
            f"Fetch completed: fetch_run_id={fetch_run.id}, "
            f"created={result.jobs_created}, updated={result.jobs_updated}, "
            f"skipped={result.jobs_skipped}, invalid={len(result.validation_errors)}"
        )

        return {
            "fetch_run_id": fetch_run.id,
            "status": fetch_run.status,
            "jobs_fetched": fetch_run.jobs_fetched,
            "jobs_created": fetch_run.jobs_created,
            "jobs_updated": fetch_run.jobs_updated,
            "jobs_skipped": fetch_run.jobs_skipped,
            "jobs_invalid": fetch_run.jobs_invalid,
        }

    except Exception as e:
        logger.error(f"Error during ingestion for source {source_id}: {e}")

        # Update retry count
        fetch_run.retry_count += 1
        fetch_run.last_retry_at = timezone.now()
        fetch_run.save(update_fields=["retry_count", "last_retry_at"])

        # Check if error is transient
        if is_transient_error(e):
            # Check retry limit
            if self.request.retries < self.max_retries:
                # Check for Retry-After header
                retry_after = get_retry_after_seconds(e)
                if retry_after:
                    logger.info(f"Retrying after {retry_after} seconds (Retry-After header)")
                    raise self.retry(countdown=retry_after, exc=e) from None
                else:
                    logger.info(f"Retrying (attempt {self.request.retries + 1}/{self.max_retries})")
                    raise self.retry(exc=e) from None
            else:
                # Max retries exceeded
                logger.error(f"Max retries exceeded for source {source_id}")
                _mark_fetch_run_failed(fetch_run, f"Max retries exceeded: {str(e)}")
                raise Ignore(f"Max retries exceeded for source {source_id}") from None
        else:
            # Non-transient error, fail immediately
            _mark_fetch_run_failed(fetch_run, str(e))
            raise Ignore(f"Non-transient error for source {source_id}: {e}") from None

    finally:
        # Always attempt to release lock (only if we own it)
        if lock_token:
            released = release_source_lock(source_id, redis_client, lock_token)
            if released:
                logger.info(f"Lock released for source {source_id}")
            else:
                logger.warning(f"Lock release failed for source {source_id} (not owned or expired)")


def _create_fetch_run(source: IngestionSource, task_id: str | None) -> FetchRun:
    """Create a FetchRun in pending state, or reuse existing if task_id matches.

    This ensures that retries reuse the same FetchRun record instead of
    creating duplicates for the same logical execution.

    Args:
        source: The IngestionSource
        task_id: The Celery task ID

    Returns:
        Created or reused FetchRun instance
    """
    # Check if FetchRun already exists for this task_id (retry scenario)
    if task_id:
        existing_fetch_run = FetchRun.objects.filter(celery_task_id=task_id).first()
        if existing_fetch_run is not None:
            return cast(FetchRun, existing_fetch_run)

    # Create new FetchRun
    fetch_run: FetchRun = FetchRun.objects.create(
        source=source,
        status="pending",
        celery_task_id=task_id or "",
    )
    # Transition to running
    fetch_run.status = "running"
    fetch_run.save(update_fields=["status"])
    return fetch_run


def _mark_fetch_run_succeeded(fetch_run: FetchRun, jobs_parsed: int) -> None:
    """Mark FetchRun as succeeded.

    Args:
        fetch_run: The FetchRun to update
        jobs_parsed: Number of jobs successfully parsed
    """
    fetch_run.status = "succeeded"
    fetch_run.jobs_parsed = jobs_parsed
    fetch_run.completed_at = timezone.now()
    fetch_run.save(update_fields=["status", "jobs_parsed", "completed_at"])


def _mark_fetch_run_partially_succeeded(fetch_run: FetchRun, error_message: str) -> None:
    """Mark FetchRun as partially succeeded.

    Args:
        fetch_run: The FetchRun to update
        error_message: Error message describing partial failure
    """
    fetch_run.status = "partially_succeeded"
    fetch_run.completed_at = timezone.now()
    fetch_run.error_message = error_message
    fetch_run.save(update_fields=["status", "completed_at", "error_message"])


def _mark_fetch_run_failed(fetch_run: FetchRun, error_message: str) -> None:
    """Mark FetchRun as failed.

    Args:
        fetch_run: The FetchRun to update
        error_message: Error message describing failure
    """
    fetch_run.status = "failed"
    fetch_run.completed_at = timezone.now()
    fetch_run.error_message = error_message
    fetch_run.save(update_fields=["status", "completed_at", "error_message"])
