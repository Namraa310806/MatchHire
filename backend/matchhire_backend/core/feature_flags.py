"""
Feature Flag Framework

Provides dynamic feature flag management with support for:
- Boolean flags
- Percentage rollouts
- User-based targeting
- Environment-specific flags
- Remote configuration
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from django.core.cache import cache
from django.db import models

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Feature flag types."""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    CONDITIONAL = "conditional"


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    name: str
    flag_type: FlagType
    enabled: bool = False
    value: Any = None
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled_for_user(self, user_id: int = None, **context) -> bool:
        """
        Check if flag is enabled for a specific user.
        
        Args:
            user_id: User ID
            **context: Additional context
            
        Returns:
            True if enabled for user
        """
        if not self.enabled:
            return False
            
        if self.flag_type == FlagType.BOOLEAN:
            return self.enabled
            
        elif self.flag_type == FlagType.PERCENTAGE:
            if user_id is None:
                return False
            percentage = self.value or 0
            hash_value = int(hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest(), 16)
            return (hash_value % 100)percentage
            
        elif self.flag_type == FlagType.USER_LIST:
            if user_id is None:
                return False
            allowed_users = self.value or []
            return user_id in allowed_users
            
        elif self.flag_type == FlagType.CONDITIONAL:
            # Evaluate conditional function
            if callable(self.value):
                return self.value(user_id=user_id, **context)
            return False
            
        return False


class FlagStorage(ABC):
    """Abstract base class for flag storage."""
    
    @abstractmethod
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        pass
        
    @abstractmethod
    def set_flag(self, flag: FeatureFlag) -> bool:
        """Set a feature flag."""
        pass
        
    @abstractmethod
    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag."""
        pass
        
    @abstractmethod
    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        pass


class CacheFlagStorage(FlagStorage):
    """Cache-based flag storage."""
    
    def __init__(self, cache_backend=None, ttl: int = 300):
        self.cache_backend = cache_backend or cache
        self.ttl = ttl
        
    def _get_key(self, name: str) -> str:
        """Get cache key for flag."""
        return f"feature_flag:{name}"
        
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        data = self.cache_backend.get(self._get_key(name))
        if data:
            return FeatureFlag(**data)
        return None
        
    def set_flag(self, flag: FeatureFlag) -> bool:
        """Set a feature flag."""
        flag.updated_at = datetime.utcnow()
        data = {
            "name": flag.name,
            "flag_type": flag.flag_type.value,
            "enabled": flag.enabled,
            "value": flag.value,
            "description": flag.description,
            "created_at": flag.created_at.isoformat(),
            "updated_at": flag.updated_at.isoformat(),
            "metadata": flag.metadata,
        }
        self.cache_backend.set(self._get_key(flag.name), data, self.ttl)
        return True
        
    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag."""
        self.cache_backend.delete(self._get_key(name))
        return True
        
    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        # This requires Redis SCAN or similar
        # For now, return empty list
        return []


class DatabaseFlagStorage(FlagStorage):
    """Database-based flag storage."""
    
    def __init__(self):
        # Try to create model if it doesn't exist
        try:
            from django.apps import apps
            if not apps.is_installed("matchhire_backend.core"):
                logger.warning("Core app not installed, database flags unavailable")
                self._model = None
            else:
                self._model = None  # Would be FeatureFlag model
        except:
            self._model = None
            
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        if self._model is None:
            return None
        try:
            obj = self._model.objects.get(name=name)
            return FeatureFlag(
                name=obj.name,
                flag_type=FlagType(obj.flag_type),
                enabled=obj.enabled,
                value=obj.value,
                description=obj.description,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
                metadata=obj.metadata or {},
            )
        except self._model.DoesNotExist:
            return None
            
    def set_flag(self, flag: FeatureFlag) -> bool:
        """Set a feature flag."""
        if self._model is None:
            return False
        flag.updated_at = datetime.utcnow()
        self._model.objects.update_or_create(
            name=flag.name,
            defaults={
                "flag_type": flag.flag_type.value,
                "enabled": flag.enabled,
                "value": flag.value,
                "description": flag.description,
                "metadata": flag.metadata,
            },
        )
        return True
        
    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag."""
        if self._model is None:
            return False
        try:
            self._model.objects.filter(name=name).delete()
            return True
        except:
            return False
            
    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        if self._model is None:
            return []
        flags = []
        for obj in self._model.objects.all():
            flags.append(FeatureFlag(
                name=obj.name,
                flag_type=FlagType(obj.flag_type),
                enabled=obj.enabled,
                value=obj.value,
                description=obj.description,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
                metadata=obj.metadata or {},
            ))
        return flags


class FeatureFlagManager:
    """
    Feature flag manager.
    
    Central point for managing and checking feature flags.
    """
    
    def __init__(self, storage: FlagStorage = None):
        self.storage = storage or CacheFlagStorage()
        self._local_flags: Dict[str, FeatureFlag] = {}
        self._default_flags: Dict[str, FeatureFlag] = {}
        
    def register_default_flag(self, flag: FeatureFlag) -> None:
        """
        Register a default feature flag.
        
        Args:
            flag: Feature flag definition
        """
        self._default_flags[flag.name] = flag
        
    def is_enabled(self, name: str, user_id: int = None, 
                   default: bool = False, **context) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            name: Flag name
            user_id: User ID for user-specific flags
            default: Default value if flag not found
            **context: Additional context
            
        Returns:
            True if flag is enabled
        """
        # Check local flags first
        if name in self._local_flags:
            return self._local_flags[name].is_enabled_for_user(user_id, **context)
            
        # Check storage
        flag = self.storage.get_flag(name)
        if flag:
            return flag.is_enabled_for_user(user_id, **context)
            
        # Check default flags
        if name in self._default_flags:
            return self._default_flags[name].is_enabled_for_user(user_id, **context)
            
        return default
        
    def enable_flag(self, name: str, value: Any = None) -> bool:
        """
        Enable a feature flag.
        
        Args:
            name: Flag name
            value: Flag value (for percentage/user list flags)
            
        Returns:
            True if successful
        """
        flag = self.storage.get_flag(name)
        if flag:
            flag.enabled = True
            if value is not None:
                flag.value = value
            return self.storage.set_flag(flag)
        else:
            # Create new flag
            flag = FeatureFlag(
                name=name,
                flag_type=FlagType.BOOLEAN if value is None else FlagType.PERCENTAGE,
                enabled=True,
                value=value,
            )
            return self.storage.set_flag(flag)
            
    def disable_flag(self, name: str) -> bool:
        """
        Disable a feature flag.
        
        Args:
            name: Flag name
            
        Returns:
            True if successful
        """
        flag = self.storage.get_flag(name)
        if flag:
            flag.enabled = False
            return self.storage.set_flag(flag)
        return False
        
    def set_percentage_flag(self, name: str, percentage: float) -> bool:
        """
        Set a percentage-based feature flag.
        
        Args:
            name: Flag name
            percentage: Percentage (0-100)
            
        Returns:
            True if successful
        """
        flag = FeatureFlag(
            name=name,
            flag_type=FlagType.PERCENTAGE,
            enabled=True,
            value=min(100, max(0, percentage)),
        )
        return self.storage.set_flag(flag)
        
    def set_user_list_flag(self, name: str, user_ids: List[int]) -> bool:
        """
        Set a user list-based feature flag.
        
        Args:
            name: Flag name
            user_ids: List of user IDs
            
        Returns:
            True if successful
        """
        flag = FeatureFlag(
            name=name,
            flag_type=FlagType.USER_LIST,
            enabled=True,
            value=user_ids,
        )
        return self.storage.set_flag(flag)
        
    def set_conditional_flag(self, name: str, condition: Callable) -> bool:
        """
        Set a conditional feature flag.
        
        Args:
            name: Flag name
            condition: Callable that evaluates to bool
            
        Returns:
            True if successful
        """
        flag = FeatureFlag(
            name=name,
            flag_type=FlagType.CONDITIONAL,
            enabled=True,
            value=condition,
        )
        # Conditional flags can't be stored in cache/DB easily
        self._local_flags[name] = flag
        return True
        
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag.
        
        Args:
            name: Flag name
            
        Returns:
            FeatureFlag or None
        """
        if name in self._local_flags:
            return self._local_flags[name]
        return self.storage.get_flag(name)
        
    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        flags = list(self._local_flags.values())
        flags.extend(self.storage.list_flags())
        return flags
        
    def delete_flag(self, name: str) -> bool:
        """
        Delete a feature flag.
        
        Args:
            name: Flag name
            
        Returns:
            True if successful
        """
        self._local_flags.pop(name, None)
        return self.storage.delete_flag(name)


# Global feature flag manager instance
feature_flag_manager = FeatureFlagManager()

# Register default feature flags
feature_flag_manager.register_default_flag(FeatureFlag(
    name="search.elasticsearch",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable Elasticsearch search provider",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="search.vector_search",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable vector search capabilities",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="search.hybrid_search",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable hybrid search (keyword + vector)",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="search.faceting",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable search faceting",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="recommendations.ml_ranking",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable ML-based ranking for recommendations",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="api.rate_limiting",
    flag_type=FlagType.BOOLEAN,
    enabled=True,
    description="Enable API rate limiting",
))

feature_flag_manager.register_default_flag(FeatureFlag(
    name="performance.profiling",
    flag_type=FlagType.BOOLEAN,
    enabled=False,
    description="Enable performance profiling",
))


def feature_flag(name: str, default: bool = False):
    """
    Decorator to conditionally execute function based on feature flag.
    
    Args:
        name: Feature flag name
        default: Default value if flag not found
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if feature_flag_manager.is_enabled(name, default=default):
                return func(*args, **kwargs)
            else:
                # Return None or raise exception
                logger.debug(f"Feature flag {name} is disabled, skipping {func.__name__}")
                return None
        return wrapper
    return decorator


def if_flag_enabled(name: str, user_id: int = None, default: bool = False):
    """
    Context manager for conditional execution based on feature flag.
    
    Args:
        name: Feature flag name
        user_id: User ID
        default: Default value if flag not found
    """
    class FlagContext:
        def __enter__(self):
            return feature_flag_manager.is_enabled(name, user_id, default)
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    return FlagContext()
