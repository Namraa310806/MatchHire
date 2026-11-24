"""JWT authentication supporting both cookie (browser) and Bearer (non-browser) transports.

Per Decision 8:
- Browser clients authenticate via httpOnly Secure SameSite cookies and MUST
  pass CSRF validation on state-changing requests.
- Non-browser clients use ``Authorization: Bearer <token>`` and are exempt
  from CSRF (no ambient credentials are sent cross-site).
- Cookies are checked first; the Bearer header is the fallback.
"""

from typing import Any

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class _CookieCSRFCheck(CsrfViewMiddleware):
    """CSRFCheck variant that raises DRF PermissionDenied instead of 403 response."""

    def _reject(self, request: Any, reason: str) -> None:
        raise PermissionDenied(f"CSRF Failed: {reason}")


def _enforce_csrf(request: Any) -> None:
    """Run Django's CSRF validation for cookie-authenticated requests."""
    check = _CookieCSRFCheck(lambda req: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied(f"CSRF Failed: {reason}")


class CookieOrBearerJWTAuthentication(JWTAuthentication):
    """Authenticate via JWT in an httpOnly cookie or Authorization Bearer header."""

    def authenticate(self, request: Any) -> tuple[Any, Any] | None:
        header = get_authorization_header(request)
        if header:
            # Bearer token present: non-browser client, CSRF-exempt per Decision 8
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
        except (InvalidToken, TokenError):
            return None

        # Cookie (ambient) authentication on unsafe methods requires CSRF
        if request.method not in _SAFE_METHODS:
            _enforce_csrf(request)

        return (user, validated_token)
