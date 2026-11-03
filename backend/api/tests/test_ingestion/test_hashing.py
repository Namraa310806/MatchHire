"""Tests for job hash computation."""

from django.test import TestCase

from api.ingestion.hashing import compute_job_hash, hash_matches
from api.ingestion.record import JobRecord


class HashingTest(TestCase):
    """Tests for job hash computation."""

    def test_hash_stability(self):
        """Test hash is stable for equivalent normalized content."""
        record1 = JobRecord(
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
            skills=["Python", "JavaScript"],
            required_yoe=2.0,
        )
        record2 = JobRecord(
            source_id=2,  # Different source
            company_id=2,  # Different company
            external_id="456",  # Different external ID
            title="Software Engineer",  # Same title
            description="Job description",  # Same description
            requirements=None,
            location="Bangalore",  # Same location
            application_url="https://example.com/job2",  # Different URL
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["Python", "JavaScript"],  # Same skills
            required_yoe=2.0,  # Same YOE
        )
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertEqual(hash1, hash2)

    def test_hash_case_insensitive(self):
        """Test hash is case-insensitive for title, description, location."""
        record1 = JobRecord(
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
            skills=["Python"],
            required_yoe=2.0,
        )
        record2 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="software engineer",  # Lowercase
            description="JOB DESCRIPTION",  # Uppercase
            requirements=None,
            location="bangalore",  # Lowercase
            application_url="https://example.com/job",
            posted_date=None,
            remote_type=None,
            role_type=None,
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="INR",
            skills=["python"],  # Lowercase
            required_yoe=2.0,
        )
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertEqual(hash1, hash2)

    def test_hash_changes_on_title_change(self):
        """Test hash changes when title changes."""
        record1 = JobRecord(
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
        record2 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Senior Software Engineer",  # Changed
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_on_description_change(self):
        """Test hash changes when description changes."""
        record1 = JobRecord(
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
        record2 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Updated job description",  # Changed
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_on_location_change(self):
        """Test hash changes when location changes."""
        record1 = JobRecord(
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
        record2 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Mumbai",  # Changed
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_on_skills_change(self):
        """Test hash changes when skills change."""
        record1 = JobRecord(
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
            skills=["Python"],
            required_yoe=None,
        )
        record2 = JobRecord(
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
            skills=["Python", "JavaScript"],  # Added skill
            required_yoe=None,
        )
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_on_yoe_change(self):
        """Test hash changes when required_yoe changes."""
        record1 = JobRecord(
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
            required_yoe=2.0,
        )
        record2 = JobRecord(
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
            required_yoe=3.0,  # Changed
        )
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertNotEqual(hash1, hash2)

    def test_hash_with_null_yoe(self):
        """Test hash handles null required_yoe."""
        record1 = JobRecord(
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
        record2 = JobRecord(
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertEqual(hash1, hash2)

    def test_hash_with_null_location(self):
        """Test hash handles null location."""
        record1 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location=None,
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
        record2 = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location=None,
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertEqual(hash1, hash2)

    def test_hash_with_empty_skills(self):
        """Test hash handles empty skills list."""
        record1 = JobRecord(
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
        record2 = JobRecord(
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
        hash1 = compute_job_hash(record1)
        hash2 = compute_job_hash(record2)
        self.assertEqual(hash1, hash2)

    def test_hash_length(self):
        """Test hash is 64 characters (SHA-256 hex)."""
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
        hash_value = compute_job_hash(record)
        self.assertEqual(len(hash_value), 64)

    def test_hash_matches_function(self):
        """Test hash_matches helper function."""
        record1 = JobRecord(
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
        record2 = JobRecord(
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
        self.assertTrue(hash_matches(record1, record2))
