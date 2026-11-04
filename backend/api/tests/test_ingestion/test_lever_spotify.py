"""Tests for Lever Spotify scraper."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from api.ingestion.record import JobRecord
from api.ingestion.scrapers.lever_spotify import LeverSpotifyScraper


@pytest.fixture
def sample_fixture_path():
    """Path to sample fixture file."""
    return Path(__file__).parent.parent / "fixtures" / "ingestion" / "spotify_lever_sample.json"


@pytest.fixture
def sample_response(sample_fixture_path):
    """Load sample fixture data."""
    with open(sample_fixture_path) as f:
        return json.load(f)


class TestLeverSpotifyScraper:
    """Test Lever Spotify scraper."""

    def test_load_fixture(self, sample_response):
        """Test fixture loads correctly."""
        assert isinstance(sample_response, list)
        assert len(sample_response) == 2
        assert sample_response[0]["id"] == "2a55d6c9-c564-443a-be3e-a3851db5a93b"

    def test_fetch_with_mock(self, sample_response):
        """Test fetch with mocked HTTP response."""
        scraper = LeverSpotifyScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = sample_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = scraper.fetch("https://api.lever.co/v0/postings/spotify")

            assert len(result) == 2
            assert result[0]["id"] == "2a55d6c9-c564-443a-be3e-a3851db5a93b"
            assert result[0]["text"] == "Account Executive - Commercial, Spotify Technology"
            mock_get.assert_called_once()

    def test_fetch_adds_mode_parameter(self):
        """Test fetch adds mode=json parameter."""
        scraper = LeverSpotifyScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            scraper.fetch("https://api.lever.co/v0/postings/spotify")

            # Check that mode=json was added
            call_args = mock_get.call_args
            assert "mode=json" in call_args[0][0]

    def test_parse_valid_records(self, sample_response):
        """Test parsing valid job records."""
        scraper = LeverSpotifyScraper()
        raw_jobs = sample_response

        records = scraper.parse(raw_jobs)

        assert len(records) == 2
        assert isinstance(records[0], JobRecord)
        assert records[0].title == "Account Executive - Commercial, Spotify Technology"
        assert records[0].external_id == "2a55d6c9-c564-443a-be3e-a3851db5a93b"
        assert records[0].application_url == "https://jobs.lever.co/spotify/2a55d6c9-c564-443a-be3e-a3851db5a93b/apply"
        assert records[0].location == "New York, NY"
        assert len(scraper.parse_errors) == 0

    def test_parse_description_plain(self, sample_response):
        """Test descriptionPlain is used for description."""
        scraper = LeverSpotifyScraper()
        raw_jobs = sample_response

        records = scraper.parse(raw_jobs)

        # Description should be plain text, not HTML
        assert "<p>" not in records[0].description
        assert "<div>" not in records[0].description
        assert "Spotify Technology is our business-to-business software team" in records[0].description

    def test_parse_missing_id(self):
        """Test parsing record with missing id."""
        scraper = LeverSpotifyScraper()
        raw_job = {
            "text": "Test Job",
            "descriptionPlain": "Description",
            "applyUrl": "https://example.com",
        }

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing id" in scraper.parse_errors[0][1]

    def test_parse_missing_title(self):
        """Test parsing record with missing title."""
        scraper = LeverSpotifyScraper()
        raw_job = {
            "id": "uuid-123",
            "descriptionPlain": "Description",
            "applyUrl": "https://example.com",
        }

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing title" in scraper.parse_errors[0][1]

    def test_parse_missing_description(self):
        """Test parsing record with missing description."""
        scraper = LeverSpotifyScraper()
        raw_job = {
            "id": "uuid-123",
            "text": "Test Job",
            "applyUrl": "https://example.com",
        }

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing description" in scraper.parse_errors[0][1]

    def test_parse_missing_application_url(self):
        """Test parsing record with missing application URL."""
        scraper = LeverSpotifyScraper()
        raw_job = {
            "id": "uuid-123",
            "text": "Test Job",
            "descriptionPlain": "Description",
        }

        records = scraper.parse([raw_job])

        assert len(records) == 0
        assert len(scraper.parse_errors) == 1
        assert "Missing application URL" in scraper.parse_errors[0][1]

    def test_parse_remote_type_from_workplace_type(self):
        """Test remote type extraction from workplaceType."""
        scraper = LeverSpotifyScraper()

        # Test remote
        raw_remote = {
            "id": "1",
            "text": "Remote Job",
            "descriptionPlain": "Description",
            "workplaceType": "remote",
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_remote])
        assert records[0].remote_type == "remote"

        # Test hybrid
        raw_hybrid = {
            "id": "2",
            "text": "Hybrid Job",
            "descriptionPlain": "Description",
            "workplaceType": "hybrid",
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_hybrid])
        assert records[0].remote_type == "hybrid"

        # Test onsite
        raw_onsite = {
            "id": "3",
            "text": "On-site Job",
            "descriptionPlain": "Description",
            "workplaceType": "onsite",
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_onsite])
        assert records[0].remote_type == "on-site"

    def test_parse_role_type_from_commitment(self):
        """Test role type extraction from commitment."""
        scraper = LeverSpotifyScraper()

        # Test permanent -> full-time
        raw_permanent = {
            "id": "1",
            "text": "Permanent Job",
            "descriptionPlain": "Description",
            "categories": {"commitment": "Permanent"},
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_permanent])
        assert records[0].role_type == "full-time"

        # Test contract
        raw_contract = {
            "id": "2",
            "text": "Contract Job",
            "descriptionPlain": "Description",
            "categories": {"commitment": "Contract"},
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_contract])
        assert records[0].role_type == "contract"

        # Test internship
        raw_intern = {
            "id": "3",
            "text": "Intern Job",
            "descriptionPlain": "Description",
            "categories": {"commitment": "Internship"},
            "applyUrl": "https://example.com",
        }
        records = scraper.parse([raw_intern])
        assert records[0].role_type == "internship"

    def test_parse_salary_extraction(self):
        """Test salary extraction from salaryRange."""
        scraper = LeverSpotifyScraper()

        raw_job = {
            "id": "1",
            "text": "Test Job",
            "descriptionPlain": "Description",
            "salaryRange": {"min": 100000, "max": 150000, "currency": "USD"},
            "applyUrl": "https://example.com",
        }

        records = scraper.parse([raw_job])
        assert records[0].salary_min == 100000
        assert records[0].salary_max == 150000
        assert records[0].salary_currency == "USD"

    def test_parse_posted_date_from_created_at(self):
        """Test posted date extraction from createdAt timestamp."""
        scraper = LeverSpotifyScraper()

        raw_job = {
            "id": "1",
            "text": "Test Job",
            "descriptionPlain": "Description",
            "createdAt": 1792767640768,  # Unix timestamp in milliseconds
            "applyUrl": "https://example.com",
        }

        records = scraper.parse([raw_job])
        assert records[0].posted_date is not None
        # 1792767640768 / 1000 = 1792767640 seconds = 2026-11-03
        assert records[0].posted_date.year == 2026

    def test_validate_valid_record(self):
        """Test validation of valid record."""
        scraper = LeverSpotifyScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="uuid-123",
            title="Test Job",
            description="Test description",
            requirements=None,
            location="New York",
            application_url="https://example.com",
            posted_date=None,
            remote_type="hybrid",
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
        scraper = LeverSpotifyScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="uuid-123",
            title="",
            description="Test description",
            requirements=None,
            location="New York",
            application_url="https://example.com",
            posted_date=None,
            remote_type="hybrid",
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
        scraper = LeverSpotifyScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="uuid-123",
            title="Test Job",
            description="",
            requirements=None,
            location="New York",
            application_url="https://example.com",
            posted_date=None,
            remote_type="hybrid",
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
        scraper = LeverSpotifyScraper()
        record = JobRecord(
            source_id=1,
            company_id=1,
            external_id="uuid-123",
            title="Test Job",
            description="Test description",
            requirements=None,
            location="New York",
            application_url="",
            posted_date=None,
            remote_type="hybrid",
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
        scraper = LeverSpotifyScraper()

        # First parse with error
        scraper.parse([{"id": "1"}])
        assert len(scraper.parse_errors) > 0

        # Second parse should have cleared errors
        scraper.parse([])
        assert len(scraper.parse_errors) == 0

    def test_fetch_http_error(self):
        """Test fetch handles HTTP errors."""
        scraper = LeverSpotifyScraper()

        with patch.object(scraper.session, "get") as mock_get:
            from requests.exceptions import RequestException

            mock_get.side_effect = RequestException("Network error")

            with pytest.raises(RequestException):
                scraper.fetch("https://api.lever.co/v0/postings/spotify")

    def test_fetch_invalid_json(self):
        """Test fetch handles invalid JSON."""
        scraper = LeverSpotifyScraper()

        with patch.object(scraper.session, "get") as mock_get:
            from requests.exceptions import JSONDecodeError

            mock_response = Mock()
            mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid JSON"):
                scraper.fetch("https://api.lever.co/v0/postings/spotify")

    def test_fetch_not_array_response(self):
        """Test fetch handles non-array response."""
        scraper = LeverSpotifyScraper()

        with patch.object(scraper.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"jobs": []}  # Object, not array
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="not a JSON array"):
                scraper.fetch("https://api.lever.co/v0/postings/spotify")
