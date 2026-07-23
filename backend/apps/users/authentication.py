from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if raw_token:
            return self._authenticate_raw_token(raw_token)

        return super().authenticate(request)

    def _authenticate_raw_token(self, raw_token):
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError) as exc:
            raise AuthenticationFailed("Invalid or expired access token.") from exc


class CookieJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "apps.users.authentication.CookieJWTAuthentication"
    name = "CookieJWTAuthentication"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix="Bearer",
            bearer_format="JWT",
        )
