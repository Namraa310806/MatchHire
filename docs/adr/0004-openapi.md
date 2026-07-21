# ADR 0004: OpenAPI Documentation with drf-spectacular

## Status

Accepted

## Context

MatchHire exposes a RESTful API that needs comprehensive, accurate, and maintainable documentation. Requirements included:

- Interactive API documentation for frontend developers
- Type-safe API contracts
- Automatic schema generation from code
- Support for API versioning
- Client SDK generation potential
- Clear documentation of authentication, permissions, and response formats

## Decision

Implement OpenAPI/Swagger documentation using drf-spectacular for automatic schema generation from Django REST Framework code.

### Implementation Details

- **Library**: drf-spectacular 0.29.0
- **Schema Format**: OpenAPI 3.0
- **Schema Endpoint**: `/api/v1/schema/`
- **Swagger UI**: Available in development
- **ReDoc**: Available in development
- **API Versioning**: URL path versioning (`/api/v1/`)

### Configuration

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "MatchHire API",
    "DESCRIPTION": "Backend API for MatchHire recruitment platform.",
    "VERSION": "v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Authentication", "description": "User authentication endpoints"},
        {"name": "Users", "description": "User management endpoints"},
        # ... more tags
    ],
    "SECURITY": [{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}],
}
```

### Schema Features

- Automatic schema generation from serializers and views
- Enum documentation for status fields
- Tag-based endpoint organization
- JWT authentication scheme documentation
- Request/response example generation
- Pagination documentation

## Alternatives Considered

### Alternative 1: Manual Documentation (Markdown/Confluence)

- **Pros**: Full control, no dependencies
- **Cons**: Easily becomes outdated, manual maintenance burden, no interactive testing

### Alternative 2: drf-yasg (Yet Another Swagger Generator)

- **Pros**: Popular, mature library
- **Cons**: Less active development, more manual configuration required, less consistent with DRF patterns

### Alternative 3: django-rest-swagger (deprecated)

- **Pros**: Simple setup
- **Cons**: Deprecated, unmaintained, limited features

### Alternative 4: Custom API Documentation

- **Pros**: Tailored to needs
- **Cons**: High maintenance cost, reinventing the wheel, no standard format

## Pros

- **Automatic Generation**: Schema generated from code, always up-to-date
- **Interactive Documentation**: Swagger UI allows testing endpoints directly
- **Type Safety**: Clear request/response types
- **Standard Format**: OpenAPI is industry standard, tooling ecosystem
- **Client Generation**: Can generate client SDKs (TypeScript, Python, etc.)
- **Version Control**: Schema changes tracked in git
- **Minimal Maintenance**: Changes in code automatically reflected in schema
- **Authentication Documentation**: JWT scheme clearly documented

## Cons

- **Library Dependency**: Adds dependency on drf-spectacular
- **Learning Curve**: Developers need to understand drf-spectacular decorators
- **Schema Size**: Large schemas can be slow to generate
- **Customization Limits**: Complex custom schemas may require workarounds
- **Performance**: Schema generation adds overhead to startup

## Future Implications

- Consider adding schema validation in CI/CD to prevent breaking changes
- May need to implement schema versioning for backward compatibility
- Consider generating TypeScript client SDKs for the frontend
- May need to add custom extensions for non-standard API features
- Consider adding automated API contract testing

## Related Decisions

- [ADR 0002: JWT Authentication](0002-jwt-authentication.md) - JWT scheme documented in OpenAPI
- [ADR 0005: Role-Based Access Control](0005-rbac.md) - Permission requirements documented per endpoint

## References

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.0)
- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
