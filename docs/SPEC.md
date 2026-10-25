# MatchHire Product Specification

## Document Purpose

This is the authoritative, implementation-ready specification for MatchHire. All product requirements, workflows, and acceptance criteria are defined here. Where this specification is silent or ambiguous, decisions must be recorded in `docs/DECISIONS.md` before implementation.

## Product Purpose

MatchHire is a candidate-first job aggregation and matching platform focused on freshers in India's Tier-2 and Tier-3 cities. The platform automatically fetches job listings from official company sources, matches them to user profiles, and provides a curated feed of relevant opportunities.

**Core Invariant:** Jobs enter the system ONLY through automated fetchers from official company sources. No human, user, or admin can create jobs manually.

## Target Users

**Primary Target:**
- Fresh graduates (0-2 years experience) in India's Tier-2 and Tier-3 cities
- Candidates seeking their first or early-career opportunities
- Users who may have limited access to established job platforms or recruitment networks

**Explicitly Out of Scope:**
- Recruiters or HR professionals
- Company dashboards or employer-facing interfaces
- Recruiter job-posting workflows
- Applicant Tracking System (ATS) integrations
- Experienced professionals (>2 years) as primary audience

## MVP Scope

The MVP focuses on:

1. **Automated Job Ingestion:** Fetch job listings from approved company career pages
2. **Candidate Profiles:** Capture skills, experience, and preferences
3. **Matching:** Match candidates to jobs based on relevance (TF-IDF initially)
4. **Candidate Feed:** Display matched jobs to candidates
5. **Job Application Tracking:** Record when candidates click to apply

**Explicitly Out of MVP:**
- Resume parsing
- Skill extraction from resumes
- Message/communication features
- Company management interfaces
- Advanced semantic matching (sentence-transformers deferred)
- Mobile applications (web-only initially)

## Candidate-First Workflows

### Registration and Profile Creation

**Workflow:**
1. Candidate registers with email and password
2. Completes profile with:
   - Education details
   - Skills (from a predefined or open set)
   - Work experience (if any)
   - Job preferences (location, role type, expected salary)
3. Optional: Upload resume for future use (not parsed in MVP)

**Profile Requirements:**
- Email authentication required
- Profile can be incomplete but matching quality improves with more data
- **Skills:** Candidates enter skills as free-text; system normalizes to canonical names from fixed 500+ term vocabulary; unknown skills are logged but not used for matching (fixed vocabulary decision)
- Experience measured in years; zero is valid

### Job Discovery

**Workflow:**
1. Candidate views personalized job feed based on profile match scores
2. Jobs are ranked by relevance, with sponsored jobs boosted
3. Candidate can filter by location, role type, experience level
4. Candidate can view job details (description, requirements, company, application link)

**Feed Behavior:**
- Only active, non-stale jobs appear
- Jobs are sorted by final score (base relevance + sponsored boost)
- Sponsored jobs are marked as such
- Candidate cannot create jobs

### Application Flow

**Workflow:**
1. Candidate clicks "Apply" on a job
2. System records the application click with timestamp
3. Candidate is redirected to the original company application URL
4. System tracks application for analytics and potential follow-up

**Invariants:**
- MatchHire does not host the application form
- Application happens on the company's own system
- MatchHire only records the click and redirects

## Job Ingestion and Source Trust

### Source Approval Policy

**Core Rule:** Jobs are ingested ONLY from approved, automated sources.

**Source Types:**
- Official company career pages
- Company ATS (where accessible without authentication)
- Government job portals (future)
- Approved aggregator APIs (future)

**Source Requirements:**
- Must be publicly accessible without authentication
- Must respect robots.txt and rate limits
- Must not require CAPTCHA solving or bypassing anti-bot protections
- Must not violate terms of service
- Legal review required for gray-area sources

**Approval Process:**
- Sources proposed based on company list (pending source-review task)
- Legal/policy review for terms and access restrictions
- Technical feasibility assessment (scrapability, rate limits)
- Approved sources added to configuration
- **Important:** No source is marked as approved until the source-review task is completed; sources are candidates for approval, not pre-approved

### Ingestion Pipeline

**Stages:**
1. **Fetch:** Retrieve job listings from source at scheduled intervals
2. **Parse:** Extract structured data (title, description, requirements, location, etc.)
3. **Deduplicate:** Identify existing jobs vs. new listings
4. **Store:** Persist job records with source metadata
5. **Match:** Trigger matching for affected candidates

**Automation:**
- Scheduled via Celery Beat
- Each source has its own fetch schedule
- Failed fetches are retried with exponential backoff
- Multiple consecutive failures trigger alerts

### Scraping Libraries (Decision 7)

**MVP Stack Decision:**
- **requests** for HTTP requests to public JSON APIs and simple HTML pages
- **Playwright** for JavaScript-rendered portals (headless Chromium)
- **Scrapy:** NOT in MVP stack (rejected due to complexity; Playwright chosen for JS rendering)

**Rationale:**
- requests is sufficient for public JSON APIs and static HTML
- Playwright handles JS-rendered pages that requests cannot
- Scrapy would add complexity without clear benefit for MVP scale
- Can add Scrapy later if performance becomes an issue

**Library Usage:**
- requests: default for all HTTP requests
- Playwright: opt-in for sources requiring JS rendering
- BeautifulSoup4: HTML parsing (via requests)
- lxml: XML/HTML parsing (via requests)

**Source Classification:**
- Public JSON API: use requests
- Static HTML: use requests + BeautifulSoup4
- JS-rendered: use Playwright (marked in source configuration)

**Verification:**
- Each source must be verified before scraper implementation
- Check robots.txt, terms of service, rate limits
- Test endpoint response structure before building scraper
- Document verification status per source

### Source Trust and Identity

**Stable Source Identity:**
- Each job must have a stable identifier from the source (job ID, slug, or URL)
- Source ID + external ID uniquely identifies a job
- If source provides no ID, use URL as fallback
- If neither available, use content hash (last resort, higher false-positive risk)

**Content Hash:**
- Used to detect changes in job content
- Not used as primary identity
- Content changes trigger job updates, not duplicate creation

**job_hash Definition:**
- Computed from normalized fields: title, description, location, required_skills, required_yoe
- Normalization: lowercase, trim whitespace, normalize HTML entities
- Used for content-change detection, not as primary identity
- Hash algorithm: SHA-256 (standard, collision-resistant)
- Stored in Job.job_hash field

**Content Change Handling:**
- When job's content changes but source ID is the same: UPDATE existing row
- Update: title, description, location, required_skills, required_yoe, job_hash, last_seen_at
- Do NOT create a new row
- Invalidate cached match scores for this job
- Trigger re-matching for affected candidates

**Identity Failures:**
- If identity cannot be established reliably, mark job for manual review
- Do not create duplicate jobs due to identity ambiguity

## Job Lifecycle and Stale-Job Handling

### Lifecycle States

1. **Active (is_active=True):** Job visible in candidate feeds, apply link is live
2. **Inactive (is_active=False):** Job hidden from feeds, apply link disabled
3. **Archived:** Historical record, never visible (optional, for audit)

### State Transitions

**First Ingestion:**
- New job → Active (is_active=True, immediately visible)

**Subsequent Refreshes:**
- Job found in source with same ID → Update content, remain Active, update last_seen_at
- Job found with different content → Update content, remain Active, update last_seen_at, update job_hash
- Job missing from source during a SUCCESSFUL fetch → increment consecutive_misses counter

**Deactivation Rule:**
- Job becomes inactive (is_active=False) after N consecutive SUCCESSFUL fetches in which the job is absent
- Failed or partial fetch runs MUST NOT count as evidence of disappearance
- A broken scraper must not mass-close jobs
- Default threshold N=3 (configurable per source)

**Failed Fetch Handling:**
- Failed fetch (source unreachable, network error, 5xx, timeout): does NOT increment consecutive_misses
- Partial fetch (some jobs fetched, others failed): does NOT increment consecutive_misses for missing jobs
- Only a successful fetch where the job is absent counts as evidence of disappearance

**Safety Valve (Proposed - Awaiting Approval):**
- If a single run would deactivate more than X% of a company's jobs, skip deactivation and raise an alert
- Proposed X=20% (EXPLICITLY UNRESOLVED - requires approval)
- Prevents mass closure due to scraper bugs or source changes

**Reactivation:**
- Inactive job reappears in source → Transition back to Active (is_active=True)
- Reset consecutive_misses to 0
- Requires source ID match
- Should be rare; treat as potential data quality issue

**apply_url Behavior:**
- For Active jobs: apply link is live and redirects to company's application URL
- For Inactive jobs: apply link is disabled; API returns error for apply endpoint
- Lightweight periodic HEAD/GET check on apply_url sample (optional, not in MVP)

**Cache Invalidation:**
- When job becomes inactive: invalidate cached match scores for this job
- When job reactivates: trigger re-matching for affected candidates
- When job content changes: invalidate cached match scores for this job

### Stale Thresholds

**Default Configuration:**
- Deactivate after N=3 consecutive successful fetches where job is absent
- Fetch interval per source (e.g., daily, weekly)
- Safety valve: deactivate max 20% of company's jobs per run (proposed, requires approval)

**Source-Specific Overrides:**
- High-velocity sources (daily updates): shorter thresholds possible
- Low-velocity sources (monthly updates): longer thresholds possible
- Configured in Company or IngestionSource model

## Candidate Profiles

### Profile Data

**Core Fields:**
- User account (email, password, auth)
- Education: degree, institution, graduation year
- Skills: list of skills with proficiency (optional)
- Experience: total years, individual entries
- Preferences: location, role type, salary range, remote preference

**Optional Fields:**
- Resume file (for future parsing)
- Portfolio links
- Social profiles (LinkedIn, GitHub)
- Bio/introduction

### Skills

**Skill Representation (Decision 3):**
- **Candidate-facing input:** Free-text entry for flexibility
- **Internal representation:** Normalized to canonical names from fixed 500+ term vocabulary
- **Normalization:** Case-insensitive, trimmed whitespace, mapped to canonical names via aliases (e.g., "js" → "JavaScript", "k8s" → "Kubernetes")
- **Unknown skills:** Skills not in vocabulary are logged but excluded from TF-IDF matching (no dynamic vocabulary expansion in MVP)
- **Duplicate skills:** Duplicates after normalization are removed (candidate cannot list "JavaScript" and "js" as separate skills)
- **Fixed vocabulary:** Vocabulary derived from skills dictionary; shared with future resume extraction; no automatic updates; changes require explicit migration

**Proficiency:**
- Optional for MVP
- Could be: beginner, intermediate, advanced
- Affects match score weighting (if implemented)

### Experience

**Experience Measurement:**
- Total years (float or integer)
- Individual entries: role, company, duration, description
- Zero years is valid (freshers)
- Missing experience means unknown (not zero)

**Experience Semantics:**
- Distinguish "0 years" (explicitly fresher) from "unknown" (not provided)
- "Unknown" should not disqualify from matching
- Explicit "0 years" may affect certain eligibility rules

### Preferences

**Preference Types:**
- Location: city, state, or "remote"
- Role type: full-time, internship, contract
- Salary range: min, max, currency
- Remote preference: on-site, remote, hybrid, any

**Matching Impact:**
- Location mismatch may reduce score
- Salary below candidate minimum may reduce score
- Preferences are soft constraints, not hard filters

## Match-Score Semantics

### Base Match Score

**Purpose:**
- Quantify relevance of a job to a candidate
- Range: 0.0 to 1.0 (or 0-100, decision required)
- Computed from TF-IDF similarity in MVP

**Components (MVP):**
- Skills overlap: TF-IDF cosine similarity between job requirements and candidate skills
- Experience match: candidate experience meets job requirements
- Location match: candidate location preference alignment
- (Future: semantic similarity, resume parsing, behavior signals)

**Interpretation:**
- Higher score = more relevant
- 0.0 = no relevance
- 1.0 = perfect match
- Displayed to candidates as "match percentage"

### Experience Matching (Decision 1)

**Match Score Formula:**
```
match_score = 0.50 * skill_similarity + 0.30 * experience_match + 0.20 * keyword_overlap
```

**Experience Match Rules:**

**Job Specifies Zero Years (required_yoe = 0):**
- Score = 1.0 (full match) for any candidate experience
- Explicit "0 years required" or "fresher" in job
- Does not penalize candidates with experience
- Unknown candidate experience (user_yoe = null): score = 1.0 (treated as meeting requirement)
- Example: Job requires 0 years, candidate has 0 years → score = 1.0
- Example: Job requires 0 years, candidate has 5 years → score = 1.0
- Example: Job requires 0 years, candidate has null years → score = 1.0

**Job Requires Positive Minimum (required_yoe > 0):**
- Formula: `min(user_yoe / required_yoe, 1.0)` when user_yoe is known and not null
- Candidate experience >= minimum: score = 1.0 (capped)
- Candidate experience < minimum: partial credit = user_yoe / required_yoe
- Unknown candidate experience (user_yoe = null): score = 0.0 (assume not qualified)
- Example: Job requires 2 years, candidate has 2 years → score = 1.0
- Example: Job requires 2 years, candidate has 5 years → score = 1.0 (capped)
- Example: Job requires 2 years, candidate has 1 year → score = 0.5
- Example: Job requires 2 years, candidate has null years → score = 0.0

**Job Specifies Range (e.g., "0-2 years", "2-5 years"):**
- If range includes 0 (e.g., "0-2 years"): treat minimum as 0 (score = 1.0 for all)
- If range excludes 0 (e.g., "2-5 years"): use minimum value (2) in formula
- Candidate within range: score = 1.0
- Candidate below range: partial credit using minimum of range
- Candidate above range: score = 1.0 (overqualification not penalized)
- Unknown candidate experience (user_yoe = null): score = 0.0 unless range includes 0
- Example: Job specifies "0-2 years", candidate has 1 year → score = 1.0
- Example: Job specifies "0-2 years", candidate has 5 years → score = 1.0
- Example: Job specifies "2-5 years", candidate has 1 year → score = 0.5
- Example: Job specifies "2-5 years", candidate has null years → score = 0.0

**Experience Missing or Unknown from Job:**
- Job has no experience requirement: treat as required_yoe = 0 (score = 1.0 for all)
- Candidate experience unknown (user_yoe = null): score = 1.0 (meets "no requirement" rule)

**Division by Zero Protection:**
- When required_yoe = 0: experience_match = 1.0 (no division performed)
- When user_yoe is null: experience_match = 0.0 (unless required_yoe = 0, then 1.0)
- Formula only applied when both required_yoe > 0 and user_yoe is not null

### Sponsored Job Behavior (Decision 2)

**Sponsorship Concept:**
- Companies can pay to boost job visibility
- Sponsorship is separate from relevance
- Does not affect the base match score

**Score Units:**
- Store match scores as floats in [0.0, 1.0] internally
- Convert to percentages only at the API boundary for display
- Base relevance score and final ranking score both in [0.0, 1.0]

**Ranking Behavior:**
- Compute base relevance score for all jobs (0.0 to 1.0)
- Apply sponsored boost to final ranking score only
- Sponsored jobs appear higher in feed, even with lower relevance
- Original base relevance score remains available for display

**Boost Mechanism:**
- Boost range: configurable 0.0 to 0.15 (maximum boost)
- Boost applies only when base score exceeds threshold (threshold TBD - awaiting approval)
- Proposed threshold: base score > 0.40 (requires approval)
- Final score = base_score + boost (capped at 1.0)
- Boost is configurable per job or sponsorship tier
- Multiple sponsored jobs ranked by base score among themselves

**Transparency:**
- Sponsored jobs clearly marked in UI with is_sponsored flag
- Base relevance score displayed separately as match percentage
- Final ranking score used for sorting, not displayed
- Candidates can see the match score is organic

**Tie Handling:**
- Jobs with same final score: sort by posted date (newest first)
- Sponsored ties: sort by sponsorship tier, then base score, then date

**Invariants:**
- Sponsorship cannot fabricate a better relevance score
- Base score remains true to candidate-job compatibility
- No hidden manipulation of ranking
- Boost cannot create matches below the threshold

### TF-IDF Vocabulary and Vector Versioning (Decision 3)

**Strategy Decision: Fixed Vocabulary**

**Choice:** Use a fixed vocabulary for the MVP TF-IDF implementation.

**Rationale:**
- Precomputed job vectors never go stale with a fixed vocabulary
- Simpler architecture: no version management, no re-matching needed
- Vocabulary derived from the 500+ term skills dictionary (shared with resume extraction)
- Ensures compatibility between job vectors and user vectors over time
- Eliminates complexity of vector staleness detection and regeneration

**Vocabulary Source:**
- Fixed skills dictionary with 500+ terms (canonical names + aliases)
- Canonical name + category per skill
- Aliases mapped to canonical names (e.g., "js" → "JavaScript", "k8s" → "Kubernetes")
- Vocabulary built once from this dictionary at system initialization
- No automatic vocabulary updates without explicit migration

**Initial Vocabulary Creation:**
- Use the skills dictionary as the fixed vocabulary
- Build TF-IDF vectorizer using scikit-learn with this vocabulary
- Include unigrams (single terms) from the dictionary
- Stopwords removed (English + technical stopwords)
- No lemmatization or stemming (rely on dictionary aliases)

**Persistence:**
- Vectorizer saved as pickle or joblib file
- Stored in local filesystem (or S3 in production)
- No versioning needed (fixed vocabulary)
- Metadata: creation date, vocabulary size, dictionary version

**Loading:**
- At startup, load the vectorizer with fixed vocabulary
- No fallback mechanism (vocabulary is stable)
- If vectorizer fails to load, system fails fast (critical dependency)

**Vector Computation:**
- Job vectors precomputed at ingestion time using fixed vocabulary
- User vectors computed on profile change using same fixed vocabulary
- **Consistency guarantee:** Both vectors use the same fixed vocabulary, same preprocessing (lowercase, trim, normalize HTML entities), and same feature ordering (alphabetical by canonical skill name)
- Compatibility guaranteed: same vocabulary, preprocessing, and ordering for both
- No stale vector detection needed (vocabulary never changes)

**Vocabulary Updates (Future):**
- Vocabulary changes require explicit migration
- Process: update skills dictionary → recompute all job vectors → recompute all user vectors
- Not automated in MVP; manual migration with downtime
- Alternative (post-MVP): versioned vectors if vocabulary volatility becomes a problem

**Model-Score Association:**
- MatchScore table does NOT need vectorizer_version field (fixed vocabulary)
- Scores remain valid indefinitely
- No re-matching on vocabulary changes (vocabulary doesn't change)

**Alternatives Considered and Rejected:**
- Versioned vectors: Rejected for MVP due to complexity (stale detection, re-matching, compatibility management)
- Dynamic vocabulary: Rejected as it would make precomputed job vectors stale

**Consequences:**
- Skills dictionary is critical; changes require migration
- Vocabulary cannot evolve automatically
- Simpler architecture for MVP
- Post-MVP may need versioned vectors if vocabulary volatility is high

## Authentication, Authorization, and API Security

### Authentication Model

**Candidate Authentication:**
- Email + password registration
- **Primary transport:** httpOnly, Secure, SameSite cookies for browser clients
- **Token format:** JWT (access token + refresh token)
- Access token: 15 minute expiration
- Refresh token: 7 day expiration with rotation
- Tokens delivered in cookies, never in JSON body for browser clients
- Password reset via email (MVP may defer)

**Bearer Authentication:**
- **Allowed only for non-browser clients** (mobile apps, CLI tools, API integrations)
- Bearer token in `Authorization: Bearer <token>` header
- Same JWT tokens, different transport
- Browser clients MUST use cookie-based auth only

**No Recruiter Accounts:**
- Recruiter authentication not in MVP
- No company dashboard access
- No job creation endpoints

### Authorization

**Candidate Permissions:**
- View own profile
- Edit own profile
- View job feed
- View job details
- Record application clicks
- Delete own account

**No Admin Job Creation:**
- Django admin cannot create jobs
- Admin can only manage ingestion sources and system config
- Admin cannot bypass ingestion pipeline

### API Security

**Session/Cookie Security:**
- Secure, HttpOnly cookies in production
- SameSite=Strict or Lax (proposed: Lax for better UX, requires approval)
- CSRF protection enabled for all state-changing cookie-authenticated requests
- Session timeout TBD (proposed: 7 days inactivity, requires approval)

**CSRF Protection:**
- Enabled for all POST/PUT/DELETE endpoints using cookie authentication
- CSRF token must be included in request headers or body
- Bearer authentication (non-browser clients) bypasses CSRF
- Frontend must include CSRF token for all state-changing requests
- Django's built-in CSRF middleware handles validation

**CORS Boundaries:**
- Frontend origin whitelisted in production
- Local development: allow localhost
- No wildcard CORS in production

**Token Authentication:**
- **Chosen:** Django SimpleJWT for JWT implementation
- Access token: 15 minute expiration
- Refresh token: 7 day expiration
- Refresh token rotation with blacklist after use
- Token revocation on logout (blacklist refresh token)
- Password change revokes all refresh tokens

### Rate Limiting

**API Rate Limits:**
- Per-user rate limits on API endpoints
- Anonymous rate limits (if public endpoints exist)
- Prevent abuse of application-click tracking

## Resume Handling, Consent, Retention, and Deletion

### Resume Purpose (Decision 9)

**Permitted Uses:**
- Future skill extraction and profile enrichment
- Matching improvement (if resume parsing implemented)
- Candidate's own reference

**Not Permitted:**
- Sharing with third parties without consent
- Using for non-matching purposes
- Storing longer than retention period without justification

### Consent

**Consent Model:**
- Explicit consent required at upload
- Clear disclosure of purpose (matching, profile enrichment)
- Option to withdraw consent
- Consent recorded with timestamp

**Consent Withdrawal:**
- Candidate can delete resume at any time
- Profile data extracted from resume is retained (unless explicitly deleted)
- Matching scores derived from resume may need recalculation (decision required)

### Retention

**Retention Policy (Decision Required):**
- Legal retention period not established
- **Proposed (not approved):** retain resume for 1 year after account deletion or consent withdrawal
- **Proposed (not approved):** retain extracted profile data until account deletion
- Operational records (application clicks) retained for analytics (decision required)
- **Important:** The one-year retention period is a proposal, not an established requirement. Do not claim automatic deletion of parsed data, caches, or derived records unless that behavior is specified and later implemented.

**Deletion Propagation:**
- Account deletion → resume file deleted
- Resume deletion → file removed, profile data remains
- Profile deletion → all personal data removed, anonymized analytics retained

### Data Minimization

**Principles:**
- Store only what is necessary for matching
- Resume content not displayed to other users
- Extracted data used only for matching
- No PII exposed in logs

## Subscription Entitlements, Free-Tier Limits, and Paid Features

### Free-Tier Features

**Included in Free Tier:**
- Basic profile creation
- Job feed with relevance matching
- Application tracking
- Daily match view quota (decision required)

**Free-Tier Quota (Decision 11)**

**Quota Definition:**
- Unit: number of matched jobs viewed per day
- Reset period: daily (reset timezone TBD - awaiting approval)
- Boundary: per user account

**What Counts as One Match:**
- Viewing a job in the matched feed counts toward quota
- Repeated views of the same job: count once per day (decision required)
- Failed requests or errors do not count
- Concurrent requests: use atomic counter to avoid double-counting

**Quota Exhaustion:**
- When quota exhausted: block new match views
- Display upgrade prompt
- Allow viewing non-matched jobs (if applicable)
- Upgrade to paid tier resets quota

**Free-Tier Limits (Explicitly Unresolved - Awaiting Approval):**
- Exact daily match limit: TBD (requires approval)
- Reset timezone: TBD (requires approval)
- Repeat-view rule: Whether to count repeated views of same job per day - TBD (requires approval)
- Basic matching (already included)

**Quota Enforcement:**
- Atomic counter in Redis with DB fallback
- Rate limiting at application level
- Consistent across retries and concurrent requests

### Paid Features (Future)

**Potential Paid Features:**
- Unlimited match views
- Priority matching
- Early access to new jobs
- Advanced filters
- Resume review (human or AI)
- Application insights

**Not in MVP:**
- No paid tier implementation in MVP
- Subscription and billing deferred
- Razorpay integration planned but not implemented

## Worker Concurrency (Decision 6)

**Authoritative Concurrency Table (Proposed for Production):**

| Queue Name | Purpose | Proposed Concurrency | Reasoning |
|------------|---------|---------------------|-----------|
| fetch_queue | Job fetching from sources | 2 | Lower concurrency to respect rate limits and avoid overwhelming sources |
| parse_queue | Job parsing and normalization | 4 | Higher concurrency for CPU-bound parsing tasks |
| match_queue | Match score computation | 3 | Balanced for batch scoring operations |

**Existing Documentation Reference:**
- Some documentation references fetch_queue=5, parse_queue=3, match_queue=3
- This is inconsistent with the proposed 2/4/3 configuration
- Proposed 2/4/3 aligns with rate limit considerations (fetch_queue) and CPU-bound nature (parse_queue)

**Current Phase 0 Configuration:**
- base.py defines queue names (fetch_queue, parse_queue, match_queue) but does NOT set concurrency values
- Concurrency is configured in Celery worker command line or worker configuration
- Docker Compose worker command: `celery -A config worker -l info -Q default,fetch_queue,parse_queue,match_queue` (no concurrency specified)
- Concurrency must be added to worker configuration in Phase 2 when implementing actual workers

**Configuration Implementation:**
- Concurrency settings to be added in Celery worker configuration (e.g., `--concurrency=2` for fetch_queue worker)
- Separate worker processes per queue or single worker with queue priorities
- Proposed values above are targets for production tuning
- Can be adjusted based on actual load testing in Phase 8

**Idempotency:**
- All tasks must be idempotent
- Use task IDs or deduplication keys to prevent duplicate execution
- FetchRun.celery_task_id for correlation
- Concurrent requests handled via database constraints and atomic operations

**Retry Behavior:**
- Transient failures (network, rate limits): retry with exponential backoff
- Persistent failures (malformed data, 404): log, alert, no retry
- Max retries: 3 for transient errors
- Backoff with jitter to avoid thundering herd

**Overlapping Prevention:**
- Celery Beat with unique task names prevents overlapping scheduled fetches
- FetchRun.status prevents concurrent fetches for same source
- Per-company lock in task implementation

## Operational Expectations, Observability, and Failure Handling

### Uptime and Availability

**Targets:**
- 99.5% uptime for job feed
- 99% uptime for candidate accounts
- Scheduled maintenance windows announced

### Observability

**Metrics to Track:**
- Job ingestion success rate per source
- Fetch latency per source
- Match score distribution
- Application click rate
- User registration rate
- API error rates
- Celery task failure rates

**Logging:**
- Structured logging (JSON format in production)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- No secrets in logs
- Logs shipped to centralized service (Sentry planned)

**Monitoring:**
- Health check endpoint (implemented)
- Database connection monitoring
- Redis connection monitoring
- Celery worker monitoring (Flower planned)
- Alerting on critical failures

### Failure Handling

**Ingestion Failures:**
- Transient failures: retry with exponential backoff
- Persistent failures: alert, pause source
- Partial failures: log, continue with other jobs
- Source outage: mark all jobs from source as stale after threshold

**Matching Failures:**
- Matching task failure: retry with limited attempts
- Model loading failure: alert, pause matching
- Score computation failure: log, assign default score (decision required)

**API Failures:**
- Database connection failure: return 503, alert
- Redis connection failure: degrade gracefully (decision required)
- Auth service failure: return 401/403, log

**Candidate-Facing Failures:**
- Display friendly error messages
- Never expose internal stack traces
- Provide retry guidance where appropriate

### Data Quality

**Job Data Quality:**
- Validation at ingestion (required fields)
- Normalization (locations, dates, salary ranges)
- Duplicate detection and prevention
- Stale job cleanup

**Candidate Data Quality:**
- Profile validation (email format, required fields)
- Skill normalization
- Experience validation (non-negative years)

## Acceptance Criteria

### Phase 1: Data Model and Basic Ingestion

**Acceptance Criteria:**
1. Database schema matches `docs/DB_SCHEMA.md`
2. Models can be created and migrated without errors
3. Celery tasks can fetch from a test source
4. Jobs can be stored with source metadata
5. Deduplication works correctly
6. Tests pass for all model and task logic

### Phase 2: Matching and Candidate Feed

**Acceptance Criteria:**
1. Candidate can create profile
2. Jobs can be matched to candidates using TF-IDF
3. Match scores are computed and stored
4. Candidate feed displays jobs ranked by score
5. Sponsored jobs appear higher but are marked
6. Application clicks are recorded

### Phase 3: Frontend Integration

**Acceptance Criteria:**
1. React frontend displays job feed
2. Candidate can create and edit profile
3. Matching scores displayed to candidates
4. Application flow works end-to-end
5. Responsive design for mobile

### Ongoing Acceptance

**Criteria:**
1. All tests pass before deployment
2. No regressions in matching quality
3. Ingestion success rate > 95%
4. API response time p95 < 500ms
5. No critical security vulnerabilities

## Unresolved Questions and Future Decisions

See `docs/DECISIONS.md` for unresolved decisions and their status.
