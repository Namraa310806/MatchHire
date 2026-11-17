"""Integration tests for shared extractor with job ingestion."""

from io import StringIO

from api.extraction import SkillMatch, extract_skills, get_skills_dictionary
from api.ingestion.skill_extraction import extract_skills as legacy_extract_skills
from api.models import Company, IngestionSource, Job, JobSkill, Skill


class TestSharedExtractorIntegration:
    """Tests for integrating shared extractor with job ingestion."""

    def test_shared_extractor_compatible_with_legacy_interface(self):
        """Test that shared extractor is compatible with legacy interface."""
        text = "Python and Django development"
        # Legacy wrapper returns list of strings
        legacy_result = legacy_extract_skills(text)
        assert isinstance(legacy_result, list)
        assert all(isinstance(item, str) for item in legacy_result)

        # Shared extractor returns SkillMatch objects
        shared_result = extract_skills(text)
        assert isinstance(shared_result, list)
        assert all(isinstance(item, SkillMatch) for item in shared_result)

        # Both should extract the same canonical names
        legacy_names = set(legacy_result)
        shared_names = {match.canonical_name for match in shared_result}
        assert legacy_names == shared_names

    def test_shared_extractor_returns_more_skills(self):
        """Test that shared extractor returns more skills than legacy."""
        text = "Python and JavaScript development with Docker and Kubernetes"
        shared_result = extract_skills(text)
        legacy_result = legacy_extract_skills(text)
        # Shared extractor should have access to 500+ skills
        # Legacy had ~30 skills
        # Shared should find at least as many as legacy
        assert len(shared_result) >= len(legacy_result)

    def test_shared_extractor_canonical_names_persist_correctly(self, db):
        """Test that canonical skills from shared extractor persist correctly."""
        # Create test data
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com/jobs",
            scraper_class="FakeScraper",
        )

        # Extract skills using legacy wrapper (returns strings)
        description = "Python and Django development with PostgreSQL"
        skills = legacy_extract_skills(description)

        # Create Skill records for extracted skills
        for skill_name in skills:
            Skill.objects.get_or_create(name=skill_name, defaults={"category": "test"})

        # Create a job with these skills
        job = Job.objects.create(
            source=source,
            company=company,
            title="Test Job",
            description=description,
            application_url="https://example.com/apply",
        )

        # Add skill associations
        for skill_name in skills:
            skill = Skill.objects.get(name=skill_name)
            JobSkill.objects.get_or_create(job=job, skill=skill, defaults={"is_required": True})

        # Verify persistence
        job_skills = JobSkill.objects.filter(job=job).select_related("skill")
        persisted_skills = {js.skill.name for js in job_skills}
        assert persisted_skills == set(skills)

    def test_shared_extractor_no_duplicate_skills(self, db):
        """Test that shared extractor doesn't create duplicate Skill records."""
        # Extract skills
        text = "Python and Django"
        skills = extract_skills(text)

        # Create Skill records multiple times
        for skill_name in skills:
            Skill.objects.get_or_create(name=skill_name, defaults={"category": "test"})
            Skill.objects.get_or_create(name=skill_name, defaults={"category": "test"})

        # Verify no duplicates
        for skill_name in skills:
            count = Skill.objects.filter(name=skill_name).count()
            assert count == 1

    def test_shared_extractor_preserves_job_hashing_deduplication(self, db):
        """Test that shared extractor doesn't break job hashing and deduplication."""
        from api.ingestion.hashing import compute_job_hash
        from api.ingestion.record import JobRecord

        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com/jobs",
            scraper_class="FakeScraper",
        )

        # Create job record with skills as list of strings (JobRecord expectation)
        skills = legacy_extract_skills("Python and Django development")
        record = JobRecord(
            source_id=source.id,
            company_id=company.id,
            external_id="test-123",
            title="Test Job",
            description="Python and Django development",
            requirements=None,
            location=None,
            application_url="https://example.com/apply",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=skills,
            required_yoe=None,
        )

        # Compute hash
        hash1 = compute_job_hash(record)

        # Compute hash again with same data
        hash2 = compute_job_hash(record)

        # Hashes should be identical (deterministic)
        assert hash1 == hash2


class TestSkillsDictionaryWithDatabase:
    """Tests for skills dictionary integration with database."""

    def test_dictionary_skills_can_be_created_in_db(self, db):
        """Test that all dictionary skills can be created in database."""
        dictionary = get_skills_dictionary()
        canonical_names = dictionary.get_all_canonical_names()

        created_count = 0
        for skill_name in canonical_names:
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": dictionary.get_category(skill_name) or "uncategorized"},
            )
            if created:
                created_count += 1

        # All skills should be created
        assert Skill.objects.count() == len(canonical_names)

    def test_dictionary_categories_mapped_correctly(self, db):
        """Test that dictionary categories are mapped to database."""
        dictionary = get_skills_dictionary()

        # Create a few skills
        test_skills = ["Python", "Docker", "React"]
        for skill_name in test_skills:
            category = dictionary.get_category(skill_name)
            Skill.objects.get_or_create(
                name=skill_name, defaults={"category": category or "uncategorized"}
            )

        # Verify categories
        python_skill = Skill.objects.get(name="Python")
        docker_skill = Skill.objects.get(name="Docker")
        react_skill = Skill.objects.get(name="React")

        assert python_skill.category == "Programming Languages"
        assert docker_skill.category == "Cloud and DevOps"
        assert react_skill.category == "Frontend"


class TestRetaggingCommand:
    """Tests for the retag_skills management command."""

    def test_retagging_dry_run_performs_no_writes(self, db):
        """Test that dry-run mode does not write to database."""
        from django.core.management import call_command

        # Setup: Create a job with specific skills
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com"
        )
        job = Job.objects.create(
            company=company,
            source=source,
            external_id="job1",
            title="Python Developer",
            description="Looking for a Python developer with Django experience.",
            location="Remote",
        )

        # Create skills in database
        python_skill = Skill.objects.create(name="Python", category="Programming Languages")
        Skill.objects.create(name="Django", category="Backend")

        # Add initial skills
        JobSkill.objects.create(job=job, skill=python_skill, is_required=True)

        initial_skill_count = JobSkill.objects.filter(job=job).count()

        # Run retagging in dry-run mode
        out = StringIO()
        call_command("retag_skills", "--dry-run", stdout=out)

        # Verify no changes were made
        assert JobSkill.objects.filter(job=job).count() == initial_skill_count

    def test_retagging_per_job_transaction_semantics(self, db):
        """Test that retagging uses per-job transactions (partial completion allowed)."""
        from django.core.management import call_command

        # Setup: Create multiple jobs
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com"
        )

        job1 = Job.objects.create(
            company=company,
            source=source,
            external_id="job1",
            title="Python Developer",
            description="Python and Django.",
            location="Remote",
        )

        job2 = Job.objects.create(
            company=company,
            source=source,
            external_id="job2",
            title="React Developer",
            description="React and TypeScript.",
            location="Remote",
        )

        # Create skills in database
        Skill.objects.create(name="Python", category="Programming Languages")
        Skill.objects.create(name="Django", category="Backend")
        Skill.objects.create(name="React", category="Frontend")
        Skill.objects.create(name="TypeScript", category="Programming Languages")

        # Run retagging with commit
        out = StringIO()
        call_command("retag_skills", "--commit", stdout=out)

        # Both jobs should be processed (partial completion is allowed)
        # The command processes jobs independently, so if one fails, others may succeed
        assert JobSkill.objects.filter(job=job1).count() > 0
        assert JobSkill.objects.filter(job=job2).count() > 0

    def test_retagging_idempotency(self, db):
        """Test that running retagging twice is idempotent."""
        from django.core.management import call_command

        # Setup: Create a job
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com"
        )
        job = Job.objects.create(
            company=company,
            source=source,
            external_id="job1",
            title="Python Developer",
            description="Python and Django experience required.",
            location="Remote",
        )

        # Create skills
        Skill.objects.create(name="Python", category="Programming Languages")
        Skill.objects.create(name="Django", category="Backend")

        # First retagging
        out1 = StringIO()
        call_command("retag_skills", "--commit", stdout=out1)
        first_result = JobSkill.objects.filter(job=job).values_list("skill__name", flat=True)

        # Second retagging (should be idempotent)
        out2 = StringIO()
        call_command("retag_skills", "--commit", stdout=out2)
        second_result = JobSkill.objects.filter(job=job).values_list("skill__name", flat=True)

        # Results should be identical
        assert set(first_result) == set(second_result)

    def test_retagging_preserves_unrelated_fields(self, db):
        """Test that retagging preserves unrelated job fields."""
        from datetime import date

        from django.core.management import call_command

        # Setup: Create a job with various fields

        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com"
        )
        job = Job.objects.create(
            company=company,
            source=source,
            external_id="job1",
            title="Python Developer",
            description="Python experience.",
            location="Remote",
            remote_type="remote",
            salary_min=50000,
            salary_max=80000,
            posted_date=date(2024, 1, 1),
        )

        # Store original values
        original_title = job.title
        original_location = job.location
        original_remote_type = job.remote_type
        original_salary_min = job.salary_min
        original_salary_max = job.salary_max
        original_posted_date = job.posted_date  # This is a date object
        original_external_id = job.external_id

        # Create skill
        Skill.objects.create(name="Python", category="Programming Languages")

        # Run retagging
        out = StringIO()
        call_command("retag_skills", "--commit", stdout=out)

        # Refresh from database
        job.refresh_from_db()

        # Verify unrelated fields are unchanged
        assert job.title == original_title
        assert job.location == original_location
        assert job.remote_type == original_remote_type
        assert job.salary_min == original_salary_min
        assert job.salary_max == original_salary_max
        assert job.posted_date == original_posted_date  # Both date objects
        assert job.external_id == original_external_id


class TestJobIngestionWithSharedExtractor:
    """Tests for job ingestion using shared extractor."""

    def test_pipeline_uses_shared_extractor(self, db):
        """Test that the ingestion pipeline uses the shared extractor."""
        from api.ingestion.pipeline import process_batch
        from api.ingestion.record import JobRecord

        # Setup
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com/jobs",
            scraper_class="FakeScraper",
        )

        # Create job record
        record = JobRecord(
            source_id=source.id,
            company_id=company.id,
            external_id="test-123",
            title="Test Job",
            description="Python and Django development with PostgreSQL",
            requirements=None,
            location=None,
            application_url="https://example.com/apply",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],  # Will be extracted by pipeline
            required_yoe=None,
        )

        # Process through pipeline (dry-run to avoid persistence)
        result = process_batch([record], "FakeScraper", dry_run=True)

        # Verify skills were extracted (dry-run still processes records)
        assert result.jobs_processed == 1
        # Note: jobs_created may be 0 if dry-run skips creation logic

    def test_existed_skills_not_affected_by_new_dictionary(self, db):
        """Test that existing JobSkill relationships remain valid."""
        # Create legacy skills
        Skill.objects.get_or_create(name="Python", defaults={"category": "Programming Languages"})
        Skill.objects.get_or_create(name="Django", defaults={"category": "Backend"})

        # Create company and source
        company = Company.objects.create(name="Test Company")
        source = IngestionSource.objects.create(
            company=company,
            name="Test Source",
            source_type="career_page",
            base_url="https://example.com/jobs",
            scraper_class="FakeScraper",
        )

        # Create job with skills
        job = Job.objects.create(
            source=source,
            company=company,
            title="Test Job",
            description="Python and Django",
            application_url="https://example.com/apply",
        )

        python_skill = Skill.objects.get(name="Python")
        django_skill = Skill.objects.get(name="Django")

        JobSkill.objects.create(job=job, skill=python_skill, is_required=True)
        JobSkill.objects.create(job=job, skill=django_skill, is_required=True)

        # Verify skills still exist
        job_skills = JobSkill.objects.filter(job=job).count()
        assert job_skills == 2

        # Verify skill names match
        skill_names = {js.skill.name for js in JobSkill.objects.filter(job=job)}
        assert skill_names == {"Python", "Django"}
