"""Tests for job persistence (bulk upsert)."""


from django.test import TestCase

from api.ingestion.persistence import bulk_upsert_jobs
from api.ingestion.record import JobRecord
from api.models import Company, IngestionSource, Job, JobSkill, Skill


class PersistenceTest(TestCase):
    """Tests for job persistence operations."""

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
            scraper_class="FakeScraper",
        )
        # Seed skills
        self.python_skill = Skill.objects.create(name="Python", category="programming")
        self.js_skill = Skill.objects.create(name="JavaScript", category="programming")

    def test_create_new_job(self):
        """Test creating a new job."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python"],
            required_yoe=None,
        )
        result = bulk_upsert_jobs([record])
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(result.jobs_updated, 0)
        self.assertEqual(Job.objects.count(), 1)

        job = Job.objects.get(external_id="123")
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.source, self.source)

    def test_idempotent_reprocessing(self):
        """Test re-processing same batch is idempotent."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        # First ingestion
        result1 = bulk_upsert_jobs([record])
        self.assertEqual(result1.jobs_created, 1)
        self.assertEqual(result1.jobs_updated, 0)

        # Second ingestion (same content)
        result2 = bulk_upsert_jobs([record])
        self.assertEqual(result2.jobs_created, 0)
        self.assertEqual(result2.jobs_updated, 0)
        self.assertEqual(Job.objects.count(), 1)

    def test_update_on_content_change(self):
        """Test job is updated when content changes."""
        record1 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        # First ingestion
        bulk_upsert_jobs([record1])
        job = Job.objects.get(external_id="123")
        original_hash = job.job_hash

        # Update with changed content
        record2 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",  # Same external ID
            title="Senior Software Engineer",  # Changed
            description="Updated job description",  # Changed
            requirements=None,
            location="Mumbai",  # Changed
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record2])
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(result.jobs_updated, 1)

        job.refresh_from_db()
        self.assertEqual(job.title, "Senior Software Engineer")
        self.assertEqual(job.description, "Updated job description")
        self.assertEqual(job.location, "Mumbai")
        self.assertNotEqual(job.job_hash, original_hash)

    def test_deduplicate_within_batch(self):
        """Test duplicate records within batch are handled."""
        record1 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        record2 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",  # Same external ID
            title="Different Title",  # Different content
            description="Different description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record1, record2])
        # First record wins, second is deduplicated
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(Job.objects.count(), 1)

        job = Job.objects.get(external_id="123")
        self.assertEqual(job.title, "Software Engineer")  # First record

    def test_skill_associations_created(self):
        """Test skill associations are created."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python", "JavaScript"],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record])
        self.assertEqual(result.skill_associations_created, 2)

        job = Job.objects.get(external_id="123")
        self.assertEqual(job.jobskill_set.count(), 2)

    def test_skill_associations_no_duplicates(self):
        """Test skill associations have no duplicates."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python", "JavaScript"],
            required_yoe=None,
        )

        bulk_upsert_jobs([record])
        job = Job.objects.get(external_id="123")
        self.assertEqual(job.jobskill_set.count(), 2)

        # Reprocess
        bulk_upsert_jobs([record])
        job.refresh_from_db()
        self.assertEqual(job.jobskill_set.count(), 2)  # Still 2, not 4

    def test_unknown_skills_ignored(self):
        """Test skills not in vocabulary are ignored."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python", "UnknownSkill"],  # UnknownSkill not in DB
            required_yoe=None,
        )

        bulk_upsert_jobs([record])
        # Only Python is associated
        job = Job.objects.get(external_id="123")
        self.assertEqual(job.jobskill_set.count(), 1)
        self.assertEqual(job.jobskill_set.first().skill.name, "Python")

    def test_invalid_source_id_rejected(self):
        """Test record with invalid source_id is rejected."""
        record = JobRecord(
            source_id=99999,  # Invalid
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record])
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertIn("Source ID", result.validation_errors[0].reason)

    def test_invalid_company_id_rejected(self):
        """Test record with invalid company_id is rejected."""
        record = JobRecord(
            source_id=self.source.id,
            company_id=99999,  # Invalid
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record])
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertIn("Company ID", result.validation_errors[0].reason)

    def test_fallback_identity_by_url(self):
        """Test fallback identity using application_url when no external_id."""
        record1 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id=None,  # No external ID
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        bulk_upsert_jobs([record1])
        self.assertEqual(Job.objects.count(), 1)

        # Same URL, should update
        record2 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id=None,
            title="Senior Software Engineer",  # Changed
            description="Updated description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",  # Same URL
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([record2])
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(result.jobs_updated, 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_batch_with_mixed_valid_invalid(self):
        """Test batch with both valid and invalid records."""
        valid_record = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        invalid_record = JobRecord(
            source_id=99999,  # Invalid
            company_id=self.company.id,
            external_id="456",
            title="Invalid Job",
            description="Invalid description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/456",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )

        result = bulk_upsert_jobs([valid_record, invalid_record])
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_transaction_rollback_on_persistence_failure(self):
        """Test transaction rollback on mid-transaction failure.

        This test calls the public bulk_upsert_jobs() API and injects a Python
        exception during processing of the second record to verify that the
        internal transaction.atomic() boundary rolls back all writes including
        both Job and JobSkill associations.
        """
        from unittest.mock import patch

        from api.ingestion import persistence

        # Create two valid records with skills to test JobSkill rollback
        valid_record1 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://acme.com/jobs/123",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python", "JavaScript"],  # Skills for JobSkill rollback test
            required_yoe=None,
        )

        valid_record2 = JobRecord(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="456",
            title="Data Scientist",
            description="Job description",
            requirements=None,
            location="Mumbai",
            application_url="https://acme.com/jobs/456",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python"],
            required_yoe=None,
        )

        # Create a pre-existing job to verify it's unaffected
        _ = Job.objects.create(
            source_id=self.source.id,
            company_id=self.company.id,
            external_id="999",
            title="Pre-existing Job",
            description="Description",
            requirements=None,
            location="Delhi",
            application_url="https://acme.com/jobs/999",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            job_hash="hash",
            is_active=True,
        )

        initial_job_count = Job.objects.count()
        initial_jobskill_count = JobSkill.objects.count()

        # Patch _create_job to raise an exception after it's called once
        original_create = persistence._create_job
        call_count = [0]

        def mock_create_with_exception(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second record triggers exception
                raise Exception("Simulated Python exception during job creation")
            return original_create(*args, **kwargs)

        with patch.object(
            persistence, "_create_job", side_effect=mock_create_with_exception
        ):
            with self.assertRaises(Exception) as context:
                # Call the public API directly - it has internal transaction.atomic()
                bulk_upsert_jobs([valid_record1, valid_record2])

        self.assertIn("Simulated Python exception", str(context.exception))

        # Verify transaction rollback - no new jobs created despite first call succeeding
        self.assertEqual(Job.objects.count(), initial_job_count)

        # Verify JobSkill rollback - no skill associations created
        self.assertEqual(JobSkill.objects.count(), initial_jobskill_count)

        # Verify pre-existing records are unaffected
        self.assertTrue(Job.objects.filter(external_id="999").exists())
        self.assertEqual(Job.objects.count(), initial_job_count)
