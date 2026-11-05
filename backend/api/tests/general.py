"""General API and Celery tests."""

from django.test import TestCase
from rest_framework.test import APIClient


class HealthCheckTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_ok(self):
        """Test health check returns OK when database and Redis are healthy."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["redis"], "ok")
