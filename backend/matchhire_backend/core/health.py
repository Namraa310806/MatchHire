"""
Health and Readiness Probes

Provides health, readiness, and liveness endpoints for Kubernetes/Docker.
"""

import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Health check utilities.
    
    Performs various health checks for the application.
    """
    
    def __init__(self):
        self._checks: List[str] = []
        
    def check_database(self) -> HealthCheckResult:
        """
        Check database connectivity.
        
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            if result and result[0] == 1:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    duration_ms=duration_ms,
                    metadata={"query_time_ms": duration_ms},
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database query returned unexpected result",
                    duration_ms=duration_ms,
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def check_cache(self) -> HealthCheckResult:
        """
        Check cache connectivity.
        
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            # Test set and get
            test_key = "health_check_test"
            cache.set(test_key, "test", 10)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            if result == "test":
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    message="Cache connection successful",
                    duration_ms=duration_ms,
                    metadata={"operation_time_ms": duration_ms},
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="cache",
                    status=HealthStatus.UNHEALTHY,
                    message="Cache returned unexpected value",
                    duration_ms=duration_ms,
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Cache health check failed: {e}")
            return HealthCheckResult(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                message=f"Cache connection failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def check_disk_space(self, threshold_percent: float = 90.0) -> HealthCheckResult:
        """
        Check disk space.
        
        Args:
            threshold_percent: Alert threshold percentage
            
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            disk_usage = psutil.disk_usage('/')
            percent_used = disk_usage.percent
            
            if percent_used < threshold_percent:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk space adequate: {percent_used:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": percent_used,
                        "free_gb": disk_usage.free / 1024 / 1024 / 1024,
                        "total_gb": disk_usage.total / 1024 / 1024 / 1024,
                    },
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.DEGRADED,
                    message=f"Disk space low: {percent_used:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": percent_used,
                        "free_gb": disk_usage.free / 1024 / 1024 / 1024,
                        "total_gb": disk_usage.total / 1024 / 1024 / 1024,
                    },
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Disk space health check failed: {e}")
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk space check failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def check_memory(self, threshold_percent: float = 90.0) -> HealthCheckResult:
        """
        Check memory usage.
        
        Args:
            threshold_percent: Alert threshold percentage
            
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used < threshold_percent:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage adequate: {percent_used:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": percent_used,
                        "available_gb": memory.available / 1024 / 1024 / 1024,
                        "total_gb": memory.total / 1024 / 1024 / 1024,
                    },
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"Memory usage high: {percent_used:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": percent_used,
                        "available_gb": memory.available / 1024 / 1024 / 1024,
                        "total_gb": memory.total / 1024 / 1024 / 1024,
                    },
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Memory health check failed: {e}")
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def check_cpu(self, threshold_percent: float = 80.0) -> HealthCheckResult:
        """
        Check CPU usage.
        
        Args:
            threshold_percent: Alert threshold percentage
            
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            if cpu_percent < threshold_percent:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="cpu",
                    status=HealthStatus.HEALTHY,
                    message=f"CPU usage adequate: {cpu_percent:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": cpu_percent,
                        "cpu_count": psutil.cpu_count(),
                    },
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="cpu",
                    status=HealthStatus.DEGRADED,
                    message=f"CPU usage high: {cpu_percent:.1f}% used",
                    duration_ms=duration_ms,
                    metadata={
                        "percent_used": cpu_percent,
                        "cpu_count": psutil.cpu_count(),
                    },
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"CPU health check failed: {e}")
            return HealthCheckResult(
                name="cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"CPU check failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def check_elasticsearch(self) -> HealthCheckResult:
        """
        Check Elasticsearch connectivity (if enabled).
        
        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()
        
        try:
            from django.conf import settings
            from apps.search.providers.elasticsearch_provider import ElasticsearchProvider
            
            provider = ElasticsearchProvider()
            client = provider.client
            
            if client and client.ping():
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="elasticsearch",
                    status=HealthStatus.HEALTHY,
                    message="Elasticsearch connection successful",
                    duration_ms=duration_ms,
                    metadata={"cluster_name": client.info().get("cluster_name", "unknown")},
                )
            else:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    name="elasticsearch",
                    status=HealthStatus.UNHEALTHY,
                    message="Elasticsearch connection failed",
                    duration_ms=duration_ms,
                )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Elasticsearch health check failed: {e}")
            return HealthCheckResult(
                name="elasticsearch",
                status=HealthStatus.UNHEALTHY,
                message=f"Elasticsearch check failed: {str(e)}",
                duration_ms=duration_ms,
            )
            
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dictionary with overall health status and individual check results
        """
        checks = [
            self.check_database(),
            self.check_cache(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_cpu(),
        ]
        
        # Optional Elasticsearch check
        try:
            from django.conf import settings
            if getattr(settings, "SEARCH_PROVIDER", None) == "elasticsearch":
                checks.append(self.check_elasticsearch())
        except:
            pass
            
        # Determine overall status
        statuses = [check.status for check in checks]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
            
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "duration_ms": check.duration_ms,
                    "metadata": check.metadata,
                }
                for check in checks
            ],
        }


class ReadinessChecker:
    """
    Readiness check utilities.
    
    Checks if the application is ready to serve traffic.
    """
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self._startup_time = datetime.utcnow()
        
    def is_ready(self) -> Dict[str, Any]:
        """
        Check if application is ready.
        
        Returns:
            Dictionary with readiness status
        """
        # Run critical health checks
        db_check = self.health_checker.check_database()
        cache_check = self.health_checker.check_cache()
        
        # Application is ready if critical services are healthy
        critical_checks = [db_check, cache_check]
        all_healthy = all(check.status == HealthStatus.HEALTHY for check in critical_checks)
        
        # Check minimum startup time
        uptime = (datetime.utcnow() - self._startup_time).total_seconds()
        min_startup_time = 10  # seconds
        
        if uptime < min_startup_time:
            return {
                "ready": False,
                "message": f"Application still starting up (uptime: {uptime:.1f}s)",
                "uptime_seconds": uptime,
            }
            
        return {
            "ready": all_healthy,
            "message": "Application ready" if all_healthy else "Critical services not healthy",
            "checks": {
                "database": db_check.status.value,
                "cache": cache_check.status.value,
            },
            "uptime_seconds": uptime,
        }


class LivenessChecker:
    """
    Liveness check utilities.
    
    Checks if the application is alive (not deadlocked).
    """
    
    def is_alive(self) -> Dict[str, Any]:
        """
        Check if application is alive.
        
        Returns:
            Dictionary with liveness status
        """
        # Simple liveness check - just return success
        # If this endpoint is unreachable, the container is considered dead
        return {
            "alive": True,
            "message": "Application is alive",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global instances
health_checker = HealthChecker()
readiness_checker = ReadinessChecker()
liveness_checker = LivenessChecker()
