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
