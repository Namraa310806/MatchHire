"""
Health Monitoring System.

This module provides health monitoring capabilities for all components
in the search, ranking, and recommendation systems.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import time
from .core import ObservabilityConfig, ObservabilityComponent


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition."""
    
    name: str
    component: ObservabilityComponent
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: int = 30
    timeout_seconds: int = 10
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "component": self.component.value,
            "interval_seconds": self.interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
        }


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    name: str
    component: ObservabilityComponent
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "component": self.component.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class ComponentHealth:
    """Health status for a component."""
    
    component: ObservabilityComponent
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    check_results: List[HealthCheckResult] = field(default_factory=list)
    consecutive_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "component": self.component.value,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_results": [r.to_dict() for r in self.check_results[-10:]],  # Last 10 checks
            "consecutive_failures": self.consecutive_failures,
        }


class HealthMonitor:
    """
    Health monitor for all components.
    
    This monitor runs periodic health checks and aggregates health
    status for all components in the system.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the health monitor.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._health_checks: Dict[str, HealthCheck] = {}
        self._component_health: Dict[ObservabilityComponent, ComponentHealth] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Initialize component health
        for component in ObservabilityComponent:
            self._component_health[component] = ComponentHealth(component=component)
        
        # Register default health checks
        self._register_default_health_checks()
        
        # Start background worker if enabled
        if config.enabled:
            self._start_worker()
    
    def _register_default_health_checks(self) -> None:
        """Register default health checks for all components."""
        # Search health check
        self.register_health_check(
            HealthCheck(
                name="search_engine",
                component=ObservabilityComponent.SEARCH,
                check_function=self._check_search_health,
            )
        )
        
        # Ranking health check
        self.register_health_check(
            HealthCheck(
                name="ranking_pipeline",
                component=ObservabilityComponent.RANKING,
                check_function=self._check_ranking_health,
            )
        )
        
        # Recommendation health check
        self.register_health_check(
            HealthCheck(
                name="recommendation_engine",
                component=ObservabilityComponent.RECOMMENDATION,
                check_function=self._check_recommendation_health,
            )
        )
        
        # Provider health check
        self.register_health_check(
            HealthCheck(
                name="provider",
                component=ObservabilityComponent.PROVIDER,
                check_function=self._check_provider_health,
            )
        )
        
        # Cache health check
        self.register_health_check(
            HealthCheck(
                name="cache",
                component=ObservabilityComponent.CACHE,
                check_function=self._check_cache_health,
            )
        )
    
    def _check_search_health(self) -> Dict[str, Any]:
        """Check search engine health."""
        try:
            # This would check the actual search engine
            # For now, return healthy
            return {
                "status": "healthy",
                "message": "Search engine is operational",
                "details": {
                    "active_connections": 0,
                    "queue_size": 0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Search engine health check failed: {str(e)}",
                "error": str(e),
            }
    
    def _check_ranking_health(self) -> Dict[str, Any]:
        """Check ranking pipeline health."""
        try:
            # This would check the actual ranking pipeline
            return {
                "status": "healthy",
                "message": "Ranking pipeline is operational",
                "details": {
                    "active_signals": 0,
                    "cache_hit_rate": 0.0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Ranking pipeline health check failed: {str(e)}",
                "error": str(e),
            }
    
    def _check_recommendation_health(self) -> Dict[str, Any]:
        """Check recommendation engine health."""
        try:
            # This would check the actual recommendation engine
            return {
                "status": "healthy",
                "message": "Recommendation engine is operational",
                "details": {
                    "active_strategies": 0,
                    "cache_hit_rate": 0.0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Recommendation engine health check failed: {str(e)}",
                "error": str(e),
            }
    
    def _check_provider_health(self) -> Dict[str, Any]:
        """Check search provider health."""
        try:
            # This would check the actual provider (PostgreSQL, Elasticsearch, etc.)
            return {
                "status": "healthy",
                "message": "Search provider is operational",
                "details": {
                    "provider": "postgresql",  # Would get from registry
                    "connection_pool_size": 10,
                    "active_connections": 0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Search provider health check failed: {str(e)}",
                "error": str(e),
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            # This would check the actual cache
            return {
                "status": "healthy",
                "message": "Cache is operational",
                "details": {
                    "cache_size": 0,
                    "hit_rate": 0.0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Cache health check failed: {str(e)}",
                "error": str(e),
            }
    
    def register_health_check(self, health_check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            health_check: Health check to register
        """
        with self._lock:
            self._health_checks[health_check.name] = health_check
    
    def unregister_health_check(self, name: str) -> None:
        """
        Unregister a health check.
        
        Args:
            name: Name of health check to unregister
        """
        with self._lock:
            if name in self._health_checks:
                del self._health_checks[name]
    
    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._run_health_checks,
            daemon=True,
            name="HealthMonitorWorker"
        )
        self._worker_thread.start()
    
    def _run_health_checks(self) -> None:
        """Run health checks in the background."""
        while self._running:
            try:
                self.run_all_health_checks()
                time.sleep(self._config.health_check_interval_seconds)
            except Exception as e:
                print(f"Error running health checks: {e}")
                time.sleep(self._config.health_check_interval_seconds)
    
    def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all registered health checks.
        
        Returns:
            Dictionary of health check results by name
        """
        results = {}
        
        with self._lock:
            health_checks = list(self._health_checks.values())
        
        for health_check in health_checks:
            if not health_check.enabled:
                continue
            
            result = self.run_health_check(health_check)
            results[health_check.name] = result
            
            # Update component health
            self._update_component_health(health_check.component, result)
        
        return results
    
    def run_health_check(self, health_check: HealthCheck) -> HealthCheckResult:
        """
        Run a single health check.
        
        Args:
            health_check: Health check to run
            
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Run check function with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Health check '{health_check.name}' timed out")
            
            # Set timeout (Unix only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(health_check.timeout_seconds)
            except (AttributeError, ValueError):
                # Windows or no signal support, skip timeout
                pass
            
            check_result = health_check.check_function()
            
            # Cancel alarm
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine status
            status_str = check_result.get("status", "unknown")
            try:
                status = HealthStatus(status_str)
            except ValueError:
                status = HealthStatus.UNKNOWN
            
            result = HealthCheckResult(
                name=health_check.name,
                component=health_check.component,
                status=status,
                message=check_result.get("message", ""),
                details=check_result.get("details", {}),
                duration_ms=duration_ms,
                error=check_result.get("error"),
            )
            
        except TimeoutError as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                name=health_check.name,
                component=health_check.component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {health_check.timeout_seconds}s",
                duration_ms=duration_ms,
                error=str(e),
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                name=health_check.name,
                component=health_check.component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                error=str(e),
            )
        
        return result
    
    def _update_component_health(
        self,
        component: ObservabilityComponent,
        result: HealthCheckResult,
    ) -> None:
        """
        Update component health based on check result.
        
        Args:
            component: Component
            result: Health check result
        """
        with self._lock:
            component_health = self._component_health[component]
            component_health.last_check = result.timestamp
            component_health.check_results.append(result)
            
            # Keep check results bounded
            if len(component_health.check_results) > 100:
                component_health.check_results = component_health.check_results[-100:]
            
            # Update consecutive failures
            if result.status == HealthStatus.UNHEALTHY:
                component_health.consecutive_failures += 1
            else:
                component_health.consecutive_failures = 0
            
            # Update overall status
            if result.status == HealthStatus.HEALTHY:
                if component_health.status == HealthStatus.UNKNOWN:
                    component_health.status = HealthStatus.HEALTHY
            elif result.status == HealthStatus.UNHEALTHY:
                if component_health.consecutive_failures >= 3:
                    component_health.status = HealthStatus.UNHEALTHY
                else:
                    component_health.status = HealthStatus.DEGRADED
    
    def get_component_health(self, component: ObservabilityComponent) -> ComponentHealth:
        """
        Get health status for a component.
        
        Args:
            component: Component to check
            
        Returns:
            Component health
        """
        with self._lock:
            return self._component_health[component]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get overall health status.
        
        Returns:
            Health status dictionary
        """
        with self._lock:
            component_statuses = {
                comp.value: health.to_dict()
                for comp, health in self._component_health.items()
            }
            
            # Determine overall status
            statuses = [health.status for health in self._component_health.values()]
            
            if HealthStatus.UNHEALTHY in statuses:
                overall_status = HealthStatus.UNHEALTHY
            elif HealthStatus.DEGRADED in statuses:
                overall_status = HealthStatus.DEGRADED
            elif HealthStatus.HEALTHY in statuses:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN
            
            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "components": component_statuses,
                "health_checks": [check.to_dict() for check in self._health_checks.values()],
            }
    
    def is_healthy(self) -> bool:
        """
        Check if the system is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        status = self.get_status()
        return status["overall_status"] == HealthStatus.HEALTHY.value
    
    def shutdown(self) -> None:
        """Shutdown the health monitor."""
        self._running = False
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
