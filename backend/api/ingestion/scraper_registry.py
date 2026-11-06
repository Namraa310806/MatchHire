"""Scraper registry for loading scraper classes by name."""

from importlib import import_module

from .base_scraper import BaseJobScraper

# Registry of allowed scraper classes
# Format: "class_name": (module_path, class_name)
_ALLOWED_SCRAPERS: dict[str, tuple[str, str]] = {
    "FakeScraper": ("api.ingestion.fake_scraper", "FakeScraper"),
    "GreenhouseStripeScraper": ("api.ingestion.scrapers.greenhouse_stripe", "GreenhouseStripeScraper"),
    "LeverSpotifyScraper": ("api.ingestion.scrapers.lever_spotify", "LeverSpotifyScraper"),
    # Development-only seed scraper for synthetic job data
    # This scraper generates fictional data for local development and testing
    # It routes through the standard ingestion pipeline to preserve the job-creation invariant
    "DevSeedScraper": ("api.ingestion.scrapers.dev_seed", "DevSeedScraper"),
}


def load_scraper(scraper_class: str) -> BaseJobScraper:
    """Load a scraper class by name.

    Args:
        scraper_class: The scraper class name (e.g., "FakeScraper")

    Returns:
        An instance of the requested scraper class

    Raises:
        ValueError: If scraper_class is not in the allowed registry
        ImportError: If the scraper module cannot be imported
        AttributeError: If the scraper class does not exist in the module
    """
    if scraper_class not in _ALLOWED_SCRAPERS:
        raise ValueError(
            f"Unknown or invalid scraper class: {scraper_class}. "
            f"Allowed scrapers: {list(_ALLOWED_SCRAPERS.keys())}"
        )

    module_path, class_name = _ALLOWED_SCRAPERS[scraper_class]
    module = import_module(module_path)
    scraper_cls = getattr(module, class_name)

    scraper: BaseJobScraper = scraper_cls()
    return scraper


def register_scraper(class_name: str, module_path: str) -> None:
    """Register a new scraper class.

    This is for future use when real scrapers are implemented.
    Registration should happen during application initialization.

    Args:
        class_name: The class name (e.g., "GoogleCareerPageScraper")
        module_path: The full Python module path (e.g., "api.scrapers.google")

    Raises:
        ValueError: If class_name is already registered
    """
    if class_name in _ALLOWED_SCRAPERS:
        raise ValueError(f"Scraper class {class_name} is already registered")

    _ALLOWED_SCRAPERS[class_name] = (module_path, class_name)
