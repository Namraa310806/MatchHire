# ADR 0002: JWT Authentication with Cookie-Based Storage

## Status

Accepted

## Context

MatchHire needed a secure, stateless authentication mechanism that would work seamlessly with a React frontend and support both web and potential mobile clients. Requirements included:

- Secure token transmission
- Automatic token refresh
- Protection against XSS and CSRF attacks
- Support for role-based access control
- Compatibility with Django REST Framework

## Decision

Implement JWT (JSON Web Tokens) authentication with cookie-based token storage using djangorestframework-simplejwt.

### Implementation Details

- **Access Token Lifetime**: 15 minutes
- **Refresh Token Lifetime**: 7 days
- **Token Storage**: httpOnly cookies (not localStorage)
- **Token Refresh**: Automatic rotation on each refresh
- **Token Blacklisting**: Old refresh tokens blacklisted after rotation
- **Cookie Security**: Secure flag in production, SameSite=Lax

### Configuration

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

JWT_ACCESS_COOKIE_NAME = "access_token"
JWT_REFRESH_COOKIE_NAME = "refresh_token"
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_SECURE = not DEBUG
```

### Custom Authentication Backend

Implemented `CookieJWTAuthentication` in `apps/users/authentication.py` to extract tokens from cookies instead of Authorization headers.

## Alternatives Considered

### Alternative 1: Session-Based Authentication

- **Pros**: Django built-in, simple to implement, server-side session invalidation
- **Cons**: Requires session storage, not stateless, harder to scale horizontally, not ideal for SPA/mobile

### Alternative 2: JWT with Authorization Header

- **Pros**: Standard approach, stateless, works across all clients
- **Cons**: Vulnerable to XSS if stored in localStorage, requires manual token management in frontend

### Alternative 3: OAuth2 / OpenID Connect

- **Pros**: Industry standard, supports third-party login, sophisticated token management
- **Cons**: Overkill for single-tenant application, additional infrastructure complexity, external dependencies

## Pros

- **Security**: httpOnly cookies prevent XSS attacks
- **CSRF Protection**: SameSite=Lax prevents CSRF attacks
- **Automatic Refresh**: Frontend doesn't need complex token refresh logic
- **Stateless**: No server-side session storage required
- **Scalability**: Easy to scale horizontally without session affinity
- **Mobile Ready**: Same authentication works for future mobile apps
- **Token Rotation**: Refresh token rotation prevents token theft replay attacks

## Cons

- **Cookie Size Limits**: Cookies have size limits (4KB), though JWTs typically fit
- **Cross-Domain Issues**: Cookies are domain-specific, complicating multi-domain setups
- **Logout Complexity**: Immediate logout requires server-side token blacklisting
- **No Server-Side Invalidation**: Can't invalidate tokens without blacklisting infrastructure

## Future Implications

- Consider adding short-lived token blacklisting for immediate logout
- May need to implement token revocation lists for compromised accounts
- Consider adding device fingerprinting for enhanced security
- May need to support multiple concurrent sessions per user

## Related Decisions

- [ADR 0005: Role-Based Access Control](0005-rbac.md) - JWT payloads include role information for authorization

## References

- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [djangorestframework-simplejwt documentation](https://django-rest-framework-simplejwt.readthedocs.io/)
