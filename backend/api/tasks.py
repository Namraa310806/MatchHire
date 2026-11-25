"""Celery tasks for automated job ingestion and resume parsing."""

import logging
import threading
import time
import uuid
from typing import Any, cast

import requests
from celery import shared_task
from celery.exceptions import Ignore
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.utils import OperationalError
from django.utils import timezone
from redis import Redis
from redis.exceptions import RedisError

from api.extraction import (
    ExperienceEstimate,
    SkillMatch,
    estimate_experience_years,
    extract_domain_keywords,
    extract_skills,
    get_skills_dictionary,
)
from api.github import client as github_client
from api.github import services as github_services
from api.github import status as github_status
from api.ingestion.pipeline import process_batch
from api.ingestion.scraper_registry import load_scraper
from api.models import (
    CandidateGitHubProfile,
    CandidateProfile,
    FetchRun,
    IngestionSource,
    Skill,
)
from api.resume import services
from api.resume import status as resume_status
from api.resume.pdf import ResumeValidationError, extract_text
from api.resume.sections import segment_resume

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


# ---------------------------------------------------------------------------
# Resume parsing task
# ---------------------------------------------------------------------------

_RESUME_TRANSIENT_ERRORS = (OSError, OperationalError, RedisError)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    queue="parse_queue",
)
def parse_resume_task(
    self, profile_id: int, task_id: str, expected_resume_name: str
) -> dict[str, Any]:
    """Parse a stored resume PDF and update the candidate profile.

    Args:
        profile_id: CandidateProfile ID that owns the resume.
        task_id: Resume task ID (also the Celery task ID); status key.
        expected_resume_name: Storage name the task was queued for; used to
            detect resume replacement and prevent stale writes.

    Returns:
        Dict summarizing the outcome (no resume content or PII).
    """
    logger.info(f"Resume parse task received: task_id={task_id}, profile_id={profile_id}")

    record = resume_status.get_status(task_id)
    if record is None:
        logger.warning(f"Resume task {task_id} has no status record (expired?)")
        raise Ignore(f"Resume task {task_id} status record missing")

    # Tolerate duplicate delivery: terminal or in-progress states exit early
    if record["status"] in resume_status.TERMINAL_STATUSES:
        logger.info(f"Resume task {task_id} already terminal: {record['status']}")
        raise Ignore(f"Resume task {task_id} already {record['status']}")

    # Per-task lock prevents concurrent duplicate execution
    lock_key = f"resume:lock:{task_id}"
    if not _cache_add(lock_key, "1", timeout=600):
        logger.info(f"Resume task {task_id} already locked, skipping duplicate")
        raise Ignore(f"Resume task {task_id} already processing")

    try:
        resume_status.update_status(task_id, status=resume_status.STATUS_PROCESSING)

        try:
            profile = CandidateProfile.objects.select_related("user").get(id=profile_id)
        except CandidateProfile.DoesNotExist:
            resume_status.fail_status(task_id, "processing_error")
            logger.error(f"Resume task {task_id}: profile {profile_id} not found")
            raise Ignore(f"Profile {profile_id} not found") from None

        # Consent and ownership/staleness checks before touching the file
        if not profile.resume_consent_given:
            resume_status.fail_status(task_id, "missing_consent")
            raise Ignore(f"Resume task {task_id}: consent withdrawn")

        if not profile.resume_file or profile.resume_file.name != expected_resume_name:
            category = (
                "resume_deleted"
                if not profile.resume_file
                else "resume_replaced"
            )
            resume_status.fail_status(task_id, category)
            logger.info(f"Resume task {task_id}: {category}")
            raise Ignore(f"Resume task {task_id}: {category}")

        # Load stored file bytes
        try:
            with default_storage.open(profile.resume_file.name, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            logger.error(f"Resume task {task_id}: storage read failed: {exc}")
            _retry_or_fail(self, task_id, exc, "file_unavailable")
            return {"task_id": task_id, "status": "failed"}

        # Structural validation + text extraction (permanent errors -> failed)
        try:
            pdf = extract_text(data)
        except ResumeValidationError as exc:
            resume_status.fail_status(task_id, exc.code)
            logger.info(f"Resume task {task_id}: validation failed ({exc.code})")
            raise Ignore(f"Resume task {task_id}: invalid resume ({exc.code})") from None

        if not pdf.has_text_layer:
            resume_status.fail_status(task_id, "no_text_layer")
            logger.info(f"Resume task {task_id}: no text layer (scanned PDF?)")
            raise Ignore(f"Resume task {task_id}: no text layer")

        # Segment + extract (stage failures degrade to partial, not silent)
        sections = segment_resume(pdf.text)
        stage_errors: list[str] = []
        skills: list[Any] = []
        domain_keywords: list[Any] = []
        experience: Any = None

        try:
            skills = extract_skills(pdf.text)
        except Exception as exc:  # noqa: BLE001 - stage isolation
            stage_errors.append("skills")
            logger.error(f"Resume task {task_id}: skill extraction failed: {exc}")

        try:
            domain_keywords = extract_domain_keywords(pdf.text)
        except Exception as exc:  # noqa: BLE001 - stage isolation
            stage_errors.append("domain_keywords")
            logger.error(f"Resume task {task_id}: domain extraction failed: {exc}")

        try:
            experience = estimate_experience_years(pdf.text)
        except Exception as exc:  # noqa: BLE001 - stage isolation
            stage_errors.append("experience")
            logger.error(f"Resume task {task_id}: experience estimation failed: {exc}")

        if experience is None:
            if "experience" not in stage_errors:
                stage_errors.append("experience")
            experience = ExperienceEstimate(
                total_years=None,
                confidence="none",
                methodology="Experience estimation stage failed",
            )

        if stage_errors and not (skills or domain_keywords or experience):
            resume_status.fail_status(task_id, "processing_error")
            raise Ignore(f"Resume task {task_id}: all extraction stages failed")

        # Persist atomically; re-verify staleness inside the transaction so
        # a newer upload cannot be overwritten by this older task.
        try:
            with transaction.atomic():
                locked = CandidateProfile.objects.select_for_update().get(id=profile_id)
                if not locked.resume_file or locked.resume_file.name != expected_resume_name:
                    resume_status.fail_status(task_id, "resume_replaced")
                    logger.info(f"Resume task {task_id}: superseded before persist")
                    raise Ignore(f"Resume task {task_id}: superseded")
                result_summary = services.persist_resume_extraction(
                    locked, skills, domain_keywords, experience
                )
        except OperationalError as exc:
            logger.error(f"Resume task {task_id}: persist failed: {exc}")
            _retry_or_fail(self, task_id, exc, "processing_error")
            return {"task_id": task_id, "status": "failed"}

        services.invalidate_matching_caches(profile_id)

        result_summary.update(
            {
                "pages": pdf.page_count,
                "sections_found": sections.found,
                "stage_errors": stage_errors,
            }
        )

        final_status = (
            resume_status.STATUS_PARTIAL if stage_errors else resume_status.STATUS_COMPLETED
        )
        resume_status.update_status(task_id, status=final_status, result=result_summary)
        logger.info(
            f"Resume task {task_id}: {final_status} "
            f"(skills={result_summary['skills_found']}, "
            f"keywords={result_summary['domain_keywords']}, "
            f"experience={result_summary['experience_years']})"
        )
        return {"task_id": task_id, "status": final_status, **result_summary}

    except Ignore:
        raise
    except _RESUME_TRANSIENT_ERRORS as exc:
        logger.error(f"Resume task {task_id}: transient error: {exc}")
        _retry_or_fail(self, task_id, exc, "processing_error")
        return {"task_id": task_id, "status": "failed"}
    except Exception:  # noqa: BLE001 - last-resort isolation
        logger.exception(f"Resume task {task_id}: unexpected error")
        resume_status.fail_status(task_id, "processing_error")
        raise Ignore(f"Resume task {task_id}: unexpected error") from None
    finally:
        _cache_delete(lock_key)


def _cache_add(key: str, value: str, timeout: int) -> bool:
    """Atomic cache add (SET NX semantics) via the Django cache backend."""
    from django.core.cache import cache

    return bool(cache.add(key, value, timeout=timeout))


def _cache_delete(key: str) -> None:
    from django.core.cache import cache

    cache.delete(key)


def _retry_or_fail(
    task: Any, task_id: str, exc: Exception, category: str
) -> None:
    """Retry transient failures up to max_retries, then mark failed."""
    if task.request.retries < task.max_retries:
        raise task.retry(exc=exc) from None
    resume_status.fail_status(task_id, category)


# ---------------------------------------------------------------------------
# GitHub profile sync task
# ---------------------------------------------------------------------------

_GITHUB_LOCK_TTL_SECONDS = 900


# Lua scripts for atomic lock ownership operations. Compare the stored
# token before mutating so a stale execution can never renew, overwrite,
# or delete a successor's lock.
RENEW_EXECUTION_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("pexpire", KEYS[1], ARGV[2])
else
    return 0
end
"""


def _lock_redis_client() -> Redis:
    """Raw Redis client for execution locks (same convention as ingestion)."""
    redis_url = getattr(settings, "REDIS_LOCK_URL", settings.CELERY_BROKER_URL)
    return Redis.from_url(redis_url)


class _ExecutionLock:
    """Owned Redis lock for a single task execution.

    Acquire is ``SET key token NX EX ttl``. Renewal and release are Lua
    compare-and-mutate scripts, so they are atomic with respect to expiry
    and successor acquisition — a stale execution can never extend,
    overwrite, or delete a lock it no longer owns. Any Redis error marks
    ownership lost: the task fails closed and never persists without a
    concurrency guarantee.
    """

    def __init__(
        self,
        key: str,
        ttl: int = _GITHUB_LOCK_TTL_SECONDS,
        redis_client: Redis | None = None,
    ) -> None:
        self.key = key
        self.ttl = ttl
        self.token = str(uuid.uuid4())
        self.ownership_lost = False
        self._redis = redis_client if redis_client is not None else _lock_redis_client()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def acquire(self) -> bool:
        acquired = self._redis.set(self.key, self.token, nx=True, ex=self.ttl)
        return bool(acquired)

    def start_renewal(self) -> None:
        interval = max(self.ttl // 3, 1)
        self._thread = threading.Thread(
            target=self._renew_loop, args=(interval,), daemon=True
        )
        self._thread.start()

    def _renew_loop(self, interval: float) -> None:
        while not self._stop.wait(interval):
            self.renew()

    def renew(self) -> bool:
        """Atomically extend TTL iff we still own the lock."""
        if self.ownership_lost:
            return False
        try:
            result = self._redis.eval(
                RENEW_EXECUTION_LOCK_SCRIPT,
                1,
                self.key,
                self.token,
                str(self.ttl * 1000),
            )
        except Exception:  # noqa: BLE001 - fail closed
            self.ownership_lost = True
            return False
        if not result:
            self.ownership_lost = True
            return False
        return True

    def owns(self) -> bool:
        """Cheap atomic read used as an early-out before persistence.

        The authoritative guard is the DB fencing token checked inside the
        persist transaction; this only avoids a wasted persist attempt.
        """
        if self.ownership_lost:
            return False
        try:
            return bool(self._redis.get(self.key) == self.token)
        except Exception:  # noqa: BLE001 - fail closed
            self.ownership_lost = True
            return False

    def stop(self) -> None:
        self._stop.set()

    def release(self) -> None:
        """Atomically delete the lock iff we still own it."""
        try:
            self._redis.eval(RELEASE_LOCK_SCRIPT, 1, self.key, self.token)
        except Exception:  # noqa: BLE001 - TTL expiry is the fallback
            pass


_GITHUB_TRANSIENT_ERRORS = (
    requests.Timeout,
    requests.ConnectionError,
    github_client.GitHubRateLimitError,
    github_client.GitHubServerError,
    RedisError,
    OperationalError,
)


def _is_eligible_repo(repo: github_client.GitHubRepo) -> bool:
    """Skip forks, archived, and empty repos (size is KB; 0 = empty)."""
    return not repo.fork and not repo.archived and repo.size_kb > 0


def _fetch_repo_languages(
    repos: list[github_client.GitHubRepo],
) -> tuple[dict[str, dict[str, int]], list[str]]:
    """Fetch languages per eligible repo.

    Returns (repo_full_name -> {language: bytes}, stage_errors). Per-repo
    4xx/404 failures skip that repo; transient failures propagate for
    task-level retry.
    """
    per_repo: dict[str, dict[str, int]] = {}
    stage_errors: list[str] = []

    for repo in repos:
        try:
            per_repo[repo.full_name] = github_client.get_repo_languages(
                repo.full_name
            )
        except github_client.GitHubUserNotFoundError:
            # Repo deleted since listing: benign, not an incomplete snapshot.
            continue
        except github_client.GitHubAPIError as exc:
            if isinstance(exc, github_client.GitHubRateLimitError):
                raise
            stage_errors.append("repo_metadata")

    return per_repo, stage_errors


def _aggregate_language_bytes(
    per_repo: dict[str, dict[str, int]],
) -> dict[str, int]:
    """Sum bytes-by-language across all fetched repos."""
    totals: dict[str, int] = {}
    for languages in per_repo.values():
        for lang, byte_count in languages.items():
            totals[lang] = totals.get(lang, 0) + byte_count
    return totals


def _fetch_readmes(
    repos: list[github_client.GitHubRepo], limit: int
) -> tuple[dict[str, str], list[str]]:
    """Fetch README text for up to ``limit`` repos (priority-ordered)."""
    readmes: dict[str, str] = {}
    stage_errors: list[str] = []
    for repo in repos[:limit]:
        try:
            readmes[repo.full_name] = github_client.get_readme(repo.full_name)
        except github_client.GitHubUserNotFoundError:
            continue
        except github_client.GitHubAPIError as exc:
            if isinstance(exc, github_client.GitHubRateLimitError):
                raise
            stage_errors.append("readme")
    return readmes, stage_errors


def _build_evidence_items(
    repos: list[github_client.GitHubRepo],
    repo_languages: dict[str, dict[str, int]],
    readmes: dict[str, str],
) -> tuple[list[tuple[Skill, dict[str, Any]]], int]:
    """Extract skills from repo metadata + READMEs via the shared engine.

    Returns (evidence_items, skills_found). Origins are bounded repo tags;
    no proficiency or experience is inferred.
    """
    skill_origins: dict[str, dict[str, Any]] = {}

    def _collect(text: str, origin: str) -> None:
        for match in extract_skills(text):
            entry = skill_origins.setdefault(
                match.canonical_name,
                {"match": match, "origins": set()},
            )
            entry["origins"].add(origin)

    for repo in repos:
        corpus_parts = [
            repo.name,
            repo.full_name,
            repo.description,
            " ".join(repo.topics),
            " ".join(repo_languages.get(repo.full_name, {}).keys()),
        ]
        readme = readmes.get(repo.full_name)
        if readme:
            corpus_parts.append(readme)
        _collect("\n".join(p for p in corpus_parts if p), f"repo:{repo.full_name}")

    dictionary = get_skills_dictionary()
    items: list[tuple[Skill, dict[str, Any]]] = []
    for canonical, entry in skill_origins.items():
        match: SkillMatch = entry["match"]
        category = dictionary.get_category(canonical) or match.category
        skill, _created = Skill.objects.get_or_create(
            name=canonical, defaults={"category": category}
        )
        origins = sorted(entry["origins"])[:20]
        detail: dict[str, Any] = {"origins": origins}
        if match.matched_alias:
            detail["matched_alias"] = match.matched_alias
        items.append((skill, detail))

    items.sort(key=lambda pair: pair[0].name)
    return items, len(items)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    queue="parse_queue",
)
def sync_github_profile_task(
    self, profile_id: int, task_id: str, sync_token: str, github_username: str
) -> dict[str, Any]:
    """Sync a candidate's connected GitHub profile.

    Fetches the public profile, eligible repos, language stats, and bounded
    README text; verifies account identity; then persists the snapshot and
    replaces only ``github``-source skill evidence — all atomically.

    Args:
        profile_id: CandidateProfile ID that owns the connection.
        task_id: Sync task ID (also the status key and Celery task ID).
        sync_token: Token issued at dispatch; stale tasks fail ``superseded``.
        github_username: Lowercase-normalized username at dispatch time.

    Returns:
        Dict summarizing the outcome (counts only, no PII).
    """
    logger.info(f"GitHub sync task received: task_id={task_id}, profile_id={profile_id}")

    record = github_status.get_status(task_id)
    if record is None:
        logger.warning(f"GitHub task {task_id} has no status record (expired?)")
        raise Ignore(f"GitHub task {task_id} status record missing")

    if record["status"] in github_status.TERMINAL_STATUSES:
        logger.info(f"GitHub task {task_id} already terminal: {record['status']}")
        raise Ignore(f"GitHub task {task_id} already {record['status']}")

    lock = _ExecutionLock(f"github:lock:{task_id}")
    try:
        lock_acquired = lock.acquire()
    except Exception:  # noqa: BLE001 - lock backend unavailable: fail closed
        logger.exception(f"GitHub task {task_id}: lock backend unavailable")
        github_status.fail_status(task_id, "github_unavailable")
        raise Ignore(f"GitHub task {task_id}: lock backend unavailable") from None
    if not lock_acquired:
        logger.info(f"GitHub task {task_id} already locked, skipping duplicate")
        raise Ignore(f"GitHub task {task_id} already processing")
    lock.start_renewal()

    try:
        github_status.update_status(task_id, status=github_status.STATUS_PROCESSING)

        try:
            profile = CandidateProfile.objects.select_related("user").get(
                id=profile_id
            )
        except CandidateProfile.DoesNotExist:
            github_status.fail_status(task_id, "processing_error")
            raise Ignore(f"Profile {profile_id} not found") from None

        try:
            connection = profile.github_profile
        except CandidateGitHubProfile.DoesNotExist:
            github_status.fail_status(task_id, "disconnected")
            raise Ignore(f"GitHub task {task_id}: connection removed") from None

        if connection.sync_token is None or str(connection.sync_token) != sync_token:
            github_status.fail_status(task_id, "superseded")
            logger.info(f"GitHub task {task_id}: superseded by newer sync")
            raise Ignore(f"GitHub task {task_id}: superseded") from None

        # Claim a DB fencing token under the row lock. Persist re-verifies
        # it inside the same transaction, so even if the Redis execution
        # lock is lost mid-flight, a stale execution cannot write.
        try:
            fencing_token = github_services.claim_execution_fencing(
                connection.id, sync_token
            )
        except github_services.SyncStateError as exc:
            github_status.fail_status(task_id, exc.category)
            raise Ignore(f"GitHub task {task_id}: {exc.category}") from None

        # Identity resolution (cached GET /users/{login}).
        try:
            gh_user = github_client.get_user(connection.github_username)
        except github_client.GitHubUserNotFoundError:
            github_status.fail_status(task_id, "user_not_found")
            raise Ignore(f"GitHub task {task_id}: user not found") from None
        except github_client.GitHubAuthError:
            github_status.fail_status(task_id, "github_auth")
            raise Ignore(f"GitHub task {task_id}: auth failure") from None
        except github_client.GitHubRateLimitError as exc:
            _github_retry_or_fail(
                self, task_id, exc, "rate_limited", exc.retry_after
            )
            return {"task_id": task_id, "status": "failed"}
        except _GITHUB_TRANSIENT_ERRORS as exc:
            _github_retry_or_fail(self, task_id, exc, "github_unavailable")
            return {"task_id": task_id, "status": "failed"}
        except github_client.GitHubAPIError:
            github_status.fail_status(task_id, "github_unavailable")
            raise Ignore(f"GitHub task {task_id}: API error") from None

        # Early identity check; persist re-verifies under row lock.
        if (
            connection.github_user_id is not None
            and connection.github_user_id != gh_user.id
        ):
            github_status.fail_status(task_id, "identity_mismatch")
            raise Ignore(f"GitHub task {task_id}: identity mismatch") from None

        # Repo enumeration.
        try:
            repos = github_client.list_user_repos(
                gh_user.login, int(settings.GITHUB_MAX_REPOS)
            )
        except github_client.GitHubRateLimitError as exc:
            _github_retry_or_fail(
                self, task_id, exc, "rate_limited", exc.retry_after
            )
            return {"task_id": task_id, "status": "failed"}
        except _GITHUB_TRANSIENT_ERRORS as exc:
            _github_retry_or_fail(self, task_id, exc, "github_unavailable")
            return {"task_id": task_id, "status": "failed"}
        except github_client.GitHubAPIError:
            github_status.fail_status(task_id, "github_unavailable")
            raise Ignore(f"GitHub task {task_id}: repos API error") from None

        eligible = [r for r in repos if _is_eligible_repo(r)]

        stage_errors: list[str] = []
        evidence_items: list[tuple[Skill, dict[str, Any]]] | None = None
        skills_found = 0
        language_bytes: dict[str, int] = {}
        readmes: dict[str, str] = {}

        repo_languages: dict[str, dict[str, int]] = {}
        try:
            repo_languages, lang_errors = _fetch_repo_languages(eligible)
            stage_errors.extend(lang_errors)
            language_bytes = _aggregate_language_bytes(repo_languages)
        except github_client.GitHubRateLimitError as exc:
            _github_retry_or_fail(
                self, task_id, exc, "rate_limited", exc.retry_after
            )
            return {"task_id": task_id, "status": "failed"}
        except _GITHUB_TRANSIENT_ERRORS as exc:
            _github_retry_or_fail(self, task_id, exc, "github_unavailable")
            return {"task_id": task_id, "status": "failed"}

        try:
            readmes, readme_errors = _fetch_readmes(
                eligible, int(settings.GITHUB_MAX_README_REPOS)
            )
            stage_errors.extend(readme_errors)
        except github_client.GitHubRateLimitError as exc:
            _github_retry_or_fail(
                self, task_id, exc, "rate_limited", exc.retry_after
            )
            return {"task_id": task_id, "status": "failed"}
        except _GITHUB_TRANSIENT_ERRORS as exc:
            _github_retry_or_fail(self, task_id, exc, "github_unavailable")
            return {"task_id": task_id, "status": "failed"}

        try:
            evidence_items, skills_found = _build_evidence_items(
                eligible, repo_languages, readmes
            )
        except Exception as exc:  # noqa: BLE001 - stage isolation
            stage_errors.append("skills")
            logger.error(f"GitHub task {task_id}: skill extraction failed: {exc}")

        result_summary = {
            "repos_listed": len(repos),
            "repos_eligible": len(eligible),
            "skills_found": skills_found,
            "languages": len(language_bytes),
            "readmes": len(readmes),
            "stage_errors": sorted(set(stage_errors)),
        }

        if stage_errors:
            # Incomplete snapshot: preserve the last complete successful
            # evidence set and profile snapshot; report partial only.
            github_status.update_status(
                task_id, status=github_status.STATUS_PARTIAL, result=result_summary
            )
            logger.warning(
                f"GitHub task {task_id}: partial sync, stage_errors="
                f"{result_summary['stage_errors']} (previous snapshot kept)"
            )
            return {"task_id": task_id, "status": "partial", **result_summary}

        # Execution must still own the lock immediately before persisting;
        # a delayed execution must never overwrite a newer snapshot.
        if not lock.owns():
            logger.warning(
                f"GitHub task {task_id}: lock ownership lost before persist; "
                "aborting without writing (status left to lock owner)"
            )
            raise Ignore(f"GitHub task {task_id}: lock ownership lost")

        fields = {
            "github_login_raw": gh_user.login,
            "github_username": gh_user.login.lower(),
            "github_name": gh_user.name,
            "github_bio": gh_user.bio,
            "public_repo_count": gh_user.public_repos,
            "language_bytes": language_bytes,
        }

        try:
            github_services.persist_github_sync(
                connection.id,
                sync_token,
                gh_user.id,
                fields=fields,
                evidence_items=evidence_items,
                fencing_token=fencing_token,
            )
        except github_services.SyncStateError as exc:
            github_status.fail_status(task_id, exc.category)
            logger.info(f"GitHub task {task_id}: {exc.category} at persist")
            raise Ignore(f"GitHub task {task_id}: {exc.category}") from None
        except OperationalError as exc:
            _github_retry_or_fail(self, task_id, exc, "processing_error")
            return {"task_id": task_id, "status": "failed"}

        services.invalidate_matching_caches(profile_id)

        github_status.update_status(
            task_id, status=github_status.STATUS_COMPLETED, result=result_summary
        )
        logger.info(
            f"GitHub task {task_id}: completed "
            f"(repos={len(eligible)}, skills={skills_found}, "
            f"languages={len(language_bytes)})"
        )
        return {"task_id": task_id, "status": "completed", **result_summary}

    except Ignore:
        raise
    except _GITHUB_TRANSIENT_ERRORS as exc:
        logger.error(f"GitHub task {task_id}: transient error: {exc}")
        _github_retry_or_fail(self, task_id, exc, "github_unavailable")
        return {"task_id": task_id, "status": "failed"}
    except Exception:  # noqa: BLE001 - last-resort isolation
        logger.exception(f"GitHub task {task_id}: unexpected error")
        github_status.fail_status(task_id, "processing_error")
        raise Ignore(f"GitHub task {task_id}: unexpected error") from None
    finally:
        lock.stop()
        lock.release()


def _github_retry_or_fail(
    task: Any,
    task_id: str,
    exc: Exception,
    category: str,
    retry_after: int | None = None,
) -> None:
    """Retry transient GitHub failures up to max_retries, then mark failed."""
    if task.request.retries < task.max_retries:
        if retry_after:
            raise task.retry(countdown=retry_after, exc=exc) from None
        raise task.retry(exc=exc) from None
    github_status.fail_status(task_id, category)
