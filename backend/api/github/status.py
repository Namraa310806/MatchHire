"""Redis-backed task status store for GitHub profile sync.

Mirrors ``api.resume.status``: records live in the Django cache under
``github:task:<task_id>`` with a configurable TTL. Records contain no
tokens, raw API payloads, or PII beyond the candidate's own task state.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from django.conf import settings
from django.core.cache import cache

STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"

TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_PARTIAL, STATUS_FAILED}

VALID_STATUSES = {
    STATUS_QUEUED,
    STATUS_PROCESSING,
    STATUS_COMPLETED,
    STATUS_PARTIAL,
    STATUS_FAILED,
}

# Error categories safe to expose to candidates. Internal exception details
# are logged server-side only and never written to the status record.
ERROR_CATEGORIES = {
    "invalid_username",
    "user_not_found",
    "github_unavailable",
    "github_auth",
    "rate_limited",
    "identity_mismatch",
    "account_conflict",
    "disconnected",
    "superseded",
    "processing_error",
}

ERROR_MESSAGES = {
    "invalid_username": "The GitHub username is invalid.",
    "user_not_found": "No GitHub user exists with that username.",
    "github_unavailable": "GitHub could not be reached. Please try again later.",
    "github_auth": "GitHub authentication failed on the server.",
    "rate_limited": "GitHub rate limit reached. Please try again later.",
    "identity_mismatch": "The GitHub username no longer matches the connected account.",
    "account_conflict": "This GitHub account is already connected to another candidate.",
    "disconnected": "The GitHub account was disconnected before sync finished.",
    "superseded": "This sync was replaced by a newer request.",
    "processing_error": "GitHub sync failed unexpectedly.",
}


def _key(task_id: str) -> str:
    return f"github:task:{task_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_task_id() -> str:
    """Generate a new sync task ID (also used as the Celery task ID)."""
    return str(uuid.uuid4())


def create_status(
    task_id: str, candidate_id: int, github_username: str
) -> dict[str, Any]:
    """Create a queued status record for a newly dispatched sync."""
    record: dict[str, Any] = {
        "task_id": task_id,
        "candidate_id": candidate_id,
        "status": STATUS_QUEUED,
        "github_username": github_username,
        "error_category": None,
        "error_message": None,
        "result": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    _write(task_id, record)
    return record


def get_status(task_id: str) -> dict[str, Any] | None:
    """Return the status record, or None if missing/expired."""
    raw = cache.get(_key(task_id))
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return cast(dict[str, Any], json.loads(raw))
        except (ValueError, TypeError):
            return None
    if isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    return None


def update_status(
    task_id: str,
    *,
    status: str,
    error_category: str | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Transition a status record. Returns the updated record or None."""
    record = get_status(task_id)
    if record is None:
        return None

    record["status"] = status
    record["updated_at"] = _now()
    if error_category is not None:
        record["error_category"] = error_category
        record["error_message"] = ERROR_MESSAGES.get(
            error_category, ERROR_MESSAGES["processing_error"]
        )
    if result is not None:
        record["result"] = result
    _write(task_id, record)
    return record


def fail_status(task_id: str, error_category: str) -> dict[str, Any] | None:
    """Mark a task as failed with a safe error category."""
    if error_category not in ERROR_CATEGORIES:
        error_category = "processing_error"
    return update_status(task_id, status=STATUS_FAILED, error_category=error_category)


def _write(task_id: str, record: dict[str, Any]) -> None:
    ttl = settings.GITHUB_TASK_STATUS_TTL_SECONDS
    cache.set(_key(task_id), json.dumps(record), timeout=ttl)
