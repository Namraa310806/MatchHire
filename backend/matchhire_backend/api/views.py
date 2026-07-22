import os
import redis
import shutil
import time
from django.db import connections
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from matchhire_backend.core.env import get_env


VERSION = "1.0.0"
COMMIT = "unknown"
START_TIME = time.time()


@extend_schema(
	tags=["System"],
	summary="Health check",
	description="Check system health and dependency status.",
	request=None,
	responses={
		200: OpenApiResponse(description="Health status retrieved successfully.")
	}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """General health check endpoint."""
    return Response({"status": "healthy"})


@extend_schema(
	tags=["System"],
	summary="Liveness probe",
	description="Check if the application is running.",
	request=None,
	responses={
		200: OpenApiResponse(description="Application is alive.")
	}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_live(request):
    """Liveness probe - checks if Django application is running."""
    return Response({"status": "healthy"})


@extend_schema(
	tags=["System"],
	summary="Readiness probe",
	description="Check if the application is ready to accept traffic.",
	request=None,
	responses={
		200: OpenApiResponse(description="Application is ready."),
		503: OpenApiResponse(description="Application is not ready.")
	}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_ready(request):
    """Readiness probe - checks database, Redis, and Celery connectivity."""
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database
    database_healthy = False
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_healthy = True
    except Exception as e:
        database_healthy = False
    health_status["checks"]["database"] = database_healthy
    
    # Check Redis
    redis_healthy = False
    try:
        redis_url = get_env("REDIS_URL", default="redis://redis:6379/0")
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        redis_healthy = bool(client.ping())
    except Exception:
        redis_healthy = False
    health_status["checks"]["redis"] = redis_healthy
    
    # Check Celery (optional - don't fail if not available)
    celery_healthy = False
    try:
        from celery import current_app
        inspect = current_app.control.inspect(timeout=2)
        stats = inspect.stats()
        celery_healthy = stats is not None and len(stats) > 0
    except Exception:
        celery_healthy = False
    health_status["checks"]["celery"] = celery_healthy
    
    # Determine overall health (critical services only)
    is_healthy = database_healthy and redis_healthy
    
    if is_healthy:
        health_status["status"] = "healthy"
        return Response(health_status)
    else:
        health_status["status"] = "unhealthy"
        return Response(health_status, status=503)


@extend_schema(
	tags=["System"],
	summary="Detailed health check",
	description="Detailed health check with disk usage and uptime.",
	request=None,
	responses={
		200: OpenApiResponse(description="Detailed health status retrieved successfully.")
	}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_detailed(request):
    """Detailed health check with additional metrics."""
    health_status = {
        "status": "healthy",
        "checks": {},
        "metrics": {}
    }
    
    # Check database
    database_healthy = False
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_healthy = True
    except Exception:
        database_healthy = False
    health_status["checks"]["database"] = database_healthy
    
    # Check Redis
    redis_healthy = False
    try:
        redis_url = get_env("REDIS_URL", default="redis://redis:6379/0")
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        redis_healthy = bool(client.ping())
    except Exception:
        redis_healthy = False
    health_status["checks"]["redis"] = redis_healthy
    
    # Check Celery
    celery_healthy = False
    celery_workers = 0
    try:
        from celery import current_app
        inspect = current_app.control.inspect(timeout=2)
        stats = inspect.stats()
        if stats:
            celery_healthy = True
            celery_workers = len(stats)
    except Exception:
        pass
    health_status["checks"]["celery"] = celery_healthy
    health_status["metrics"]["celery_workers"] = celery_workers
    
    # Disk usage
    try:
        disk_usage = shutil.disk_usage("/")
        health_status["metrics"]["disk"] = {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent_used": round((disk_usage.used / disk_usage.total) * 100, 2)
        }
    except Exception:
        health_status["metrics"]["disk"] = None
    
    # Application uptime
    uptime = time.time() - START_TIME
    health_status["metrics"]["uptime_seconds"] = round(uptime, 2)
    
    # Determine overall health
    is_healthy = database_healthy and redis_healthy
    health_status["status"] = "healthy" if is_healthy else "unhealthy"
    
    status_code = 200 if is_healthy else 503
    return Response(health_status, status=status_code)


@extend_schema(
	tags=["System"],
	summary="Version information",
	description="Get application version and deployment information.",
	request=None,
	responses={
		200: OpenApiResponse(description="Version information retrieved successfully.")
	}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def version_info(request):
    """Version endpoint - returns version, commit, and environment."""
    from django.conf import settings
    
    return Response({
        "version": VERSION,
        "commit": COMMIT,
        "environment": get_env("ENVIRONMENT", default="development"),
        "service": "matchhire-backend",
        "uptime_seconds": round(time.time() - START_TIME, 2)
    })

