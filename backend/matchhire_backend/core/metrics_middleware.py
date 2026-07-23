"""
Middleware to track HTTP request metrics for Prometheus.
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin

from matchhire_backend.core.metrics import (
    track_http_request,
)

logger = logging.getLogger(__name__)


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to track HTTP request metrics for Prometheus.

    Tracks:
    - Request count by method, endpoint, and status
    - Request duration by method and endpoint
    - Request count by status code
    """

    def process_request(self, request):
        """Record request start time."""
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        """Record request metrics."""
        if not hasattr(request, "start_time"):
            return response

        # Calculate request duration
        duration = time.time() - request.start_time

        # Get endpoint path (remove query parameters)
        endpoint = request.path
        method = request.method
        status = response.status_code

        # Track metrics
        try:
            track_http_request(method, endpoint, status, duration)
        except Exception as e:
            logger.warning(f"Failed to track HTTP metrics: {e}")

        return response

    def process_exception(self, request, exception):
        """Handle exceptions in metrics tracking."""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            try:
                track_http_request(request.method, request.path, 500, duration)
            except Exception as e:
                logger.warning(f"Failed to track exception metrics: {e}")
        return None
