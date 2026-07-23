"""
IP-based rate limiting for authentication endpoints.

Provides additional protection against brute force attacks by rate limiting
based on IP address in addition to user-based rate limiting.
"""

import sys
from rest_framework.throttling import AnonRateThrottle
import logging


logger = logging.getLogger("matchhire.security")

# Check if we're in test mode
TESTING = "test" in sys.argv


class IPLoginRateThrottle(AnonRateThrottle):
    """
    IP-based rate limiting for login attempts.

    Limits login attempts from a single IP address to prevent brute force attacks.
    This works in addition to the user-based rate limiting.

    Rate: 5 requests per hour per IP
    """

    scope = "ip_login"
    rate = "5/hour"

    def get_cache_key(self, request, view):
        """
        Generate cache key based on IP address.

        Uses X-Forwarded-For header if available (for proxy setups),
        otherwise uses REMOTE_ADDR.

        Disabled during tests to avoid rate limiting issues.
        """
        if TESTING:
            return None
        ident = self.get_ident(request)
        return f"{self.scope}:{ident}"

    def get_ident(self, request):
        """
        Get client IP address from request.

        Handles proxy setups by checking X-Forwarded-For header.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Get the first IP in the chain (original client)
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip

    def throttle_failure(self):
        """
        Log throttling event for security monitoring.
        """
        logger.warning(
            f"IP_RATE_LIMIT_EXCEEDED | scope={self.scope} | rate={self.rate}"
        )
        super().throttle_failure()


class IPRegistrationRateThrottle(AnonRateThrottle):
    """
    IP-based rate limiting for registration attempts.

    Limits registration attempts from a single IP address to prevent
    automated account creation.

    Rate: 3 requests per hour per IP
    """

    scope = "ip_registration"
    rate = "3/hour"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if TESTING:
            return None
        return f"{self.scope}:{ident}"

    def get_ident(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip

    def throttle_failure(self):
        logger.warning(
            f"IP_RATE_LIMIT_EXCEEDED | scope={self.scope} | rate={self.rate}"
        )
        super().throttle_failure()


class IPPasswordResetRateThrottle(AnonRateThrottle):
    """
    IP-based rate limiting for password reset attempts.

    Limits password reset attempts from a single IP address.

    Rate: 3 requests per hour per IP
    """

    scope = "ip_password_reset"
    rate = "3/hour"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if TESTING:
            return None
        return f"{self.scope}:{ident}"

    def get_ident(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip

    def throttle_failure(self):
        logger.warning(
            f"IP_RATE_LIMIT_EXCEEDED | scope={self.scope} | rate={self.rate}"
        )
        super().throttle_failure()
