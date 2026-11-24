"""Authentication endpoints for candidate accounts.

Implements Decision 8 transport rules:
- ``/api/auth/register/`` creates a candidate account and profile.
- ``/api/auth/login/`` is the browser transport: sets httpOnly JWT cookies
  and never returns tokens in the response body.
- ``/api/auth/token/`` and ``/api/auth/token/refresh/`` are the non-browser
  (Bearer) transport and return token pairs as JSON.
- ``/api/auth/logout/`` blacklists the refresh token and clears cookies.
"""

from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.models import CandidateProfile, User


def _set_jwt_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly JWT cookies on the response."""
    max_age_access = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    max_age_refresh = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        access_token,
        max_age=max_age_access,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        domain=settings.JWT_COOKIE_DOMAIN,
        path=settings.JWT_COOKIE_PATH,
    )
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE,
        refresh_token,
        max_age=max_age_refresh,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        domain=settings.JWT_COOKIE_DOMAIN,
        path=settings.JWT_COOKIE_PATH,
    )


def _clear_jwt_cookies(response: Response) -> None:
    """Expire JWT cookies on the response."""
    response.delete_cookie(
        settings.JWT_AUTH_COOKIE,
        path=settings.JWT_COOKIE_PATH,
        domain=settings.JWT_COOKIE_DOMAIN,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE,
        path=settings.JWT_COOKIE_PATH,
        domain=settings.JWT_COOKIE_DOMAIN,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )


class RegisterView(APIView):
    """Register a new candidate account with email and password."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_token"

    def post(self, request: Any) -> Response:
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        first_name = (request.data.get("first_name") or "").strip()
        last_name = (request.data.get("last_name") or "").strip()

        if not email or not password:
            return Response(
                {"detail": "email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password, user=User(email=email))
        except DjangoValidationError as exc:
            return Response(
                {"detail": "Password does not meet requirements.", "errors": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        CandidateProfile.objects.create(user=user)

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            status=status.HTTP_201_CREATED,
        )


class CookieLoginView(APIView):
    """Browser login: authenticate and set httpOnly JWT cookies."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_token"

    def post(self, request: Any) -> Response:
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""

        user = authenticate(request, username=email, password=password)
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        get_token(request)  # ensures the CSRF cookie is issued for subsequent POSTs
        response = Response({"detail": "Login successful."})
        _set_jwt_cookies(response, str(refresh.access_token), str(refresh))
        return response


class BearerTokenObtainView(TokenObtainPairView):
    """Non-browser login: return JWT pair as JSON (Bearer transport)."""

    permission_classes = (AllowAny,)  # type: ignore[assignment]
    throttle_classes = (ScopedRateThrottle,)  # type: ignore[assignment]
    throttle_scope = "auth_token"


class BearerTokenRefreshView(TokenRefreshView):
    """Non-browser refresh: rotate refresh token and return new pair."""

    permission_classes = (AllowAny,)  # type: ignore[assignment]
    throttle_classes = (ScopedRateThrottle,)  # type: ignore[assignment]
    throttle_scope = "auth_token"


class CookieTokenRefreshView(APIView):
    """Browser refresh: rotate the refresh cookie and set new cookies."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_token"

    def post(self, request: Any) -> Response:
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if not raw_refresh:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user_id = refresh.payload["user_id"]
            jti = refresh.payload.get("jti")
            if jti:
                from rest_framework_simplejwt.token_blacklist.models import (
                    BlacklistedToken,
                    OutstandingToken,
                )

                # Reject reuse of an already-rotated (blacklisted) refresh token
                if BlacklistedToken.objects.filter(
                    token__jti=jti
                ).exists():
                    raise TokenError("Token has already been rotated")
                outstanding = OutstandingToken.objects.filter(jti=jti).first()
                if outstanding:
                    BlacklistedToken.objects.get_or_create(token=outstanding)
            user = User.objects.get(id=user_id)
            new_refresh_token = RefreshToken.for_user(user)
        except (TokenError, KeyError, TypeError, User.DoesNotExist):
            return Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        get_token(request)  # refresh CSRF cookie alongside rotated JWT cookies
        response = Response({"detail": "Token refreshed."})
        _set_jwt_cookies(
            response, str(new_refresh_token.access_token), str(new_refresh_token)
        )
        return response


class LogoutView(APIView):
    """Log out: blacklist the refresh token (cookie or body) and clear cookies."""

    permission_classes = [AllowAny]

    def post(self, request: Any) -> Response:
        raw_refresh = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE
        )
        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except TokenError:
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_jwt_cookies(response)
        return response
