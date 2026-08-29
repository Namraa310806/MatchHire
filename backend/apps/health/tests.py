from django.test import TestCase
from unittest.mock import patch, MagicMock


class HealthCheckTests(TestCase):
    def test_health_endpoint_returns_200(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_json(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_endpoint_has_correct_structure(self):
        response = self.client.get('/api/health/')
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('dependencies', data)
        self.assertIn('database', data['dependencies'])
        self.assertIn('redis', data['dependencies'])

    def test_health_endpoint_database_connectivity(self):
        response = self.client.get('/api/health/')
        data = response.json()
        # Database should be ok since test database is available
        self.assertEqual(data['dependencies']['database'], 'ok')

    @patch('apps.health.views.redis.Redis')
    def test_health_endpoint_redis_connectivity_when_available(self, mock_redis):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        response = self.client.get('/api/health/')
        data = response.json()
        self.assertEqual(data['dependencies']['redis'], 'ok')

    @patch('apps.health.views.redis.Redis')
    def test_health_endpoint_handles_redis_unavailability(self, mock_redis):
        mock_redis.side_effect = Exception('Redis unavailable')
        
        response = self.client.get('/api/health/')
        data = response.json()
        self.assertEqual(data['dependencies']['redis'], 'error')
        self.assertEqual(data['status'], 'error')
