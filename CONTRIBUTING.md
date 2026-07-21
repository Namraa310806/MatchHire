# Contributing to MatchHire

Thank you for your interest in contributing to MatchHire! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Branch Naming](#branch-naming)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Review Expectations](#code-review-expectations)
- [Documentation Requirements](#documentation-requirements)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [maintainer email/contact].

## Getting Started

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- A code editor (VS Code, PyCharm, etc.)

### Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/your-username/matchhire.git
cd matchhire
```

3. Add the upstream remote:
```bash
git remote add upstream https://github.com/original-owner/matchhire.git
```

4. Copy the development environment file:
```bash
cp .env.development .env
```

5. Build and start the containers:
```bash
docker compose up --build
```

6. Run database migrations:
```bash
docker compose exec web python manage.py migrate
```

## Development Workflow

### 1. Create a Branch

Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write code following the [coding standards](docs/development/coding-standards.md)
- Add tests for your changes
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
docker compose exec web python manage.py test

# Run specific app tests
docker compose exec web python manage.py test apps.your-app

# Check code quality
docker compose exec web python manage.py check
```

### 4. Commit Your Changes

Follow the [commit message conventions](#commit-message-conventions).

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

Create a pull request against the main branch of the upstream repository.

### 7. Address Review Feedback

Make requested changes and update your PR until approved.

### 8. Sync with Upstream

After your PR is merged, sync your fork:

```bash
git checkout main
git pull upstream main
git push origin main
```

## Branch Naming

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes
- `chore/` - Maintenance tasks

Examples:
- `feature/add-job-search-filters`
- `fix/resume-parsing-error`
- `docs/update-api-documentation`
- `refactor/matching-service-optimization`

## Commit Message Conventions

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```
feat(matching): add semantic similarity scoring

Implement sentence-transformers based semantic matching
to improve job-candidate match quality beyond keyword matching.

Closes #123
```

```
fix(resumes): handle PDF parsing errors gracefully

Add proper error handling for corrupted PDF files and
return meaningful error messages to users.

Fixes #456
```

```
docs(api): update authentication endpoint documentation

Clarify JWT token refresh flow and add examples for
common authentication scenarios.
```

### Guidelines

- Use the imperative mood ("add" not "added" or "adds")
- Limit the subject line to 50 characters
- Wrap the body at 72 characters
- Reference relevant issues in the footer

## Pull Request Process

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Closes #123

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing performed

## Checklist
- [ ] Code follows coding standards
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Logging added where appropriate
- [ ] No breaking changes (or documented)
```

### PR Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer approval required
3. Address all review comments
4. Update PR description if scope changes

### Merge Requirements

- All tests passing
- Code review approved
- Documentation updated
- No merge conflicts
- Up-to-date with main branch

## Testing Requirements

### Test Coverage

- Aim for >80% test coverage on new code
- All new features must have tests
- Bug fixes must include regression tests

### Test Types

- Unit tests for individual components
- Integration tests for service layer
- API tests for endpoints
- Operational tests for system health

### Running Tests

```bash
# Run all tests
docker compose exec web python manage.py test

# Run specific app tests
docker compose exec web python manage.py test apps.matching

# Run with coverage
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
```

### Test Guidelines

- Write descriptive test names
- Each test should be independent
- Use factories for test data
- Mock external dependencies
- Test both success and failure cases

## Code Review Expectations

### For Contributors

- Keep PRs focused and small
- Respond to review comments promptly
- Explain complex logic in comments
- Update documentation for API changes
- Add tests for new functionality

### For Reviewers

- Provide constructive feedback
- Explain reasoning for suggestions
- Approve when changes are ready
- Check for security implications
- Verify documentation is updated

### Review Checklist

- [ ] Code follows project standards
- [ ] Tests are adequate and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate
- [ ] Logging is sufficient
- [ ] Backward compatibility maintained

## Documentation Requirements

### When to Update Documentation

- Adding new API endpoints
- Changing existing API behavior
- Adding new configuration options
- Changing deployment procedures
- Adding new architecture components

### Documentation Types

- **Code Documentation**: Docstrings for functions, classes, and modules
- **API Documentation**: OpenAPI schema updates via drf-spectacular
- **Architecture Documentation**: Update `docs/architecture/` for structural changes
- **ADR Documentation**: Create ADR for significant technical decisions
- **Developer Documentation**: Update `docs/development/` for workflow changes

### Documentation Standards

- Use clear, concise language
- Include examples where helpful
- Keep documentation up-to-date with code
- Use consistent formatting
- Add diagrams for complex flows

## Additional Guidelines

### Security

- Never commit secrets or credentials
- Report security vulnerabilities privately
- Follow security best practices
- Validate all user inputs
- Use parameterized queries

### Performance

- Consider performance implications
- Add database indexes for frequently queried fields
- Use caching where appropriate
- Optimize database queries
- Profile slow operations

### Backward Compatibility

- Avoid breaking changes
- Document any breaking changes clearly
- Provide migration paths for breaking changes
- Deprecate features before removal

### Questions?

- Open an issue for questions
- Check existing documentation first
- Be specific in your questions
- Provide context and examples

## Recognition

Contributors will be recognized in the project's CONTRIBUTORS file and release notes.

Thank you for contributing to MatchHire!
