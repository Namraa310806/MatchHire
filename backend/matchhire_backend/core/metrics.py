"""
Prometheus metrics for MatchHire backend.

Provides comprehensive metrics for:
- HTTP requests (count, duration, status codes)
- Database operations
- Cache operations
- Celery tasks
- Business operations
"""
import time
from functools import wraps
from typing import Callable, Any

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import CollectorRegistry
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

http_requests_by_status = Counter(
    'http_requests_by_status_total',
    'HTTP requests by status code',
    ['status'],
    registry=REGISTRY
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=REGISTRY
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    registry=REGISTRY
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type'],
    registry=REGISTRY
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['backend'],
    registry=REGISTRY
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['backend'],
    registry=REGISTRY
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'backend'],
    registry=REGISTRY
)

# Celery metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks executed',
    ['task_name', 'status'],
    registry=REGISTRY
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=REGISTRY
)

celery_worker_active_tasks = Gauge(
    'celery_worker_active_tasks',
    'Number of active Celery tasks',
    registry=REGISTRY
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue'],
    registry=REGISTRY
)

# Business metrics
resumes_uploaded_total = Counter(
    'resumes_uploaded_total',
    'Total resumes uploaded',
    registry=REGISTRY
)

jobs_created_total = Counter(
    'jobs_created_total',
    'Total jobs created',
    registry=REGISTRY
)

applications_submitted_total = Counter(
    'applications_submitted_total',
    'Total applications submitted',
    registry=REGISTRY
)

matching_operations_total = Counter(
    'matching_operations_total',
    'Total matching operations performed',
    registry=REGISTRY
)

notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['notification_type'],
    registry=REGISTRY
)

interviews_scheduled_total = Counter(
    'interviews_scheduled_total',
    'Total interviews scheduled',
    registry=REGISTRY
)

# System metrics
application_info = Info(
    'application_info',
    'Application information',
    registry=REGISTRY
)

application_uptime_seconds = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds',
    registry=REGISTRY
)


# Track application start time
_start_time = time.time()


def init_metrics():
    """Initialize application metrics."""
    application_info.info({
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'service': 'matchhire-backend',
    })
    logger.info("Prometheus metrics initialized")


def update_uptime():
    """Update application uptime metric."""
    uptime = time.time() - _start_time
    application_uptime_seconds.set(uptime)


def track_db_connections():
    """Update database connection metrics."""
    try:
        if hasattr(connection, 'pool') and connection.pool:
            db_connections_active.set(len(connection.pool._pool))
    except Exception as e:
        logger.warning(f"Failed to track DB connections: {e}")


def track_cache_metrics():
    """Update cache metrics if available."""
    try:
        # Redis-specific metrics
        if hasattr(cache, 'client') and hasattr(cache.client, 'connection_pool'):
            # This would require redis-py specific implementation
            pass
    except Exception as e:
        logger.warning(f"Failed to track cache metrics: {e}")


def track_celery_queue_length():
    """Update Celery queue length metrics."""
    try:
        from kombu import Connection
        from matchhire_backend.core.env import get_env
        
        broker_url = get_env("CELERY_BROKER_URL", default="redis://redis:6379/0")
        
        if broker_url.startswith('redis://'):
            import redis
            client = redis.Redis.from_url(broker_url)
            
            # Get queue lengths for common queues
            queues = ['celery', 'default', 'matching', 'notifications']
            for queue in queues:
                try:
                    length = client.llen(queue)
                    celery_queue_length.labels(queue=queue).set(length)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Failed to track Celery queue length: {e}")


def track_http_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """
    Track HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    http_requests_by_status.labels(status=status).inc()


def track_db_query(operation: str, duration: float) -> None:
    """
    Track database query metrics.
    
    Args:
        operation: Query operation (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def track_db_error(error_type: str) -> None:
    """
    Track database error metrics.
    
    Args:
        error_type: Type of database error
    """
    db_errors_total.labels(error_type=error_type).inc()


def track_cache_hit(backend: str = 'default') -> None:
    """
    Track cache hit.
    
    Args:
        backend: Cache backend name
    """
    cache_hits_total.labels(backend=backend).inc()
    cache_operations_total.labels(operation='hit', backend=backend).inc()


def track_cache_miss(backend: str = 'default') -> None:
    """
    Track cache miss.
    
    Args:
        backend: Cache backend name
    """
    cache_misses_total.labels(backend=backend).inc()
    cache_operations_total.labels(operation='miss', backend=backend).inc()


def track_celery_task(task_name: str, status: str, duration: float = None) -> None:
    """
    Track Celery task metrics.
    
    Args:
        task_name: Name of the Celery task
        status: Task status (success, failure, retry)
        duration: Task duration in seconds (optional)
    """
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    if duration is not None:
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def track_resume_upload() -> None:
    """Track resume upload metric."""
    resumes_uploaded_total.inc()


def track_job_creation() -> None:
    """Track job creation metric."""
    jobs_created_total.inc()


def track_application_submission() -> None:
    """Track application submission metric."""
    applications_submitted_total.inc()


def track_matching_operation() -> None:
    """Track matching operation metric."""
    matching_operations_total.inc()


def track_notification_sent(notification_type: str) -> None:
    """
    Track notification sent metric.
    
    Args:
        notification_type: Type of notification sent
    """
    notifications_sent_total.labels(notification_type=notification_type).inc()


def track_interview_scheduled() -> None:
    """Track interview scheduled metric."""
    interviews_scheduled_total.inc()


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.
    
    Returns:
        Metrics in Prometheus text format
    """
    # Update dynamic metrics before exporting
    update_uptime()
    track_db_connections()
    track_cache_metrics()
    track_celery_queue_length()
    
    return generate_latest(REGISTRY)


def track_time(metric: Histogram, labels: dict[str, str] = None) -> Callable:
    """
    Decorator to track function execution time.
    
    Args:
        metric: Prometheus Histogram metric
        labels: Labels to apply to the metric
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                raise
        return wrapper
    return decorator
