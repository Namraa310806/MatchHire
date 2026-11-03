"""Tests for years of experience extraction."""

from django.test import TestCase

from api.ingestion.experience_extraction import extract_required_yoe


class ExperienceExtractionTest(TestCase):
    """Tests for years of experience extraction."""

    def test_extract_fresher(self):
        """Test extracting 'fresher' as 0 years."""
        description = "This is a fresher position for recent graduates."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_fresh_graduate(self):
        """Test extracting 'fresh graduate' as 0 years."""
        description = "Position for fresh graduate with no experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_zero_years(self):
        """Test extracting '0 years' as 0.0."""
        description = "0 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_zero_year(self):
        """Test extracting '0 year' as 0.0."""
        description = "0 year experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_range_including_zero(self):
        """Test extracting range including 0 as 0.0."""
        description = "0-2 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_range_with_to(self):
        """Test extracting range with 'to' including 0."""
        description = "0 to 2 years experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_range_excluding_zero(self):
        """Test extracting range excluding 0 as minimum."""
        description = "1-3 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 1.0)

    def test_extract_range_2_to_5(self):
        """Test extracting 2-5 years as 2.0."""
        description = "2-5 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 2.0)

    def test_extract_at_least(self):
        """Test extracting 'at least X years' as X."""
        description = "At least 3 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 3.0)

    def test_extract_minimum(self):
        """Test extracting 'minimum X years' as X."""
        description = "Minimum 5 years experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 5.0)

    def test_extract_plus_years(self):
        """Test extracting 'X+ years' as X."""
        description = "3+ years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 3.0)

    def test_extract_plus_years_with_space(self):
        """Test extracting 'X + years' as X."""
        description = "3 + years of experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 3.0)

    def test_extract_single_year(self):
        """Test extracting single year requirement."""
        description = "3 years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 3.0)

    def test_extract_of_experience(self):
        """Test extracting 'X years of experience'."""
        description = "4 years of experience needed."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 4.0)

    def test_no_experience_requirement(self):
        """Test when no experience requirement is found."""
        description = "This is a job description with no experience mentioned."
        yoe = extract_required_yoe(description)
        self.assertIsNone(yoe)

    def test_empty_description(self):
        """Test empty description returns None."""
        yoe = extract_required_yoe("")
        self.assertIsNone(yoe)

    def test_none_description(self):
        """Test None description returns None."""
        yoe = extract_required_yoe(None)
        self.assertIsNone(yoe)

    def test_case_insensitive(self):
        """Test extraction is case-insensitive."""
        description = "FRESHER position with 0 YEARS experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_punctuation_variations(self):
        """Test extraction handles punctuation."""
        description = "3+ years. of experience, required!"
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 3.0)

    def test_ambiguous_text(self):
        """Test ambiguous text returns None."""
        description = "Some experience is good but not specific."
        yoe = extract_required_yoe(description)
        self.assertIsNone(yoe)

    def test_contradictory_requirements(self):
        """Test contradictory requirements (first match wins)."""
        description = "0-2 years but also 5+ years mentioned."
        yoe = extract_required_yoe(description)
        # First match wins (0-2 includes 0)
        self.assertEqual(yoe, 0.0)

    def test_explicit_zero_vs_implicit_zero(self):
        """Test explicit 0 is distinguished from missing."""
        description = "0 years experience explicitly stated."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 0.0)

    def test_extract_experience_keyword(self):
        """Test 'experience' keyword pattern."""
        description = "5 years experience in software development."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 5.0)

    def test_large_year_value(self):
        """Test large year value."""
        description = "10+ years of experience required."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 10.0)

    def test_at_least_lowercase(self):
        """Test 'at least' in lowercase."""
        description = "at least 2 years of experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 2.0)

    def test_minimum_lowercase(self):
        """Test 'minimum' in lowercase."""
        description = "minimum 1 year experience."
        yoe = extract_required_yoe(description)
        self.assertEqual(yoe, 1.0)
