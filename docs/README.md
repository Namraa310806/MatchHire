# Documentation

This directory contains comprehensive documentation for the MatchHire project.

## Structure

```
docs/
├── architecture/              # Architecture documentation
├── adr/                       # Architecture Decision Records
├── api/                       # API documentation
├── deployment/                # Deployment guides
├── development/               # Developer guides
└── guides/                    # User guides
```

## Architecture Documentation

Contains system architecture and design documentation:

- **system-overview.md**: High-level architecture, Django apps, service layer, request lifecycle, authentication flow, background processing, notification flow, analytics flow, deployment overview

## Architecture Decision Records (ADR)

Records of significant technical decisions made during development:

- **0001-service-layer.md**: Decision to use service layer pattern
- **0002-jwt-authentication.md**: Decision to use JWT with cookie-based storage
- **0003-celery-background-processing.md**: Decision to use Celery for background tasks
- **0004-openapi.md**: Decision to use drf-spectacular for OpenAPI documentation
- **0005-rbac.md**: Decision to implement role-based access control

Each ADR includes:
- Problem statement
- Decision made
- Alternatives considered
- Pros and cons
- Future implications

## API Documentation

Contains API reference documentation and examples.

## Deployment Documentation

Contains guides for deploying MatchHire to production environments.

## Development Documentation

Contains guides for developers working on the codebase:

- **developer-guide.md**: Comprehensive setup and development instructions
- **coding-standards.md**: Code style and best practices
- **engineering-principles.md**: Core engineering principles
- **definition-of-done.md**: Quality assurance checklist

## User Guides

Contains guides for end users of the platform.

## Adding Documentation

When adding new documentation:

1. Choose the appropriate directory based on the document type
2. Use clear, descriptive filenames
3. Follow existing formatting and style
4. Include relevant diagrams where helpful
5. Update this README if adding new document types

## Documentation Standards

- Use Markdown for all documentation
- Include table of contents for long documents
- Use code blocks with language specification
- Include examples where helpful
- Link to related documents
- Keep documentation up to date with code changes
