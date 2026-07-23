"""
Elasticsearch custom analyzers.

This module defines custom analyzers for text processing including
standard analyzer, lowercase, ASCII folding, edge n-gram, autocomplete,
search analyzer, synonym placeholder, and custom normalizers.
"""

from typing import Dict, Any


class Analyzers:
    """
    Elasticsearch custom analyzers.

    Provides production-ready analyzers for text processing including
    standard analyzer, lowercase, ASCII folding, edge n-gram, autocomplete,
    search analyzer, synonym placeholder, and custom normalizers.
    """

    # Analysis settings
    ANALYSIS_SETTINGS = {
        "analysis": {
            "analyzer": {
                "standard": {
                    "type": "standard",
                    "stopwords": "_english_",
                },
                "lowercase": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                },
                "ascii_folding": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
                "edge_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"],
                },
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase", "asciifolding"],
                },
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
                "synonym_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "synonym_filter"],
                },
            },
            "tokenizer": {
                "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"],
                },
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"],
                },
            },
            "filter": {
                "synonym_filter": {
                    "type": "synonym",
                    "synonyms": [
                        # Placeholder for future synonym configuration
                        # "js, javascript",
                        # "ts, typescript",
                        # "py, python",
                    ],
                },
                "english_stopwords": {
                    "type": "stop",
                    "stopwords": "_english_",
                },
                "english_stemmer": {
                    "type": "stemmer",
                    "name": "english",
                },
                "english_possessive": {
                    "type": "stemmer",
                    "name": "possessive_english",
                },
            },
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase"],
                },
                "ascii_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase", "asciifolding"],
                },
                "keyword_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase", "asciifolding"],
                    "char_filter": [],
                },
            },
        },
    }

    @classmethod
    def get_analysis_settings(cls) -> Dict[str, Any]:
        """
        Get analysis settings for index configuration.

        Returns:
            Analysis settings dictionary
        """
        return cls.ANALYSIS_SETTINGS.copy()

    @classmethod
    def get_index_settings(cls, custom_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get complete index settings including analysis.

        Args:
            custom_settings: Optional custom settings to merge

        Returns:
            Complete index settings
        """
        from .mappings import Mappings

        settings = Mappings.BASE_SETTINGS.copy()
        settings.update(cls.ANALYSIS_SETTINGS)

        if custom_settings:
            settings.update(custom_settings)

        return settings

    @classmethod
    def add_synonym(cls, synonym: str) -> None:
        """
        Add a synonym to the synonym filter.

        Args:
            synonym: Synonym mapping (e.g., "js, javascript")
        """
        cls.ANALYSIS_SETTINGS["analysis"]["filter"]["synonym_filter"]["synonyms"].append(
            synonym
        )

    @classmethod
    def set_synonyms(cls, synonyms: list) -> None:
        """
        Set the complete list of synonyms.

        Args:
            synonyms: List of synonym mappings
        """
        cls.ANALYSIS_SETTINGS["analysis"]["filter"]["synonym_filter"]["synonyms"] = synonyms

    @classmethod
    def get_synonyms(cls) -> list:
        """
        Get the current list of synonyms.

        Returns:
            List of synonym mappings
        """
        return cls.ANALYSIS_SETTINGS["analysis"]["filter"]["synonym_filter"]["synonyms"]
