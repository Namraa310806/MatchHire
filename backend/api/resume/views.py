"""Resume upload, status, and deletion endpoints.

Contract (see docs/RESUME_PROCESSING.md):
- ``POST /api/resumes/``        multipart upload -> 202 Accepted
- ``GET  /api/resumes/status/<task_id>/`` -> processing status
- ``DELETE /api/resumes/``      delete stored resume (profile data retained)
"""

import logging
import uuid
from typing import Any, cast

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.models import CandidateProfile
from api.resume import services
from api.resume import status as resume_status
from api.resume.pdf import ResumeValidationError, validate_pdf_bytes
from api.tasks import parse_resume_task

logger = logging.getLogger(__name__)

_CONSENT_TRUE = {"true", "1", "on", "yes"}


def _get_profile(user: Any) -> CandidateProfile:
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return cast(CandidateProfile, profile)


def _public_status(record: dict[str, Any]) -> dict[str, Any]:
    """Return the candidate-safe subset of a status record."""
    return {
        "task_id": record["task_id"],
        "status": record["status"],
        "error_category": record.get("error_category"),
        "error_message": record.get("error_message"),
        "result": record.get("result"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }


class ResumeUploadView(APIView):
    """Accept a resume PDF for asynchronous parsing."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resume_upload"

    def post(self, request: Any) -> Response:
        profile = _get_profile(request.user)

        consent = str(request.data.get("consent", "")).strip().lower()
        if consent not in _CONSENT_TRUE:
            return Response(
                {
                    "detail": "Explicit consent is required to process a resume.",
                    "error_category": "missing_consent",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded = request.FILES.get("file") or request.FILES.get("resume")
        if uploaded is None:
            return Response(
                {"detail": "A PDF file is required.", "error_category": "empty_file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded.size is not None and uploaded.size > _max_upload_bytes():
            return Response(
                {
                    "detail": "File exceeds the maximum allowed size.",
                    "error_category": "file_too_large",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = uploaded.read()
        try:
            validate_pdf_bytes(data)
        except ResumeValidationError as exc:
            return Response(
                {"detail": str(exc), "error_category": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Safe generated storage name; no user-controlled path components
        storage_name = f"resumes/{profile.id}/{uuid.uuid4().hex}.pdf"
        old_name = profile.resume_file.name if profile.resume_file else ""
        old_uploaded_at = profile.resume_uploaded_at
        old_consent = profile.resume_consent_given

        try:
            default_storage.save(storage_name, ContentFile(data))
        except OSError as exc:
            logger.error(f"Resume storage save failed for profile {profile.id}: {exc}")
            return Response(
                {"detail": "Unable to store the uploaded file. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Point the profile at the new file before dispatch so the task and
        # eager-mode execution see consistent state.
        profile.resume_file = storage_name
        profile.resume_uploaded_at = timezone.now()
        profile.resume_consent_given = True
        profile.save(
            update_fields=[
                "resume_file",
                "resume_uploaded_at",
                "resume_consent_given",
                "updated_at",
            ]
        )

        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, storage_name)

        try:
            parse_resume_task.apply_async(
                args=[profile.id, task_id, storage_name],
                task_id=task_id,
                queue="parse_queue",
            )
        except Exception as exc:  # noqa: BLE001 - dispatch failure must not orphan state
            logger.error(f"Resume task dispatch failed for task {task_id}: {exc}")
            _rollback_upload(
                profile, storage_name, old_name, old_uploaded_at, old_consent
            )
            resume_status.fail_status(task_id, "processing_error")
            return Response(
                {"detail": "Unable to queue resume processing. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # New file is now the live resume; remove the replaced file if any.
        if old_name and old_name != storage_name:
            try:
                default_storage.delete(old_name)
            except OSError as exc:
                logger.warning(f"Could not delete replaced resume {old_name}: {exc}")

        record = resume_status.get_status(task_id) or {}
        return Response(
            {
                "task_id": task_id,
                "status": record.get("status", resume_status.STATUS_QUEUED),
                "status_url": f"/api/resumes/status/{task_id}/",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def delete(self, request: Any) -> Response:
        """Delete the stored resume file. Extracted profile data is retained."""
        profile = _get_profile(request.user)
        services.delete_resume_file(profile)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResumeStatusView(APIView):
    """Return the processing status of the caller's own resume task."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Any, task_id: str) -> Response:
        profile = _get_profile(request.user)
        record = resume_status.get_status(task_id)

        # Missing/expired records and other candidates' tasks are
        # indistinguishable to avoid leaking task existence.
        if record is None or record.get("candidate_id") != profile.id:
            return Response(
                {"detail": "Task not found or expired."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_public_status(record))


def _max_upload_bytes() -> int:
    from django.conf import settings

    return int(settings.RESUME_MAX_UPLOAD_BYTES)


def _rollback_upload(
    profile: CandidateProfile,
    new_name: str,
    old_name: str,
    old_uploaded_at: Any,
    old_consent: bool,
) -> None:
    """Restore profile file reference and remove the orphaned new file."""
    try:
        default_storage.delete(new_name)
    except OSError as exc:
        logger.warning(f"Could not delete orphaned resume {new_name}: {exc}")

    profile.resume_file = old_name
    profile.resume_uploaded_at = old_uploaded_at
    profile.resume_consent_given = old_consent
    profile.save(
        update_fields=[
            "resume_file",
            "resume_uploaded_at",
            "resume_consent_given",
            "updated_at",
        ]
    )
