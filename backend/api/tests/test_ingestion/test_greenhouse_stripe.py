"""Tests for Greenhouse Stripe scraper."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from api.ingestion.record import JobRecord
from api.ingestion.scrapers.greenhouse_stripe import GreenhouseStripeScraper


@pytest.fixture
def sample_fixture_path():
    """Path to sample fixture file."""
    return Path(__file__).parent.parent / "fixtures" / "ingestion" / "stripe_greenhouse_sample.json"


@pytest.fixture
def sample_response(sample_fixture_path):
    """Load sample fixture data."""
    with open(sample_fixture_path) as f:
        return json.load(f)


class TestGreenhouseStripeScraper:
    """Test Greenhouse Stripe scraper."""

    def test_load_fixture(self, sample_response):
        """Test fixture loads correctly."""
        assert "jobs" in sample_response
        assert len(sample_response["jobs"]) == 2
        assert sample_response["meta"]["total"] == 2

    def test_fetch_with_mock(self, sample_response):
        """Test fetch with mocked HTTP response."""
        scraper = GreenhouseStripeScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = sample_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = scraper.fetch("https://boards-api.greenhouse.io/v1/boards/stripe/jobs")

            assert len(result) == 2
            assert result[0]["id"] == 8172510
            assert result[0]["title"] == "Abuse Investigator"
            mock_get.assert_called_once()

    def test_fetch_adds_content_parameter(self):
        """Test fetch adds content=true parameter."""
        scraper = GreenhouseStripeScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"jobs": [], "meta": {"total": 0}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            scraper.fetch("https://boards-api.greenhouse.io/v1/boards/stripe/jobs")

            # Check that content=true was added
            call_args = mock_get.call_args
            assert "content=true" in call_args[0][0]

    def test_parse_valid_records(self, sample_response):
        """Test parsing valid job records."""
        scraper = GreenhouseStripeScraper()
        raw_jobs = sample_response["jobs"]

        records = scraper.parse(raw_jobs)

        assert len(records) == 2
        assert isinstance(records[0], JobRecord)
        assert records[0].title == "Abuse Investigator"
        assert records[0].external_id == "8172510"
        assert records[0].application_url == "https://stripe.com/jobs/search?gh_jid=8172510"
        assert records[0].location == "Seattle"  # First location from comma-separated
        assert len(scraper.parse_errors) == 0

    def test_parse_html_unescaping(self, sample_response):
        """Test HTML content is double-escaped correctly."""
        scraper = GreenhouseStripeScraper()
        raw_jobs = sample_response["jobs"]

        records = scraper.parse(raw_jobs)

        # Content should be unescaped (no &lt; &gt; entities)
        assert "<h2>" in records[0].description
        assert "<p>" in records[0].description
        assert "&lt;" not in records[0].description
        assert "&gt;" not in records[0].description

    def test_parse_missing_title(self):
        """Test parsing record with missing title."""
        scraper = GreenhouseStripeScraper()
        raw_job = {"id": 12345, "content": "<p>Description</p>", "absolute_url": "https://example.com"}

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing title" in scraper.parse_errors[0][1]

    def test_parse_missing_description(self):
        """Test parsing record with missing description."""
        scraper = GreenhouseStripeScraper()
        raw_job = {
            "id": 12345,
            "title": "Test Job",
            "content": "",
            "absolute_url": "https://example.com",
        }

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing description" in scraper.parse_errors[0][1]

    def test_parse_missing_application_url(self):
        """Test parsing record with missing application URL."""
        scraper = GreenhouseStripeScraper()
        raw_job = {"id": 12345, "title": "Test Job", "content": "<p>Description</p>"}

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing application URL" in scraper.parse_errors[0][1]

    def test_parse_remote_type_detection(self):
        """Test remote type detection from location."""
        scraper = GreenhouseStripeScraper()

        # Test remote
        raw_remote = {
            "id": 1,
            "title": "Remote Job",
            "content": "<p>Description</p>",
            "location": {"name": "Remote"},
            "absolute_url": "https://example.com",
        }
        records = scraper.parse([raw_remote])
        assert records[0].remote_type == "remote"

        # Test hybrid
        raw_hybrid = {
            "id": 2,
            "title": "Hybrid Job",
            "content": "<p>Description</p>",
            "location": {"name": "San Francisco Hybrid"},
            "absolute_url": "https://example.com",
        }
        records = scraper.parse([raw_hybrid])
        assert records[0].remote_type == "hybrid"

        # Test on-site
        raw_onsite = {
            "id": 3,
            "title": "On-site Job",
            "content": "<p>Description</p>",
            "location": {"name": "New York City"},
            "absolute_url": "https://example.com",
        }
        records = scraper.parse([raw_onsite])
        assert records[0].remote_type == "on-site"

    def test_parse_posted_date_extraction(self):
        """Test posted date extraction from timestamps."""
        scraper = GreenhouseStripeScraper()

        raw_job = {
            "id": 1,
            "title": "Test Job",
            "content": "<p>Description</p>",
            "location": {"name": "San Francisco"},
            "absolute_url": "https://example.com",
            "first_published": "2026-09-09T10:50:29-04:00",
        }

        records = scraper.parse([raw_job])
        assert records[0].posted_date is not None
        assert records[0].posted_date.year == 2026
        assert records[0].posted_date.month == 9
        assert records[0].posted_date.day == 9

    def test_validate_valid_record(self):
        """Test validation of valid record."""
        scraper = GreenhouseStripeScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Test Job",
            description="Test description",
            requirements=None,
            location="San Francisco",
            application_url="https://example.com",
            posted_date=None,
            remote_type="remote",
            role_type="full-time",
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            skills=[],
            required_yoe=None,
        )

        assert scraper.validate(record) is True

    def test_validate_empty_title(self):
        """Test validation rejects empty title."""
        scraper = GreenhouseStripeScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="",
            description="Test description",
            requirements=None,
            location="San Francisco",
            application_url="https://example.com",
            posted_date=None,
            remote_type="remote",
            role_type="full-time",
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            skills=[],
            required_yoe=None,
        )

        assert scraper.validate(record) is False

    def test_validate_empty_description(self):
        """Test validation rejects empty description."""
        scraper = GreenhouseStripeScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Test Job",
            description="",
            requirements=None,
            location="San Francisco",
            application_url="https://example.com",
            posted_date=None,
            remote_type="remote",
            role_type="full-time",
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            skills=[],
            required_yoe=None,
        )

        assert scraper.validate(record) is False

    def test_validate_empty_application_url(self):
        """Test validation rejects empty application URL."""
        scraper = GreenhouseStripeScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="123",
            title="Test Job",
            description="Test description",
            requirements=None,
            location="San Francisco",
            application_url="",
            posted_date=None,
            remote_type="remote",
            role_type="full-time",
            experience_min_years=None,
            experience_max_years=None,
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            skills=[],
            required_yoe=None,
        )

        assert scraper.validate(record) is False

    def test_parse_errors_dont_leak(self):
        """Test parse errors are cleared between invocations."""
        scraper = GreenhouseStripeScraper()

        # First parse with error
        scraper.parse([{"id": 1}])
        assert len(scraper.parse_errors) > 0

        # Second parse should have cleared errors
        scraper.parse([])
        assert len(scraper.parse_errors) == 0

    def test_fetch_http_error(self):
        """Test fetch handles HTTP errors."""
        scraper = GreenhouseStripeScraper()

        with patch.object(scraper.session, "get") as mock_get:
            from requests.exceptions import RequestException

            mock_get.side_effect = RequestException("Network error")

            with pytest.raises(RequestException):
                scraper.fetch("https://boards-api.greenhouse.io/v1/boards/stripe/jobs")

    def test_fetch_invalid_json(self):
        """Test fetch handles invalid JSON."""
        scraper = GreenhouseStripeScraper()

        with patch.object(scraper.session, "get") as mock_get:
            from requests.exceptions import JSONDecodeError

            mock_response = Mock()
            mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid JSON"):
                scraper.fetch("https://boards-api.greenhouse.io/v1/boards/stripe/jobs")

    def test_fetch_missing_jobs_field(self):
        """Test fetch handles response missing jobs field."""
        scraper = GreenhouseStripeScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"meta": {"total": 0}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="missing 'jobs' field"):
                scraper.fetch("https://boards-api.greenhouse.io/v1/boards/stripe/jobs")
