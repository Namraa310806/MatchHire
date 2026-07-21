# Changelog

All notable changes to MatchHire will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Engineering standards and repository foundation documentation
- Architecture documentation (system overview)
- Architecture Decision Records (ADRs) for major technical decisions
- Developer guide with comprehensive setup instructions
- Coding standards document
- Contribution guide for external contributors
- Definition of done checklist for quality assurance
- Repository roadmap outlining past, present, and future phases
- Repository health files (SECURITY.md, SUPPORT.md, CODE_OF_CONDUCT.md)
- Project vision document
- Engineering principles document

### Changed
- Improved README with comprehensive project information
- Added documentation structure under `docs/` directory

## [1.0.0] - 2026-07-21

### Added
- Initial release of MatchHire backend
- Django 5.1.7 with Django REST Framework 3.15.2
- JWT authentication with cookie-based token storage
- Role-Based Access Control (RBAC) with candidate, recruiter, and admin roles
- User management with custom user model
- Resume management system
- Resume parsing for PDF and DOCX formats
- Structured resume data extraction (skills, experience, education)
- Job posting and management
- Job application workflow
- AI-powered matching engine with weighted scoring (skills 60%, experience 30%, education 10%)
- Interview scheduling and management
- Notification system with real-time delivery
- Analytics dashboard for recruiters
- Admin and moderation features
- Celery background processing for async tasks
- OpenAPI/Swagger documentation via drf-spectacular
- API hardening with rate limiting per endpoint
- Security enhancements (input validation, SQL injection prevention, XSS prevention)
- Comprehensive test suite
- Docker-based development environment
- PostgreSQL database
- Redis cache and message broker
- Nginx reverse proxy
- Environment-based configuration system
- Request ID middleware for distributed tracing
- Custom exception handling
- Security audit functions
- Startup validation checks

### Security
- JWT access token lifetime: 15 minutes
- JWT refresh token lifetime: 7 days
- Refresh token rotation on each use
- Token blacklisting after rotation
- httpOnly cookies for XSS prevention
- SameSite=Lax for CSRF prevention
- Secure cookie flag in production
- Rate limiting per endpoint type
- Input validation via serializers
- SQL injection prevention via ORM
- XSS prevention via DRF serializers

## [0.3.0] - 2026-06-15

### Added
- Interview scheduling and management
- Notification system
- Analytics dashboard
- Admin and moderation features

### Changed
- Improved matching algorithm performance
- Enhanced error handling

## [0.2.0] - 2026-05-01

### Added
- Resume parsing (PDF, DOCX)
- Structured resume data extraction
- Job posting and management
- Job application workflow
- Basic matching algorithm

### Changed
- Improved user authentication flow
- Enhanced RBAC implementation

## [0.1.0] - 2026-04-01

### Added
- Initial Django project setup
- Docker development environment
- PostgreSQL database
- Redis integration
- Custom user model
- JWT authentication
- Basic API structure
- Role-Based Access Control
- Initial test suite

## Version Format

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

## Release Process

1. Update version in appropriate files
2. Update CHANGELOG.md
3. Create git tag
4. Build and release
5. Update documentation

[Unreleased]: https://github.com/your-org/matchhire/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/matchhire/releases/tag/v1.0.0
[0.3.0]: https://github.com/your-org/matchhire/releases/tag/v0.3.0
[0.2.0]: https://github.com/your-org/matchhire/releases/tag/v0.2.0
[0.1.0]: https://github.com/your-org/matchhire/releases/tag/v0.1.0
