"""Tests for seed_dev_data management command and domain validation."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from api.models import (
    ApplicationClick,
    CandidateProfile,
    CandidateSkill,
    Company,
    IngestionSource,
    Job,
    JobSkill,
    MatchScore,
    Skill,
    WorkExperience,
)

User = get_user_model()


class TestSeedDevDataCommand:
    """Tests for the seed_dev_data management command."""

    def test_command_creates_expected_dataset(self, db):
        """Test that first execution creates the expected dataset."""
        # Run the command with DEBUG=True
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify companies
        assert Company.objects.count() == 3
        assert IngestionSource.objects.count() == 3

        # Verify jobs (6 jobs from DevSeedScraper)
        assert Job.objects.count() == 6

        # Verify users and profiles
        assert User.objects.count() == 2
        assert CandidateProfile.objects.count() == 2

        # Verify skills (20 skills defined in command)
        assert Skill.objects.count() >= 20

        # Verify candidate skills
        assert CandidateSkill.objects.count() >= 10  # At least 5 per candidate

        # Verify work experience
        assert WorkExperience.objects.count() >= 1  # At least 1 for candidate1

        # Verify match scores (2 candidates × 6 jobs = 12 scores)
        assert MatchScore.objects.count() == 12

        # Verify application clicks (high-scoring matches only)
        assert ApplicationClick.objects.count() >= 1

    def test_command_is_idempotent(self, db):
        """Test that second execution creates no duplicate records."""
        # First run
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")
        first_company_count = Company.objects.count()
        first_job_count = Job.objects.count()
        first_user_count = User.objects.count()
        first_profile_count = CandidateProfile.objects.count()
        first_skill_count = Skill.objects.count()
        first_match_count = MatchScore.objects.count()

        # Second run
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify no duplicates
        assert Company.objects.count() == first_company_count
        assert Job.objects.count() == first_job_count
        assert User.objects.count() == first_user_count
        assert CandidateProfile.objects.count() == first_profile_count
        assert Skill.objects.count() == first_skill_count
        assert MatchScore.objects.count() == first_match_count

    def test_command_preserves_stable_relationships(self, db):
        """Test that repeated execution preserves stable relationships."""
        # First run
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Record relationships
        user1 = User.objects.get(email="candidate1@example.invalid")
        profile1 = user1.candidateprofile
        skills1 = set(profile1.candidateskill_set.values_list("skill__name", flat=True))

        # Second run
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify relationships preserved
        user1_reloaded = User.objects.get(email="candidate1@example.invalid")
        profile1_reloaded = user1_reloaded.candidateprofile
        skills1_reloaded = set(
            profile1_reloaded.candidateskill_set.values_list("skill__name", flat=True)
        )

        assert skills1 == skills1_reloaded

    def test_command_refuses_to_run_in_production(self, db):
        """Test that the command refuses to run when DEBUG=False."""
        with override_settings(DEBUG=False):
            with pytest.raises(CommandError) as exc_info:
                call_command("seed_dev_data")

            assert "cannot run in production" in str(exc_info.value)

    def test_command_does_not_delete_existing_data(self, db):
        """Test that the command does not delete existing unrelated data."""
        # Create some unrelated data
        Company.objects.create(
            name="Unrelated Company",
            website="https://unrelated.example.invalid",
            description="Unrelated company for testing",
        )
        User.objects.create_user(
            email="unrelated@example.invalid", password="password"
        )

        # Run seed command
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify unrelated data still exists
        assert Company.objects.filter(name="Unrelated Company").exists()
        assert User.objects.filter(email="unrelated@example.invalid").exists()

    def test_command_uses_transaction_safety(self, db):
        """Test that a failure midway through seeding rolls back the transaction."""
        # Create a company before seeding to verify it remains unchanged on failure
        Company.objects.create(
            name="PreExisting Company",
            website="https://preexisting.example.invalid",
            description="Company created before seed attempt",
        )
        pre_company_count = Company.objects.count()

        # Test transaction safety by triggering a real failure
        # We'll patch the Skill.objects.get_or_create to fail on first call
        from unittest.mock import patch

        original_get_or_create = Skill.objects.get_or_create

        call_count = [0]

        def failing_get_or_create(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # Fail on first skill creation
                raise RuntimeError("Simulated database failure")
            return original_get_or_create(*args, **kwargs)

        with override_settings(DEBUG=True):
            with patch.object(Skill.objects, "get_or_create", failing_get_or_create):
                with pytest.raises(CommandError, match="Failed to seed development data"):
                    call_command("seed_dev_data")

        # Verify transaction rolled back - company count should be unchanged
        assert Company.objects.count() == pre_company_count
        # Verify the pre-existing company still exists
        assert Company.objects.filter(name="PreExisting Company").exists()
        # Verify no new skills were created (rollback worked)
        assert Skill.objects.count() == 0

    def test_synthetic_jobs_use_ingestion_pipeline(self, db):
        """Test that synthetic jobs enter through the approved ingestion pipeline."""
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify all jobs have valid source and company
        for job in Job.objects.all():
            assert job.source is not None
            assert job.company is not None
            assert job.source.scraper_class == "DevSeedScraper"
            assert job.external_id is not None  # All seeded jobs have external IDs

        # Verify jobs have job_hash (computed by pipeline)
        for job in Job.objects.all():
            assert job.job_hash is not None
            assert len(job.job_hash) == 64  # SHA-256 hex length

    def test_synthetic_data_is_clearly_fictional(self, db):
        """Test that all synthetic data is clearly marked as fictional."""
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

        # Verify companies use example.invalid domains
        for company in Company.objects.all():
            assert "example.invalid" in company.website

        # Verify job application URLs use example.invalid
        for job in Job.objects.all():
            assert "example.invalid" in job.application_url

        # Verify candidate emails use example.invalid
        for user in User.objects.all():
            assert "example.invalid" in user.email


class TestDomainValidation:
    """Tests for domain-level validation of relationships and constraints."""

    @pytest.fixture(autouse=True)
    def setup_seed_data(self, db):
        """Seed data before each domain validation test."""
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")

    def test_user_to_candidate_profile_relationship(self, db):
        """Test User ↔ CandidateProfile relationship."""
        # Each user should have exactly one profile
        for user in User.objects.all():
            assert hasattr(user, "candidateprofile")
            assert user.candidateprofile is not None

        # Each profile should have exactly one user
        for profile in CandidateProfile.objects.all():
            assert profile.user is not None

    def test_candidate_profile_to_skill_relationships(self, db):
        """Test CandidateProfile ↔ CandidateSkill ↔ Skill relationships."""
        # Verify foreign keys point to valid records
        for candidate_skill in CandidateSkill.objects.all():
            assert candidate_skill.candidate is not None
            assert candidate_skill.skill is not None
            assert CandidateProfile.objects.filter(
                id=candidate_skill.candidate.id
            ).exists()
            assert Skill.objects.filter(id=candidate_skill.skill.id).exists()

        # Verify unique constraint (candidate, skill)
        for profile in CandidateProfile.objects.all():
            skill_ids = list(
                profile.candidateskill_set.values_list("skill__id", flat=True)
            )
            assert len(skill_ids) == len(set(skill_ids))  # No duplicates

    def test_candidate_profile_to_work_experience_relationship(self, db):
        """Test CandidateProfile ↔ WorkExperience relationship."""
        # Verify foreign keys point to valid records
        for work_exp in WorkExperience.objects.all():
            assert work_exp.candidate is not None
            assert CandidateProfile.objects.filter(
                id=work_exp.candidate.id
            ).exists()

        # Verify experience belongs to the correct candidate
        for profile in CandidateProfile.objects.all():
            work_exps = profile.workexperience_set.all()
            for exp in work_exps:
                assert exp.candidate == profile

    def test_company_to_job_relationship(self, db):
        """Test Company ↔ Job relationship."""
        # Verify foreign keys point to valid records
        for job in Job.objects.all():
            assert job.company is not None
            assert Company.objects.filter(id=job.company.id).exists()

        # Verify jobs belong to the correct company
        for company in Company.objects.all():
            jobs = company.job_set.all()
            for job in jobs:
                assert job.company == company

    def test_ingestion_source_to_job_relationship(self, db):
        """Test IngestionSource ↔ Job relationship."""
        # Verify foreign keys point to valid records
        for job in Job.objects.all():
            assert job.source is not None
            assert IngestionSource.objects.filter(id=job.source.id).exists()

        # Verify jobs belong to the correct source
        for source in IngestionSource.objects.all():
            jobs = source.job_set.all()
            for job in jobs:
                assert job.source == source

    def test_job_to_skill_relationships(self, db):
        """Test Job ↔ JobSkill ↔ Skill relationships."""
        # Verify foreign keys point to valid records
        for job_skill in JobSkill.objects.all():
            assert job_skill.job is not None
            assert job_skill.skill is not None
            assert Job.objects.filter(id=job_skill.job.id).exists()
            assert Skill.objects.filter(id=job_skill.skill.id).exists()

        # Verify unique constraint (job, skill)
        for job in Job.objects.all():
            skill_ids = list(job.jobskill_set.values_list("skill__id", flat=True))
            assert len(skill_ids) == len(set(skill_ids))  # No duplicates

    def test_candidate_job_match_score_relationships(self, db):
        """Test CandidateProfile ↔ MatchScore ↔ Job relationships."""
        # Verify foreign keys point to valid records
        for match_score in MatchScore.objects.all():
            assert match_score.candidate is not None
            assert match_score.job is not None
            assert CandidateProfile.objects.filter(
                id=match_score.candidate.id
            ).exists()
            assert Job.objects.filter(id=match_score.job.id).exists()

        # Verify unique constraint (candidate, job)
        for profile in CandidateProfile.objects.all():
            job_ids = list(profile.matchscore_set.values_list("job__id", flat=True))
            assert len(job_ids) == len(set(job_ids))  # No duplicates

        # Verify match scores are in valid range
        for match_score in MatchScore.objects.all():
            assert Decimal("0.0") <= match_score.base_score <= Decimal("1.0")
            assert Decimal("0.0") <= match_score.final_score <= Decimal("1.0")

    def test_candidate_job_application_click_relationships(self, db):
        """Test CandidateProfile ↔ ApplicationClick ↔ Job relationships."""
        # Verify foreign keys point to valid records
        for app_click in ApplicationClick.objects.all():
            assert app_click.candidate is not None
            assert app_click.job is not None
            assert CandidateProfile.objects.filter(
                id=app_click.candidate.id
            ).exists()
            assert Job.objects.filter(id=app_click.job.id).exists()

        # Verify clicks belong to the correct candidate and job
        for profile in CandidateProfile.objects.all():
            clicks = profile.applicationclick_set.all()
            for click in clicks:
                assert click.candidate == profile

    def test_required_fields_populated(self, db):
        """Test that required fields are populated."""
        # Verify users
        for user in User.objects.all():
            assert user.email
            assert user.password

        # Verify candidate profiles
        for profile in CandidateProfile.objects.all():
            assert profile.user is not None

        # Verify jobs
        for job in Job.objects.all():
            assert job.title
            assert job.description
            assert job.application_url
            assert job.source is not None
            assert job.company is not None

        # Verify skills
        for skill in Skill.objects.all():
            assert skill.name

    def test_nullable_fields_used_correctly(self, db):
        """Test that nullable fields are used correctly."""
        # Verify job nullable fields can be None
        for job in Job.objects.all():
            # These fields are nullable
            assert job.requirements is None or isinstance(job.requirements, str)
            assert job.location is None or isinstance(job.location, str)
            assert job.remote_type is None or isinstance(job.remote_type, str)
            assert job.role_type is None or isinstance(job.role_type, str)

    def test_job_deduplication_intact(self, db):
        """Test that job deduplication remains intact."""
        # Run seed command twice
        with override_settings(DEBUG=True):
            call_command("seed_dev_data")
        first_job_count = Job.objects.count()

        with override_settings(DEBUG=True):
            call_command("seed_dev_data")
        second_job_count = Job.objects.count()

        # Verify no duplicate jobs created
        assert first_job_count == second_job_count

        # Verify unique constraint (source, external_id) works
        for job in Job.objects.all():
            duplicates = Job.objects.filter(
                source=job.source, external_id=job.external_id
            )
            assert duplicates.count() == 1

    def test_foreign_key_integrity(self, db):
        """Test that foreign keys maintain integrity."""
        # Verify all foreign keys point to existing records
        for candidate_skill in CandidateSkill.objects.all():
            assert CandidateProfile.objects.filter(
                id=candidate_skill.candidate_id
            ).exists()
            assert Skill.objects.filter(id=candidate_skill.skill_id).exists()

        for work_exp in WorkExperience.objects.all():
            assert CandidateProfile.objects.filter(
                id=work_exp.candidate_id
            ).exists()

        for job in Job.objects.all():
            assert IngestionSource.objects.filter(id=job.source_id).exists()
            assert Company.objects.filter(id=job.company_id).exists()

        for job_skill in JobSkill.objects.all():
            assert Job.objects.filter(id=job_skill.job_id).exists()
            assert Skill.objects.filter(id=job_skill.skill_id).exists()

        for match_score in MatchScore.objects.all():
            assert CandidateProfile.objects.filter(
                id=match_score.candidate_id
            ).exists()
            assert Job.objects.filter(id=match_score.job_id).exists()

        for app_click in ApplicationClick.objects.all():
            assert CandidateProfile.objects.filter(
                id=app_click.candidate_id
            ).exists()
            assert Job.objects.filter(id=app_click.job_id).exists()

    def test_unique_constraints_prevent_duplicates(self, db):
        """Test that unique constraints prevent duplicate logical relationships."""
        # Verify unique constraints exist in model metadata
        assert ("candidate", "skill") in CandidateSkill._meta.unique_together
        assert ("job", "skill") in JobSkill._meta.unique_together

    def test_no_invalid_cross_user_relationships(self, db):
        """Test that no invalid cross-user or cross-company relationships exist."""
        # Verify all candidate skills belong to the correct candidate
        for profile in CandidateProfile.objects.all():
            skills = profile.candidateskill_set.all()
            for skill_rel in skills:
                assert skill_rel.candidate == profile

        # Verify all work experience belongs to the correct candidate
        for profile in CandidateProfile.objects.all():
            work_exps = profile.workexperience_set.all()
            for exp in work_exps:
                assert exp.candidate == profile

        # Verify all match scores reference valid candidate-job pairs
        for match_score in MatchScore.objects.all():
            candidate = match_score.candidate
            job = match_score.job
            assert CandidateProfile.objects.filter(id=candidate.id).exists()
            assert Job.objects.filter(id=job.id).exists()

    def test_subscription_model_does_not_exist(self, db):
        """Test that Subscription model does not exist (deferred per spec)."""
        # Verify Subscription model is not in the codebase
        import importlib.util

        spec = importlib.util.find_spec("api.models")
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            assert not hasattr(module, "Subscription"), "Subscription model should not exist"
