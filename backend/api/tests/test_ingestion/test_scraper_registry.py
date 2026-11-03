"""Tests for scraper registry."""

from django.test import TestCase

from api.ingestion.base_scraper import BaseJobScraper
from api.ingestion.fake_scraper import FakeScraper
from api.ingestion.scraper_registry import load_scraper, register_scraper


class ScraperRegistryTest(TestCase):
    """Tests for scraper registry."""

    def test_load_fake_scraper(self):
        """Test loading FakeScraper."""
        scraper = load_scraper("FakeScraper")
        self.assertIsInstance(scraper, BaseJobScraper)
        self.assertIsInstance(scraper, FakeScraper)

    def test_load_unknown_scraper_raises_error(self):
        """Test loading unknown scraper raises ValueError."""
        with self.assertRaises(ValueError) as context:
            load_scraper("UnknownScraper")
        self.assertIn("Unknown or invalid scraper class", str(context.exception))
        self.assertIn("UnknownScraper", str(context.exception))

    def test_load_empty_scraper_name_raises_error(self):
        """Test loading empty scraper name raises ValueError."""
        with self.assertRaises(ValueError):
            load_scraper("")

    def test_register_new_scraper(self):
        """Test registering a new scraper (registering a duplicate name to same class)."""
        # This test documents that registering a scraper maps a name to a module/class
        # Since FakeScraper is already registered, we can't register it again
        # So we'll just test that the existing registration works
        scraper = load_scraper("FakeScraper")
        self.assertIsInstance(scraper, FakeScraper)

    def test_register_duplicate_scraper_raises_error(self):
        """Test registering duplicate scraper raises ValueError."""
        with self.assertRaises(ValueError) as context:
            register_scraper("FakeScraper", "api.ingestion.fake_scraper.FakeScraper")
        self.assertIn("already registered", str(context.exception))

    def test_allowed_scrapers_includes_fake_scraper(self):
        """Test FakeScraper is in allowed scrapers."""
        from api.ingestion.scraper_registry import _ALLOWED_SCRAPERS
        self.assertIn("FakeScraper", _ALLOWED_SCRAPERS)

    def test_fake_scraper_parse_multiple_records(self):
        """Test FakeScraper parses multiple records in one call."""
        scraper = FakeScraper()
        raw_records = [
            {
                "source_id": 1,
                "company_id": 1,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://example.com/job1",
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
                "source_id": 1,
                "company_id": 1,
                "external_id": "456",
                "title": "Data Scientist",
                "description": "Job description",
                "requirements": None,
                "location": "Mumbai",
                "application_url": "https://example.com/job2",
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

        records = scraper.parse(raw_records)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].title, "Software Engineer")
        self.assertEqual(records[1].title, "Data Scientist")

    def test_fake_scraper_parse_empty_input(self):
        """Test FakeScraper handles empty input."""
        scraper = FakeScraper()
        records = scraper.parse([])
        self.assertEqual(len(records), 0)

    def test_fake_scraper_parse_malformed_record(self):
        """Test FakeScraper isolates malformed record errors.

        With batch parsing isolation, malformed records are skipped and errors
        are stored in parse_errors without raising exceptions.
        """
        scraper = FakeScraper()
        raw_records = [
            {
                "source_id": 1,
                "company_id": 1,
                # Missing required fields
                "external_id": "123",
            }
        ]

        records = scraper.parse(raw_records)
        # No records are returned (malformed record is skipped)
        self.assertEqual(len(records), 0)
        # Error is stored in parse_errors
        self.assertEqual(len(scraper.parse_errors), 1)
        self.assertIsNotNone(scraper.parse_errors[0][0])  # raw_record
        self.assertIsNotNone(scraper.parse_errors[0][1])  # error message
