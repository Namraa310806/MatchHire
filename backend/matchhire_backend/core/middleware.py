"""
Request ID middleware for tracking requests across the system.
"""
import uuid
import logging

from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware to add a unique request ID to each request.
    
    - Generates a UUID if not provided by client
    - Reuses client-provided X-Request-ID header if present
    - Adds request_id to request object for use in views and logging
    - Adds X-Request-ID to response headers
    """
    
    REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"
    
    def process_request(self, request):
        """Add request ID to the request object."""
        request_id = self._get_or_generate_request_id(request)
        request.id = request_id
        # Store in thread-local for logging filter access
        RequestIDFilter.request_id = request_id
        return None
    
    def process_response(self, request, response):
        """Add request ID to response headers."""
        if hasattr(request, 'id'):
            response[self.RESPONSE_HEADER] = request.id
        # Clear thread-local request ID
        RequestIDFilter.request_id = None
        return response
    
    def _get_or_generate_request_id(self, request):
        """Get request ID from header or generate new UUID."""
        request_id = request.META.get(self.REQUEST_ID_HEADER)
        
        if request_id:
            # Validate that the provided ID is a valid UUID
            try:
                uuid.UUID(request_id)
                return request_id
            except (ValueError, AttributeError, TypeError):
                # Invalid UUID, generate a new one
                logger.warning("Invalid X-Request-ID provided, generating new UUID")
                return str(uuid.uuid4())
        
        return str(uuid.uuid4())


class RequestIDFilter(logging.Filter):
    """
    Logging filter to inject request_id into log records.
    
    This filter adds the request_id to each log record if available.
    """
    request_id = None
    
    def filter(self, record):
        """Add request_id to log record if available."""
        if self.request_id:
            record.request_id = self.request_id
        else:
            record.request_id = None
        return True
