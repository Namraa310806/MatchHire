# Definition of Done

This document defines the criteria that must be satisfied for any feature, bug fix, or change to be considered complete in the MatchHire project.

## Overview

The Definition of Done (DoD) ensures that all work meets quality standards, is properly tested, documented, and ready for production. Every pull request must satisfy these criteria before merging.

## Checklist

### Tests

- [ ] **Unit tests added** for new functionality
- [ ] **Integration tests** for service layer changes
- [ ] **API tests** for endpoint changes
- [ ] **Tests cover both success and failure paths**
- [ ] **All tests passing** locally and in CI
- [ ] **Test coverage maintained or improved** (target >80% for new code)
- [ ] **No flaky tests** introduced
- [ ] **Tests are independent** and can run in any order

### Documentation

- [ ] **Code documentation**: Docstrings for all new functions, classes, and modules
- [ ] **API documentation**: OpenAPI schema updated via drf-spectacular decorators
- [ ] **Architecture documentation**: Updated if structural changes were made
- [ ] **ADR created** for significant technical decisions
- [ ] **README updated** if user-facing changes were made
- [ ] **Changelog updated** with summary of changes
- [ ] **Comments added** for complex or non-obvious logic

### Type Hints

- [ ] **Type hints added** to all function signatures
- [ ] **Type hints added** to class attributes where appropriate
- [ ] **Optional types** used correctly for nullable values
- [ ] **Type hints imported** from typing module
- [ ] **No type errors** reported by mypy (if used)

### Logging

- [ ] **Logging added** for important operations
- [ ] **Appropriate log levels** used (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- [ ] **Structured logging** with context (user_id, request_id, etc.)
- [ ] **Error logging includes stack traces** (exc_info=True)
- [ ] **No sensitive data** logged (passwords, tokens, PII)
- [ ] **Log messages are descriptive** and actionable

### OpenAPI

- [ ] **OpenAPI schema updated** for API changes
- [ ] **Schema validated** using `python manage.py spectacular --validate`
- [ ] **Request/response examples** added for complex endpoints
- [ ] **Tags assigned** to endpoints for organization
- [ ] **Authentication documented** for secured endpoints
- [ ] **Error responses documented** with status codes

### Security

- [ ] **Input validation** on all user inputs
- [ ] **SQL injection prevention** (parameterized queries via ORM)
- [ ] **XSS prevention** (proper escaping in serializers)
- [ ] **CSRF protection** enabled (via Django middleware)
- [ ] **Authentication checks** on protected endpoints
- [ ] **Authorization checks** for resource access
- [ ] **No secrets committed** (check .env files, credentials)
- [ ] **Dependency vulnerabilities** addressed (check requirements.txt)
- [ ] **Rate limiting** considered for new endpoints

### Performance

- [ ] **Database queries optimized** (select_related, prefetch_related)
- [ ] **N+1 queries eliminated**
- [ ] **Database indexes added** for frequently queried fields
- [ ] **Caching considered** for expensive operations
- [ ] **Pagination implemented** for list endpoints
- [ ] **Query performance tested** with realistic data volumes
- [ ] **No unnecessary computations** in hot paths

### Backward Compatibility

- [ ] **No breaking changes** to existing APIs
- [ ] **Breaking changes documented** if unavoidable
- [ ] **Migration path provided** for breaking changes
- [ ] **Deprecation warnings added** for deprecated features
- [ ] **Database migrations** are reversible
- [ ] **Existing tests still pass**

### Code Quality

- [ ] **Code follows coding standards** (see [coding-standards.md](coding-standards.md))
- [ ] **PEP 8 compliance** maintained
- [ ] **No dead code** or commented-out code
- [ ] **No hardcoded values** (use environment variables)
- [ ] **Imports organized** correctly (stdlib, third-party, local)
- [ ] **Variable names are descriptive**
- [ ] **Functions are small and focused** (single responsibility)
- [ ] **No code duplication** (DRY principle)

### Service Layer

- [ ] **Business logic in services**, not views
- [ ] **Services are idempotent** (safe to retry)
- [ ] **Services handle transactions** explicitly where needed
- [ ] **Services raise domain-specific exceptions**
- [ ] **Services don't handle HTTP concerns**
- [ ] **Service methods have clear contracts**

### Error Handling

- [ ] **Proper exception handling** (catch specific exceptions)
- [ ] **Meaningful error messages** returned to users
- [ ] **Errors logged with context**
- [ ] **No silent failures**
- [ ] **Graceful degradation** where appropriate
- [ ] **Custom exceptions** for domain-specific errors

### Review Requirements

- [ ] **Self-review performed** before requesting review
- [ ] **PR description complete** with context and testing notes
- [ ] **Linked to relevant issues** in PR description
- [ ] **Code reviewed by at least one maintainer**
- [ ] **Review comments addressed**
- [ ] **No merge conflicts**

### Deployment Readiness

- [ ] **Django check passes**: `python manage.py check`
- [ ] **Migrations created** if models changed
- [ ] **Migrations tested** on copy of production data
- [ ] **Environment variables documented** if new ones added
- [ ] **Deployment guide updated** if deployment process changed
- [ ] **Rollback plan considered** for risky changes

## Feature-Specific Criteria

### New API Endpoints

- [ ] All general DoD criteria
- [ ] URL follows RESTful conventions
- [ ] HTTP methods used correctly (GET, POST, PUT, DELETE)
- [ ] Status codes appropriate (200, 201, 400, 401, 403, 404, 500)
- [ ] Pagination implemented for list endpoints
- [ ] Filtering/sorting implemented where appropriate
- [ ] Rate limiting configured
- [ ] OpenAPI documentation complete

### Database Schema Changes

- [ ] All general DoD criteria
- [ ] Migration file created
- [ ] Migration reversible
- [ ] Migration tested on development database
- [ ] Data migration considered if needed
- [ ] Indexes added for performance
- [ ] Backward compatibility maintained
- [ ] Migration documented in changelog

### Background Tasks (Celery)

- [ ] All general DoD criteria
- [ ] Task is idempotent
- [ ] Task has retry configuration
- [ ] Task has timeout configuration
- [ ] Task logs appropriately
- [ ] Task error handling implemented
- [ ] Task tested both synchronously and asynchronously
- [ ] Task monitoring considered

### Frontend Changes

- [ ] All general DoD criteria
- [ ] API integration tested
- [ ] Loading states handled
- [ ] Error states handled
- [ ] Responsive design tested
- [ ] Accessibility considered
- [ ] Cross-browser compatibility tested

## Exceptions

### Hotfixes

For critical production issues, some criteria may be waived:

- Documentation updates can be done post-deployment
- Test coverage may be temporarily lower (must be improved in follow-up)
- Code review may be expedited

Must still satisfy:
- Critical tests passing
- Security review completed
- Backward compatibility maintained
- Deployment rollback plan in place

### Documentation-Only Changes

- Tests not required
- Type hints not required
- Logging not required
- OpenAPI not required

Must still satisfy:
- Documentation is accurate
- Links are valid
- Formatting is consistent
- Spelling/grammar checked

## Verification

Before merging, the author should:

1. Run the full test suite locally
2. Run `python manage.py check`
3. Verify OpenAPI schema is valid
4. Review the checklist above
5. Update the PR description with completed checklist items

## Continuous Improvement

This Definition of Done should be reviewed and updated periodically to reflect:
- New tools and practices
- Lessons learned from incidents
- Team feedback
- Changing project requirements

## References

- [Coding Standards](coding-standards.md)
- [Developer Guide](developer-guide.md)
- [Architecture Decision Records](../adr/)
- [Testing Guidelines](developer-guide.md#testing)
