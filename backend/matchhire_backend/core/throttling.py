"""
Custom DRF throttle classes for MatchHire API.

Provides scoped rate limiting for different endpoint types.
"""

from rest_framework.throttling import ScopedRateThrottle


class AnonymousRateThrottle(ScopedRateThrottle):
    """Throttle for anonymous users - 100 requests per day"""

    scope = "anonymous"


class AuthenticatedRateThrottle(ScopedRateThrottle):
    """Throttle for authenticated users - 1000 requests per day"""

    scope = "authenticated"


class LoginRateThrottle(ScopedRateThrottle):
    """Throttle for login attempts - 10 requests per hour"""

    scope = "login"


class RegistrationRateThrottle(ScopedRateThrottle):
    """Throttle for registration attempts - 5 requests per hour"""

    scope = "registration"


class ResumeUploadRateThrottle(ScopedRateThrottle):
    """Throttle for resume uploads - 30 requests per hour"""

    scope = "resume_upload"


class ResumeParsingRateThrottle(ScopedRateThrottle):
    """Throttle for resume parsing - 30 requests per hour"""

    scope = "resume_parsing"


class StructuredExtractionRateThrottle(ScopedRateThrottle):
    """Throttle for structured extraction - 30 requests per hour"""

    scope = "structured_extraction"


class JobApplyRateThrottle(ScopedRateThrottle):
    """Throttle for job applications - 100 requests per hour"""

    scope = "job_apply"


class MatchingRateThrottle(ScopedRateThrottle):
    """Throttle for matching operations - 100 requests per hour"""

    scope = "matching"


class InterviewScheduleRateThrottle(ScopedRateThrottle):
    """Throttle for interview scheduling - 50 requests per hour"""

    scope = "interview_schedule"


class NotificationRateThrottle(ScopedRateThrottle):
    """Throttle for notification operations - 500 requests per hour"""

    scope = "notification"


class AdminRateThrottle(ScopedRateThrottle):
    """Throttle for admin operations - 200 requests per hour"""

    scope = "admin"


class AnalyticsRateThrottle(ScopedRateThrottle):
    """Throttle for analytics operations - 100 requests per hour"""

    scope = "analytics"
