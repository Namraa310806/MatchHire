from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from matchhire_backend.core.startup_checks import get_dependency_status


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    dependency_status = get_dependency_status()
    is_healthy = all(status == "connected" for status in dependency_status.values())
    return Response(
        {
            "status": "ok" if is_healthy else "degraded",
            "version": "1.0",
            "database": dependency_status["database"],
            "redis": dependency_status["redis"],
        }
    )

