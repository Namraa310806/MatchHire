"""Persistence services for GitHub connection sync and disconnect.

All multi-write operations are transactional. Account verification and
evidence replacement happen inside a single transaction so a stale or
unauthorized task can never write partial state.
"""

import logging
from typing import Any, cast

from django.db import transaction
from django.utils import timezone

from api import evidence
from api.evidence import SOURCE_GITHUB
from api.github import status as github_status
from api.models import (
    CandidateGitHubProfile,
    CandidateProfile,
    Skill,
)

logger = logging.getLogger(__name__)


# OWNERSHIP CONTRACT: the database fencing token claimed by
# ``claim_execution_fencing`` -- not Redis lock acquisition -- formally
# transfers execution ownership. Redis acquisition alone does not fence out
# the current owner: between a successor's Redis acquire and its fencing
# claim, the prior owner may still legitimately persist (it remains the last
# formal owner). Once the successor claims, the prior owner's fencing token
# mismatches inside the persist transaction and its write is rejected. The
# Redis lock is a duplicate-delivery/efficiency guard; fencing is
# authoritative.


class SyncStateError(Exception):
    """Raised when a sync task's state checks fail before persisting.

    ``category`` is a safe status error category (never contains internals).
    """

    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


@transaction.atomic
def claim_execution_fencing(connection_id: int, sync_token: str) -> int:
    """Claim the next fencing value for a sync execution.

    Locks the connection row, verifies it still exists and the sync token
    still matches, then increments ``exec_fencing``. Called once per task
    execution before fetching; the returned value must be passed to
    ``persist_github_sync`` so the persist transaction can reject any
    execution that has been superseded by a newer claim.

    Returns:
        The fencing value claimed by this execution.

    Raises:
        SyncStateError: ``disconnected`` or ``superseded``.
    """
    try:
        locked = (
            CandidateGitHubProfile.objects.select_for_update()
            .select_related("profile")
            .get(id=connection_id)
        )
    except CandidateGitHubProfile.DoesNotExist:
        raise SyncStateError("disconnected") from None

    if locked.sync_token is None or str(locked.sync_token) != sync_token:
        raise SyncStateError("superseded")

    locked.exec_fencing += 1
    locked.save(update_fields=["exec_fencing", "updated_at"])
    return int(locked.exec_fencing)


@transaction.atomic
def persist_github_sync(
    connection_id: int,
    sync_token: str,
    github_user_id: int,
    *,
    fields: dict[str, Any],
    evidence_items: list[tuple[Skill, dict[str, Any]]] | None,
    fencing_token: int | None = None,
) -> CandidateGitHubProfile:
    """Verify identity/token and persist a completed sync atomically.

    Locks the connection row and verifies, inside the transaction:
    - the connection still exists (else ``disconnected``),
    - ``sync_token`` still matches (else ``superseded``),
    - ``github_user_id`` matches the fetched identity (else
      ``identity_mismatch``; a NULL stored id is adopted).

    Then updates snapshot fields, sets ``last_synced_at``, clears
    ``active_sync_task_id``, and — when ``evidence_items`` is provided —
    replaces the candidate's ``github``-source skill evidence.

    Returns:
        The updated connection.

    Raises:
        SyncStateError: with a safe category when checks fail.
    """
    try:
        locked = (
            CandidateGitHubProfile.objects.select_for_update()
            .select_related("profile")
            .get(id=connection_id)
        )
    except CandidateGitHubProfile.DoesNotExist:
        raise SyncStateError("disconnected") from None

    if locked.sync_token is None or str(locked.sync_token) != sync_token:
        raise SyncStateError("superseded")

    if locked.github_user_id is None:
        locked.github_user_id = github_user_id
    elif locked.github_user_id != github_user_id:
        raise SyncStateError("identity_mismatch")

    # Fencing guard (authoritative): under the same row lock as all other
    # checks, inside this transaction. A newer execution's claim increments
    # exec_fencing, so a stale execution's token no longer matches and its
    # write is rejected even if its Redis lock check passed moments earlier.
    if fencing_token is not None and locked.exec_fencing != fencing_token:
        raise SyncStateError("superseded")

    for key, value in fields.items():
        setattr(locked, key, value)
    locked.last_synced_at = timezone.now()
    locked.active_sync_task_id = None
    update_fields = [
        *fields.keys(),
        "github_user_id",
        "last_synced_at",
        "active_sync_task_id",
        "updated_at",
    ]
    locked.save(update_fields=sorted(set(update_fields)))

    if evidence_items is not None:
        evidence.replace_source_evidence(locked.profile, SOURCE_GITHUB, evidence_items)

    return cast(CandidateGitHubProfile, locked)


@transaction.atomic
def disconnect_github(profile: CandidateProfile) -> int | None:
    """Disconnect GitHub: remove github evidence and delete the connection.

    Ordering inside the transaction: capture the pending task id, remove
    ``github``-source evidence and reconcile merged skills, then delete the
    connection row. The caller fails the pending status record afterwards
    (cache writes are not transactional).

    Returns:
        The pending sync task id, or None if there was no connection.
    """
    try:
        connection = CandidateGitHubProfile.objects.select_for_update().get(
            profile=profile
        )
    except CandidateGitHubProfile.DoesNotExist:
        return None

    pending_task_id = connection.active_sync_task_id
    evidence.remove_source_evidence(profile, SOURCE_GITHUB)
    connection.delete()
    return cast(int | None, pending_task_id)


def fail_pending_sync(task_id: str | None, category: str = "disconnected") -> None:
    """Mark a pending sync status record failed (best-effort, post-commit)."""
    if task_id:
        github_status.fail_status(task_id, category)
