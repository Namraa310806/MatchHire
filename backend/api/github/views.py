"""GitHub connection endpoints.

Contract (see docs/GITHUB_INTEGRATION.md):
- ``POST   /api/profile/github/``              connect or re-sync -> 202
- ``GET    /api/profile/github/``              own connection state
- ``DELETE /api/profile/github/``              disconnect (idempotent 204)
- ``GET    /api/profile/github/status/<task_id>/``  own sync task status
"""

import logging
import uuid
from typing import Any, cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.github import client as github_client
from api.github import services as github_services
from api.github import status as github_status
from api.github.validation import normalize_username
from api.models import CandidateGitHubProfile, CandidateProfile
from api.resume.services import invalidate_matching_caches
from api.tasks import sync_github_profile_task

logger = logging.getLogger(__name__)


def _get_profile(user: Any) -> CandidateProfile:
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return cast(CandidateProfile, profile)


def _public_connection(conn: CandidateGitHubProfile) -> dict[str, Any]:
    """Candidate-safe connection fields. Never includes tokens or sync_token."""
    pending = None
    if conn.active_sync_task_id:
        record = github_status.get_status(conn.active_sync_task_id)
        if record is not None:
            pending = {
                "task_id": record["task_id"],
                "status": record["status"],
                "status_url": f"/api/profile/github/status/{record['task_id']}/",
            }
    return {
        "connected": True,
        "github_username": conn.github_username,
        "github_login": conn.github_login_raw,
        "github_name": conn.github_name,
        "github_bio": conn.github_bio,
        "public_repo_count": conn.public_repo_count,
        "language_bytes": conn.language_bytes,
        "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
        "last_synced_at": (
            conn.last_synced_at.isoformat() if conn.last_synced_at else None
        ),
        "pending_sync": pending,
    }


def _public_status(record: dict[str, Any]) -> dict[str, Any]:
    """Candidate-safe subset of a sync status record."""
    return {
        "task_id": record["task_id"],
        "status": record["status"],
        "github_username": record.get("github_username"),
        "error_category": record.get("error_category"),
        "error_message": record.get("error_message"),
        "result": record.get("result"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }


def _github_error_response(exc: Exception) -> Response:
    """Map GitHub client failures to safe API responses (no internals)."""
    if isinstance(exc, github_client.GitHubUserNotFoundError):
        return Response(
            {
                "detail": "No GitHub user exists with that username.",
                "error_category": "user_not_found",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(exc, github_client.GitHubAuthError):
        logger.error("GitHub auth error during connect: %s", exc)
        return Response(
            {
                "detail": "GitHub authentication failed on the server.",
                "error_category": "github_auth",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    # Rate limit, server errors, timeouts, connection errors, invalid payloads
    logger.warning("GitHub unavailable during connect: %s", exc)
    return Response(
        {
            "detail": "GitHub could not be reached. Please try again later.",
            "error_category": "github_unavailable",
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class GitHubConnectionView(APIView):
    """Connect, inspect, and disconnect the caller's GitHub account."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "github_sync"

    def check_throttles(self, request: Any) -> None:
        # Only connect/re-sync (POST) consumes the sync throttle budget;
        # status reads and disconnect must not be starved by it.
        if request.method == "POST":
            super().check_throttles(request)

    def get(self, request: Any) -> Response:
        profile = _get_profile(request.user)
        try:
            conn = profile.github_profile
        except CandidateGitHubProfile.DoesNotExist:
            return Response(
                {"detail": "No GitHub account connected."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_public_connection(conn))

    def post(self, request: Any) -> Response:
        profile = _get_profile(request.user)

        username = normalize_username(request.data.get("github_username"))
        if username is None:
            return Response(
                {
                    "detail": "A valid GitHub username is required.",
                    "error_category": "invalid_username",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve identity BEFORE touching connection state. Failures here
        # leave the existing connection and evidence untouched.
        try:
            gh_user = github_client.get_user(username)
        except Exception as exc:  # noqa: BLE001 - mapped to safe responses
            return _github_error_response(exc)

        try:
            existing = profile.github_profile
        except CandidateGitHubProfile.DoesNotExist:
            existing = None

        if existing is not None:
            if (
                existing.github_user_id is not None
                and existing.github_user_id != gh_user.id
            ):
                # The submitted username resolves to a different GitHub
                # account than the connected identity. Never transfer or
                # silently re-point a connection; disconnect first.
                return Response(
                    {
                        "detail": (
                            "That username belongs to a different GitHub "
                            "account. Disconnect the current account first."
                        ),
                        "error_category": "identity_mismatch",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            conn = existing
        else:
            # github_user_id is the authoritative identity; also guard the
            # unique username against a different account holding the name.
            conflict = (
                CandidateGitHubProfile.objects.filter(
                    github_user_id=gh_user.id
                ).exists()
                or CandidateGitHubProfile.objects.filter(
                    github_username=username
                ).exists()
            )
            if conflict:
                return Response(
                    {
                        "detail": "This GitHub account is already connected.",
                        "error_category": "account_conflict",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            conn = CandidateGitHubProfile(profile=profile)

        # Snapshot previous state for dispatch-failure rollback.
        had_connection = existing is not None
        prev_state = (
            {
                "github_user_id": existing.github_user_id,
                "github_username": existing.github_username,
                "github_login_raw": existing.github_login_raw,
                "github_name": existing.github_name,
                "github_bio": existing.github_bio,
                "public_repo_count": existing.public_repo_count,
                "language_bytes": existing.language_bytes,
                "sync_token": existing.sync_token,
                "active_sync_task_id": existing.active_sync_task_id,
                "last_synced_at": existing.last_synced_at,
            }
            if had_connection and existing is not None
            else None
        )

        task_id = github_status.new_task_id()
        sync_token = uuid.uuid4()

        conn.github_user_id = gh_user.id
        conn.github_username = gh_user.login.lower()
        conn.github_login_raw = gh_user.login
        conn.github_name = gh_user.name
        conn.github_bio = gh_user.bio
        conn.public_repo_count = gh_user.public_repos
        conn.sync_token = sync_token
        conn.active_sync_task_id = task_id
        conn.save()

        github_status.create_status(task_id, profile.id, conn.github_username)

        try:
            sync_github_profile_task.apply_async(
                args=[profile.id, task_id, str(sync_token), conn.github_username],
                task_id=task_id,
                queue="parse_queue",
            )
        except Exception as exc:  # noqa: BLE001 - dispatch failure must not orphan state
            logger.error(f"GitHub sync dispatch failed for task {task_id}: {exc}")
            _rollback_connection(conn, had_connection, prev_state)
            github_status.fail_status(task_id, "processing_error")
            return Response(
                {"detail": "Unable to queue GitHub sync. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        record = github_status.get_status(task_id) or {}
        return Response(
            {
                "task_id": task_id,
                "status": record.get("status", github_status.STATUS_QUEUED),
                "status_url": f"/api/profile/github/status/{task_id}/",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def delete(self, request: Any) -> Response:
        """Disconnect GitHub. Removes only github-source evidence; idempotent."""
        profile = _get_profile(request.user)

        pending_task_id = github_services.disconnect_github(profile)
        github_services.fail_pending_sync(pending_task_id, "disconnected")
        invalidate_matching_caches(profile.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GitHubSyncStatusView(APIView):
    """Return the processing status of the caller's own GitHub sync task."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Any, task_id: str) -> Response:
        profile = _get_profile(request.user)
        record = github_status.get_status(task_id)

        # Missing/expired records and other candidates' tasks are
        # indistinguishable to avoid leaking task existence.
        if record is None or record.get("candidate_id") != profile.id:
            return Response(
                {"detail": "Task not found or expired."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_public_status(record))


def _rollback_connection(
    conn: CandidateGitHubProfile,
    had_connection: bool,
    prev_state: dict[str, Any] | None,
) -> None:
    """Restore pre-dispatch connection state after a dispatch failure."""
    if had_connection and prev_state is not None:
        for key, value in prev_state.items():
            setattr(conn, key, value)
        conn.save()
    else:
        conn.delete()
