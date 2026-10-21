# MatchHire Technical Decisions

This document records significant technical decisions made during development.

## Phase 0: Project Foundation

### Dependency Management: uv
**Decision:** Use `uv` for dependency management instead of pip-tools.

**Rationale:**
- `uv` is significantly faster than pip-tools for dependency resolution and installation
- Modern tooling with better lock file support
- Built-in virtual environment management
- Active development and good community adoption

**Alternatives Considered:**
- pip-tools: Mature and widely used, but slower
- Poetry: Good for pure Python projects, but can be opinionated for Django projects

### Django Settings Split
**Decision:** Split settings into base, development, test, and production configurations.

**Rationale:**
- Clear separation of concerns
- Environment-specific configurations (DEBUG, database, security settings)
- Test settings can use eager mode for Celery and in-memory SQLite for speed
- Production settings enforce security best practices

### Celery Queues
**Decision:** Define three named queues: fetch_queue, parse_queue, match_queue.

**Rationale:**
- Separation of concerns for different task types
- Allows for dedicated workers per queue with different concurrency settings
- Better resource allocation and isolation

### Database: PostgreSQL 15
**Decision:** Use PostgreSQL 15 as the primary database.

**Rationale:**
- Robust relational database with strong ACID compliance
- Excellent support for JSONB and full-text search
- Required for production-grade applications
- Good Django ORM support

### Redis 7
**Decision:** Use Redis 7 for Celery broker and result backend.

**Rationale:**
- Fast in-memory data store
- Excellent Celery support
- Will also be used for caching in future phases
- Single Redis instance for both broker and cache (acknowledged risk: Redis outage affects both)

### Test Strategy
**Decision:** Use pytest with pytest-django, eager mode for Celery in tests.

**Rationale:**
- pytest provides better test discovery and fixtures than unittest
- pytest-django integrates well with Django
- Eager mode makes Celery tests synchronous and deterministic
- In-memory SQLite for faster test execution

### Python Version: 3.12
**Decision:** Use Python 3.12.

**Rationale:**
- Latest stable Python version with performance improvements
- Good library support
- Modern language features (type hints, pattern matching, etc.)

### Tooling
**Decision:** Use ruff for linting/formatting, mypy for type checking, pre-commit for git hooks.

**Rationale:**
- ruff is much faster than flake8/black combined
- mypy provides static type checking for better code quality
- pre-commit ensures code quality checks run before commits
