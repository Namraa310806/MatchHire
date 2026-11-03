"""Tests for job record validation."""

from django.test import TestCase

from api.ingestion.record import JobRecord
from api.ingestion.validation import validate_job_record


class ValidationTest(TestCase):
    """Tests for job record validation."""

    def test_valid_record(self):
        """Test a valid record passes validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNone(error)
        if error:
            self.assertIsNone(error.raw_record)

    def test_invalid_source_id(self):
        """Test invalid source_id fails validation."""
        record = JobRecord(
            source_id=0,  # Invalid
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIn("source_id", error.reason)
        self.assertIsNone(error.raw_record)

    def test_invalid_company_id(self):
        """Test invalid company_id fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=-1,  # Invalid
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIn("company_id", error.reason)
        self.assertIsNone(error.raw_record)

    def test_empty_external_id(self):
        """Test empty external_id fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="",  # Empty but not None
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIsNone(error.raw_record)

    def test_empty_title(self):
        """Test empty title fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="",  # Empty
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "missing_field")
        self.assertIsNone(error.raw_record)

    def test_empty_description(self):
        """Test empty description fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="",  # Empty
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "missing_field")
        self.assertIsNone(error.raw_record)

    def test_empty_application_url(self):
        """Test empty application_url fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="",  # Empty
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
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "missing_field")
        self.assertIsNone(error.raw_record)

    def test_invalid_experience_range(self):
        """Test invalid experience range (min > max) fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=5.0,  # Greater than max
            experience_max_years=2.0,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIn("experience range", error.reason)
        self.assertIsNone(error.raw_record)

    def test_valid_experience_range(self):
        """Test valid experience range passes validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=2.0,
            experience_max_years=5.0,  # Valid range
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNone(error)

    def test_invalid_salary_range(self):
        """Test invalid salary range (min > max) fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=1000000.0,  # Greater than max
            salary_max=500000.0,
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIn("salary range", error.reason)
        self.assertIsNone(error.raw_record)

    def test_valid_salary_range(self):
        """Test valid salary range passes validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=500000.0,
            salary_max=1000000.0,  # Valid range
            salary_currency="INR",
            skills=[],
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNone(error)

    def test_none_skills_list(self):
        """Test None skills list fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=None,  # Should be empty list instead
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "invalid_value")
        self.assertIsNone(error.raw_record)

    def test_empty_skills_list(self):
        """Test empty skills list passes validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=[],  # Valid empty list
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNone(error)

    def test_salary_currency_empty_with_salary(self):
        """Test empty salary currency with salary fields fails validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=500000.0,
            salary_max=None,
            salary_currency="",  # Empty
            skills=[],
            required_yoe=None,
        )
        error = validate_job_record(record)
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, "missing_field")
        self.assertIsNone(error.raw_record)

    def test_null_external_id_allowed(self):
        """Test null external_id is allowed."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id=None,  # Null is allowed
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="https://example.com/job",
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
        error = validate_job_record(record)
        self.assertIsNone(error)
