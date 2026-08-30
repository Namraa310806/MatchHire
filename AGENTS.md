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

## Celery and Asynchronous Task Rules

14. **Celery is orchestration only** - Celery tasks must not contain scraping logic, HTML parsing, JSON extraction, normalization rules, or database upsert logic. These responsibilities belong to scrapers and the ingestion service.

15. **Scrapers remain independent of Celery** - Scrapers must work independently without requiring Celery. They should be testable without a Celery worker.

16. **Tasks must be idempotent** - Celery tasks may execute more than once. Idempotency must be achieved through database uniqueness constraints and idempotent upsert logic, not through Celery task IDs.

17. **Do not use Redis as job source of truth** - Redis is the Celery broker only. PostgreSQL remains the source of truth for job records. Do not use Redis for job deduplication or storage.

18. **Retry only transient failures** - Transient failures (timeout, 429, 500, 502, 503, 504) may be retried. Permanent failures (malformed data, unknown source, validation errors) must not endlessly retry.

19. **Do not retry malformed/permanent failures indefinitely** - Malformed payloads, unsupported formats, missing required fields, and unknown sources must fail permanently without retry.

20. **Task arguments/results must be serializable** - Task arguments and results must be simple serializable values (strings, integers, booleans, lists, dicts). Do not pass Django QuerySets, model instances, database connections, or scraper instances.

21. **Do not allow arbitrary task execution** - Use a controlled source registry. Do not allow task arguments such as Python import paths, shell commands, arbitrary URLs, or arbitrary scraper classes.

22. **At-least-once execution semantics** - Celery provides at-least-once execution semantics. Correctness must not depend on a task running exactly once. Use database uniqueness and idempotent upsert as the correctness mechanism.

23. **Database transactions must not wrap network calls** - Do not hold PostgreSQL transactions during HTTP requests. Fetch first, then open a transaction for persistence.

24. **Bounded retry with exponential backoff** - Retries must be bounded (e.g., max 3 retries) with exponential backoff. Do not create infinite retry loops or use extremely aggressive retry intervals.

25. **HTTP 429 handling** - HTTP 429 must be treated as transient. Respect the Retry-After header when available (capped at reasonable bounds). Do not hammer the source or implement anti-bot bypassing.

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
- **Real vs fictional sources**: Clearly distinguish between real official company sources (e.g., Stripe via Greenhouse ATS, Spotify via Lever ATS, Linear via Ashby ATS) and fictional demo sources (e.g., Nexus Technologies). Only real sources should be used in production.
- **Scraper/persistence separation**: Scrapers must not perform database operations. Use the ingestion service for persistence to enable future Celery integration.
- **Deterministic fixtures**: Unit tests must use deterministic fixture data, not live network requests. Tests should not fail due to external website availability.
- **No user job creation**: Do not create public APIs allowing users to create arbitrary job records.
- **No matching logic in scrapers**: Scrapers should only normalize job data. Matching algorithms belong to future phases.
- **No secrets/logging**: Never log secrets, passwords, or sensitive data. Do not hardcode credentials.
- **No live network dependency in tests**: All scraper tests must use fixture data, not live HTTP requests.
- **No anti-bot bypass**: Do not implement CAPTCHA solving, proxy rotation, stealth browser automation, or any mechanism to bypass access controls. If a source blocks automated access, select another legitimate official source.

## Multi-Source Scraper Implementation Rules

- **Extend BaseJobScraper**: All new scrapers must extend BaseJobScraper and implement the contract (get_source_identifier, fetch, extract, normalize).
- **Use NormalizedJob**: All scrapers must return NormalizedJob objects with the required fields (source, external_id, title, description, application_url).
- **Register in SOURCE_REGISTRY**: New sources must be added to SOURCE_REGISTRY in apps/jobs/scrapers/registry.py. This is the authoritative list of supported sources.
- **Create Company record**: Each source must have a corresponding Company record in the database with the matching slug.
- **Create fixture data**: Each scraper must have deterministic fixture data in apps/jobs/scrapers/fixtures/{source}_jobs.json for testing.
- **Write comprehensive tests**: Each scraper must have a test class in tests_scrapers.py covering extraction, normalization, validation, and edge cases.
- **Register periodic schedule**: New sources should have a schedule registered via register_schedule command in apps/jobs/management/commands/register_schedule.py.
- **ATS pattern diversity**: When adding new sources, prioritize different ATS patterns (e.g., Greenhouse, Lever, Ashby, Workday, SmartRecruiters) to demonstrate scraper flexibility.
- **Verify API accessibility**: Before implementing a scraper, verify the source's public API is accessible, documented, and requires no authentication.
- **Handle ATS-specific quirks**: Each ATS has different response formats, field names, and pagination strategies. Normalize these in the scraper's extract/normalize methods.
- **HTML to text conversion**: Use BeautifulSoup for HTML-to-text conversion when needed. Add beautifulsoup4 to requirements.txt.
- **Employment type normalization**: Map source-specific employment types to normalized values (FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP).
- **Location handling**: Preserve location information from the source. Normalize to a consistent format if possible.
- **Skills extraction**: Implement basic keyword-based skill extraction from descriptions. More sophisticated NLP can be added in future phases.
- **Keyword extraction**: Extract keywords from department, team, location, and other relevant fields for searchability.
- **Error handling**: Use ScrapingError for scraper-specific errors with descriptive messages. Handle network timeouts and API errors gracefully.
- **No secrets in scrapers**: Scrapers must not require authentication or secrets. Only use public APIs that don't require credentials.

## Ingestion Operational Layer Rules (Phase 4C)

- **PostgreSQL as source of truth**: IngestionRun records in PostgreSQL are the authoritative source for ingestion state. Redis is only the Celery broker, not a storage layer for run state.
- **IngestionRun creation**: One logical IngestionRun per ingestion operation. Retries reuse the same logical IngestionRun to avoid creating misleading "failed" records during active retry attempts.
- **Status state machine**: IngestionRun status follows controlled transitions: PENDING → RUNNING → (RETRYING → RUNNING)* → (SUCCEEDED | PARTIAL | FAILED). RETRYING is an in-progress state, not a terminal failure.
- **Retry semantics**: Transient failures move the run to RETRYING status, not FAILED. Only after retry exhaustion does the run become FAILED. The retry_count field tracks retry attempts.
- **Error information bounds**: Store only bounded error information (error_type, error_message) without secrets, passwords, JWTs, full payloads, or stack traces. Limit message size to 1000 characters.
- **Source health derivation**: Source health (HEALTHY, DEGRADED, FAILING, UNKNOWN) must be derived from recent IngestionRun records. RETRYING status is treated as DEGRADED (in-progress), not as a terminal failure. Do not create a separate SourceHealth model unless genuinely required.
- **Overlap prevention**: Use database constraints (UniqueConstraint with condition) to prevent concurrent RUNNING runs for the same source. Do not introduce distributed locking infrastructure unless database constraints are insufficient.
- **Scheduling security**: Only sources in SOURCE_REGISTRY may be scheduled. Schedules are registered via controlled management command (register_schedule) into django-celery-beat's database. Do not allow arbitrary URLs or user-configured schedules.
- **Idempotent scheduling**: Scheduled runs must remain safe and idempotent. PostgreSQL uniqueness prevents duplicate jobs even if a schedule runs multiple times. The register_schedule command is safe to run repeatedly.
- **Admin read-only**: IngestionRun admin interface must be read-only (no add/change/delete permissions) to preserve operational integrity.
- **Management command safety**: The ingestion_status command is for inspection only. The register_schedule command is for deterministic schedule setup. Do not add commands that allow modifying ingestion state or triggering arbitrary runs.
- **No complex monitoring**: Do not build full monitoring dashboards, Prometheus/Grafana, or OpenTelemetry in this phase unless already present. Use IngestionRun + management command for operational visibility.
- **Schedule intervals**: Use reasonable scheduling intervals (e.g., 4 hours for Stripe). Do not use extremely aggressive intervals (e.g., every minute) that could hammer sources. Test schedules (test_schedule command) are for verification only and must be removed after testing.
