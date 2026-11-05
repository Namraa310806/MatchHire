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

## Phase 0: Specification Decisions

### Decision 1: Experience Matching
**Status:** Accepted

**Topic:** How required experience is interpreted when matching candidates to jobs.

**Final Decision:**
- Match score formula: `match_score = 0.50 * skill_similarity + 0.30 * experience_match + 0.20 * keyword_overlap`
- Job specifies zero years (required_yoe = 0): experience_match = 1.0 for any candidate experience; unknown candidate experience (user_yoe = null) = 1.0.
- Job requires positive minimum (required_yoe > 0): Formula `min(user_yoe / required_yoe, 1.0)` when user_yoe known and not null; candidate >= minimum = 1.0; candidate < minimum = partial credit; unknown candidate (user_yoe = null) = 0.0.
- Job specifies range (e.g., "0-2 years"): If range includes 0, treat as required_yoe = 0 (score = 1.0); if range excludes 0, use minimum value; overqualification not penalized (score = 1.0); unknown candidate (user_yoe = null) = 0.0 unless range includes 0.
- Experience missing from job: Treat as required_yoe = 0 (score = 1.0 for all); unknown candidate experience = 1.0.
- Division by zero protection: When required_yoe = 0, experience_match = 1.0 (no division performed); when user_yoe is null, experience_match = 0.0 unless required_yoe = 0.
- No hard cutoff; partial credit preserved in all cases.
- Examples: Job requires 0 years, candidate has 0 years → 1.0; Job requires 2 years, candidate has 1 year → 0.5; Job requires 2 years, candidate has null years → 0.0.

**Reasoning:**
- Fixed weights (50/30/20) from Playbook provide clear, reproducible scoring.
- Explicit zero handling prevents division by zero (most fresher roles).
- Partial credit preserves matching signal even when requirements aren't fully met.
- Distinguishing explicit zero from unknown is important for fresher targeting.

**Alternatives Considered:**
- Hard eligibility rules (disqualify if experience doesn't match): Rejected as too rigid for MVP.
- Ignore experience entirely: Rejected as it's an important matching signal.
- Dynamic weights: Rejected as they would require tuning with real data.

**Consequences:**
- Matching logic must distinguish NULL from 0 in experience fields.
- Experience_match always in [0.0, 1.0].
- Tests must cover all combinations of job requirements and candidate experience.

**Unresolved:**
- None for MVP.

---

### Decision 2: Base Match Score vs. Sponsored Boost
**Status:** Proposed (threshold requires approval)

**Topic:** Definition of base match score, its range, and how sponsored placement affects final ranking.

**Final Decision:**
- Score units: Store match scores as floats in [0.0, 1.0] internally; convert to percentages only at API boundary.
- Base match score: Range 0.0 to 1.0; represents pure relevance from TF-IDF and matching rules.
- Sponsored boost: Separate from relevance; applied to final ranking only; does not affect base score.
- Boost range: Configurable 0.0 to 0.15 (maximum boost from Playbook).
- Boost threshold: Applies only when base score exceeds threshold (proposed: > 0.40, requires approval).
- Final score: base_score + boost (capped at 1.0).
- Ranking: Compute base relevance for all jobs; apply sponsored boost to final score; sort by final score.
- Transparency: Sponsored jobs clearly marked in UI with is_sponsored flag; base relevance score displayed separately as match percentage; final ranking score used for sorting, not displayed.
- Tie handling: Jobs with same final score sorted by posted date (newest first); sponsored ties sorted by tier, then base score, then date.
- Invariants: Sponsorship cannot fabricate a better relevance score; base score remains true to compatibility; boost cannot create matches below threshold.

**Reasoning:**
- Separating relevance from monetization preserves candidate trust.
- Fixed boost range (0.0-0.15) from Playbook provides clear boundaries.
- Threshold ensures boost only applies to reasonably relevant matches.
- Original relevance score available for evaluation prevents hidden manipulation.
- Clear sponsorship labeling maintains transparency.

**Alternatives Considered:**
- Sponsored jobs modify base score directly: Rejected as it would misrepresent compatibility.
- No sponsored jobs in MVP: Rejected as monetization is planned.
- Sponsored jobs shown in separate section: Rejected as it reduces visibility.
- Boost without threshold: Rejected as it would boost irrelevant jobs.

**Consequences:**
- MatchScore table must store both base_score and final_score.
- Job table needs is_sponsored and sponsored_boost fields.
- Frontend must display both scores and sponsorship labels.
- Ranking query must use final_score for sorting.
- API must format base_score as percentage for display.

**Unresolved:**
- Base score threshold for boost application (proposed: > 0.40, requires approval).

---

### Decision 3: TF-IDF Vocabulary and Vector Versioning
**Status:** Accepted

**Topic:** How TF-IDF vocabulary/vectorizer is created, persisted, loaded, and versioned.

**Final Decision:**
- Strategy: Fixed vocabulary (not versioned vectors).
- Vocabulary source: Fixed skills dictionary with 500+ terms (canonical names + aliases); vocabulary must be created and populated during Phase 1 setup (not claiming to already exist).
- Initial vocabulary creation: Create skills dictionary with 500+ terms (canonical names + aliases); build TF-IDF vectorizer using scikit-learn; include unigrams from dictionary; remove English stopwords; no lemmatization or stemming (rely on dictionary aliases).
- Persistence: Vectorizer saved as pickle/joblib; stored in local filesystem (or S3 in production); no versioning needed (fixed vocabulary).
- Loading: At startup, load the vectorizer with fixed vocabulary; no fallback mechanism (vocabulary is stable); if vectorizer fails to load, system fails fast.
- Vector computation: Job vectors precomputed at ingestion time using fixed vocabulary; user vectors computed on profile change using same fixed vocabulary; compatibility guaranteed; no stale vector detection needed.
- Vocabulary updates (future): Vocabulary changes require explicit migration; process: update skills dictionary → recompute all job vectors → recompute all user vectors; not automated in MVP; manual migration with downtime.
- Model-score association: MatchScore table does NOT need vectorizer_version field (fixed vocabulary); scores remain valid indefinitely; no re-matching on vocabulary changes (vocabulary doesn't change).
- Sentence-transformer integration: Deferred to later enhancement phase; not in MVP.

**Reasoning:**
- Precomputed job vectors never go stale with a fixed vocabulary.
- Simpler architecture: no version management, no re-matching needed.
- Vocabulary derived from the 500+ term skills dictionary (shared with resume extraction).
- Ensures compatibility between job vectors and user vectors over time.
- Eliminates complexity of vector staleness detection and regeneration.

**Alternatives Considered and Rejected:**
- Versioned vectors: Rejected for MVP due to complexity (stale detection, re-matching, compatibility management).
- Dynamic vocabulary: Rejected as it would make precomputed job vectors stale.

**Consequences:**
- Skills dictionary is critical; changes require migration.
- Vocabulary cannot evolve automatically.
- Simpler architecture for MVP.
- Post-MVP may need versioned vectors if vocabulary volatility is high.

**Unresolved:**
- None for MVP.

**Candidate Skill Input Experience:**
- Candidates enter skills as free-text for flexibility
- System normalizes to canonical names from fixed vocabulary via aliases (e.g., "js" → "JavaScript")
- Unknown skills are logged but excluded from TF-IDF matching (no dynamic vocabulary expansion)
- Duplicate skills after normalization are removed
- This distinction between candidate input and internal representation is explicit across all documentation

---

### Decision 4: Job Lifecycle and Staleness
**Status:** Accepted

**Topic:** Lifecycle of an ingested job, including first ingestion, refreshes, staleness, closure, and reactivation.

**Final Decision:**
- Lifecycle states: Active (is_active=True), Inactive (is_active=False), Archived (optional, for audit).
- First ingestion: New job → Active (is_active=True, immediately visible).
- Subsequent refreshes: Job found with same ID → update content, remain Active, update last_seen_at; job found with different content → update content, remain Active, update last_seen_at, update job_hash; job missing from source during SUCCESSFUL fetch → increment consecutive_misses counter.
- Deactivation rule: Job becomes inactive (is_active=False) after N consecutive SUCCESSFUL fetches in which the job is absent; failed or partial fetch runs MUST NOT count as evidence of disappearance; default threshold N=3 (configurable per source).
- Failed fetch handling: Failed fetch (source unreachable, network error, 5xx, timeout) does NOT increment consecutive_misses; partial fetch (some jobs fetched, others failed) does NOT increment consecutive_misses for missing jobs; only a successful fetch where the job is absent counts as evidence of disappearance.
- Safety valve: If a single run would deactivate more than X% of a company's jobs, skip deactivation and raise an alert; proposed X=20% (EXPLICITLY UNRESOLVED - requires approval); prevents mass closure due to scraper bugs or source changes.
- Reactivation: Inactive job reappears in source → transition back to Active (is_active=True); reset consecutive_misses to 0; requires source ID match; should be rare (manual review recommended).
- apply_url behavior: For Active jobs, apply link is live and redirects to company's application URL; for Inactive jobs, apply link is disabled; API returns error for apply endpoint; lightweight periodic HEAD/GET check on apply_url sample (optional, not in MVP).
- Cache invalidation: When job becomes inactive, invalidate cached match scores for this job; when job reactivates, trigger re-matching for affected candidates; when job content changes, invalidate cached match scores for this job.

**Reasoning:**
- Immediate hiding of stale jobs prevents candidates from applying to closed positions.
- Threshold of 3 consecutive misses balances responsiveness with false-positive avoidance.
- Distinguishing source failure from job disappearance prevents premature closure.
- Safety valve prevents mass closure due to scraper bugs.

**Alternatives Considered:**
- Keep stale jobs visible until closed: Rejected as it wastes candidate effort.
- Immediate closure on first miss: Rejected as too aggressive (temporary glitches).
- No reactivation allowed: Rejected as it would lose valid job data.

**Consequences:**
- Job.is_active field (boolean, not status enum).
- Job.consecutive_misses counter.
- Job.last_seen_at timestamp for staleness detection.
- Job.job_hash for content change detection.
- IngestionSource.stale_threshold configurable per source.
- Celery task for periodic staleness detection.

**Unresolved:**
- Safety valve percentage X (proposed: 20%, EXPLICITLY UNRESOLVED - requires approval).

---

### Decision 5: Stable Source Identity vs. Content Hash
**Status:** Accepted

**Topic:** Distinction between stable external identifier and content hash for job identity and deduplication.

**Final Decision:**
- Stable source identity: Each job must have stable identifier from source (job ID, slug, or URL); source ID + external ID uniquely identifies a job; if source provides no ID, use URL as fallback; if neither available, use content hash as last resort (higher false-positive risk).
- Content hash: Used to detect changes in job content; not used as primary identity; content changes trigger job updates, not duplicate creation.
- job_hash definition: Computed from normalized fields (title, description, location, required_skills, required_yoe); normalization: lowercase, trim whitespace, normalize HTML entities; used for content-change detection, not as primary identity; hash algorithm: SHA-256 (standard, collision-resistant); stored in Job.job_hash field.
- Content change handling: When job's content changes but source ID is the same, UPDATE existing row; update: title, description, location, required_skills, required_yoe, job_hash, last_seen_at; do NOT create a new row; invalidate cached match scores for this job; trigger re-matching for affected candidates.
- Identity and deduplication: Primary identity = source + external_id (if available); fallback identity = application_url (if no external ID); last resort = content hash (manual review required); content changes update existing job, do not create duplicates; URL changes without ID change = treat as same job if content similar; ID changes without URL change = treat as potential duplicate, manual review.
- Identity failures: If identity cannot be established reliably, mark job for manual review; do not create duplicate jobs due to identity ambiguity.

**Reasoning:**
- Stable source IDs are the most reliable identity mechanism.
- Content hash alone is insufficient (content updates would create duplicates).
- Fallback hierarchy balances reliability with coverage.
- SHA-256 is standard and collision-resistant.

**Alternatives Considered:**
- Content hash as primary identity: Rejected as it treats content updates as new jobs.
- URL as primary identity: Rejected as URLs can change without job identity changing.
- Reject jobs without stable IDs: Rejected as it would limit source coverage.

**Consequences:**
- Job.external_id field (nullable).
- Job.application_url field (not null, used as fallback).
- Job.job_hash field for change detection.
- Unique constraint on (source, external_id) where external_id is not null.
- Application logic for identity resolution hierarchy.
- Manual review queue for ambiguous identities.

**Unresolved:**
- Threshold for content similarity when treating as same job (if needed).

---

### Decision 6: Celery Queues and Concurrency
**Status:** Accepted

**Topic:** Task categories, retry behavior, idempotency requirements, and concurrency boundaries.

**Final Decision:**
- Named queues: fetch_queue, parse_queue, match_queue (already configured in base.py).
- Task categories: Fetch tasks → fetch_queue; Parse tasks → parse_queue; Match tasks → match_queue.
- Authoritative concurrency table (proposed for production):
  - fetch_queue: 2 workers (lower concurrency to respect rate limits)
  - parse_queue: 4 workers (higher concurrency for CPU-bound parsing)
  - match_queue: 3 workers (balanced for batch scoring operations)
- Existing documentation reference: Some docs reference fetch_queue=5, parse_queue=3, match_queue=3 (inconsistent with proposed 2/4/3).
- Current Phase 0 configuration: base.py defines queue names but NOT concurrency values; Docker Compose worker command has no concurrency specified; concurrency to be added in Phase 2.
- Retry behavior: Transient failures (network, rate limits) → retry with exponential backoff; persistent failures (malformed data, 404) → log, alert, no retry; max retries: 3 for transient errors.
- Idempotency: All tasks must be idempotent; use task IDs or deduplication keys to prevent duplicate execution; FetchRun.celery_task_id for correlation.
- Overlapping scheduled fetches: Use Celery Beat with unique task names or locks to prevent overlapping; FetchRun.status prevents concurrent fetches for same source.
- Worker retries: Use Celery's autoretry_for with exponential backoff; idempotent task implementation prevents double effects.

**Reasoning:**
- Queue separation allows resource allocation and isolation.
- Idempotency prevents duplicate jobs or inconsistent state.
- Concurrency boundaries prevent source rate limit violations.
- Proposed 2/4/3 aligns with rate limit considerations (fetch_queue) and CPU-bound nature (parse_queue).
- Existing documentation inconsistencies (5/3/3) noted but not adopted.

**Alternatives Considered:**
- Single queue for all tasks: Rejected as it prevents resource optimization.
- No idempotency (rely on locks): Rejected as it's error-prone.
- No retry on failures: Rejected as transient failures are common.
- Using existing 5/3/3 configuration: Rejected as it doesn't align with rate limit and CPU-bound considerations.

**Consequences:**
- Celery configuration already in place (base.py) for queue names.
- Task implementation must include idempotency checks.
- FetchRun table for tracking and deduplication.
- Beat schedule with unique task names.
- Concurrency settings (2/4/3) are proposed targets; to be implemented in Phase 2 worker configuration.
- Current Phase 0 has no concurrency values configured (to be added later).

**Unresolved:**
- None for MVP (proposed concurrency: fetch_queue=2, parse_queue=4, match_queue=3).

---

### Decision 7: Scraping Source Legitimacy and Access Rules
**Status:** Proposed (requires legal/policy review)

**Topic:** Source approval policy for company career pages and permitted job sources.

**Proposed Resolution:**
- Source approval policy: Jobs ingested ONLY from approved, automated sources; no publicly accessible page is automatically permitted.
- Source types: Official company career pages; company ATS (where accessible without authentication); government job portals (future); approved aggregator APIs (future).
- Source requirements: Must be publicly accessible without authentication; must respect robots.txt and rate limits; must not require CAPTCHA solving or bypassing anti-bot protections; must not violate terms of service; legal review required for gray-area sources.
- Approval process: Sources proposed based on company list; legal/policy review for terms and access restrictions; technical feasibility assessment (scrapability, rate limits); approved sources added to configuration.
- Access rules: Respect robots.txt directives; observe rate limits (default: 1 request per second, configurable); identify with user agent; no authentication or paywall bypass; no CAPTCHA solving; stop on 429 (rate limit) with exponential backoff.
- Source-specific failure handling: 429 → backoff and retry; 403 → pause and alert (may be blocked); 404 → job closed; 5xx → retry with backoff; persistent failures → pause source and alert.

**Reasoning:**
- Legal compliance is critical for a production platform.
- Respecting robots.txt and rate limits is ethical and practical.
- Explicit approval process prevents unauthorized scraping.

**Alternatives Considered:**
- Scrape all publicly accessible pages: Rejected as it violates terms and risks legal issues.
- Ignore robots.txt: Rejected as unethical and may lead to blocking.
- Bypass authentication: Rejected as it violates terms and may be illegal.

**Consequences:**
- IngestionSource.is_active flag for source approval.
- Legal review process required before adding sources.
- Application-level rate limiting per source.
- Robots.txt parser and compliance checker.
- Alerting for access violations (403, CAPTCHA detection).

**Unresolved:**
- Default rate limit values (to be tuned per source).
- Legal review process ownership (who approves sources).
- Handling of sources with ambiguous terms (gray areas).
- Whether to use paid scraping services for difficult sources.

---

### Decision 8: Cookie Authentication and CSRF
**Status:** Accepted

**Topic:** Authentication model and security expectations for browser-based requests.

**Final Decision:**
- Authentication model: Email + password registration; primary transport: httpOnly, Secure, SameSite cookies for browser clients; token format: JWT (access token + refresh token); access token: 15 minute expiration; refresh token: 7 day expiration with rotation; tokens delivered in cookies, never in JSON body for browser clients; password reset via email (MVP may defer).
- Bearer authentication: Allowed only for non-browser clients (mobile apps, CLI tools, API integrations); Bearer token in `Authorization: Bearer <token>` header; same JWT tokens, different transport; browser clients MUST use cookie-based auth only.
- No recruiter accounts: Recruiter authentication not in MVP; no company dashboard access; no job creation endpoints.
- Session/cookie security: Secure, HttpOnly cookies in production; SameSite=Strict or Lax (proposed: Lax for better UX, requires approval); CSRF protection enabled for all state-changing cookie-authenticated requests; session timeout TBD (proposed: 7 days inactivity, requires approval).
- CSRF protection: Enabled for all POST/PUT/DELETE endpoints using cookie authentication; CSRF token must be included in request headers or body; Bearer authentication (non-browser clients) bypasses CSRF; frontend must include CSRF token for all state-changing requests; Django's built-in CSRF middleware handles validation.
- CORS boundaries: Frontend origin whitelisted in production; local development: allow localhost; no wildcard CORS in production.
- Token authentication: Django SimpleJWT chosen for JWT implementation; access token: 15 minute expiration; refresh token: 7 day expiration; refresh token rotation with blacklist after use; token revocation on logout (blacklist refresh token); password change revokes all refresh tokens.

**Reasoning:**
- httpOnly cookies are primary for browser security (Playbook requirement).
- JWT with SimpleJWT provides standard token management.
- Bearer auth restricted to non-browser clients (security boundary).
- CSRF protection essential for cookie-based auth.
- Lax SameSite proposed for better UX (needs approval).

**Alternatives Considered:**
- Token-only authentication: Rejected as CSRF protection is still needed for web UI.
- No CSRF protection: Rejected as it's a security vulnerability.
- Wildcard CORS: Rejected as it's insecure.
- DRF TokenAuthentication instead of JWT: Rejected as JWT is more flexible for mobile apps.

**Consequences:**
- Django's built-in CSRF middleware (already configured).
- Django SimpleJWT for JWT implementation.
- DRF authentication classes (to be configured).
- CORS middleware (django-cors-headers likely needed).
- Secure cookie settings in production settings.
- Session configuration (timeout, backend).

**Unresolved:**
- SameSite cookie policy (proposed: Lax, requires approval).
- Session timeout duration (proposed: 7 days, requires approval).

---

### Decision 9: Resume Consent, Retention, and Deletion
**Status:** Proposed (retention policies explicitly unresolved - requires legal review)

**Topic:** Purpose of resume data, consent model, retention policy, and deletion behavior.

**Proposed Resolution:**
- Resume purpose: Future skill extraction and profile enrichment; matching improvement (if resume parsing implemented); candidate's own reference.
- Not permitted: Sharing with third parties without consent; using for non-matching purposes; storing longer than retention period without justification.
- Consent model: Explicit consent required at upload; clear disclosure of purpose (matching, profile enrichment); option to withdraw consent; consent recorded with timestamp.
- Consent withdrawal: Candidate can delete resume at any time; profile data extracted from resume is retained (unless explicitly deleted); matching scores derived from resume may need recalculation (TBD).
- Retention policy (explicitly unresolved - awaiting legal review): Resume retention period EXPLICITLY UNRESOLVED (1 year is a proposal, not approved); extracted profile data retention EXPLICITLY UNRESOLVED (until account deletion is a proposal); operational records (application clicks) retention period EXPLICITLY UNRESOLVED.
- **Important:** All retention periods are proposals, not established requirements. Do not claim automatic deletion of parsed data, caches, or derived records unless that behavior is specified and later implemented.
- Deletion propagation: Account deletion → resume file deleted; resume deletion → file removed, profile data remains; profile deletion → all personal data removed, anonymized analytics retained.
- Data minimization: Store only what is necessary for matching; resume content not displayed to other users; extracted data used only for matching; no PII exposed in logs.

**Reasoning:**
- Explicit consent is required by data protection regulations.
- Clear retention limits prevent indefinite data storage.
- Separation of resume file from extracted data allows flexible deletion.
- One-year period is a proposal requiring legal approval.

**Alternatives Considered:**
- Implied consent by upload: Rejected as it may not comply with regulations.
- Indefinite retention: Rejected as it violates data minimization.
- Delete extracted profile data with resume: Rejected as it degrades matching quality.
- Automatic deletion of all derived data: Rejected as not specified in requirements.

**Consequences:**
- CandidateProfile.resume_consent_given field.
- CandidateProfile.resume_uploaded_at timestamp.
- Background job for resume deletion after retention period.
- Anonymization pipeline for analytics data.
- Logging practices to avoid PII exposure.

**Unresolved (Explicitly Awaiting Legal Review):**
- Legal retention period for resume files (1 year is a proposal, EXPLICITLY UNRESOLVED).
- Retention period for extracted profile data (until account deletion is a proposal, EXPLICITLY UNRESOLVED).
- Application click retention period for analytics (EXPLICITLY UNRESOLVED).
- Whether to recalculate match scores after resume deletion (EXPLICITLY UNRESOLVED).
- Legal requirements for anonymization (GDPR, India DPDP Act) (EXPLICITLY UNRESOLVED).
- Whether parsed data, caches, or derived records are automatically deleted (not specified, EXPLICITLY UNRESOLVED).

---

### Decision 10: Initial Company and Source List
**Status:** Pending (not a blocker for Phase 1 core data model)

**Topic:** How initial set of companies and career-page sources will be selected, reviewed, approved, and maintained.

**Current Status:**
- No finalized list of companies or sources exists in the repository.
- Source material does not provide a verified list of companies.
- The complete original company list from the MatchHire documentation is NOT represented as approved sources.
- Source approval is a pending task requiring research, legal review, and verification.

**Original Company List (Pending Source-Review Task):**
The following companies are candidates for source review but are NOT approved:
- Google
- Microsoft
- Amazon
- Infosys
- TCS
- Wipro
- Qualcomm
- Samsung
- Flipkart
- Swiggy
- Zomato
- Razorpay

**Important:** Listing a company as a candidate source does NOT authorize ingestion. Each source requires its own technical and legal/policy review before activation.

**Proposed Approach:**
- Selection criteria: Companies with strong presence in Tier-2/3 cities; companies with accessible career pages; companies with high volume of fresher hiring; diverse industry representation.
- Approval process: Legal review of source terms; technical feasibility assessment; rate limit evaluation; pilot testing before full ingestion.
- Maintenance: Regular review of source performance; removal of sources that become unavailable; addition of new sources based on candidate demand.
- Per-source documentation: fetch method (public JSON API / HTML / JS-rendered), verification status, terms/robots review flag.
- **Important:** No source is marked as approved until the source-review task is completed; sources are candidates for approval, not pre-approved.

**Phase 1 Dependencies:**
- Core data model implementation (Company, IngestionSource, Job models) does NOT require a finalized company list.
- Phase 1 can implement models, migrations, and ingestion pipeline with test/dummy sources.
- Real source-specific ingestion requires approved sources before activation.
- Source approval is a requirement before any source is activated, not before data model implementation.

**Reasoning:**
- Cannot fabricate company partnerships or source approvals.
- Legal and technical review is required before scraping.
- Pilot testing validates scrapability before full deployment.
- Separating data model implementation from source approval allows iterative development.
- Original company list must be reviewed and verified before any source is activated.

**Alternatives Considered:**
- Seed with placeholder companies: Rejected as it would require replacement later.
- Start with no sources: Rejected as it prevents testing and validation.
- Auto-discover sources: Rejected as it violates approval policy.
- Mark sources as approved without review: Rejected as it violates legal and technical requirements.

**Consequences:**
- Company and IngestionSource tables will be empty initially.
- Seed script required for initial approved sources (after source-review task completes).
- Documentation of selection criteria in DECISIONS.md.
- Source approval workflow (manual process).
- Phase 1 can proceed with test sources; real ingestion awaits approval.
- **Pending task:** Complete source-review task to select, verify, and approve initial companies.

**Unresolved:**
- Actual list of initial companies and sources (pending source-review task).
- Ownership of source selection and approval process.
- Criteria for "Tier-2/3 presence" (geographic definition).
- Legal review ownership and timeline.
- Per-source fetch method and verification status (to be documented for each source after review).

---

### Decision 11: Free-Tier Quota Semantics
**Status:** Proposed (explicitly unresolved items require approval)

**Topic:** Meaning of free-tier quota, counting rules, reset period, and behavior on exhaustion.

**Final Decision:**
- Quota definition: Unit = number of matched jobs viewed per day (NOT application clicks).
- Reset period: daily (reset timezone EXPLICITLY UNRESOLVED - awaiting approval).
- Boundary: per user account.
- What counts as one match: Viewing a job in the matched feed counts toward quota; repeated views of the same job: counting rule EXPLICITLY UNRESOLVED (requires approval); failed requests or errors do not count; concurrent requests: use atomic counter to avoid double-counting.
- Quota exhaustion: When quota exhausted: block new match views; display upgrade prompt; allow viewing non-matched jobs (if applicable); upgrade to paid tier resets quota.
- Free-tier limits (explicitly unresolved - awaiting approval): Exact daily match limit EXPLICITLY UNRESOLVED (requires approval); reset timezone EXPLICITLY UNRESOLVED (requires approval); repeat-view rule EXPLICITLY UNRESOLVED (requires approval); basic matching (already included).
- Quota enforcement: Atomic counter in Redis with DB fallback; rate limiting at application level; consistent across retries and concurrent requests.

**Reasoning:**
- Daily match counter from Playbook (not monthly application clicks).
- Match views are the meaningful action to count (not applications).
- Daily reset is simple and predictable (timezone TBD).
- Atomic counting prevents quota evasion via concurrent requests.
- Exact values intentionally left unresolved for stakeholder approval.

**Alternatives Considered:**
- Count application clicks instead of match views: Rejected (Playbook specifies match counter).
- Rolling 30-day window: Rejected as it's more complex to implement.
- No quota enforcement: Rejected as it prevents monetization.

**Consequences:**
- Subscription table (deferred to paid tier implementation).
- Match view tracking (not application clicks).
- Atomic counter for quota usage.
- Middleware or service layer for quota enforcement.
- Rate limiting at application level.

**Unresolved (Explicitly Awaiting Approval):**
- Exact daily match limit (number).
- Reset timezone (UTC, IST, or user's timezone).
- Whether to count repeated views of same job per day (yes/no with deduplication rule).

---

## Summary of Decision Status

**Accepted:**
- Decision 1: Experience Matching
- Decision 3: TF-IDF Vocabulary and Vector Versioning (Fixed Vocabulary)
- Decision 4: Job Lifecycle and Staleness
- Decision 5: Stable Source Identity vs. Content Hash
- Decision 6: Celery Queues and Concurrency
- Decision 8: Cookie Authentication and CSRF

**Proposed (requires approval):**
- Decision 2: Base Match Score vs. Sponsored Boost (threshold requires approval)
- Decision 7: Scraping Source Legitimacy and Access Rules (requires legal review)
- Decision 9: Resume Consent, Retention, and Deletion (requires legal review)
- Decision 10: Initial Company and Source List (not a blocker for Phase 1)
- Decision 11: Free-Tier Quota Semantics (limit and timezone require approval)

---

## Phase 1 Scope Discrepancy (Unresolved)

**Issue:** Disagreement between approved Phase 1 scope and `docs/DB_SCHEMA.md` migration strategy.

**Approved Phase 1 Scope (from implementation prompt):**
- Includes 12 entities: User, CandidateProfile, Skill, CandidateSkill, WorkExperience, Company, IngestionSource, FetchRun, Job, JobSkill, MatchScore, ApplicationClick
- Explicitly excludes Subscription (deferred to Phase 3)

**DB_SCHEMA.md Migration Strategy (lines 726-738):**
- Phase 1: User, CandidateProfile, Skill, CandidateSkill, WorkExperience, Company, IngestionSource, FetchRun, Job, JobSkill (10 entities)
- Phase 2: MatchScore, ApplicationClick (2 entities)
- Phase 3: Subscription (future)

**Resolution Action Taken:**
- Implemented all 12 approved entities in Phase 1, including MatchScore and ApplicationClick
- Excluded Subscription as specified (deferred to Phase 3)
- This discrepancy remains unresolved and requires stakeholder decision

**Status:** Resolved - DB_SCHEMA.md migration strategy updated to reflect approved Phase 1 scope (12 entities including MatchScore and ApplicationClick).

---

## Phase 2A: Job Ingestion Pipeline Foundation

### Scraper Configuration Location
**Status:** Implemented

**Topic:** Where to store scraper class configuration.

**Final Decision:**
- Added `scraper_class` field (CharField, nullable, max_length=255) to `IngestionSource` model
- Scraper configuration lives at the source level, not company level
- This is appropriate because a company may have multiple sources (career page, ATS, API) with different scrapers
- Migration 0005_ingestionsource_scraper_class added the field

**Rationale:**
- Source-specific metadata belongs at the source level
- A company may have multiple sources requiring different scrapers
- Aligns with existing model structure where source-specific configuration lives

**Alternatives Considered:**
- Add to Company model: Rejected as a company may have multiple sources with different scrapers
- Separate configuration table: Rejected as overengineering for this phase

**Consequences:**
- New migration required and created
- Admin interface updated to include scraper_class in readonly fields
- Tests updated to include scraper_class in test fixtures

---

### Schema Field Nullability Adjustment
**Status:** Implemented

**Topic:** Adjusting Job model field nullability for optional fields.

**Final Decision:**
- Changed Job model fields to allow NULL: `requirements`, `location`, `remote_type`, `role_type`
- Previous definition used `blank=True` but not `null=True` for these fields
- Updated to `blank=True, null=True` to properly represent optional fields

**Rationale:**
- These fields are truly optional per the specification
- `blank=True` only affects form validation, not database constraints
- `null=True` allows database-level representation of missing values
- Prevents NOT NULL constraint failures during ingestion

**Alternatives Considered:**
- Keep as blank-only: Rejected as it causes NOT NULL constraint failures
- Use empty strings: Rejected as it conflates "not provided" with "explicitly empty"

**Consequences:**
- Migration 0006_alter_job_location_alter_job_remote_type_and_more created
- Ingestion pipeline updated to convert None to empty string for requirements before save
- Existing tests updated to use jobskill_set instead of skills accessor

---

### Scraper Registry Implementation
**Status:** Implemented

**Topic:** How to load and validate scraper classes.

**Final Decision:**
- Implemented `_ALLOWED_SCRAPERS` registry mapping class names to (module_path, class_name) tuples
- `load_scraper(scraper_class)` validates against registry before loading
- Registry stored as module-level dictionary for security (no arbitrary imports)
- Registry initialized with only FakeScraper for tests
- `register_scraper()` function provided for future real scraper registration

**Rationale:**
- Explicit whitelist prevents unsafe arbitrary imports
- Tuple format (module, class) clearer than full dotted path for class

---

## Phase 2B: First Real Company Scrapers

### Source Selection for Phase 2B
**Status:** Implemented

**Topic:** Selection of first real company job sources for Phase 2B implementation.

**Final Decision:**
- Selected 2 real company sources with publicly accessible JSON APIs
- Source 1: Stripe (Greenhouse ATS) - `https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true`
- Source 2: Spotify (Lever ATS) - `https://api.lever.co/v0/postings/spotify?mode=json`
- Third source deferred (2 sources is sufficient for Phase 2B per specification)

---

## Phase 2C: Reliable Automated Ingestion with Celery

### FetchRun Lifecycle States
**Status:** Implemented

**Topic:** Lifecycle states and counters for FetchRun to track ingestion execution.

**Final Decision:**
- Enhanced FetchRun model with proper lifecycle states: pending, running, succeeded, partially_succeeded, failed
- Added counters: jobs_fetched, jobs_parsed, jobs_created, jobs_updated, jobs_skipped, jobs_invalid
- Added retry tracking: retry_count, last_retry_at
- Removed obsolete fields: jobs_stale, jobs_closed (not used in Phase 2C)
- Added indexes: (source, started_at), (status, started_at) for efficient querying
- Terminal states (succeeded, partially_succeeded, failed) always set completed_at timestamp
- Error information stored in error_message field

**Rationale:**
- Clear lifecycle states enable monitoring and debugging
- Counters provide visibility into ingestion pipeline performance
- Retry tracking supports reliability improvements
- Indexes support operational queries (recent runs, failed runs per source)

**Alternatives Considered:**
- Keep original minimal FetchRun: Rejected as insufficient for monitoring
- Use separate logging table: Rejected as FetchRun is the right place for execution metadata

**Consequences:**
- Migration 0007 created to update FetchRun schema
- Admin interface updated to show new fields
- Celery tasks write state transitions and counters

---

### Celery Task Architecture
**Status:** Implemented

**Topic:** How Celery tasks orchestrate ingestion without duplicating business logic.

**Final Decision:**
- Created `ingest_source_task` as single orchestration task in `api/tasks.py`
- Task responsibilities: source validation, lock acquisition, pipeline execution, FetchRun lifecycle, error handling
- Business logic (parsing, normalization, validation, persistence) remains in existing pipeline modules
- Task delegates to `process_batch()` from ingestion pipeline
- Task handles lock acquisition/release, retry logic, and FetchRun state management
- Returns structured result dict with fetch_run_id and counts

**Rationale:**
- Separation of concerns: tasks orchestrate, pipeline processes
- Existing synchronous pipeline remains reusable for dry-run and manual commands
- No code duplication between task and command execution paths

**Alternatives Considered:**
- Move business logic into tasks: Rejected as it would duplicate code and break dry-run
- Create separate pipeline for Celery: Rejected as unnecessary complexity

**Consequences:**
- New `api/tasks.py` module with task orchestration
- `ingest_jobs` command continues to use synchronous pipeline
- Task and command share same `process_batch()` logic

---

### Distributed Locking Strategy
**Status:** Implemented

**Topic:** How to prevent concurrent ingestion for the same source across multiple workers.

**Final Decision:**
- Redis-based distributed locks using Redlock-style pattern with unique ownership tokens
- Lock key: `ingestion_lock:source:{source_id}`
- Lock lifetime: 3600 seconds (1 hour) by default
- Lock acquisition: `redis.set(key, unique_token, nx=True, ex=timeout)` - stores UUID token
- Lock release: Lua script for atomic compare-and-delete (verifies ownership before deletion)
- Functions: `acquire_source_lock()` returns token or None, `release_source_lock(token)` returns bool
- Lock acquisition failure: task ignores and exits (no retry)
- Lock release on error: always released in finally block with ownership verification
- Lock expiration: prevents deadlock if worker crashes
- Redis errors: raise `SourceLockError` for explicit handling

**Rationale:**
- Redis provides distributed coordination across workers
- Unique UUID token prevents one task from deleting another's lock after expiry
- Lua script ensures atomic compare-and-delete (safe release)
- 1-hour timeout covers normal ingestion plus retries
- Finally block ensures lock release even on errors
- Ownership verification prevents race conditions

**Alternatives Considered:**
- Blind key deletion: Rejected (unsafe, can delete another task's lock after expiry)
- Static lock value: Rejected (no ownership verification)
- Database-level lock: Rejected (doesn't work across workers with separate DB connections)
- Process-local lock: Rejected (doesn't prevent concurrent execution across workers)
- Celery's built-in lock: Not suitable for source-level locking (task-level only)
- Redis Redlock library: Rejected (additional dependency, overkill for single-source locks)

**Consequences:**
- Lock functions in `api/tasks.py`: `acquire_source_lock()`, `release_source_lock()`
- Task acquires lock before ingestion, releases in finally block
- Redis URL configurable via `REDIS_LOCK_URL` setting (defaults to CELERY_BROKER_URL)
- Lua script stored as constant for atomic operations

**Failure Modes:**
- Redis unavailable: lock acquisition raises `SourceLockError`, task skipped
- Lock expiration: if task runs >1 hour, lock auto-expires (next task can proceed)
- Worker crash: lock auto-expires after timeout
- Wrong token on release: Lua script returns 0, lock not deleted (safe)

---

### FetchRun Reuse Across Retries
**Status:** Implemented

**Topic:** How to prevent duplicate FetchRun records when Celery retries a task.

**Final Decision:**
- FetchRun created once per logical execution, reused across retries via `celery_task_id` lookup
- `_create_fetch_run()` queries for existing FetchRun with matching `celery_task_id` before creating new
- If existing FetchRun found, return it (reuse instead of duplicate)
- Retry count and timestamp updated in exception handler before retry
- Terminal states (succeeded, failed, partially_succeeded) written once at completion
- Lock release in finally block regardless of retry state

**Rationale:**
- Celery retries use the same task ID across attempts
- Reusing FetchRun provides single audit trail per logical execution
- Prevents duplicate records conflating attempts with executions
- Retry tracking in single record provides clear history

**Alternatives Considered:**
- Create new FetchRun on every retry: Rejected (duplicates audit trail, conflates attempts with executions)
- Use database transactions for uniqueness: Rejected (adds complexity, Celery async makes transactional guarantees difficult)
- No FetchRun for retries: Rejected (loses retry history)

**Consequences:**
- `_create_fetch_run()` now checks for existing FetchRun before creating
- FetchRun filtering by `celery_task_id` ensures reuse
- Retry count and timestamp updated in exception handler
- Test added to verify FetchRun reuse logic

**Failure Modes:**
- If task_id is not unique across executions (unlikely), retries could conflate different executions
- Worker crash without finally execution could leave FetchRun in 'running' state (mitigated by lock expiry)

---

### Retry Policy
**Status:** Implemented
**Status:** Implemented

**Topic:** When and how to retry failed ingestion tasks.

**Final Decision:**
- Transient errors: retry with exponential backoff, max 3 retries
- Transient error types: requests.Timeout, requests.ConnectionError, HTTP 429, HTTP 5xx, RedisError
- Non-transient errors: no retry, immediate failure
- Non-transient error types: HTTP 4xx (except 429), ValueError, invalid configuration, malformed data
- Retry backoff: exponential with jitter, max 600 seconds (10 minutes)
- Retry-After header: if HTTP 429 includes Retry-After, use that value
- Retry count tracked in FetchRun.retry_count and FetchRun.last_retry_at
- Max retries exceeded: mark FetchRun as failed with "Max retries exceeded" error

**Rationale:**
- Transient errors are worth retrying (network issues, rate limits)
- Non-transient errors indicate real problems (config, data)
- Bounded retries prevent infinite loops
- Exponential backoff reduces load on failing sources
- Retry-After respects server-provided guidance

**Alternatives Considered:**
- Retry all errors: Rejected as it wastes resources on permanent failures
- No retries: Rejected as transient errors are common
- Unlimited retries: Rejected as it causes infinite loops

**Consequences:**
- Task decorator: `@shared_task(max_retries=3, autoretry_for=(requests.Timeout, ...), retry_backoff=True, retry_backoff_max=600, retry_jitter=True)`
- `is_transient_error()` function classifies errors
- `get_retry_after_seconds()` extracts Retry-After header
- Task checks `self.request.retries` vs `self.max_retries` before retry

---

### Celery Beat Scheduling
**Status:** Implemented

**Topic:** How to schedule periodic ingestion for active sources.

**Final Decision:**
- Use django-celery-beat's DatabaseScheduler for dynamic scheduling
- Provide `sync_beat_schedule` management command to sync IngestionSource to PeriodicTask table
- Command reads active IngestionSource records and creates/updates PeriodicTask entries
- Schedule interval based on `IngestionSource.fetch_interval_hours`
- Schedule mapping: 1h → hourly crontab, 6h → every 6h crontab, 12h → every 12h crontab, 24h → daily crontab
- Custom intervals: use IntervalSchedule with seconds (interval_hours * 3600)
- Task routing: all ingestion tasks use `fetch_queue`
- Inactive sources: corresponding PeriodicTask entries disabled automatically
- Command supports `--dry-run` flag for preview
- Manual sync required when adding/modifying sources

**Rationale:**
- Database scheduler allows dynamic changes without code deployment
- Manual sync command provides explicit control and auditability
- Source-specific intervals respect rate limits and update frequency
- fetch_queue isolation allows separate worker concurrency settings
- Avoids startup dependency on database for schedule generation

**Alternatives Considered:**
- Hardcoded schedule in code: Rejected as requires deployment for changes
- Dynamic schedule generation in celery.py: Rejected (startup dependency on database, complex error handling)
- Signal-based auto-sync on IngestionSource save: Rejected (database writes trigger schedule changes, potential race conditions)
- Use cron on host: Rejected as it doesn't integrate with Celery
- Single queue for all tasks: Rejected as it prevents per-queue concurrency tuning

**Consequences:**
- New `api/management/commands/sync_beat_schedule.py` module
- `CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"` in base settings
- Worker command includes `-Q fetch_queue` to process ingestion tasks
- Django admin interface for PeriodicTask management
- Operator must run `python manage.py sync_beat_schedule` after source changes

**Deployment Requirement:**
- Single Beat process required (multiple Beats would create duplicate schedules)
- Run sync command on startup or after source configuration changes

---

### Spotify Request-Delay Enforcement
**Status:** Implemented

**Topic:** How to respect Spotify's crawl-delay requirement from robots.txt.

**Final Decision:**
- Detect Spotify sources by checking source name or scraper class for "spotify" or "lever"
- If detected, apply 1-second sleep before fetch
- Implementation: `time.sleep(1)` before `scraper.fetch()`
- Only applied to identified Spotify/Lever sources
- Not applied to other sources (no universal delay)

**Rationale:**
- Respects documented crawl-delay requirement
- Minimal impact on other sources
- Simple implementation without complex rate-limiting framework

**Alternatives Considered:**
- Universal 1-second delay for all sources: Rejected as unnecessary for sources without crawl-delay
- Sophisticated rate-limiting library: Rejected as overkill for Phase 2C
- Ignore crawl-delay: Rejected as it violates robots.txt

**Consequences:**
- Delay added in `ingest_source_task()` before fetch
- Sources without crawl-delay not affected
- Future phase may add per-source delay configuration

---

### Concurrency Configuration
**Status:** Implemented

**Topic:** Worker concurrency settings for Docker Compose.

**Final Decision:**
- Worker concurrency: `-c 2` (2 worker processes)
- Task limit per child: `--max-tasks-per-child=1000` (prevent memory leaks)
- Queue configuration: `-Q default,fetch_queue,parse_queue,match_queue`
- Concurrency aligns with Decision 6 (fetch_queue=2 proposed)
- Health check: `celery -A config inspect ping` every 30s

**Rationale:**
- Lower concurrency respects rate limits (fetch_queue specifically)
- max-tasks-per-child prevents long-running memory accumulation
- Health check enables Docker Compose restart on failure

**Alternatives Considered:**
- Default concurrency (CPU count): Rejected as too high for rate-limited fetching
- No max-tasks-per-child: Rejected as memory leaks accumulate over time
- No health check: Rejected as no recovery from worker crashes

**Consequences:**
- Docker Compose worker command updated with concurrency settings
- Health check enables orchestration-level recovery
- Note: parse_queue and match_queue not yet used (future phases)

---

### Operational Management Commands
**Status:** Implemented

**Topic:** Management commands for operational visibility and manual triggering.

**Final Decision:**
- `inspect_fetch_runs`: View recent FetchRun records with filtering
  - Options: `--source <id>`, `--status <status>`, `--limit <n>`
  - Displays: source, status, counters, error messages, timestamps
- `trigger_ingestion`: Manually trigger ingestion for a source via Celery
  - Option: `--source <id>` (required)
  - Returns: Celery task ID for tracking
- `ingest_jobs`: Retained with dry-run support
  - Updated to suggest `trigger_ingestion` for background execution

**Rationale:**
- Inspect command enables debugging and monitoring
- Trigger command supports manual ingestion without waiting for schedule
- Dry-run command remains for validation

**Alternatives Considered:**
- No manual commands: Rejected as operational need for manual triggers
- Web admin only: Rejected as CLI is faster for operations

**Consequences:**
- New management commands in `api/management/commands/`
- Commands respect concurrency protection (trigger uses same task)
- Dry-run continues to use synchronous pipeline
- Both sources have robots.txt permission and no authentication requirement
- Both sources provide stable JSON responses with application URLs

**Rationale:**
- Greenhouse and Lever are well-documented ATS ecosystems with public APIs
- Both require no authentication and allow robots.txt access
- Structured JSON responses simplify parsing and reduce errors
- Direct application URLs available in responses
- Good test coverage with fixture data possible

**Alternatives Considered:**
- Ashby ATS: Rejected due to robots.txt disallowing `/api/` path
- Workable ATS: Rejected due to restrictive rate limit (8 requests in 40 seconds)
- Additional Greenhouse or Lever boards: Deferred to future phases (2 sources sufficient for MVP)

**Consequences:**
- `GreenhouseStripeScraper` class implemented in `api/ingestion/scrapers/greenhouse_stripe.py`
- `LeverSpotifyScraper` class implemented in `api/ingestion/scrapers/lever_spotify.py`
- Both scrapers registered in `_ALLOWED_SCRAPERS` registry
- Fixture data saved under `backend/api/tests/fixtures/ingestion/`
- Source research documented in `docs/INGESTION_SOURCES.md`

---

### HTTP Client Implementation
**Status:** Implemented

**Topic:** HTTP client library and configuration for scrapers.

**Final Decision:**
- Use `requests` library for HTTP client (already in pyproject.toml dependencies)
- Explicit connection and read timeouts: (10, 30) seconds
- Descriptive User-Agent header: "MatchHire-Ingestion/1.0 (+https://github.com/Namraa310806/MatchHire)"
- Use requests.Session for connection pooling
- Handle HTTP failures explicitly with exception types
- Handle invalid JSON with JSONDecodeError

**Rationale:**
- `requests` is already listed in Phase 0 decision 7 as the HTTP library
- Explicit timeouts prevent hanging requests
- Descriptive User-Agent allows source identification
- Session object provides connection pooling for efficiency

**Alternatives Considered:**
- Playwright: Rejected for JSON APIs (overkill for simple HTTP requests)
- Custom HTTP client: Rejected as requests is well-tested and maintained

**Consequences:**
- Added `requests>=2.31.0` to pyproject.toml dependencies
- Both scrapers use requests.Session internally
- Tests mock session.get() for offline testing

---

### Dry-Run Management Command
**Status:** Implemented

**Topic:** Django management command for job ingestion with dry-run support.

**Final Decision:**
- Implemented `python manage.py ingest_jobs --source <source-name> --dry-run`
- Command loads IngestionSource by name
- Resolves scraper through registry
- Fetches, parses, normalizes, validates records
- Displays summary of what would be created/updated/skipped
- `--dry-run` flag skips persistence stage entirely
- Dry-run verification compares job count before and after to ensure no writes occurred
- Real ingestion requires explicit invocation (no --dry-run flag)

**Rationale:**
- Dry-run allows previewing ingestion without side effects
- Verification step ensures dry-run guarantee is maintained
- Command-line interface consistent with Django conventions
- Summary output provides clear visibility into ingestion results

**Alternatives Considered:**
- No dry-run mode: Rejected as it prevents safe testing
- Always dry-run by default: Rejected as it requires explicit flag for real ingestion
- Separate command for dry-run: Rejected as single command with flag is simpler

**Consequences:**
- Management command created at `api/management/commands/ingest_jobs.py`
- Pipeline updated with `dry_run` parameter to skip persistence
- Management directory structure created
- Command reports job count before/after for verification

---

### Fixture Data Organization
**Status:** Implemented

**Topic:** Organization and structure of test fixture data.

**Final Decision:**
- Fixtures stored under `backend/api/tests/fixtures/ingestion/`
- Sample fixtures: `stripe_greenhouse_sample.json`, `spotify_lever_sample.json`
- Fixtures contain realistic sanitized job data (2-3 jobs each)
- Fixtures exclude credentials, cookies, personal data
- Tests use fixtures with mocked HTTP responses
- Tests do not depend on live network availability

**Rationale:**
- Sanitized fixtures enable offline testing
- Separate fixture files per source keeps organization clear
- No credentials or sensitive data in fixtures prevents security issues
- Mocked HTTP responses ensure test reliability and speed

**Alternatives Considered:**
- Live network tests: Rejected as they make tests flaky and slow
- Full response fixtures: Rejected as they may contain unnecessary data
- No fixtures (only live tests): Rejected as it prevents offline testing

**Consequences:**
- Fixture directory structure created
- 39 new tests added (18 for Greenhouse, 21 for Lever)
- All tests pass (170 total: 131 Phase 2A + 39 Phase 2B)
- Tests use unittest.mock.patch for HTTP mocking

---

### Source-Specific Test Coverage
**Status:** Implemented

**Topic:** Test coverage for real scrapers.

**Final Decision:**
- Source-specific test files: `test_greenhouse_stripe.py`, `test_lever_spotify.py`
- Tests cover: fetch, parse, validate, error handling, edge cases
- Tests use fixtures and mocked HTTP responses
- Tests verify: HTML unescaping, date parsing, remote type detection, salary extraction
- Tests verify: missing required fields, invalid JSON, HTTP errors
- All Phase 2A tests remain passing (no regressions)

**Rationale:**
- Source-specific tests isolate scraper logic
- Comprehensive coverage ensures reliability
- Fixture-based tests are fast and deterministic
- Edge case testing prevents production issues

**Alternatives Considered:**
- Generic scraper tests only: Rejected as they wouldn't test source-specific logic
- Integration tests with live endpoints: Rejected as they're flaky and require network

**Consequences:**
- 39 new tests added (Phase 2B)
- All 170 tests pass (131 Phase 2A + 39 Phase 2B)
- Ruff linting passes with fixes
- MyPy type checking passes with fixes
- Django system check passes

---

### Application URL Verification
**Status:** Verified

**Topic:** Manual verification of application URLs from fixtures.

**Final Decision:**
- Verified 3 application URLs manually (2 Stripe, 1 Spotify)
- All URLs open to valid job pages with correct titles and descriptions
- Stripe URLs: https://stripe.com/jobs/search?gh_jid=8172510 (Abuse Investigator), https://stripe.com/jobs/search?gh_jid=8265686 (Writer, Content Marketing)
- Spotify URL: https://jobs.lever.co/spotify/2a55d6c9-c564-443a-be3e-a3851db5a93b (Account Executive - Commercial)
- Verification date: 2026-11-03
- No fabricated URLs; all from actual fixture data

**Rationale:**
- Manual verification ensures application URLs are functional
- Confirms scraper correctly extracts and stores application URLs
- Prevents broken application links in production

**Alternatives Considered:**
- Skip verification: Rejected as broken URLs would be a critical failure
- Automated verification: Deferred as manual verification sufficient for Phase 2B

**Consequences:**
- Application URLs verified as working
- Scraper URL extraction logic validated
- Documentation updated with verification results

---

## Phase 2B Summary

**Implemented:**
- 2 real company scrapers (Stripe/Greenhouse, Spotify/Lever)
- Scraper registry updated with real scrapers
- 39 new tests with fixtures and mocked HTTP
- Dry-run management command with verification
- Source research documented in INGESTION_SOURCES.md
- Application URLs manually verified
- All quality checks passing (ruff, mypy, Django check)

**Not Implemented (Per Phase 2B Scope):**
- Third source (2 sources sufficient per specification)
- Celery scheduling
- Celery Beat
- Automatic recurring fetches
- Retry orchestration
- Playwright/browser automation
- Matching algorithms
- Resume parsing
- Frontend work
- Recruiter functionality
- Payments or subscriptions

**Test Results:**
- Command: `uv run pytest api/tests/test_ingestion/ -v`
- Result: 170 passed in 1.66s (131 Phase 2A + 39 Phase 2B)
- Exit code: 0

**Quality Checks:**
- Ruff: All checks passed
- MyPy: Success: no issues found in 47 source files
- Django check: System check identified no issues (0 silenced)

**Git Status:**
- Branch: main
- Working tree: Uncommitted changes (Phase 2B implementation)
- Latest commit: 9d2e824 phase2a: implement job ingestion pipeline foundation
- Fail-fast validation for unknown or invalid scrapers
- Registry can be extended in future phases without code changes

**Alternatives Considered:**
- Direct import based on string: Rejected as security risk (arbitrary imports)
- Dynamic class loading from plugin system: Rejected as overengineering for this phase
- Configuration file for scrapers: Rejected as database field is sufficient

**Consequences:**
- Registry is module-level state (shared across application)
- Only FakeScraper registered in Phase 2A
- Real scrapers will be registered in future phases

---

### Required Years of Experience Mapping
**Status:** Implemented

**Topic:** How extracted `required_yoe` maps to Job model fields.

**Final Decision:**
- `required_yoe` from extraction is mapped to `experience_min_years` in Job model
- If `experience_min_years` is already set in the record, it takes precedence
- If `experience_min_years` is None but `required_yoe` is set, use `required_yoe`
- `experience_max_years` is not populated from extraction (ranges not extracted in Phase 2A)

**Rationale:**
- Job model has `experience_min_years` and `experience_max_years` for ranges
- Extraction produces a single value (`required_yoe`)
- Mapping to `experience_min_years` is the natural fit for "minimum required"
- Allows explicit record-level values to override extraction

**Alternatives Considered:**
- Store as separate field: Rejected as Job model already has experience fields
- Ignore extraction result for persistence: Rejected as it loses extracted data
- Store in both min and max: Rejected as extraction doesn't produce ranges

**Consequences:**
- Extraction result used in persistence via mapping
- Test for experience extraction updated to check `experience_min_years`
- Future phases may add range extraction for `experience_max_years`

---

### Skill Dictionary Scope
**Status:** Implemented

**Topic:** Size and composition of skills dictionary for Phase 2A.

**Final Decision:**
- Implemented representative skills dictionary with ~30 terms
- Covers programming languages, frameworks, tools, and platforms
- Includes canonical names and aliases (e.g., "js" → "JavaScript", "k8s" → "Kubernetes")
- Dictionary is replaceable (not hardcoded in extraction logic)
- Designed for expansion to 500+ terms in production per Decision 3

**Rationale:**
- Representative subset sufficient for Phase 2A testing
- Demonstrates the pattern without implementing full vocabulary
- Future migration can expand to full 500+ term vocabulary
- Replaceable design allows vocabulary updates without code changes

**Alternatives Considered:**
- Implement full 500+ term vocabulary: Rejected as outside Phase 2A scope
- Use no skills dictionary: Rejected as it doesn't demonstrate the pattern
- Hardcode in extraction logic: Rejected as it prevents vocabulary updates

**Consequences:**
- Skills extraction works with subset for testing
- Future vocabulary expansion will be migration-based
- Dictionary is in `skill_extraction.py` for easy replacement

---

### Description Length Limit
**Status:** Implemented

**Topic:** Maximum description length for normalization.

**Final Decision:**
- Set `MAX_DESCRIPTION_LENGTH = 50000` characters in normalization
- Descriptions exceeding this limit are rejected with ValueError
- Limit chosen based on practical considerations (not from schema)

**Rationale:**
- Prevents abusive or malformed records from consuming excessive storage
- 50k characters is generous (approximately 10k words)
- Schema TextField has no hard limit, but application-level validation is prudent
- Rejects obviously oversized descriptions early in pipeline

**Alternatives Considered:**
- No limit: Rejected as it doesn't prevent abuse
- Schema-level limit: Rejected as TextField doesn't support max_length
- Much smaller limit (e.g., 10k): Rejected as too restrictive for legitimate long descriptions

**Consequences:**
- Normalization rejects oversized descriptions
- Validation error reported to caller
- Configurable constant for future adjustment

---

### Shared Scraper Parsing-Error Contract
**Status:** Implemented

**Topic:** How scrapers report parsing errors to the ingestion pipeline.

**Final Decision:**
- Base class contract: `BaseJobScraper` provides shared error-reporting mechanism
- Error representation: List of tuples `(raw_record: dict, error_msg: str)` stored in `parse_errors` attribute
- Error collection: Each scraper initializes with empty `parse_errors` list via `__init__()`
- Error recording: Scrapers use `_record_parse_error(raw_record, error_msg)` helper method
- Error lifecycle: Each `parse()` invocation must call `_clear_parse_errors()` at start to prevent error leakage between batches
- Pipeline consumption: Pipeline reads `scraper.parse_errors` directly (no `hasattr` check needed - it's guaranteed by base class)
- Public signature unchanged: `parse(raw: list[dict]) -> list[JobRecord]` - error reporting is side-channel, not part of return value
- Malformed record handling: Scrapers catch exceptions per-record, record error via base helper, and continue parsing remaining records
- Valid records continue: Records that parse successfully continue through the pipeline even when other records in the same batch fail
- Error attribution: Each error includes the original raw input for debugging and attribution

**Rationale:**
- Formalizing the contract in the base class ensures all scrapers (including future production scrapers) implement error reporting consistently
- Base class initialization guarantees `parse_errors` attribute exists for all scraper instances
- Explicit `_clear_parse_errors()` prevents error leakage between parse invocations
- Helper method `_record_parse_error()` provides consistent error format
- Removing `hasattr` check from pipeline eliminates FakeScraper-specific assumptions
- Side-channel error reporting keeps the public signature simple (returns only valid records)

**Alternatives Considered:**
- Return errors from parse() method: Rejected as it would complicate the public signature and require handling errors in every caller
- Use exceptions for errors: Rejected as exceptions would stop parsing of remaining records in the batch
- Log errors only: Rejected as it loses attribution and makes debugging difficult
- FakeScraper-specific implementation: Rejected as production scrapers wouldn't know to implement it

**Consequences:**
- All scrapers must call `_clear_parse_errors()` at start of `parse()`
- All scrapers must use `_record_parse_error()` for parsing failures
- Pipeline reads `scraper.parse_errors` without `hasattr` check
- Errors are guaranteed to be available for any BaseJobScraper implementation
- Test added using SimpleTestScraper (independent of FakeScraper) to verify contract
