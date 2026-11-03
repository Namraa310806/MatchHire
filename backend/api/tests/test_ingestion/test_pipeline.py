"""Tests for ingestion pipeline orchestration."""

from datetime import date
from typing import Any

from django.test import TestCase

from api.ingestion.base_scraper import BaseJobScraper
from api.ingestion.pipeline import process_batch
from api.ingestion.record import JobRecord
from api.ingestion.scraper_registry import register_scraper
from api.models import Company, IngestionSource, Job, Skill


class PipelineTest(TestCase):
    """Tests for end-to-end pipeline."""

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
        Skill.objects.create(name="Python", category="programming")
        Skill.objects.create(name="JavaScript", category="programming")

    def test_end_to_end_pipeline(self):
        """Test complete pipeline from raw records to database."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description with Python and JavaScript skills",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],  # Will be extracted by pipeline
                "required_yoe": None,  # Will be extracted by pipeline
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(Job.objects.count(), 1)

        job = Job.objects.get(external_id="123")
        self.assertEqual(job.title, "Software Engineer")
        # Skills should be extracted
        self.assertEqual(job.jobskill_set.count(), 2)

    def test_pipeline_normalization(self):
        """Test pipeline normalizes records."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "  Software Engineer  ",  # Extra whitespace
                "description": "<p>Job description</p>",  # HTML tags
                "requirements": None,
                "location": "bangalore",  # Lowercase
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 1)

        job = Job.objects.get(external_id="123")
        self.assertEqual(job.title, "Software Engineer")  # Trimmed
        self.assertNotIn("<p>", job.description)  # HTML removed
        self.assertEqual(job.location, "Bangalore")  # Title case

    def test_pipeline_skill_extraction(self):
        """Test pipeline extracts skills."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "We need Python and JavaScript developers",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        process_batch(raw_records, "FakeScraper")
        job = Job.objects.get(external_id="123")
        self.assertEqual(job.jobskill_set.count(), 2)

    def test_pipeline_experience_extraction(self):
        """Test pipeline extracts experience."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Position for fresher with 0 years experience",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        process_batch(raw_records, "FakeScraper")
        job = Job.objects.get(external_id="123")
        self.assertEqual(job.experience_min_years, 0.0)

    def test_pipeline_validation_rejection(self):
        """Test pipeline rejects invalid records."""
        raw_records = [
            {
                "source_id": 99999,  # Invalid: source doesn't exist
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(Job.objects.count(), 0)

    def test_pipeline_empty_batch(self):
        """Test pipeline handles empty batch."""
        result = process_batch([], "FakeScraper")
        self.assertEqual(result.jobs_processed, 0)
        self.assertEqual(result.jobs_created, 0)

    def test_pipeline_multiple_records(self):
        """Test pipeline processes multiple records."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "456",
                "title": "Data Scientist",
                "description": "Job description",
                "requirements": None,
                "location": "Mumbai",
                "application_url": "https://acme.com/jobs/456",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 2)
        self.assertEqual(Job.objects.count(), 2)

    def test_parsing_error_reported(self):
        """Test parsing errors are counted and reported."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": "invalid-date",  # Will cause parsing error
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(result.validation_errors[0].error_type, "parsing_error")
        self.assertIsNotNone(result.validation_errors[0].raw_record)

    def test_normalization_error_reported(self):
        """Test normalization errors are counted and reported."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "invalid-url",  # Will cause normalization error
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(result.validation_errors[0].error_type, "normalization_error")
        self.assertIsNotNone(result.validation_errors[0].record)

    def test_all_errors_reported_together(self):
        """Test parsing and normalization errors are all reported.

        Note: With batch parsing isolation, malformed records are skipped but
        valid records continue through the pipeline.
        """
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": "invalid-date",  # Parsing error for this record only
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "456",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/456",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
        ]

        result = process_batch(raw_records, "FakeScraper")
        # First record has parsing error, second record should succeed
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(result.validation_errors[0].error_type, "parsing_error")
        self.assertEqual(result.jobs_created, 1)  # Valid record was ingested
        # Verify the error includes the raw record for attribution
        self.assertIsNotNone(result.validation_errors[0].raw_record)
        self.assertEqual(result.validation_errors[0].raw_record["external_id"], "123")

    def test_mixed_batch_with_multiple_malformed_records(self):
        """Test batch with multiple malformed records isolates failures.

        Verifies that:
        - Valid records are successfully ingested
        - Malformed records produce attributable parsing errors
        - Errors include the original raw record
        - No records are silently discarded
        """
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "valid-1",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/valid-1",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "malformed-1",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/malformed-1",
                "posted_date": "invalid-date-1",  # Parsing error
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "valid-2",
                "title": "Data Scientist",
                "description": "Job description",
                "requirements": None,
                "location": "Mumbai",
                "application_url": "https://acme.com/jobs/valid-2",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "malformed-2",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/malformed-2",
                "posted_date": "invalid-date-2",  # Parsing error
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
        ]

        result = process_batch(raw_records, "FakeScraper")

        # 2 valid records should be ingested
        self.assertEqual(result.jobs_created, 2)
        self.assertEqual(Job.objects.count(), 2)

        # 2 parsing errors should be reported
        self.assertEqual(len(result.validation_errors), 2)
        for error in result.validation_errors:
            self.assertEqual(error.error_type, "parsing_error")
            self.assertIsNotNone(error.raw_record)

        # Verify the specific malformed records are in errors
        error_external_ids = {
            e.raw_record["external_id"] for e in result.validation_errors
        }
        self.assertEqual(error_external_ids, {"malformed-1", "malformed-2"})

        # Verify valid records are in database
        valid_job_ids = {job.external_id for job in Job.objects.all()}
        self.assertEqual(valid_job_ids, {"valid-1", "valid-2"})


class SimpleTestScraper(BaseJobScraper):
    """Simple test scraper that implements only the base contract.

    Used to verify the shared parsing-error contract works for any
    BaseJobScraper implementation, not just FakeScraper.
    """

    def __init__(self, fixtures: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self.fixtures = fixtures or []

    def fetch(self, url: str) -> list[dict[str, Any]]:
        """Return fixtures (ignores URL)."""
        return self.fixtures

    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse raw fixture data into JobRecords using base class error mechanism."""
        self._clear_parse_errors()
        records = []

        for raw_record in raw:
            try:
                posted_date = None
                if raw_record.get("posted_date"):
                    posted_date = date.fromisoformat(raw_record["posted_date"])

                records.append(
                    JobRecord(
                        source_id=raw_record["source_id"],
                        company_id=raw_record["company_id"],
                        external_id=raw_record.get("external_id"),
                        title=raw_record["title"],
                        description=raw_record["description"],
                        requirements=raw_record.get("requirements"),
                        location=raw_record.get("location"),
                        application_url=raw_record["application_url"],
                        posted_date=posted_date,
                        remote_type=raw_record.get("remote_type"),
                        role_type=raw_record.get("role_type"),
                        experience_min_years=raw_record.get("experience_min_years"),
                        experience_max_years=raw_record.get("experience_max_years"),
                        salary_min=raw_record.get("salary_min"),
                        salary_max=raw_record.get("salary_max"),
                        salary_currency=raw_record.get("salary_currency", "INR"),
                        skills=raw_record.get("skills", []),
                        required_yoe=raw_record.get("required_yoe"),
                    )
                )
            except Exception as e:
                # Use base class helper for error reporting
                self._record_parse_error(raw_record, str(e))

        return records

    def validate(self, job: JobRecord) -> bool:
        """Validate JobRecord."""
        if not job.title or not job.title.strip():
            return False
        if not job.description or not job.description.strip():
            return False
        if not job.application_url or not job.application_url.strip():
            return False
        if job.source_id <= 0:
            return False
        if job.company_id <= 0:
            return False
        return True


class BaseContractTest(TestCase):
    """Tests for the shared base class parsing-error contract."""

    @classmethod
    def setUpClass(cls):
        """Register SimpleTestScraper for testing."""
        super().setUpClass()
        register_scraper("SimpleTestScraper", "api.tests.test_ingestion.test_pipeline")

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
            scraper_class="SimpleTestScraper",
        )
        # Seed skills
        Skill.objects.create(name="Python", category="programming")
        Skill.objects.create(name="JavaScript", category="programming")

    def test_base_scraper_can_parse_valid_records(self):
        """Test a base-class-only scraper can parse valid records."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "SimpleTestScraper")
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_base_scraper_reports_malformed_records(self):
        """Test a base-class-only scraper reports malformed records through shared mechanism."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": "invalid-date",  # Will cause parsing error
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "SimpleTestScraper")
        self.assertEqual(result.jobs_created, 0)
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(result.validation_errors[0].error_type, "parsing_error")
        self.assertIsNotNone(result.validation_errors[0].raw_record)

    def test_base_scraper_valid_records_continue_through_pipeline(self):
        """Test valid records from the same batch are persisted even when some are malformed."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "valid-1",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/valid-1",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "malformed-1",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/malformed-1",
                "posted_date": "invalid-date",  # Parsing error
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            },
        ]

        result = process_batch(raw_records, "SimpleTestScraper")
        # Valid record should be ingested
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(Job.objects.count(), 1)
        # Malformed record should produce error
        self.assertEqual(len(result.validation_errors), 1)
        self.assertEqual(result.validation_errors[0].error_type, "parsing_error")

    def test_errors_retain_original_raw_input(self):
        """Test parsing errors retain the original raw input for attribution."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "abc123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/abc123",
                "posted_date": "invalid-date",
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "SimpleTestScraper")
        self.assertEqual(len(result.validation_errors), 1)
        error = result.validation_errors[0]
        self.assertIsNotNone(error.raw_record)
        self.assertEqual(error.raw_record["external_id"], "abc123")
        self.assertEqual(error.raw_record["posted_date"], "invalid-date")

    def test_errors_do_not_leak_between_invocations(self):
        """Test parsing errors from a previous invocation do not leak into the next."""
        scraper = SimpleTestScraper()

        # First invocation with malformed record
        raw_records_1 = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": "invalid-date",
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]
        scraper.parse(raw_records_1)
        self.assertEqual(len(scraper.parse_errors), 1)

        # Second invocation with valid record - errors should be cleared
        raw_records_2 = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "456",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/456",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]
        scraper.parse(raw_records_2)
        self.assertEqual(len(scraper.parse_errors), 0)
