# MatchHire Database Schema Specification

## Document Purpose

This document defines the implementation-ready database schema for MatchHire. All entities, fields, relationships, constraints, and lifecycle behaviors are specified here. This schema must be consistent with `docs/SPEC.md` and decisions recorded in `docs/DECISIONS.md`.

## Schema Principles

1. **No Manual Job Creation:** No model, endpoint, or admin form allows creating jobs outside the ingestion pipeline.
2. **Candidate-First:** Schema supports candidate workflows; recruiter/employer tables are excluded from MVP.
3. **Auditability:** All important state changes are tracked with timestamps.
4. **Data Integrity:** Constraints enforce business rules where feasible; application-level enforcement where database constraints are insufficient.
5. **Performance:** Indexes support expected query patterns (candidate feed, matching, ingestion monitoring).

## Entity Overview

**Core Entities:**
- `User`: Django auth user (candidate accounts)
- `CandidateProfile`: Extended candidate information
- `Skill`: Candidate skills (normalized)
- `WorkExperience`: Candidate work history
- `Company`: Companies with approved sources
- `IngestionSource`: Approved job sources (career pages, ATS)
- `FetchRun`: Individual fetch attempts from sources
- `Job`: Job listings from sources
- `JobSkill`: Skills required by jobs
- `MatchScore`: Candidate-job match scores
- `ApplicationClick`: Candidate application clicks
- `Subscription`: Candidate subscription entitlements (future)

**Supporting Entities:**
- None (fixed vocabulary strategy, no versioning needed)

## Entity Specifications

### User

**Purpose:** Django's built-in auth user, representing candidate accounts.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `email` (EmailField, unique, not null): Candidate email
- `password` (CharField, not null): Hashed password
- `first_name` (CharField, blank): Optional first name
- `last_name` (CharField, blank): Optional last name
- `is_active` (BooleanField, default True): Account active status
- `is_staff` (BooleanField, default False): Admin access (not for job creation)
- `date_joined` (DateTimeField, auto_now_add): Registration timestamp
- `last_login` (DateTimeField, null, blank): Last login timestamp

**Constraints:**
- `email` must be unique
- `password` hashed via Django's default (PBKDF2)

**Indexes:**
- Index on `email` for login queries
- Index on `is_active` for filtering active users

**Lifecycle:**
- Created on registration
- Deleted when account is deleted (CASCADE to profile)
- `is_active=False` for soft deletion or deactivation

**Relationships:**
- One-to-one to `CandidateProfile` (CASCADE delete)

**Note:** Django's built-in User model will be extended with custom user model or use proxy model for additional fields like plan ENUM and daily_match_count (to be implemented in Phase 1).

**Application-Level Enforcement:**
- Staff users cannot create jobs (no endpoint, serializer restriction)
- Job creation only through ingestion pipeline

---

### CandidateProfile

**Purpose:** Extended candidate information beyond Django auth user.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `user` (OneToOneField to User, not null, on_delete=CASCADE): Associated user
- `phone` (CharField, blank, max_length=20): Optional phone number
- `location` (CharField, blank, max_length=100): City/state preference
- `remote_preference` (CharField, choices, blank): 'on-site', 'remote', 'hybrid', 'any'
- `salary_min` (DecimalField, null, blank, max_digits=10, decimal_places=2): Minimum expected salary
- `salary_max` (DecimalField, null, blank, max_digits=10, decimal_places=2): Maximum expected salary
- `salary_currency` (CharField, default='INR', max_length=3): Currency code
- `role_type_preference` (CharField, choices, blank): 'full-time', 'internship', 'contract', 'any'
- `bio` (TextField, blank): Short introduction
- `total_experience_years` (DecimalField, null, blank, max_digits=4, decimal_places=2): Total experience (0.0 to 99.99)
- `resume_file` (FileField, blank, max_length=255): Resume file path
- `resume_uploaded_at` (DateTimeField, null, blank): Resume upload timestamp
- `resume_consent_given` (BooleanField, default False): Consent for resume processing
- `created_at` (DateTimeField, auto_now_add): Profile creation timestamp
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `user` must be unique (OneToOneField enforces this)
- `salary_min` <= `salary_max` (application-level check)
- `total_experience_years` >= 0 (application-level check)

**Indexes:**
- Index on `user` for reverse lookups
- Index on `location` for candidate discovery (future)
- Index on `remote_preference` for filtering

**Relationships:**
- Many-to-many to `Skill` through `CandidateSkill` (or inline skills)
- One-to-many to `WorkExperience`
- One-to-one to `User`

**Lifecycle:**
- Created on registration (can be incomplete)
- Updated as candidate adds information
- Deleted when user is deleted (CASCADE)

**Application-Level Enforcement:**
- Experience validation (non-negative)
- Salary range validation
- Resume consent required before processing

---

### Skill

**Purpose:** Normalized skill taxonomy for matching (fixed vocabulary from Decision 3).

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `name` (CharField, unique, not null, max_length=100): Canonical skill name (e.g., "Python", "React", "JavaScript")
- `category` (CharField, blank, max_length=50): Skill category (e.g., "programming", "framework")
- `created_at` (DateTimeField, auto_now_add): Creation timestamp

**Constraints:**
- `name` must be unique (case-insensitive via application normalization)
- Only skills from the fixed 500+ term vocabulary are stored; unknown inputs are logged but not added to this table

**Indexes:**
- Index on `name` for skill lookups
- Index on `category` for filtering

**Relationships:**
- Many-to-many to `CandidateProfile` (through intermediate table)
- Many-to-many to `Job` (through `JobSkill`)

**Lifecycle:**
- Pre-seeded from fixed skills dictionary (500+ terms with canonical names + aliases)
- Not auto-created from candidate input (fixed vocabulary strategy)
- Never deleted (mark as deprecated if needed)

**Application-Level Enforcement:**
- Normalization: lowercase, trim whitespace, map aliases to canonical names
- Skill name uniqueness enforced case-insensitively
- Candidate input normalized against vocabulary; unknown skills excluded from matching

---

### CandidateSkill (Intermediate Table)

**Purpose:** Many-to-many relationship between candidates and skills with proficiency.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `candidate` (ForeignKey to CandidateProfile, not null, on_delete=CASCADE)
- `skill` (ForeignKey to Skill, not null, on_delete=PROTECT)
- `proficiency` (CharField, choices, blank, max_length=20): 'beginner', 'intermediate', 'advanced'
- `created_at` (DateTimeField, auto_now_add): Association timestamp

**Constraints:**
- Unique together: (`candidate`, `skill`)

**Indexes:**
- Index on `candidate` for skill lookups
- Index on `skill` for reverse lookups
- Unique index on (`candidate`, `skill`)

**Relationships:**
- Many-to-one to `CandidateProfile`
- Many-to-one to `Skill`

**Lifecycle:**
- Created when candidate adds skill
- Deleted when candidate removes skill or profile deleted

---

### WorkExperience

**Purpose:** Candidate work history entries.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `candidate` (ForeignKey to CandidateProfile, not null, on_delete=CASCADE)
- `company_name` (CharField, not null, max_length=200): Company name
- `role` (CharField, not null, max_length=200): Job title/role
- `description` (TextField, blank): Role description
- `start_date` (DateField, null, blank): Start date
- `end_date` (DateField, null, blank): End date (null if current)
- `location` (CharField, blank, max_length=100): Job location
- `created_at` (DateTimeField, auto_now_add): Entry creation timestamp
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `end_date` >= `start_date` (application-level check)
- If `end_date` is null, treat as current role

**Indexes:**
- Index on `candidate` for profile queries
- Index on `start_date`, `end_date` for experience calculation

**Relationships:**
- Many-to-one to `CandidateProfile`

**Lifecycle:**
- Created when candidate adds experience
- Updated when candidate edits
- Deleted when candidate removes or profile deleted

**Application-Level Enforcement:**
- Date validation
- Total experience calculated from entries (not stored redundantly)

---

### Company

**Purpose:** Companies with approved or candidate job sources (see Decision 10 for source approval process).

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `name` (CharField, unique, not null, max_length=200): Company name
- `website` (URLField, blank, max_length=500): Company website
- `description` (TextField, blank): Company description
- `is_active` (BooleanField, default True): Company active status
- `created_at` (DateTimeField, auto_now_add): Creation timestamp
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `name` must be unique

**Indexes:**
- Index on `name` for lookups
- Index on `is_active` for filtering

**Relationships:**
- One-to-many to `IngestionSource`
- One-to-many to `Job`

**Lifecycle:**
- Created when source is approved
- Deactivated if all sources disabled or company requests removal
- Not deleted (soft delete via `is_active`)

---

### IngestionSource

**Purpose:** Approved job sources (career pages, ATS) for automated ingestion.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `company` (ForeignKey to Company, not null, on_delete=PROTECT): Associated company
- `name` (CharField, not null, max_length=200): Source name (e.g., "Company Career Page")
- `source_type` (CharField, choices, not null, max_length=50): 'career_page', 'ats', 'api', 'other'
- `base_url` (URLField, not null, max_length=500): Base URL of source
- `listing_url_pattern` (CharField, blank, max_length=500): URL pattern for job listings
- `job_url_pattern` (CharField, blank, max_length=500): URL pattern for individual jobs
- `fetch_interval_hours` (IntegerField, default=24): Fetch interval in hours
- `stale_threshold` (IntegerField, default=3): Number of consecutive misses before closing
- `is_active` (BooleanField, default True): Source active status
- `last_fetched_at` (DateTimeField, null, blank): Last successful fetch timestamp
- `last_fetch_status` (CharField, blank, max_length=50): 'success', 'failure', 'partial'
- `consecutive_failures` (IntegerField, default=0): Consecutive fetch failures
- `created_at` (DateTimeField, auto_now_add): Creation timestamp
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `fetch_interval_hours` > 0
- `stale_threshold` >= 1
- `consecutive_failures` >= 0

**Indexes:**
- Index on `company` for company queries
- Index on `is_active` for active sources
- Index on `last_fetched_at` for scheduling
- Unique index on (`company`, `base_url`) to prevent duplicate sources

**Relationships:**
- Many-to-one to `Company`
- One-to-many to `FetchRun`
- One-to-many to `Job`

**Lifecycle:**
- Created after source approval (legal, technical review)
- Deactivated if source becomes unavailable or violates terms
- Fetch runs create `FetchRun` records
- Failed fetches increment `consecutive_failures`
- Successful fetches reset `consecutive_failures` to 0

**Application-Level Enforcement:**
- Only approved sources can be created (admin or seeded)
- Source cannot be created via public API
- Rate limiting enforced at application level

---

### FetchRun

**Purpose:** Individual fetch attempts from sources.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `source` (ForeignKey to IngestionSource, not null, on_delete=CASCADE): Source fetched
- `status` (CharField, choices, not null, max_length=50): 'pending', 'running', 'success', 'failure', 'partial'
- `started_at` (DateTimeField, auto_now_add): Fetch start timestamp
- `completed_at` (DateTimeField, null, blank): Fetch completion timestamp
- `jobs_fetched` (IntegerField, default=0): Number of jobs fetched
- `jobs_created` (IntegerField, default=0): Number of new jobs created
- `jobs_updated` (IntegerField, default=0): Number of existing jobs updated
- `jobs_stale` (IntegerField, default=0): Number of jobs marked stale
- `jobs_closed` (IntegerField, default=0): Number of jobs closed
- `error_message` (TextField, blank): Error details if failed
- `celery_task_id` (CharField, blank, max_length=255): Associated Celery task ID

**Constraints:**
- `jobs_fetched`, `jobs_created`, `jobs_updated`, `jobs_stale`, `jobs_closed` >= 0
- `completed_at` >= `started_at` (application-level check)

**Indexes:**
- Index on `source` for source history
- Index on `status` for monitoring
- Index on `started_at` for time-series queries
- Index on `celery_task_id` for task correlation

**Relationships:**
- Many-to-one to `IngestionSource`

**Lifecycle:**
- Created when fetch task starts
- Updated during fetch (running → success/failure/partial)
- Retained for monitoring and debugging
- Can be archived after N days (decision required)

**Application-Level Enforcement:**
- Idempotency: duplicate task IDs should not create duplicate runs
- Atomic counters for job counts

---

### Job

**Purpose:** Job listings from approved sources.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `source` (ForeignKey to IngestionSource, not null, on_delete=PROTECT): Source of job
- `company` (ForeignKey to Company, not null, on_delete=PROTECT): Company offering job
- `external_id` (CharField, blank, max_length=255): Source-specific job ID
- `title` (CharField, not null, max_length=300): Job title
- `description` (TextField, not null): Job description
- `requirements` (TextField, blank): Job requirements
- `location` (CharField, blank, max_length=200): Job location
- `remote_type` (CharField, choices, blank, max_length=50): 'on-site', 'remote', 'hybrid'
- `role_type` (CharField, choices, blank, max_length=50): 'full-time', 'internship', 'contract'
- `experience_min_years` (DecimalField, null, blank, max_digits=4, decimal_places=2): Minimum experience required
- `experience_max_years` (DecimalField, null, blank, max_digits=4, decimal_places=2): Maximum experience (if range)
- `salary_min` (DecimalField, null, blank, max_digits=10, decimal_places=2): Minimum salary
- `salary_max` (DecimalField, null, blank, max_digits=10, decimal_places=2): Maximum salary
- `salary_currency` (CharField, blank, max_length=3): Currency code
- `application_url` (URLField, not null, max_length=1000): External application URL
- `posted_date` (DateField, null, blank): Original posting date from source
- `first_seen_at` (DateTimeField, auto_now_add): First ingestion timestamp
- `last_seen_at` (DateTimeField, auto_now=True): Last successful refresh timestamp
- `job_hash` (CharField, blank, max_length=64): SHA-256 hash of normalized fields (title, description, location, required_skills, required_yoe)
- `is_active` (BooleanField, default True): Job active status (visible in feeds)
- `is_sponsored` (BooleanField, default False): Sponsored job flag
- `sponsored_boost` (DecimalField, null, blank, max_digits=3, decimal_places=2): Sponsored boost value (0.0 to 0.15)
- `consecutive_misses` (IntegerField, default=0): Consecutive successful fetches where job was absent
- `created_at` (DateTimeField, auto_now_add): Database record creation
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `experience_min_years` >= 0
- `experience_max_years` >= `experience_min_years` (if both set)
- `salary_min` <= `salary_max` (if both set)
- `consecutive_misses` >= 0
- `sponsored_boost` between 0.0 and 0.15 (if set)
- Unique together: (`source`, `external_id`) if `external_id` is not null

**Indexes:**
- Index on `source` for source queries
- Index on `company` for company queries
- Index on `is_active` for filtering active jobs
- Index on `is_sponsored` for sponsored job queries
- Index on `last_seen_at` for staleness detection
- Index on `posted_date` for sorting
- Unique index on (`source`, `external_id`) where `external_id` is not null
- Index on `application_url` for fallback identity
- Composite index on (`is_active`, `last_seen_at`) for staleness queries

**Relationships:**
- Many-to-one to `IngestionSource`
- Many-to-one to `Company`
- Many-to-many to `Skill` through `JobSkill`
- One-to-many to `MatchScore`
- One-to-many to `ApplicationClick`

**Lifecycle:**
- **Active (is_active=True):** Initially active on first ingestion; visible in feeds; apply link live
- **Inactive (is_active=False):** Hidden from feeds; apply link disabled
- **Archived:** Historical record (never visible, optional)

**State Transitions:**
- New job → Active (is_active=True)
- Job found in source (successful fetch) → update content, remain Active, update last_seen_at, update job_hash
- Job missing from source during SUCCESSFUL fetch → increment consecutive_misses
- Job becomes inactive after N consecutive SUCCESSFUL fetches where absent (default N=3)
- Failed or partial fetch → does NOT increment consecutive_misses
- Inactive job reappears → transition back to Active, reset consecutive_misses to 0
- Safety valve: if single run would deactivate >X% of company's jobs, skip deactivation and alert (proposed X=20%)

**Application-Level Enforcement:**
- No manual job creation (no endpoint or admin form)
- Jobs only created through ingestion pipeline
- job_hash computed from normalized fields before save
- External ID normalization (trim, validate)
- Failed fetches must not cause deactivation

**Identity and Deduplication (Decision 5):**
- Primary identity: `source` + `external_id` (if available)
- Fallback identity: `application_url` (if no external ID)
- Last resort: content hash (high false-positive risk, manual review)
- job_hash: SHA-256 of normalized (title, description, location, required_skills, required_yoe)
- Content changes update existing job, do not create duplicates
- URL changes without ID change: treat as same job if content similar
- ID changes without URL change: treat as potential duplicate, manual review

---

### JobSkill (Intermediate Table)

**Purpose:** Many-to-many relationship between jobs and required skills.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `job` (ForeignKey to Job, not null, on_delete=CASCADE)
- `skill` (ForeignKey to Skill, not null, on_delete=PROTECT)
- `is_required` (BooleanField, default True): Whether skill is required or preferred
- `created_at` (DateTimeField, auto_now_add): Association timestamp

**Constraints:**
- Unique together: (`job`, `skill`)

**Indexes:**
- Index on `job` for job skill lookups
- Index on `skill` for reverse lookups
- Unique index on (`job`, `skill`)

**Relationships:**
- Many-to-one to `Job`
- Many-to-one to `Skill`

**Lifecycle:**
- Created when job is parsed with skills
- Updated if job skills change
- Deleted when job is deleted

---

### MatchScore

**Purpose:** Candidate-job match scores with component breakdown.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `candidate` (ForeignKey to CandidateProfile, not null, on_delete=CASCADE)
- `job` (ForeignKey to Job, not null, on_delete=CASCADE)
- `base_score` (DecimalField, not null, max_digits=5, decimal_places=4): Base relevance score (0.0 to 1.0)
- `final_score` (DecimalField, not null, max_digits=5, decimal_places=4): Final score after sponsored boost (0.0 to 1.0, capped)
- `skill_similarity` (DecimalField, null, blank, max_digits=5, decimal_places=4): Skills similarity score (0.0 to 1.0, 50% weight)
- `experience_match` (DecimalField, null, blank, max_digits=5, decimal_places=4): Experience component score (0.0 to 1.0, 30% weight)
- `keyword_overlap` (DecimalField, null, blank, max_digits=5, decimal_places=4): Keyword overlap score (0.0 to 1.0, 20% weight)
- `computed_at` (DateTimeField, auto_now_add): Score computation timestamp
- `updated_at` (DateTimeField, auto_now=True): Last update timestamp

**Constraints:**
- `base_score` between 0.0 and 1.0
- `final_score` between 0.0 and 1.0 (capped)
- Component scores between 0.0 and 1.0 (if set)
- Unique together: (`candidate`, `job`)

**Indexes:**
- Index on `candidate` for candidate feed queries
- Index on `job` for reverse lookups
- Index on `final_score` for ranking
- Unique index on (`candidate`, `job`)
- Composite index on (`candidate`, `final_score`) for feed queries

**Relationships:**
- Many-to-one to `CandidateProfile`
- Many-to-one to `Job`

**Lifecycle:**
- Created when job is matched to candidate
- Updated when job content changes or candidate profile changes
- Deleted when job is closed or candidate deleted
- No recompute on vocabulary changes (fixed vocabulary strategy)

**Application-Level Enforcement:**
- Score range validation
- Component score validation
- Atomic updates to prevent race conditions

**Score Semantics (Decision 2):**
- `base_score`: Pure relevance from TF-IDF and matching rules (0.0 to 1.0)
- `final_score`: `base_score` + `sponsored_boost` (from Job, capped at 1.0)
- Component scores stored for breakdown: skill_similarity (50%), experience_match (30%), keyword_overlap (20%)
- Sponsored jobs have higher `final_score` but same `base_score`
- No vectorizer_version field (fixed vocabulary strategy)

**Experience Match Semantics (Decision 1):**
- Match score formula: `match_score = 0.50 * skill_similarity + 0.30 * experience_match + 0.20 * keyword_overlap`
- Job specifies zero years (required_yoe = 0): experience_match = 1.0 for any candidate experience; unknown candidate experience (user_yoe = null) = 1.0
- Job requires positive minimum (required_yoe > 0): Formula `min(user_yoe / required_yoe, 1.0)` when user_yoe known and not null; candidate >= minimum = 1.0; candidate < minimum = partial credit; unknown candidate (user_yoe = null) = 0.0
- Job specifies range (e.g., "0-2 years"): If range includes 0, treat as required_yoe = 0 (score = 1.0); if range excludes 0, use minimum value; overqualification not penalized (score = 1.0); unknown candidate (user_yoe = null) = 0.0 unless range includes 0
- Experience missing from job: Treat as required_yoe = 0 (score = 1.0 for all); unknown candidate experience = 1.0
- Division by zero protection: When required_yoe = 0, experience_match = 1.0 (no division performed); when user_yoe is null, experience_match = 0.0 unless required_yoe = 0
- Experience score is one component of relevance, not a guarantee of candidate eligibility

---

### ApplicationClick

**Purpose:** Record when candidates click to apply for jobs.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `candidate` (ForeignKey to CandidateProfile, not null, on_delete=CASCADE)
- `job` (ForeignKey to Job, not null, on_delete=CASCADE)
- `clicked_at` (DateTimeField, auto_now_add): Click timestamp
- `ip_address` (GenericIPAddressField, blank): IP address (for fraud detection)
- `user_agent` (CharField, blank, max_length=500): User agent string

**Constraints:**
- None (multiple clicks allowed, rate-limited at application level)

**Indexes:**
- Index on `candidate` for candidate application history
- Index on `job` for job analytics
- Index on `clicked_at` for time-series queries
- Composite index on (`candidate`, `job`, `clicked_at`) for deduplication

**Relationships:**
- Many-to-one to `CandidateProfile`
- Many-to-one to `Job`

**Lifecycle:**
- Created when candidate clicks "Apply"
- Never deleted (retained for analytics)
- Can be anonymized after retention period

**Application-Level Enforcement:**
- Rate limiting per candidate (prevents abuse)
- Application clicks are recorded for analytics only (NOT used for free-tier quota; quota is based on match views per Decision 11)
- No deduplication enforced at database level (allow repeated clicks for accurate analytics)

---

### Subscription (Future, Not MVP)

**Purpose:** Candidate subscription entitlements and quotas.

**Fields:**
- `id` (BigAutoField, PK): Unique identifier
- `candidate` (OneToOneField to CandidateProfile, not null, on_delete=CASCADE)
- `tier` (CharField, choices, not null, max_length=50): 'free', 'basic', 'premium'
- `daily_match_quota` (IntegerField, default=10): Daily match view quota (TBD - requires approval)
- `matches_used_today` (IntegerField, default=0): Match views used today
- `current_day_date` (DateField, auto_now_add): Current day for quota tracking
- `is_active` (BooleanField, default True): Subscription active status
- `started_at` (DateTimeField, auto_now_add): Subscription start
- `updated_at` (DateTimeField, auto_now=True): Last update

**Constraints:**
- `daily_match_quota` >= 0
- `matches_used_today` >= 0
- `matches_used_today` <= `daily_match_quota`

**Indexes:**
- Index on `candidate` for candidate queries
- Index on `tier` for analytics

**Relationships:**
- One-to-one to `CandidateProfile`

**Lifecycle:**
- Created on registration (free tier)
- Updated on quota usage or upgrade
- Reset daily (application-level job)

**Application-Level Enforcement:**
- Quota counting and enforcement
- Daily reset
- Atomic increments to prevent race conditions

**Quota Semantics (Decision 11):**
- Unit: match views per day (NOT application clicks)
- Reset: daily (timezone TBD - requires approval)
- Counting: viewing a job in matched feed counts; repeated views of same job count once per day (TBD)
- Deduplication: one count per job per candidate per day (TBD)

---

## Deletion Behavior

**CASCADE Deletes:**
- User → CandidateProfile (profile deleted with user)
- CandidateProfile → CandidateSkill, WorkExperience, MatchScore, ApplicationClick, Subscription
- IngestionSource → FetchRun (source deletion removes fetch history)
- Job → JobSkill, MatchScore, ApplicationClick

**PROTECT Deletes:**
- Company → IngestionSource (cannot delete company with active sources)
- Company → Job (cannot delete company with jobs)
- IngestionSource → Job (cannot delete source with jobs)
- Skill → CandidateSkill, JobSkill (cannot delete skill in use)

**Soft Deletes:**
- Company: `is_active=False` instead of deletion
- IngestionSource: `is_active=False` instead of deletion
- Job: `is_active=False` instead of deletion (no archived status enum, just boolean)

**Retention:**
- FetchRun: Retained for N days (decision required)
- ApplicationClick: Retained for analytics (decision required)

---

## Application-Level vs. Database Constraints

**Database Constraints (Enforced by DB):**
- Primary keys and foreign keys
- Unique constraints (email, skill names, source+external_id)
- Not null constraints
- Check constraints (where supported by PostgreSQL)
- CASCADE/PROTECT on deletes

**Application-Level Enforcement (Python):**
- Business logic validation (salary ranges, experience ranges)
- Complex cross-field validation
- Idempotency (Celery tasks)
- Rate limiting
- Quota enforcement
- Data normalization (skill names, locations)
- Content hash computation
- Authorization (no manual job creation)

---

## Expected Query Patterns

**Candidate Feed:**
```sql
SELECT j.*, ms.final_score
FROM job j
JOIN match_score ms ON j.id = ms.job_id
WHERE ms.candidate_id = :candidate_id
  AND j.is_active = true
ORDER BY ms.final_score DESC, j.posted_date DESC
LIMIT 20;
```

**Job Ingestion:**
```sql
SELECT * FROM job
WHERE source_id = :source_id
  AND external_id = :external_id;
```

**Staleness Detection:**
```sql
SELECT * FROM job
WHERE is_active = true
  AND last_seen_at < :threshold;
```

**Application History:**
```sql
SELECT j.*, ac.clicked_at
FROM application_click ac
JOIN job j ON ac.job_id = j.id
WHERE ac.candidate_id = :candidate_id
ORDER BY ac.clicked_at DESC;
```

**Source Monitoring:**
```sql
SELECT * FROM fetch_run
WHERE source_id = :source_id
ORDER BY started_at DESC
LIMIT 10;
```

---

## Performance Considerations

**Indexes for Performance:**
- Compound indexes for candidate feed queries
- Indexes on status fields for filtering
- Indexes on timestamps for time-series queries
- Unique indexes for deduplication

**Query Optimization:**
- Candidate feed uses pagination (20 jobs per page)
- Matching results cached or materialized for performance (future)
- TF-IDF computation in background, not in request path

**Scaling Considerations:**
- MatchScore table will grow large (candidates × jobs)
- Consider partitioning by candidate or time (future)
- Archive old match scores (decision required)

---

## Migration Strategy

**Phase 1:**
- Create User, CandidateProfile, Skill, CandidateSkill, WorkExperience
- Create Company, IngestionSource, FetchRun
- Create Job, JobSkill

**Phase 2:**
- Create MatchScore
- Create ApplicationClick

**Phase 3 (Future):**
- Create Subscription when paid tier implemented

**Data Seeding:**
- Seed initial skills taxonomy from fixed 500+ term vocabulary (Decision 3)
- Seed initial companies and sources (after source-review task completes - see Decision 10)
- Seed initial TF-IDF vectorizer version
- **Important:** No companies or sources are pre-approved; source-review task must complete before any real ingestion

---

## Unresolved Questions

See `docs/DECISIONS.md` for unresolved schema decisions and their status.
