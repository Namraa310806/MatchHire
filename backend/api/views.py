from django.conf import settings
from django.db import connection
from redis import Redis
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    def get(self, request):
        health_status = {"status": "ok", "database": "ok", "redis": "ok"}

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "error"

        # Check Redis
        try:
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "error"

        status_code = 200 if health_status["status"] == "ok" else 503
        return Response(health_status, status=status_code)
