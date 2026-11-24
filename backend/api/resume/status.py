"""Redis-backed task status store for resume parsing.

Status records are stored in the Django cache (Redis in deployed
environments, locmem in tests) as JSON under ``resume:task:<task_id>``
with a configurable TTL. Records contain no resume content, filesystem
paths, or internal exception details.
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
    "invalid_pdf",
    "corrupt_pdf",
    "encrypted_pdf",
    "empty_pdf",
    "empty_file",
    "file_too_large",
    "no_text_layer",
    "missing_consent",
    "resume_replaced",
    "resume_deleted",
    "file_unavailable",
    "processing_error",
}

ERROR_MESSAGES = {
    "invalid_pdf": "The uploaded file is not a valid PDF.",
    "corrupt_pdf": "The PDF could not be read.",
    "encrypted_pdf": "Password-protected PDFs are not supported.",
    "empty_pdf": "The PDF has no readable pages.",
    "empty_file": "The uploaded file is empty.",
    "file_too_large": "The file exceeds the maximum allowed size.",
    "no_text_layer": "No text layer was found; scanned PDFs are not supported.",
    "missing_consent": "Resume processing consent is required.",
    "resume_replaced": "This resume was replaced by a newer upload.",
    "resume_deleted": "The resume was deleted before processing finished.",
    "file_unavailable": "The stored resume file is unavailable.",
    "processing_error": "Resume processing failed unexpectedly.",
}


def _key(task_id: str) -> str:
    return f"resume:task:{task_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_task_id() -> str:
    """Generate a new resume parse task ID (also used as the Celery task ID)."""
    return str(uuid.uuid4())


def create_status(task_id: str, candidate_id: int, resume_name: str) -> dict[str, Any]:
    """Create a queued status record for a newly dispatched task."""
    record: dict[str, Any] = {
        "task_id": task_id,
        "candidate_id": candidate_id,
        "status": STATUS_QUEUED,
        "resume_name": resume_name,
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
    ttl = settings.RESUME_TASK_STATUS_TTL_SECONDS
    cache.set(_key(task_id), json.dumps(record), timeout=ttl)
