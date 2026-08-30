"""
Source registry for controlled scraper mapping.

This module provides a controlled registry mapping source identifiers
to their corresponding scraper classes and company slugs.

This prevents arbitrary source execution and ensures only
explicitly supported sources can be ingested.

Security: Do not allow user-provided arbitrary Python modules/classes.
Only sources in this registry are valid for execution.
"""

from typing import Dict, Type, Tuple
from apps.jobs.scrapers.base import BaseJobScraper
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.scrapers.stripe import StripeScraper


# Source registry: maps source identifier to (scraper_class, company_slug)
# This is the authoritative list of supported sources.
SOURCE_REGISTRY: Dict[str, Tuple[Type[BaseJobScraper], str]] = {
    'nexus_technologies': (NexusTechnologiesScraper, 'nexus-technologies'),
    'stripe': (StripeScraper, 'stripe'),
}


def get_scraper(source: str) -> Tuple[Type[BaseJobScraper], str]:
    """
    Get the scraper class and company slug for a source identifier.
    
    Args:
        source: The source identifier (e.g., 'stripe', 'nexus_technologies')
    
    Returns:
        Tuple of (scraper_class, company_slug)
    
    Raises:
        ValueError: If the source is not in the registry
    """
    if source not in SOURCE_REGISTRY:
        available = ', '.join(sorted(SOURCE_REGISTRY.keys()))
        raise ValueError(
            f"Unknown source: '{source}'. "
            f"Available sources: {available}"
        )
    
    return SOURCE_REGISTRY[source]


def is_source_supported(source: str) -> bool:
    """
    Check if a source identifier is supported.
    
    Args:
        source: The source identifier to check
    
    Returns:
        True if the source is in the registry, False otherwise
    """
    return source in SOURCE_REGISTRY


def get_supported_sources() -> list:
    """
    Get a list of all supported source identifiers.
    
    Returns:
        List of source identifier strings
    """
    return sorted(SOURCE_REGISTRY.keys())
