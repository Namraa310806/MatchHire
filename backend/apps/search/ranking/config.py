"""
Ranking Configuration.

This module provides configuration classes for the ranking system.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SignalConfig:
    """Configuration for a ranking signal."""
    
    enabled: bool = True
    weight: float = 1.0
    normalization: str = "min_max"
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "weight": self.weight,
            "normalization": self.normalization,
            "params": self.params,
        }


@dataclass
class ProfileConfig:
    """Configuration for a ranking profile."""
    
    name: str
    profile_type: str
    description: str
    signal_weights: Dict[str, float] = field(default_factory=dict)
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "profile_type": self.profile_type,
            "description": self.description,
            "signal_weights": self.signal_weights,
            "pipeline_config": self.pipeline_config,
            "metadata": self.metadata,
        }


@dataclass
class CacheConfig:
    """Configuration for ranking cache."""
    
    enabled: bool = True
    max_size: int = 1000
    default_ttl: int = 300
    cleanup_interval: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "cleanup_interval": self.cleanup_interval,
        }


@dataclass
class MonitoringConfig:
    """Configuration for ranking monitoring."""
    
    enabled: bool = True
    collect_signal_metrics: bool = True
    collect_pipeline_metrics: bool = True
    collect_cache_metrics: bool = True
    metrics_retention_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "collect_signal_metrics": self.collect_signal_metrics,
            "collect_pipeline_metrics": self.collect_pipeline_metrics,
            "collect_cache_metrics": self.collect_cache_metrics,
            "metrics_retention_hours": self.metrics_retention_hours,
        }


@dataclass
class RankingConfig:
    """Main configuration for the ranking system."""
    
    default_profile: str = "candidate_search"
    cache: CacheConfig = field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    signal_configs: Dict[str, SignalConfig] = field(default_factory=dict)
    profile_configs: Dict[str, ProfileConfig] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "default_profile": self.default_profile,
            "cache": self.cache.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "signal_configs": {
                name: config.to_dict()
                for name, config in self.signal_configs.items()
            },
            "profile_configs": {
                name: config.to_dict()
                for name, config in self.profile_configs.items()
            },
        }
