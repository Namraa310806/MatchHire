"""Tests for job record normalization."""


from django.test import TestCase

from api.ingestion.normalization import normalize_job_record
from api.ingestion.record import JobRecord


class NormalizationTest(TestCase):
    """Tests for job record normalization."""

    def test_html_entity_decoding(self):
        """Test HTML entities are decoded."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer &amp; Developer",
            description="Job with &lt;strong&gt;HTML&lt;/strong&gt; entities",
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
        normalized = normalize_job_record(record)
        self.assertIn("&", normalized.title)
        # HTML tags are removed, entities are decoded
        self.assertNotIn("<strong>", normalized.description)
        self.assertIn("HTML", normalized.description)

    def test_html_tag_removal(self):
        """Test HTML tags are removed."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="<p>Job description</p><div>More text</div>",
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
        normalized = normalize_job_record(record)
        self.assertNotIn("<p>", normalized.description)
        self.assertNotIn("<div>", normalized.description)

    def test_whitespace_trimming(self):
        """Test leading/trailing whitespace is trimmed."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="  Software Engineer  ",
            description="  Job description  ",
            requirements=None,
            location="  Bangalore  ",
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
        normalized = normalize_job_record(record)
        self.assertEqual(normalized.title, "Software Engineer")
        self.assertEqual(normalized.description, "Job description")
        self.assertEqual(normalized.location, "Bangalore")

    def test_empty_fields(self):
        """Test empty fields are handled."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id=None,
            title="Software Engineer",
            description="Job description",
            requirements="",
            location="",
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
        normalized = normalize_job_record(record)
        self.assertIsNone(normalized.requirements)
        self.assertIsNone(normalized.location)

    def test_location_title_case(self):
        """Test location is converted to title case."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="bangalore",
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
        normalized = normalize_job_record(record)
        self.assertEqual(normalized.location, "Bangalore")

    def test_url_validation(self):
        """Test URL validation."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url="invalid-url",
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
        with self.assertRaises(ValueError):
            normalize_job_record(record)

    def test_url_too_long(self):
        """Test URL length validation."""
        long_url = "https://example.com/" + "a" * 1000
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="Job description",
            requirements=None,
            location="Bangalore",
            application_url=long_url,
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
        with self.assertRaises(ValueError):
            normalize_job_record(record)

    def test_description_too_long(self):
        """Test description length validation."""
        long_desc = "a" * 50001
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description=long_desc,
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
        with self.assertRaises(ValueError):
            normalize_job_record(record)

    def test_empty_title_error(self):
        """Test empty title raises error."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="",
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
        with self.assertRaises(ValueError):
            normalize_job_record(record)

    def test_empty_description_error(self):
        """Test empty description raises error."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Software Engineer",
            description="",
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
        with self.assertRaises(ValueError):
            normalize_job_record(record)

    def test_skill_deduplication(self):
        """Test duplicate skills are removed."""
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
            skills=["Python", "Python", "JavaScript", "JavaScript"],
            required_yoe=None,
        )
        normalized = normalize_job_record(record)
        self.assertEqual(len(normalized.skills), 2)
        self.assertIn("Python", normalized.skills)
        self.assertIn("JavaScript", normalized.skills)

    def test_external_id_normalization(self):
        """Test external_id is normalized."""
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="  123  ",
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
        normalized = normalize_job_record(record)
        self.assertEqual(normalized.external_id, "123")
