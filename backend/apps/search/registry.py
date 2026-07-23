"""
Search provider registry.

This module implements a registry for managing search providers.
The registry allows for provider selection based on configuration
and makes it easy to switch between providers without changing business logic.
"""

from typing import Any, Dict, Optional, Type
from threading import Lock

from apps.search.providers.base import SearchProvider
from apps.search.providers.postgresql import PostgreSQLProvider
from apps.search.exceptions import ProviderNotRegistered, ConfigurationError


class SearchRegistry:
    """
    Registry for search providers.

    This class manages the registration and retrieval of search providers.
    It implements a singleton pattern to ensure only one registry instance exists.
    """

    _instance: Optional["SearchRegistry"] = None
    _lock = Lock()

    def __new__(cls) -> "SearchRegistry":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry (only once)."""
        if self._initialized:
            return

        self._providers: Dict[str, Type[SearchProvider]] = {}
        self._instances: Dict[str, SearchProvider] = {}
        self._current_provider: Optional[str] = None
        self._initialized = True

        # Register built-in providers
        self.register_provider("postgresql", PostgreSQLProvider)

    def register_provider(
        self,
        name: str,
        provider_class: Type[SearchProvider],
    ) -> None:
        """
        Register a search provider class.

        Args:
            name: Name to register the provider under
            provider_class: Provider class to register

        Raises:
            ValueError: If provider class is not a subclass of SearchProvider
        """
        if not issubclass(provider_class, SearchProvider):
            raise ValueError(
                f"Provider class {provider_class} must be a subclass of SearchProvider"
            )

        self._providers[name] = provider_class

    def unregister_provider(self, name: str) -> None:
        """
        Unregister a search provider.

        Args:
            name: Name of the provider to unregister
        """
        if name in self._providers:
            del self._providers[name]

        if name in self._instances:
            instance = self._instances[name]
            instance.close()
            del self._instances[name]

        if self._current_provider == name:
            self._current_provider = None

    def get_provider(
        self,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SearchProvider:
        """
        Get a search provider instance.

        Args:
            name: Name of the provider (uses current provider if None)
            config: Configuration for the provider (uses default if None)

        Returns:
            SearchProvider instance

        Raises:
            ProviderNotRegistered: If provider is not registered
            ConfigurationError: If no configuration is provided for a new instance
        """
        provider_name = name or self._current_provider

        if not provider_name:
            raise ConfigurationError("No provider specified and no current provider set")

        if provider_name not in self._providers:
            raise ProviderNotRegistered(f"Provider '{provider_name}' is not registered")

        # Return existing instance if available
        if provider_name in self._instances:
            return self._instances[provider_name]

        # Create new instance
        if config is None:
            raise ConfigurationError(
                f"Configuration required for provider '{provider_name}'"
            )

        provider_class = self._providers[provider_name]
        instance = provider_class(config)
        self._instances[provider_name] = instance

        return instance

    def set_current_provider(self, name: str) -> None:
        """
        Set the current default provider.

        Args:
            name: Name of the provider to set as current

        Raises:
            ProviderNotRegistered: If provider is not registered
        """
        if name not in self._providers:
            raise ProviderNotRegistered(f"Provider '{name}' is not registered")

        self._current_provider = name

    def get_current_provider(self) -> Optional[str]:
        """
        Get the name of the current default provider.

        Returns:
            Name of the current provider or None if not set
        """
        return self._current_provider

    def list_providers(self) -> list[str]:
        """
        List all registered provider names.

        Returns:
            List of registered provider names
        """
        return list(self._providers.keys())

    def is_registered(self, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Name of the provider to check

        Returns:
            True if provider is registered, False otherwise
        """
        return name in self._providers

    def close_all(self) -> None:
        """Close all provider instances and clear the registry."""
        for instance in self._instances.values():
            instance.close()

        self._instances.clear()
        self._current_provider = None


# Global registry instance
registry = SearchRegistry()


def get_registry() -> SearchRegistry:
    """
    Get the global search registry instance.

    Returns:
        SearchRegistry singleton instance
    """
    return registry
