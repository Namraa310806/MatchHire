from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from HttpOnly cookies.
    """
    def authenticate(self, request):
        # First try standard JWT authentication (Authorization header)
        auth_result = super().authenticate(request)
        if auth_result:
            return auth_result
        
        # Fall back to cookie-based authentication
        access_token = request.COOKIES.get('access_token')
        if access_token:
            # Manually validate the token
            try:
                validated_token = self.get_validated_token(access_token)
                return self.get_user(validated_token), validated_token
            except Exception:
                return None
        
        return None
