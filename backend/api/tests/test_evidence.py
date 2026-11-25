"""Tests for source-aware skill evidence helpers and writer integration.

Covers the evidence invariant: every production CandidateSkill write path
(resume persistence, seed command, evidence helpers) maintains
CandidateSkillEvidence rows, and source-scoped operations never touch
other sources' evidence.
"""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.test import override_settings

from api import evidence
from api.extraction import ExperienceEstimate, SkillMatch
from api.models import (
    CandidateProfile,
    CandidateSkill,
    CandidateSkillEvidence,
    Skill,
)
from api.resume.services import persist_resume_extraction

User = get_user_model()


@pytest.fixture
def profile(db):
    user = User.objects.create_user(email="evidence@example.com", password="pw")
    return CandidateProfile.objects.create(user=user)


@pytest.fixture
def skill_set(db):
    return {
        name: Skill.objects.create(name=name, category="test")
        for name in ("Python", "Django", "React", "Vue", "Go")
    }


def _experience() -> ExperienceEstimate:
    return ExperienceEstimate(total_years=None, confidence="none", methodology="test")


class TestLinkSkill:
    def test_creates_candidate_skill_and_evidence(self, profile, skill_set):
        cs, cs_created, ev, ev_created = evidence.link_skill(
            profile,
            skill_set["Python"],
            source=evidence.SOURCE_RESUME,
            detail={"matched_alias": "py"},
        )
        assert cs_created and ev_created
        assert ev.source == "resume"
        assert ev.detail == {"matched_alias": "py"}
        assert CandidateSkill.objects.filter(candidate=profile).count() == 1
        assert CandidateSkillEvidence.objects.count() == 1

    def test_idempotent_upsert_updates_detail(self, profile, skill_set):
        evidence.link_skill(
            profile, skill_set["Python"], source="manual", detail={"a": 1}
        )
        _cs, _c, ev, ev_created = evidence.link_skill(
            profile, skill_set["Python"], source="manual", detail={"a": 2}
        )
        assert not ev_created
        ev.refresh_from_db()
        assert ev.detail == {"a": 2}
        assert CandidateSkillEvidence.objects.count() == 1
        assert CandidateSkill.objects.count() == 1

    def test_same_skill_multiple_sources_coexist(self, profile, skill_set):
        evidence.link_skill(profile, skill_set["Python"], source="resume")
        evidence.link_skill(profile, skill_set["Python"], source="github")
        assert (
            CandidateSkillEvidence.objects.filter(
                candidate=profile, skill=skill_set["Python"]
            ).count()
            == 2
        )
        # One merged CandidateSkill row regardless of source count.
        assert (
            CandidateSkill.objects.filter(
                candidate=profile, skill=skill_set["Python"]
            ).count()
            == 1
        )

    def test_invalid_source_rejected(self, profile, skill_set):
        with pytest.raises(ValueError):
            evidence.link_skill(profile, skill_set["Python"], source="bogus")


class TestResumeIntegration:
    def test_resume_persist_creates_resume_evidence(self, profile, skill_set):
        persist_resume_extraction(
            profile,
            [SkillMatch(canonical_name="Python", category="test", matched_alias="py")],
            [],
            _experience(),
        )
        ev = CandidateSkillEvidence.objects.get(
            candidate=profile, skill=skill_set["Python"], source="resume"
        )
        assert ev.detail == {"matched_alias": "py"}

    def test_resume_reparse_is_additive(self, profile, skill_set):
        persist_resume_extraction(
            profile,
            [SkillMatch(canonical_name="Python", category="test")],
            [],
            _experience(),
        )
        persist_resume_extraction(
            profile,
            [SkillMatch(canonical_name="Django", category="test")],
            [],
            _experience(),
        )
        # Python evidence and CandidateSkill survive a re-parse that
        # no longer reports it (Phase 3B additive semantics preserved).
        assert (
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="resume"
            ).count()
            == 2
        )
        assert CandidateSkill.objects.filter(candidate=profile).count() == 2

    def test_resume_does_not_duplicate_evidence(self, profile, skill_set):
        match = SkillMatch(canonical_name="Python", category="test")
        persist_resume_extraction(profile, [match], [], _experience())
        persist_resume_extraction(profile, [match], [], _experience())
        assert (
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="resume"
            ).count()
            == 1
        )

    def test_resume_preserves_other_sources(self, profile, skill_set):
        evidence.link_skill(
            profile, skill_set["Python"], source="manual", detail={"origin": "user"}
        )
        persist_resume_extraction(
            profile,
            [SkillMatch(canonical_name="Python", category="test")],
            [],
            _experience(),
        )
        sources = set(
            CandidateSkillEvidence.objects.filter(
                candidate=profile, skill=skill_set["Python"]
            ).values_list("source", flat=True)
        )
        assert sources == {"manual", "resume"}
        assert (
            CandidateSkill.objects.filter(
                candidate=profile, skill=skill_set["Python"]
            ).count()
            == 1
        )


class TestSourceScopedOperations:
    def _populate(self, profile, skill_set):
        evidence.link_skill(profile, skill_set["Python"], source="manual")
        evidence.link_skill(profile, skill_set["Django"], source="resume")
        evidence.replace_source_evidence(
            profile,
            "github",
            [
                (skill_set["React"], {"origins": ["language:TypeScript"]}),
                (skill_set["Vue"], {}),
            ],
        )

    def test_replace_only_affects_own_source(self, profile, skill_set):
        self._populate(profile, skill_set)
        evidence.replace_source_evidence(
            profile, "github", [(skill_set["React"], {}), (skill_set["Go"], {})]
        )

        github_sources = set(
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="github"
            ).values_list("skill__name", flat=True)
        )
        assert github_sources == {"React", "Go"}

        # Other sources untouched.
        assert CandidateSkillEvidence.objects.filter(
            candidate=profile, source="manual", skill=skill_set["Python"]
        ).exists()
        assert CandidateSkillEvidence.objects.filter(
            candidate=profile, source="resume", skill=skill_set["Django"]
        ).exists()

        # Vue lost its only evidence -> CandidateSkill removed.
        remaining = set(
            CandidateSkill.objects.filter(candidate=profile).values_list(
                "skill__name", flat=True
            )
        )
        assert remaining == {"Python", "Django", "React", "Go"}

    def test_github_removal_preserves_resume_and_manual(self, profile, skill_set):
        # React supported by both github and resume.
        evidence.link_skill(profile, skill_set["React"], source="resume")
        evidence.replace_source_evidence(
            profile,
            "github",
            [(skill_set["React"], {}), (skill_set["Vue"], {})],
        )

        evidence.remove_source_evidence(profile, "github")

        assert not CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        ).exists()
        remaining = set(
            CandidateSkill.objects.filter(candidate=profile).values_list(
                "skill__name", flat=True
            )
        )
        assert remaining == {"React"}  # Vue unsupported -> removed
        assert CandidateSkillEvidence.objects.filter(
            candidate=profile, source="resume", skill=skill_set["React"]
        ).exists()

    def test_replace_rolls_back_on_failure(self, profile, skill_set):
        self._populate(profile, skill_set)
        before = set(
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="github"
            ).values_list("skill__name", flat=True)
        )

        with pytest.raises(IntegrityError):
            evidence.replace_source_evidence(
                profile,
                "github",
                [(skill_set["Go"], {}), (None, {})],  # type: ignore[list-item]
            )

        after = set(
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="github"
            ).values_list("skill__name", flat=True)
        )
        assert after == before  # {"React", "Vue"} — nothing partially applied

    def test_replace_rejects_resume_source(self, profile, skill_set):
        with pytest.raises(ValueError):
            evidence.replace_source_evidence(
                profile, "resume", [(skill_set["Python"], {})]
            )


class TestReconcile:
    def test_removes_only_unevidenced_rows(self, profile, skill_set):
        # Direct ORM write simulates a legacy/fixture row with no evidence.
        CandidateSkill.objects.create(candidate=profile, skill=skill_set["Python"])
        evidence.link_skill(profile, skill_set["Django"], source="manual")

        removed = evidence.reconcile_candidate_skills(profile)

        assert removed == 1
        remaining = set(
            CandidateSkill.objects.filter(candidate=profile).values_list(
                "skill__name", flat=True
            )
        )
        assert remaining == {"Django"}


class TestMigrationBackfill:
    def test_backfill_labels_existing_rows_manual(self, profile, skill_set):
        """The 0009 data migration backfills 'manual' evidence, idempotently."""
        CandidateSkill.objects.create(candidate=profile, skill=skill_set["Python"])
        CandidateSkill.objects.create(candidate=profile, skill=skill_set["Django"])

        migration = importlib.import_module(
            "api.migrations.0009_candidategithubprofile_candidateskillevidence"
        )
        migration.backfill_manual_skill_evidence(apps, None)
        migration.backfill_manual_skill_evidence(apps, None)  # idempotent

        assert (
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="manual"
            ).count()
            == 2
        )
        assert not CandidateSkillEvidence.objects.exclude(source="manual").exists()


class TestSeedEvidence:
    def test_seed_writes_manual_evidence_idempotently(self, db):
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")
            first_evidence = CandidateSkillEvidence.objects.count()
            first_candidate_skills = CandidateSkill.objects.count()
            call_command("seed_dev_data")

        assert CandidateSkillEvidence.objects.count() == first_evidence
        assert CandidateSkill.objects.count() == first_candidate_skills

        # Every seeded CandidateSkill has manual evidence.
        for cs in CandidateSkill.objects.all():
            assert CandidateSkillEvidence.objects.filter(
                candidate=cs.candidate, skill=cs.skill, source="manual"
            ).exists()
