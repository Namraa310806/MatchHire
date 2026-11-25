"""Shared transactional helpers for source-aware skill evidence.

``CandidateSkill`` remains the merged skill set consumed by matching.
``CandidateSkillEvidence`` records which source (``manual``, ``resume``,
``github``) reported each skill, so one source can never overwrite or
delete another source's evidence.

INVARIANT (application-enforced, not a DB constraint): every
``CandidateSkill`` row should have at least one evidence row. All
production writers must go through these helpers; direct ORM writes can
violate the invariant. Cross-table consistency is enforced here inside
transactions, not by database constraints.

Write semantics per source:
- ``manual`` / ``resume``: additive upserts only; existing evidence and
  CandidateSkill rows are never deleted (preserves Phase 3B resume
  semantics).
- ``github``: ``replace_source_evidence`` swaps the whole source snapshot
  atomically, then reconciles CandidateSkill membership.
- ``remove_source_evidence``: disconnect path; deletes the source's
  evidence and reconciles.

``reconcile_candidate_skills`` deletes CandidateSkill rows left with zero
evidence rows. It must only run after source-scoped deletes, never after
additive writes.
"""

from typing import Any

from django.db import transaction

from api.models import (
    CandidateProfile,
    CandidateSkill,
    CandidateSkillEvidence,
    Skill,
)

SOURCE_MANUAL = "manual"
SOURCE_RESUME = "resume"
SOURCE_GITHUB = "github"

EVIDENCE_SOURCES = {SOURCE_MANUAL, SOURCE_RESUME, SOURCE_GITHUB}


def _validate_source(source: str) -> None:
    if source not in EVIDENCE_SOURCES:
        raise ValueError(f"Unknown evidence source: {source!r}")


@transaction.atomic
def link_skill(
    candidate: CandidateProfile,
    skill: Skill,
    *,
    source: str,
    detail: dict[str, Any] | None = None,
    proficiency: str = "",
) -> tuple[CandidateSkill, bool, CandidateSkillEvidence, bool]:
    """Link a skill to a candidate with source evidence (additive).

    Ensures the merged ``CandidateSkill`` row exists and upserts the
    ``(candidate, skill, source)`` evidence row. Never deletes anything.

    Returns:
        (candidate_skill, candidate_skill_created,
         evidence, evidence_created)
    """
    _validate_source(source)

    candidate_skill, cs_created = CandidateSkill.objects.get_or_create(
        candidate=candidate,
        skill=skill,
        defaults={"proficiency": proficiency},
    )

    evidence, ev_created = CandidateSkillEvidence.objects.get_or_create(
        candidate=candidate,
        skill=skill,
        source=source,
        defaults={"detail": detail or {}},
    )
    if not ev_created and detail is not None and evidence.detail != detail:
        evidence.detail = detail
        evidence.save(update_fields=["detail", "updated_at"])

    return candidate_skill, cs_created, evidence, ev_created


@transaction.atomic
def replace_source_evidence(
    candidate: CandidateProfile,
    source: str,
    items: list[tuple[Skill, dict[str, Any]]],
) -> tuple[int, int]:
    """Atomically replace all evidence for one source, then reconcile.

    Deletes only ``(candidate, source)`` evidence rows, recreates them from
    ``items`` (``(skill, detail)`` pairs), ensures merged CandidateSkill
    rows exist, and removes CandidateSkill rows left with no evidence.
    Any failure rolls back the entire operation. NOT for resume ingestion
    (resume semantics are additive).

    Returns:
        (evidence_rows_written, candidate_skills_removed)
    """
    _validate_source(source)
    if source == SOURCE_RESUME:
        raise ValueError("replace_source_evidence must not be used for resume evidence")

    CandidateSkillEvidence.objects.filter(candidate=candidate, source=source).delete()

    written = 0
    for skill, detail in items:
        link_skill(candidate, skill, source=source, detail=detail)
        written += 1

    removed = reconcile_candidate_skills(candidate)
    return written, removed


@transaction.atomic
def remove_source_evidence(candidate: CandidateProfile, source: str) -> tuple[int, int]:
    """Delete all evidence for one source, then reconcile.

    Returns:
        (evidence_rows_deleted, candidate_skills_removed)
    """
    _validate_source(source)

    deleted, _by_model = CandidateSkillEvidence.objects.filter(
        candidate=candidate, source=source
    ).delete()

    removed = reconcile_candidate_skills(candidate)
    return int(deleted), removed


def reconcile_candidate_skills(candidate: CandidateProfile) -> int:
    """Delete CandidateSkill rows that have no remaining evidence.

    Must be called inside a transaction after source-scoped evidence
    deletes. Rows supported by any remaining source (manual, resume, or
    another source's evidence) are preserved.

    Returns:
        Number of CandidateSkill rows deleted.
    """
    evidenced_skill_ids = CandidateSkillEvidence.objects.filter(
        candidate=candidate
    ).values_list("skill_id", flat=True)

    deleted, _by_model = (
        CandidateSkill.objects.filter(candidate=candidate)
        .exclude(skill_id__in=evidenced_skill_ids)
        .delete()
    )
    return int(deleted)
