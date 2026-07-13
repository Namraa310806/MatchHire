import redis
from django.db import connections
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from matchhire_backend.core.env import get_env


VERSION = "1.0.0"
COMMIT = "unknown"


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
    """Readiness probe - checks database and Redis connectivity."""
    # Check database
    database_healthy = False
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_healthy = True
    except Exception:
        database_healthy = False
    
    # Check Redis
    redis_healthy = False
    try:
        redis_url = get_env("REDIS_URL", default="redis://redis:6379/0")
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        redis_healthy = bool(client.ping())
    except Exception:
        redis_healthy = False
    
    # Determine overall health
    is_healthy = database_healthy and redis_healthy
    
    if is_healthy:
        return Response({
            "status": "healthy",
            "database": True,
            "redis": True
        })
    else:
        return Response(
            {
                "status": "unhealthy",
                "database": database_healthy,
                "redis": redis_healthy
            },
            status=503
        )


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
        "environment": "production" if not settings.DEBUG else "development"
    })

