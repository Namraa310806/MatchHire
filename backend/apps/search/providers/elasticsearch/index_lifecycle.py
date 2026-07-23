"""
Elasticsearch index lifecycle management.

This module provides index creation, deletion, recreation, refresh,
close/open operations, aliases, versioned indices, and zero-downtime
alias switching.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IndexLifecycleManager:
    """
    Elasticsearch index lifecycle management.

    Provides index creation, deletion, recreation, refresh,
    close/open operations, aliases, versioned indices, and
    zero-downtime alias switching.
    """

    def __init__(self, client, index_prefix: str = "matchhire"):
        """
        Initialize index lifecycle manager.

        Args:
            client: Elasticsearch client instance
            index_prefix: Prefix for index names
        """
        self.client = client
        self.index_prefix = index_prefix

    def get_index_name(self, entity_type: str, version: Optional[int] = None) -> str:
        """
        Get the actual index name for an entity type.

        Args:
            entity_type: Entity type (e.g., 'job', 'candidate')
            version: Optional version number for versioned indices

        Returns:
            Index name
        """
        if version is not None:
            return f"{self.index_prefix}_{entity_type}_v{version}"
        return f"{self.index_prefix}_{entity_type}"

    def get_alias_name(self, entity_type: str) -> str:
        """
        Get the alias name for an entity type.

        Args:
            entity_type: Entity type (e.g., 'job', 'candidate')

        Returns:
            Alias name
        """
        return f"{self.index_prefix}_{entity_type}_alias"

    def create_index(
        self,
        entity_type: str,
        mapping: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
    ) -> bool:
        """
        Create an index with mapping and settings.

        Args:
            entity_type: Entity type
            mapping: Index mapping
            settings: Optional index settings
            version: Optional version number

        Returns:
            True if index was created
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return False

            body = {"mappings": mapping}
            if settings:
                body["settings"] = settings

            self.client.indices.create(index=index_name, body=body)
            logger.info(f"Created index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            raise

    def delete_index(self, entity_type: str, version: Optional[int] = None) -> bool:
        """
        Delete an index.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            True if index was deleted
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist")
                return False

            self.client.indices.delete(index=index_name)
            logger.info(f"Deleted index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            raise

    def recreate_index(
        self,
        entity_type: str,
        mapping: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
    ) -> bool:
        """
        Recreate an index (delete if exists, then create).

        Args:
            entity_type: Entity type
            mapping: Index mapping
            settings: Optional index settings
            version: Optional version number

        Returns:
            True if index was recreated
        """
        self.delete_index(entity_type, version)
        return self.create_index(entity_type, mapping, settings, version)

    def refresh_index(self, entity_type: str, version: Optional[int] = None) -> None:
        """
        Refresh an index to make changes visible to search.

        Args:
            entity_type: Entity type
            version: Optional version number
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            self.client.indices.refresh(index=index_name)
            logger.debug(f"Refreshed index {index_name}")
        except Exception as e:
            logger.error(f"Failed to refresh index {index_name}: {e}")
            raise

    def close_index(self, entity_type: str, version: Optional[int] = None) -> bool:
        """
        Close an index to free up resources.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            True if index was closed
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            if not self.client.indices.exists(index=index_name):
                return False

            self.client.indices.close(index=index_name)
            logger.info(f"Closed index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to close index {index_name}: {e}")
            raise

    def open_index(self, entity_type: str, version: Optional[int] = None) -> bool:
        """
        Open a closed index.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            True if index was opened
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            if not self.client.indices.exists(index=index_name):
                return False

            self.client.indices.open(index=index_name)
            logger.info(f"Opened index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to open index {index_name}: {e}")
            raise

    def create_alias(
        self,
        entity_type: str,
        index_name: str,
        alias_name: Optional[str] = None,
    ) -> bool:
        """
        Create an alias for an index.

        Args:
            entity_type: Entity type
            index_name: Index name to point to
            alias_name: Optional custom alias name

        Returns:
            True if alias was created
        """
        alias = alias_name or self.get_alias_name(entity_type)

        try:
            self.client.indices.put_alias(index=index_name, name=alias)
            logger.info(f"Created alias {alias} -> {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create alias {alias}: {e}")
            raise

    def delete_alias(
        self,
        entity_type: str,
        alias_name: Optional[str] = None,
    ) -> bool:
        """
        Delete an alias.

        Args:
            entity_type: Entity type
            alias_name: Optional custom alias name

        Returns:
            True if alias was deleted
        """
        alias = alias_name or self.get_alias_name(entity_type)

        try:
            self.client.indices.delete_alias(index="*", name=alias)
            logger.info(f"Deleted alias {alias}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete alias {alias}: {e}")
            raise

    def get_aliases(self, entity_type: str) -> Dict[str, Any]:
        """
        Get all aliases for an entity type.

        Args:
            entity_type: Entity type

        Returns:
            Dictionary of alias information
        """
        alias = self.get_alias_name(entity_type)

        try:
            return self.client.indices.get_alias(name=alias)
        except Exception as e:
            logger.error(f"Failed to get aliases for {entity_type}: {e}")
            raise

    def switch_alias(
        self,
        entity_type: str,
        old_index: str,
        new_index: str,
        alias_name: Optional[str] = None,
    ) -> bool:
        """
        Switch an alias from old index to new index (zero-downtime).

        Args:
            entity_type: Entity type
            old_index: Current index name
            new_index: New index name
            alias_name: Optional custom alias name

        Returns:
            True if alias was switched
        """
        alias = alias_name or self.get_alias_name(entity_type)

        try:
            actions = [
                {"remove": {"index": old_index, "alias": alias}},
                {"add": {"index": new_index, "alias": alias}},
            ]

            self.client.indices.update_aliases(body={"actions": actions})
            logger.info(f"Switched alias {alias} from {old_index} to {new_index}")
            return True

        except Exception as e:
            logger.error(f"Failed to switch alias {alias}: {e}")
            raise

    def create_versioned_index(
        self,
        entity_type: str,
        mapping: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        switch_alias: bool = True,
    ) -> str:
        """
        Create a new versioned index and optionally switch the alias.

        Args:
            entity_type: Entity type
            mapping: Index mapping
            settings: Optional index settings
            switch_alias: Whether to switch the alias to the new index

        Returns:
            New index name
        """
        # Get current version
        current_version = self._get_current_version(entity_type)
        new_version = current_version + 1

        # Create new index
        new_index = self.get_index_name(entity_type, new_version)
        self.create_index(entity_type, mapping, settings, new_version)

        # Switch alias if requested
        if switch_alias:
            old_index = self.get_index_name(entity_type, current_version) if current_version > 0 else None

            if old_index and self.client.indices.exists(index=old_index):
                self.switch_alias(entity_type, old_index, new_index)
            else:
                self.create_alias(entity_type, new_index)

        return new_index

    def _get_current_version(self, entity_type: str) -> int:
        """
        Get the current version number for an entity type.

        Args:
            entity_type: Entity type

        Returns:
            Current version number (0 if no versioned indices exist)
        """
        try:
            # Get all indices for this entity type
            index_pattern = f"{self.index_prefix}_{entity_type}_v*"
            indices = self.client.indices.get(index=index_pattern)

            max_version = 0
            for index_name in indices.keys():
                # Extract version number from index name
                if index_name.startswith(f"{self.index_prefix}_{entity_type}_v"):
                    version_str = index_name.split("_v")[-1]
                    try:
                        version = int(version_str)
                        max_version = max(max_version, version)
                    except ValueError:
                        pass

            return max_version

        except Exception as e:
            logger.error(f"Failed to get current version for {entity_type}: {e}")
            return 0

    def get_index_settings(self, entity_type: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get settings for an index.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            Index settings
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            return self.client.indices.get_settings(index=index_name)
        except Exception as e:
            logger.error(f"Failed to get settings for {index_name}: {e}")
            raise

    def get_index_mapping(self, entity_type: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get mapping for an index.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            Index mapping
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            return self.client.indices.get_mapping(index=index_name)
        except Exception as e:
            logger.error(f"Failed to get mapping for {index_name}: {e}")
            raise

    def index_exists(self, entity_type: str, version: Optional[int] = None) -> bool:
        """
        Check if an index exists.

        Args:
            entity_type: Entity type
            version: Optional version number

        Returns:
            True if index exists
        """
        index_name = self.get_index_name(entity_type, version)

        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:
            logger.error(f"Failed to check existence of {index_name}: {e}")
            return False

    def list_indices(self, entity_type: Optional[str] = None) -> List[str]:
        """
        List all indices, optionally filtered by entity type.

        Args:
            entity_type: Optional entity type filter

        Returns:
            List of index names
        """
        try:
            if entity_type:
                pattern = f"{self.index_prefix}_{entity_type}*"
            else:
                pattern = f"{self.index_prefix}*"

            return list(self.client.indices.get(index=pattern).keys())

        except Exception as e:
            logger.error(f"Failed to list indices: {e}")
            return []

    def cleanup_old_indices(
        self,
        entity_type: str,
        keep_versions: int = 2,
    ) -> int:
        """
        Clean up old versioned indices, keeping only the most recent versions.

        Args:
            entity_type: Entity type
            keep_versions: Number of recent versions to keep

        Returns:
            Number of indices deleted
        """
        try:
            # Get all versioned indices
            index_pattern = f"{self.index_prefix}_{entity_type}_v*"
            indices = self.client.indices.get(index=index_pattern)

            # Extract versions
            version_indices = []
            for index_name in indices.keys():
                if index_name.startswith(f"{self.index_prefix}_{entity_type}_v"):
                    version_str = index_name.split("_v")[-1]
                    try:
                        version = int(version_str)
                        version_indices.append((version, index_name))
                    except ValueError:
                        pass

            # Sort by version (descending)
            version_indices.sort(reverse=True)

            # Delete old indices
            deleted_count = 0
            for i, (version, index_name) in enumerate(version_indices):
                if i >= keep_versions:
                    # Check if index is not pointed to by alias
                    alias = self.get_alias_name(entity_type)
                    try:
                        alias_info = self.client.indices.get_alias(index=index_name)
                        if alias not in alias_info[index_name].get("aliases", {}):
                            self.client.indices.delete(index=index_name)
                            deleted_count += 1
                            logger.info(f"Deleted old index {index_name}")
                    except Exception:
                        pass

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old indices for {entity_type}: {e}")
            return 0
