# MatchHire Engineering Rules for Agents

This document outlines engineering rules and principles for agents working on the MatchHire project.

## Core Principles

1. **Read existing code before modifying it** - Always understand the current implementation before making changes.

2. **Work incrementally** - Implement features in small, testable increments. Do not attempt to implement entire systems at once.

3. **Stay within scope** - Do not implement features outside the current task unless explicitly required. Future phases will be implemented in their own time.

4. **Never fabricate external API behavior** - Only implement integrations based on actual API documentation. Do not assume or mock external behavior.

5. **Never hardcode secrets** - All secrets must be loaded from environment variables. Never commit secrets to the repository.

6. **Write tests for implemented behavior** - Every feature must have corresponding tests. Do not claim something works without verifying it through tests.

7. **Verify before declaring completion** - Run relevant tests and verify actual results before marking a task as complete.

8. **Preserve the planned MatchHire architecture** - The planned technology stack and architecture decisions must be respected. Avoid unnecessary rewrites.

9. **Prefer simple implementations** - Avoid unnecessary abstraction layers. Simple, readable code is preferred over complex patterns unless there's a clear need.

10. **Keep external integrations isolated** - External services and APIs should be isolated in their own modules to facilitate testing and maintenance.

11. **Make async tasks idempotent** - When Celery tasks are introduced, they must be idempotent to handle retries safely.

12. **Verified-source ingestion only** - Jobs must enter MatchHire only through the automated verified-source ingestion pipeline. Do not add endpoints allowing arbitrary users to create jobs.

13. **Avoid unnecessary rewrites** - Future architecture decisions should build upon existing foundations rather than requiring complete rewrites.

## Development Workflow

- Before starting a task, read the relevant existing code and documentation.
- Identify dependencies and ensure they are properly installed.
- Make changes in small, focused commits.
- Run tests after each significant change.
- Verify the application runs successfully before declaring completion.

## Testing Requirements

- All new features must have corresponding tests.
- Tests must verify both success and error cases.
- Integration tests must verify external service connectivity.
- Run the full test suite before submitting work.

## Security Requirements

- Never commit secrets or credentials.
- Use environment variables for all sensitive configuration.
- Validate all user inputs.
- Follow Django security best practices.
- Keep dependencies updated.

## Database Rules

- All database changes must go through Django migrations.
- Do not modify the database schema directly.
- Use PostgreSQL in production (configured in settings).
- Test migrations against a clean database.

## API Design

- Follow RESTful conventions.
- Use appropriate HTTP status codes.
- Return consistent JSON responses.
- Document API endpoints in code comments.
- Version APIs when breaking changes are introduced.

## Frontend Rules

- Use React as the frontend framework.
- Keep components small and focused.
- Use TypeScript for type safety when appropriate.
- Follow React best practices for state management.
- Ensure responsive design for mobile compatibility.

## Phase-Specific Guidelines

Each development phase has specific scope restrictions. Always verify the current phase requirements before implementing features. Do not implement features from future phases prematurely.

## Job Ingestion Rules

- **Official-source-only jobs**: Jobs must enter MatchHire only through the automated verified-source ingestion pipeline. Do not add endpoints allowing arbitrary users to create jobs.
- **Real vs fictional sources**: Clearly distinguish between real official company sources (e.g., Stripe via Greenhouse ATS) and fictional demo sources (e.g., Nexus Technologies). Only real sources should be used in production.
- **Scraper/persistence separation**: Scrapers must not perform database operations. Use the ingestion service for persistence to enable future Celery integration.
- **Deterministic fixtures**: Unit tests must use deterministic fixture data, not live network requests. Tests should not fail due to external website availability.
- **No user job creation**: Do not create public APIs allowing users to create arbitrary job records.
- **No matching logic in scrapers**: Scrapers should only normalize job data. Matching algorithms belong to future phases.
- **No secrets/logging**: Never log secrets, passwords, or sensitive data. Do not hardcode credentials.
- **No live network dependency in tests**: All scraper tests must use fixture data, not live HTTP requests.
- **No anti-bot bypass**: Do not implement CAPTCHA solving, proxy rotation, stealth browser automation, or any mechanism to bypass access controls. If a source blocks automated access, select another legitimate official source.
