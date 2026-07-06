"""
Centralized DRF exception handler for consistent error responses.

Returns consistent error format:
{
    "error": {
        "code": "...",
        "message": "...",
        "details": ...
    }
}
"""
import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    PermissionDenied,
    Throttled,
    NotFound,
)
from django.core.exceptions import ValidationError as DjangoValidationError


logger = logging.getLogger('matchhire.exceptions')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    
    Returns consistent error response format for all exceptions.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get the view and request from context
        view = context.get('view')
        request = context.get('request')
        
        # Build error response
        error_data = {
            "error": {
                "code": get_error_code(exc),
                "message": get_error_message(exc),
            }
        }
        
        # Add details if available
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                error_data["error"]["details"] = exc.detail
            elif isinstance(exc.detail, list):
                error_data["error"]["details"] = exc.detail
            else:
                error_data["error"]["details"] = str(exc.detail)
        
        # Log the exception
        log_exception(exc, view, request)
        
        # Update response data
        response.data = error_data
    
    return response


def get_error_code(exc):
    """Map exception type to error code"""
    if isinstance(exc, ValidationError):
        return "VALIDATION_ERROR"
    elif isinstance(exc, AuthenticationFailed):
        return "AUTHENTICATION_FAILED"
    elif isinstance(exc, PermissionDenied):
        return "PERMISSION_DENIED"
    elif isinstance(exc, Throttled):
        return "RATE_LIMIT_EXCEEDED"
    elif isinstance(exc, NotFound):
        return "NOT_FOUND"
    elif isinstance(exc, DjangoValidationError):
        return "VALIDATION_ERROR"
    else:
        return "INTERNAL_ERROR"


def get_error_message(exc):
    """Get user-friendly error message"""
    if isinstance(exc, Throttled):
        wait = getattr(exc, 'wait', None)
        if wait:
            return f"Rate limit exceeded. Please wait {wait} seconds before trying again."
        return "Rate limit exceeded. Please try again later."
    elif isinstance(exc, ValidationError):
        return "Validation failed. Please check your input."
    elif isinstance(exc, AuthenticationFailed):
        return "Authentication failed. Please check your credentials."
    elif isinstance(exc, PermissionDenied):
        return "You do not have permission to perform this action."
    elif isinstance(exc, NotFound):
        return "The requested resource was not found."
    else:
        return str(exc)


def log_exception(exc, view, request):
    """Log exception with context"""
    if request:
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else 'anonymous'
        endpoint = request.path
        method = request.method
        
        logger.error(
            f"Exception | type={type(exc).__name__} | user_id={user_id} | "
            f"endpoint={endpoint} | method={method} | message={str(exc)}"
        )
