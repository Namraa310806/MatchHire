"""
Tests for Elasticsearch analyzers.
"""

import pytest

from apps.search.providers.elasticsearch.analyzers import Analyzers


class TestAnalyzers:
    """Test Analyzers class."""

    def test_analysis_settings_structure(self):
        """Test analysis settings structure."""
        settings = Analyzers.get_analysis_settings()

        assert "analysis" in settings
        assert "analyzer" in settings["analysis"]
        assert "tokenizer" in settings["analysis"]
        assert "filter" in settings["analysis"]
        assert "normalizer" in settings["analysis"]

    def test_standard_analyzer(self):
        """Test standard analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "standard" in settings["analysis"]["analyzer"]
        assert settings["analysis"]["analyzer"]["standard"]["type"] == "standard"
        assert "stopwords" in settings["analysis"]["analyzer"]["standard"]

    def test_lowercase_analyzer(self):
        """Test lowercase analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "lowercase" in settings["analysis"]["analyzer"]
        assert settings["analysis"]["analyzer"]["lowercase"]["type"] == "custom"
        assert "tokenizer" in settings["analysis"]["analyzer"]["lowercase"]
        assert "filter" in settings["analysis"]["analyzer"]["lowercase"]

    def test_ascii_folding_analyzer(self):
        """Test ASCII folding analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "ascii_folding" in settings["analysis"]["analyzer"]
        assert "asciifolding" in settings["analysis"]["analyzer"]["ascii_folding"]["filter"]

    def test_edge_ngram_analyzer(self):
        """Test edge n-gram analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "edge_ngram_analyzer" in settings["analysis"]["analyzer"]
        assert settings["analysis"]["analyzer"]["edge_ngram_analyzer"]["tokenizer"] == "edge_ngram_tokenizer"

    def test_autocomplete_analyzer(self):
        """Test autocomplete analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "autocomplete_analyzer" in settings["analysis"]["analyzer"]
        assert settings["analysis"]["analyzer"]["autocomplete_analyzer"]["tokenizer"] == "autocomplete_tokenizer"

    def test_search_analyzer(self):
        """Test search analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "search_analyzer" in settings["analysis"]["analyzer"]
        assert settings["analysis"]["analyzer"]["search_analyzer"]["type"] == "custom"

    def test_synonym_analyzer(self):
        """Test synonym analyzer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "synonym_analyzer" in settings["analysis"]["analyzer"]
        assert "synonym_filter" in settings["analysis"]["analyzer"]["synonym_analyzer"]["filter"]

    def test_edge_ngram_tokenizer(self):
        """Test edge n-gram tokenizer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "edge_ngram_tokenizer" in settings["analysis"]["tokenizer"]
        assert settings["analysis"]["tokenizer"]["edge_ngram_tokenizer"]["type"] == "edge_ngram"
        assert "min_gram" in settings["analysis"]["tokenizer"]["edge_ngram_tokenizer"]
        assert "max_gram" in settings["analysis"]["tokenizer"]["edge_ngram_tokenizer"]

    def test_autocomplete_tokenizer(self):
        """Test autocomplete tokenizer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "autocomplete_tokenizer" in settings["analysis"]["tokenizer"]
        assert settings["analysis"]["tokenizer"]["autocomplete_tokenizer"]["type"] == "edge_ngram"
        assert settings["analysis"]["tokenizer"]["autocomplete_tokenizer"]["min_gram"] == 1

    def test_synonym_filter(self):
        """Test synonym filter definition."""
        settings = Analyzers.get_analysis_settings()

        assert "synonym_filter" in settings["analysis"]["filter"]
        assert settings["analysis"]["filter"]["synonym_filter"]["type"] == "synonym"
        assert "synonyms" in settings["analysis"]["filter"]["synonym_filter"]

    def test_english_stopwords_filter(self):
        """Test English stopwords filter definition."""
        settings = Analyzers.get_analysis_settings()

        assert "english_stopwords" in settings["analysis"]["filter"]
        assert settings["analysis"]["filter"]["english_stopwords"]["type"] == "stop"

    def test_english_stemmer_filter(self):
        """Test English stemmer filter definition."""
        settings = Analyzers.get_analysis_settings()

        assert "english_stemmer" in settings["analysis"]["filter"]
        assert settings["analysis"]["filter"]["english_stemmer"]["type"] == "stemmer"

    def test_lowercase_normalizer(self):
        """Test lowercase normalizer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "lowercase_normalizer" in settings["analysis"]["normalizer"]
        assert settings["analysis"]["normalizer"]["lowercase_normalizer"]["type"] == "custom"

    def test_ascii_normalizer(self):
        """Test ASCII normalizer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "ascii_normalizer" in settings["analysis"]["normalizer"]
        assert "asciifolding" in settings["analysis"]["normalizer"]["ascii_normalizer"]["filter"]

    def test_keyword_normalizer(self):
        """Test keyword normalizer definition."""
        settings = Analyzers.get_analysis_settings()

        assert "keyword_normalizer" in settings["analysis"]["normalizer"]

    def test_get_index_settings(self):
        """Test getting complete index settings."""
        settings = Analyzers.get_index_settings()

        assert "number_of_shards" in settings
        assert "number_of_replicas" in settings
        assert "refresh_interval" in settings
        assert "analysis" in settings

    def test_get_index_settings_with_custom(self):
        """Test getting index settings with custom settings."""
        custom_settings = {"number_of_shards": 5, "refresh_interval": "5s"}
        settings = Analyzers.get_index_settings(custom_settings)

        assert settings["number_of_shards"] == 5
        assert settings["refresh_interval"] == "5s"

    def test_add_synonym(self):
        """Test adding a synonym."""
        initial_synonyms = Analyzers.get_synonyms()
        initial_count = len(initial_synonyms)

        Analyzers.add_synonym("js, javascript")

        new_synonyms = Analyzers.get_synonyms()
        assert len(new_synonyms) == initial_count + 1
        assert "js, javascript" in new_synonyms

    def test_set_synonyms(self):
        """Test setting synonyms."""
        new_synonyms = ["python, py", "javascript, js", "typescript, ts"]
        Analyzers.set_synonyms(new_synonyms)

        current_synonyms = Analyzers.get_synonyms()
        assert current_synonyms == new_synonyms

    def test_get_synonyms(self):
        """Test getting synonyms."""
        synonyms = Analyzers.get_synonyms()

        assert isinstance(synonyms, list)

    def test_token_chars_in_edge_ngram(self):
        """Test token_chars configuration in edge n-gram tokenizer."""
        settings = Analyzers.get_analysis_settings()

        token_chars = settings["analysis"]["tokenizer"]["edge_ngram_tokenizer"]["token_chars"]
        assert "letter" in token_chars
        assert "digit" in token_chars

    def test_token_chars_in_autocomplete(self):
        """Test token_chars configuration in autocomplete tokenizer."""
        settings = Analyzers.get_analysis_settings()

        token_chars = settings["analysis"]["tokenizer"]["autocomplete_tokenizer"]["token_chars"]
        assert "letter" in token_chars
        assert "digit" in token_chars

    def test_analysis_settings_immutability(self):
        """Test that get_analysis_settings returns a copy."""
        settings1 = Analyzers.get_analysis_settings()
        settings2 = Analyzers.get_analysis_settings()

        # Modify settings1
        settings1["analysis"]["analyzer"]["standard"]["type"] = "modified"

        # settings2 should not be affected
        assert settings2["analysis"]["analyzer"]["standard"]["type"] == "standard"
