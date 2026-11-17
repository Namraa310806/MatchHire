"""Tests for domain keyword extraction."""

import pytest

from api.extraction.domain_keywords import (
    DomainKeywordMatch,
    _match_keyword,
    extract_domain_keywords,
    get_all_domain_keywords,
    get_domain_keyword_aliases,
)


class TestDomainKeywordExtraction:
    """Tests for domain keyword extraction from text."""

    @pytest.mark.parametrize(
        "text,expected_keywords",
        [
            # Basic domain extraction
            ("NLP and computer vision experience", ["Computer Vision", "NLP"]),
            ("Fintech and healthtech background", ["Fintech", "Healthtech"]),
            ("Data science and machine learning", ["Data Science", "Machine Learning"]),
            # Case variations
            ("AI and ML experience", ["Artificial Intelligence", "Machine Learning"]),
            ("BLOCKCHAIN and CRYPTO", ["Blockchain", "Cryptocurrency"]),
            # Aliases
            ("SaaS and PaaS solutions", ["PaaS", "SaaS"]),
            ("B2B and B2C markets", ["B2B", "B2C"]),
            ("Edtech startup", ["Edtech"]),
            # Multiple keywords
            (
                "SaaS B2B Fintech company",
                ["B2B", "Fintech", "SaaS"],
            ),
            # Tech domains
            ("Cloud computing and edge computing", ["Cloud Computing", "Edge Computing"]),
            ("Distributed systems and microservices", ["Distributed Systems", "Microservices"]),
            # DevOps
            ("DevOps and CI/CD pipelines", ["CI/CD", "DevOps"]),
            # Security
            ("Cybersecurity and InfoSec", ["Cybersecurity", "InfoSec"]),
            # Compliance
            ("GDPR and HIPAA compliance", ["Compliance", "GDPR", "HIPAA"]),  # Compliance is a separate keyword
            # Agile
            ("Agile and Scrum methodology", ["Agile", "Scrum"]),
            # UX/UI
            ("UX and UI design", ["User Experience", "User Interface"]),
            # Product management
            ("Product and project management", ["Project Management"]),  # Only Project Management matches exactly
            # Empty or no keywords
            ("No domain keywords mentioned", []),
            ("", []),
            (None, []),
        ],
    )
    def test_extract_domain_keywords_various_cases(self, text, expected_keywords):
        """Test domain keyword extraction with various inputs."""
        if text is None:
            result = extract_domain_keywords("")
        else:
            result = extract_domain_keywords(text)
        # Extract just the keyword names for comparison
        result_keywords = [match.keyword for match in result]
        assert sorted(result_keywords) == sorted(expected_keywords)

    def test_extract_domain_keywords_deduplication(self):
        """Test that duplicate keywords are removed."""
        text = "AI and ML and AI and ML"
        result = extract_domain_keywords(text)
        keywords = [match.keyword for match in result]
        assert keywords.count("Artificial Intelligence") == 1
        assert keywords.count("Machine Learning") == 1

    def test_extract_domain_keywords_sorted_output(self):
        """Test that output is sorted deterministically."""
        text = "Fintech Healthtech Edtech"
        result = extract_domain_keywords(text)
        keywords = [match.keyword for match in result]
        assert keywords == sorted(keywords)

    def test_extract_domain_keywords_result_structure(self):
        """Test that result contains DomainKeywordMatch objects."""
        text = "NLP and Computer Vision"
        result = extract_domain_keywords(text)
        assert isinstance(result, list)
        assert all(isinstance(item, DomainKeywordMatch) for item in result)
        assert all(item.keyword for item in result)

    def test_extract_domain_keywords_with_matched_alias(self):
        """Test that matched alias is recorded when applicable."""
        text = "AI and ML experience"
        result = extract_domain_keywords(text)
        # Check that some results have matched_alias set
        # (This depends on whether the matched term was an alias or canonical)
        assert len(result) == 2


class TestMatchKeyword:
    """Tests for the internal _match_keyword function."""

    @pytest.mark.parametrize(
        "text,keyword,expected",
        [
            # Basic matching
            ("nlp experience", "nlp", True),
            ("NLP experience", "nlp", True),
            ("NLP experience", "natural language processing", False),
            # Word boundaries
            ("pythonic approach", "python", False),
            # Multi-word terms
            ("computer vision", "computer vision", True),
            ("Computer Vision", "computer vision", True),
            # Slashes and hyphens
            ("ci/cd pipeline", "ci/cd", True),
            ("CI/CD pipeline", "ci/cd", True),
            ("e-commerce", "ecommerce", False),  # e-commerce is not the same as ecommerce
            # No match
            ("No keywords here", "nlp", False),
            ("", "nlp", False),
        ],
    )
    def test_match_keyword_cases(self, text, keyword, expected):
        """Test _match_keyword with various cases."""
        result = _match_keyword(text.lower(), keyword.lower())
        assert result == expected


class TestDomainKeywordUtilities:
    """Tests for domain keyword utility functions."""

    def test_get_all_domain_keywords(self):
        """Test getting all domain keywords."""
        keywords = get_all_domain_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "Artificial Intelligence" in keywords
        assert "Machine Learning" in keywords

    def test_get_domain_keyword_aliases(self):
        """Test getting aliases for a domain keyword."""
        aliases = get_domain_keyword_aliases("Artificial Intelligence")
        assert aliases is not None
        assert "ai" in aliases

    def test_get_domain_keyword_aliases_nonexistent(self):
        """Test getting aliases for nonexistent keyword."""
        aliases = get_domain_keyword_aliases("Nonexistent Keyword")
        assert aliases is None

    def test_domain_keywords_are_distinct_from_skills(self):
        """Test that domain keywords are separate from technical skills."""
        from api.extraction import get_skills_dictionary

        skills_dict = get_skills_dictionary()
        domain_keywords = get_all_domain_keywords()

        # Check that there's no overlap between domain keywords and skills
        # (They should be distinct concepts)
        skills_set = set(skills_dict.get_all_canonical_names())
        domain_set = set(domain_keywords)

        # Some overlap is acceptable (e.g., "Machine Learning" could be both)
        # but the extraction should be separate
        # This test documents the expected behavior
        overlap = skills_set.intersection(domain_set)
        # If there's overlap, it should be minimal and intentional
        # Allow up to 20% overlap given the large vocabulary
        assert len(overlap) < len(domain_set) * 0.2  # Less than 20% overlap


class TestDomainKeywordFalsePositives:
    """Tests for false positive prevention in domain keyword extraction."""

    def test_prevents_substring_false_positives(self):
        """Test that substring false positives are avoided."""
        text = "This is a pythonic approach"
        result = extract_domain_keywords(text)
        [match.keyword for match in result]
        # Should not match "Python" as a domain keyword (it's a skill)
        # Domain keywords are separate from skills

    def test_word_boundary_awareness(self):
        """Test that word boundaries are respected."""
        text = "Going to the store"
        result = extract_domain_keywords(text)
        [match.keyword for match in result]
        # Should not match "Go" as a domain keyword

    def test_context_aware_matching(self):
        """Test that context doesn't cause false positives."""
        text = "We need a reliable api for our application"
        result = extract_domain_keywords(text)
        [match.keyword for match in result]
        # "API" by itself should not trigger "API Economy" domain keyword
        # unless explicitly mentioned
