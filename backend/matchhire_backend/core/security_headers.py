"""
Security headers middleware for MatchHire backend.

Adds additional security headers beyond Django's built-in security middleware.
"""


class SecurityHeadersMiddleware:
    """
    Middleware to add additional security headers to all responses.

    Adds:
    - Content-Security-Policy: Controls resources the browser can load
    - Permissions-Policy: Controls browser features access
    - X-Permitted-Cross-Domain-Policies: Restricts cross-domain policies
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add Content-Security-Policy header
        # This prevents XSS by controlling which resources can be loaded
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "manifest-src 'self';"
        )
        response["Content-Security-Policy"] = csp

        # Add Permissions-Policy header (formerly Feature-Policy)
        # Controls which browser features can be used
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(self), "
            "fullscreen=(self), "
            "picture-in-picture=(self)"
        )
        response["Permissions-Policy"] = permissions_policy

        # Add X-Permitted-Cross-Domain-Policies
        # Restricts cross-domain policy files
        response["X-Permitted-Cross-Domain-Policies"] = "none"

        # Remove server information
        if "Server" in response:
            del response["Server"]

        return response
