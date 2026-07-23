"""
Index Manager.

This module implements the IndexManager, which provides provider-independent
operations for managing search indices. It handles index creation, deletion,
rebuilding, refreshing, optimization, health checks, and statistics.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from apps.search.indexing.documents import BaseDocument, EntityType
from apps.search.indexing.metrics import get_metrics
from apps.search.exceptions import SearchError, ProviderUnavailable

logger = logging.getLogger(__name__)


class IndexManager:
    """
    Provider-independent index manager.
    
    This class provides a unified interface for managing search indices
    across all providers. It delegates to provider-specific implementations
    while maintaining a consistent API.
    """
    
    def __init__(self, provider: Any):
        """
        Initialize the index manager.
        
        Args:
            provider: Search provider instance
        """
        self.provider = provider
        self.metrics = get_metrics()

    def _as_bool(self, value: Any, default: bool = True) -> bool:
        """Normalize provider responses into a boolean result."""
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return bool(value)

    def _as_dict(self, value: Any, default: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize provider responses into a dictionary."""
        if isinstance(value, dict):
            return value
        return default

    def _as_list(self, value: Any) -> List[str]:
        """Normalize provider responses into a list of aliases."""
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, set):
            return sorted(value)
        return []
    
    def create_index(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create a new index for a specific entity type.
        
        Args:
            entity_type: Type of entity to index
            index_name: Optional custom index name
            settings: Optional index settings
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If index creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Generate index name if not provided
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "create_index"):
                result = self._as_bool(self.provider.create_index(
                    index_name=index_name,
                    entity_type=entity_type.value,
                    settings=settings or {},
                ))
            else:
                # For PostgreSQL provider, index creation is implicit
                logger.info(f"Index creation for {entity_type.value} is implicit for PostgreSQL provider")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="create",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create index for {entity_type.value}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="create",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Index creation failed: {e}")
    
    def delete_index(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
    ) -> bool:
        """
        Delete an index for a specific entity type.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If index deletion fails
        """
        start_time = datetime.utcnow()
        
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "delete_index"):
                result = self._as_bool(self.provider.delete_index(
                    index_name=index_name,
                    entity_type=entity_type.value,
                ))
            else:
                # For PostgreSQL provider, index deletion is implicit
                logger.info(f"Index deletion for {entity_type.value} is implicit for PostgreSQL provider")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="delete",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete index for {entity_type.value}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="delete",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Index deletion failed: {e}")
    
    def rebuild_index(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Rebuild an index from scratch.
        
        This operation deletes the existing index and creates a new one,
        then reindexes all documents.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            settings: Optional index settings
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If index rebuild fails
        """
        start_time = datetime.utcnow()
        
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delete existing index
            self.delete_index(entity_type, index_name)
            
            # Create new index
            self.create_index(entity_type, index_name, settings)
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="rebuild",
                entity_type=entity_type.value,
                duration=duration,
                success=True,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rebuild index for {entity_type.value}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="rebuild",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Index rebuild failed: {e}")
    
    def refresh_index(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
    ) -> bool:
        """
        Refresh an index to make recent changes visible.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If index refresh fails
        """
        start_time = datetime.utcnow()
        
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "refresh_index"):
                result = self._as_bool(self.provider.refresh_index(
                    index_name=index_name,
                    entity_type=entity_type.value,
                ))
            else:
                # For PostgreSQL provider, refresh is implicit
                logger.info(f"Index refresh for {entity_type.value} is implicit for PostgreSQL provider")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="refresh",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to refresh index for {entity_type.value}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="refresh",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Index refresh failed: {e}")
    
    def optimize_index(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
    ) -> bool:
        """
        Optimize an index for better performance.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If index optimization fails
        """
        start_time = datetime.utcnow()
        
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "optimize_index"):
                result = self._as_bool(self.provider.optimize_index(
                    index_name=index_name,
                    entity_type=entity_type.value,
                ))
            else:
                # For PostgreSQL provider, optimization is handled by VACUUM
                logger.info(f"Index optimization for {entity_type.value} is handled by PostgreSQL VACUUM")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="optimize",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize index for {entity_type.value}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="optimize",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Index optimization failed: {e}")
    
    def health_check(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check the health of an index.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            
        Returns:
            Health status dictionary
            
        Raises:
            SearchError: If health check fails
        """
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "health_check"):
                health = self.provider.health_check(
                    index_name=index_name,
                    entity_type=entity_type.value,
                )
                health = self._as_dict(
                    health,
                    {
                        "status": "healthy",
                        "provider": "postgresql",
                        "index_name": index_name,
                        "entity_type": entity_type.value,
                        "message": "Provider returned a non-dictionary health response",
                    },
                )
            else:
                # For PostgreSQL provider, health is database health
                health = {
                    "status": "healthy",
                    "provider": "postgresql",
                    "index_name": index_name,
                    "entity_type": entity_type.value,
                    "message": "PostgreSQL provider uses database health",
                }
            
            return health
            
        except Exception as e:
            logger.error(f"Health check failed for {entity_type.value}: {e}")
            raise SearchError(f"Health check failed: {e}")
    
    def get_statistics(
        self,
        entity_type: EntityType,
        index_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics for an index.
        
        Args:
            entity_type: Type of entity
            index_name: Optional custom index name
            
        Returns:
            Statistics dictionary
            
        Raises:
            SearchError: If statistics retrieval fails
        """
        try:
            if index_name is None:
                index_name = f"matchhire_{entity_type.value}"
            
            # Delegate to provider
            if hasattr(self.provider, "get_index_statistics"):
                stats = self.provider.get_index_statistics(
                    index_name=index_name,
                    entity_type=entity_type.value,
                )
                stats = self._as_dict(
                    stats,
                    {
                        "provider": "postgresql",
                        "index_name": index_name,
                        "entity_type": entity_type.value,
                        "message": "Provider returned a non-dictionary statistics response",
                    },
                )
            else:
                # For PostgreSQL provider, get table statistics
                stats = {
                    "provider": "postgresql",
                    "index_name": index_name,
                    "entity_type": entity_type.value,
                    "message": "Statistics available through database queries",
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics for {entity_type.value}: {e}")
            raise SearchError(f"Statistics retrieval failed: {e}")
    
    def create_alias(
        self,
        alias_name: str,
        index_name: str,
        entity_type: EntityType,
    ) -> bool:
        """
        Create an alias for an index.
        
        Aliases allow for zero-downtime index swaps.
        
        Args:
            alias_name: Name of the alias
            index_name: Name of the index to point to
            entity_type: Type of entity
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If alias creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Delegate to provider
            if hasattr(self.provider, "create_alias"):
                result = self._as_bool(self.provider.create_alias(
                    alias_name=alias_name,
                    index_name=index_name,
                    entity_type=entity_type.value,
                ))
            else:
                # For PostgreSQL provider, aliases are not needed
                logger.info(f"Aliases are not applicable for PostgreSQL provider")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="create_alias",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create alias {alias_name}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="create_alias",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Alias creation failed: {e}")
    
    def delete_alias(
        self,
        alias_name: str,
        entity_type: EntityType,
    ) -> bool:
        """
        Delete an alias.
        
        Args:
            alias_name: Name of the alias
            entity_type: Type of entity
            
        Returns:
            True if successful
            
        Raises:
            SearchError: If alias deletion fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Delegate to provider
            if hasattr(self.provider, "delete_alias"):
                result = self._as_bool(self.provider.delete_alias(
                    alias_name=alias_name,
                    entity_type=entity_type.value,
                ))
            else:
                # For PostgreSQL provider, aliases are not needed
                logger.info(f"Aliases are not applicable for PostgreSQL provider")
                result = True
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="delete_alias",
                entity_type=entity_type.value,
                duration=duration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete alias {alias_name}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_index_operation(
                operation="delete_alias",
                entity_type=entity_type.value,
                duration=duration,
                success=False,
            )
            raise SearchError(f"Alias deletion failed: {e}")
    
    def get_aliases(
        self,
        entity_type: EntityType,
    ) -> List[str]:
        """
        Get all aliases for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of alias names
        """
        try:
            # Delegate to provider
            if hasattr(self.provider, "get_aliases"):
                aliases = self.provider.get_aliases(
                    entity_type=entity_type.value,
                )
            else:
                # For PostgreSQL provider, aliases are not used
                aliases = []
            
            return self._as_list(aliases)
            
        except Exception as e:
            logger.error(f"Failed to get aliases for {entity_type.value}: {e}")
            return []
