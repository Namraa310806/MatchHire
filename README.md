# MatchHire

MatchHire is a verified job aggregation and intelligent job-matching platform.

## Current Implementation Status: Phase 4C

This is Phase 4C of the MatchHire project: Ingestion Operational Layer.

**Currently implemented:**
- Django backend with Django REST Framework
- React frontend with Vite
- PostgreSQL and Redis via Docker Compose with health checks
- Health endpoint at `/api/health/` (checks database and Redis connectivity)
- Environment-based configuration (database, Redis, CORS)
- Custom user model with email-based authentication
- **Authentication System (Phases 3A-3D):**
  - Email/password registration with Django password validation
  - JWT authentication with HttpOnly cookies
  - Access token lifetime: 10 minutes
  - Refresh token lifetime: 7 days
  - Refresh token rotation with blacklisting
  - Logout with token revocation
  - Protected `/api/auth/me/` endpoint
  - Secure default permission policy (IsAuthenticated)
  - Public endpoints explicitly opt into AllowAny
  - CSRF middleware globally enabled (auth endpoints exempt with documented rationale)
  - CORS restricted to explicit origins (no wildcard with credentials)
  - Cookie security: HttpOnly, Secure in production, SameSite=Lax
  - JWT payload minimal (user_id only, no profile/job data)
  - Password hashing managed by Django
  - Safe user serialization (id, email only)
  - Generic authentication errors (no account enumeration)
- Core domain models:
  - **User Domain**: Custom User model with UserProfile (skills, experience, keywords)
  - **Company Domain**: Verified job sources with scraper configuration support
  - **Job Domain**: Jobs from verified sources with deduplication and matching metadata
    - Structured experience fields (minimum_experience_years, maximum_experience_years) for numeric matching
    - Skills/keywords semantic contract documented (skills = concrete capabilities, keywords = broader domain terms)
  - **MatchScore Domain**: Persisted match results with component scores for explainability
    - All score fields validated to range 0.0 to 1.0 (final_score, skill_similarity_score, experience_match_score, keyword_overlap_score)
  - **Subscription Domain**: Subscription state (FREE, PRO, PREMIUM plans)
  - **Analytics Domain**: ApplyClick tracking for job application analytics
- Django admin interfaces for all models (Job and IngestionRun admins are read-only to preserve operational integrity)
- Comprehensive test suite (319+ tests passing)
- Database migrations for all domain models
- Development seed data management command for local development
- Authorization boundary documented (see `backend/apps/users/AUTHORIZATION_BOUNDARY.md`)
- **Job Ingestion System (Phases 4A-4C):**
  - BaseJobScraper abstraction defining the scraper contract
  - NormalizedJob common representation for all scrapers
  - **Real official sources:**
    - Stripe (via Greenhouse ATS API - https://boards-api.greenhouse.io/v1/boards/stripe/jobs)
    - Spotify (via Lever ATS API - https://api.lever.co/v0/postings/spotify?mode=json)
    - Linear (via Ashby ATS API - https://api.ashbyhq.com/posting-api/job-board/linear)
  - **Fictional demo source:** Nexus Technologies (for demonstrating scraper contract with deterministic fixtures)
  - Job ingestion service for persistence boundary
  - Deterministic fixture-based testing (no live network dependency)
  - Source-only job invariant enforced (no user job creation)
  - Deduplication via company + external_job_id constraint
  - **Celery integration for asynchronous task execution:**
    - Celery configured with Redis as broker
    - Source registry for controlled scraper mapping (prevents arbitrary source execution)
    - Thin ingestion task (`ingest_jobs_task`) for orchestration
    - Transient vs permanent failure classification
    - Bounded retry with exponential backoff (max 3 retries)
    - HTTP 429 handling with Retry-After respect
    - Idempotent task execution (PostgreSQL uniqueness prevents duplicates)
    - Task results are serializable primitives (no ORM objects)
    - Manual ingestion command: `python manage.py ingest_jobs --source stripe` (synchronous)
    - Async ingestion command: `python manage.py ingest_jobs --source stripe --async` (queues Celery task)
    - Celery worker service in docker-compose.yml
  - **Ingestion Operational Layer (Phase 4C):**
    - IngestionRun model for tracking each ingestion execution
    - Status state machine: PENDING, RUNNING, SUCCEEDED, PARTIAL, FAILED
    - Per-run counters: fetched, normalized, created, updated, skipped, failed
    - Error information bounded in size (no secrets or stack traces)
    - Source health calculation from run history (HEALTHY, DEGRADED, FAILING, UNKNOWN)
    - Overlap prevention via database constraint (only one RUNNING run per source)
    - Celery Beat scheduling for controlled periodic ingestion (Stripe every 4 hours, Spotify every 4 hours, Linear every 4 hours, all configurable)
    - Django admin for IngestionRun inspection (read-only)
    - Management command for ingestion status: `python manage.py ingestion_status`
    - Management command for schedule registration: `python manage.py register_schedule`
    - Celery Beat service in docker-compose.yml

**Not yet implemented (planned for future phases):**
- Additional company scrapers (currently Stripe, Spotify, Linear real sources + Nexus Technologies fictional demo)
- Resume upload and parsing
- Matching engine (TF-IDF, embeddings, scoring algorithms)
- Redis caching
- Payment integration (Razorpay)
- Production deployment

## Technology Stack

- **Backend:** Python, Django 4.2.7, Django REST Framework 3.14.0
- **Frontend:** React with Vite
- **Database:** PostgreSQL 15
- **Cache/Message Broker:** Redis 7
- **Task Queue:** Celery 5.3.4
- **Task Scheduler:** django-celery-beat 2.5.0
- **Containerization:** Docker + Docker Compose

## Repository Structure

```
matchhire/
├── backend/              # Django backend
│   ├── config/          # Django project configuration
│   ├── apps/            # Django applications
│   │   ├── health/      # Health check app
│   │   ├── users/       # User domain (User, UserProfile)
│   │   ├── companies/   # Company domain (verified job sources)
│   │   ├── jobs/        # Job domain (verified jobs)
│   │   ├── matching/    # MatchScore domain
│   │   ├── subscriptions/ # Subscription domain
│   │   └── analytics/   # ApplyClick analytics domain
│   ├── manage.py
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── infrastructure/      # Infrastructure configuration
├── tests/              # Test files
├── docs/               # Documentation
├── .env.example        # Environment variables template
├── .gitignore
├── docker-compose.yml  # PostgreSQL and Redis services
├── AGENTS.md          # Engineering rules for agents
└── README.md
```

## Prerequisites

- Python 3.8+
- Node.js 18+
- Docker and Docker Compose
- Git

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd MatchHire
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your actual values (do not commit `.env` to version control).

## Starting PostgreSQL, Redis, Celery Worker, and Celery Beat

Start the infrastructure services using Docker Compose:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (database)
- Redis (cache and Celery broker)
- Celery worker (for asynchronous task execution)
- Celery Beat (for periodic scheduled ingestion)

To check service status:
```bash
docker-compose ps
```

To stop services:
```bash
docker-compose down
```

To start only specific services:
```bash
docker-compose up -d postgres redis  # Start only PostgreSQL and Redis
docker-compose up -d celery_worker  # Start only Celery worker
docker-compose up -d celery_beat  # Start only Celery Beat
```

## Starting Django Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

The Django backend will be available at `http://localhost:8000`

## Starting React Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies (if not already installed):
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The React frontend will be available at `http://localhost:5173`

## Running Tests

Run the backend test suite:

```bash
cd backend
python manage.py test
```

## Local Development Seed Data

MatchHire includes a management command to seed development data for local development and testing:

```bash
cd backend
python manage.py seed_dev_data
```

This command creates a small, deterministic dataset of fictional development data:

- **4 Companies**: Fictional technology companies (Nexus Technologies, Quantum Systems, Apex Innovations, Stellar Dynamics)
- **11 Jobs**: 2-4 jobs per company with realistic titles, descriptions, skills, and keywords
- **2 Users**: Development user accounts with fictional email addresses
- **2 UserProfiles**: Professional profiles with skills, experience, and keywords
- **8 MatchScores**: Precomputed demonstration match scores connecting profiles to jobs
- **2 Subscriptions**: One PRO and one FREE subscription
- **4 ApplyClicks**: Application click events for analytics

**Important notes about seed data:**

- All data is **fictional** and for **development/demo/testing purposes only**
- These are **not** scraped jobs from real companies
- These do **not** represent real companies or real opportunities
- Email addresses use the `.example.test` domain (e.g., `dev.user1@example.test`)
- Company and job URLs use the `example.test` domain
- Match scores are **precomputed demonstration values**, not generated by the future matching engine
- The command is **idempotent** - running it multiple times will not create duplicate records
- The command is **transaction-safe** - failures will not leave partially created data

The seed data respects MatchHire's architectural invariants:
- All jobs belong to verified company sources
- All jobs have external job IDs and deduplication hashes
- No manual job publishing workflow is created
- The data represents what a future ingestion pipeline would produce

## Health Endpoint

The health endpoint is available at:

```
GET http://localhost:8000/api/health/
```

Expected response:
```json
{
    "status": "ok",
    "dependencies": {
        "database": "ok",
        "redis": "ok"
    }
}
```

## Architecture Notes

- The backend is structured with domain-specific Django apps in the `apps/` directory
- PostgreSQL and Redis are configured with health checks in Docker Compose
- PostgreSQL credentials are configurable via environment variables in both Docker Compose and Django settings
- Environment variables are managed through `python-decouple`
- CORS is configurable via environment variables (CORS_ALLOWED_ORIGINS)
- Django REST Framework is configured with IsAuthenticated as the default permission
- Redis configuration is centralized in settings.py for future Celery integration
- Custom user model (`apps.users.User`) with email-based authentication is established
- Domain models support the future MatchHire pipeline:
  - Companies represent verified job sources only (not arbitrary job posting)
  - Jobs must enter through verified source ingestion (external IDs distinct from internal PKs)
  - MatchScore stores component scores for explainable matching (scoring algorithm not implemented)
  - Subscriptions store state only (payment processing deferred)
  - ApplyClick tracks events without storing sensitive application data
- Django admin interfaces are available for inspection (Job creation is disabled to preserve source-only ingestion)

## Future Phases

The following features are planned for implementation in future phases:

- Phase 4D: Additional company scrapers and enhanced scheduling
- Resume upload and parsing
- ML-based job matching (TF-IDF, embeddings, scoring algorithms)
- Redis caching
- Subscription and payment integration (Razorpay)
- Production deployment with Nginx

## Job Ingestion Architecture

Phases 4A-4C established the foundation for verified job ingestion with asynchronous execution and operational tracking:

```
Celery Beat (periodic scheduling)
        ↓
Celery Task (ingest_jobs_task)
        ↓
IngestionRun creation (operational tracking)
        ↓
Source Registry (controlled mapping)
        ↓
Source-specific scraper (e.g., StripeScraper, NexusTechnologiesScraper)
        ↓
BaseJobScraper contract (fetch → extract → normalize)
        ↓
NormalizedJob (common representation)
        ↓
JobIngestionService (validation + persistence)
        ↓
Job model (PostgreSQL)
        ↓
IngestionRun update (status, counters, error info)
```

**Implemented Sources:**
- **Stripe** (real official source): Uses Greenhouse ATS public API at https://boards-api.greenhouse.io/v1/boards/stripe/jobs. Greenhouse is a legitimate ATS provider used by Stripe for their official careers page. The API is public, documented, and requires no authentication.
- **Spotify** (real official source): Uses Lever ATS public API at https://api.lever.co/v0/postings/spotify?mode=json. Lever is a legitimate ATS provider used by Spotify for their official careers page. The API is public, documented, and requires no authentication.
- **Linear** (real official source): Uses Ashby ATS public API at https://api.ashbyhq.com/posting-api/job-board/linear. Ashby is a legitimate ATS provider used by Linear for their official careers page. The API is public, documented, and requires no authentication.
- **Nexus Technologies** (fictional demo): Fictional company with fictional API endpoint used for demonstrating the scraper contract with deterministic fixtures. Not a real verified source.

**Key architectural principles:**
- Celery is orchestration only (scrapers remain independent)
- Scrapers are isolated from database operations
- Source-specific logic is contained in individual scraper classes
- NormalizedJob provides a common contract for all scrapers
- Deduplication is handled via (company, external_job_id) constraint
- Tests use deterministic fixtures, not live network requests
- No public API allows arbitrary users to create jobs
- Source registry prevents arbitrary source execution
- Task execution is at-least-once (idempotency via database constraints)
- Transient failures trigger bounded retry with exponential backoff
- Permanent failures (malformed data, unknown source) do not retry
- HTTP 429 responses respect Retry-After header when available
- PostgreSQL is the source of truth for ingestion state (Redis is broker only)
- IngestionRun provides operational visibility without complex monitoring infrastructure
- Overlap prevention uses database constraints (no distributed locking required)
- Source health is derived from run history (no separate health model needed)

**Running manual ingestion (synchronous):**
```bash
cd backend
python manage.py ingest_jobs --source stripe
python manage.py ingest_jobs --source spotify
python manage.py ingest_jobs --source linear
python manage.py ingest_jobs --source stripe --dry-run
python manage.py ingest_jobs --source nexus_technologies  # fictional demo
```

**Running asynchronous ingestion (Celery):**
```bash
cd backend
python manage.py ingest_jobs --source stripe --async
python manage.py ingest_jobs --source spotify --async
python manage.py ingest_jobs --source linear --async
```

The async command queues the task to Celery for background execution. Monitor task execution via Celery worker logs or Flower (if configured).

**Celery task retry behavior:**
- Transient failures (timeout, 429, 5xx) trigger retry
- Maximum 3 retries with exponential backoff (60s, 120s, 240s)
- HTTP 429 respects Retry-After header (capped at 300s)
- Permanent failures (malformed data, unknown source) do not retry
- Task results are serializable primitives (source, fetched, created, updated, skipped, failed)
- Each task execution creates an IngestionRun record for operational tracking

**Ingestion status inspection:**
```bash
cd backend
python manage.py ingestion_status
python manage.py ingestion_status --source stripe
python manage.py ingestion_status --health
python manage.py ingestion_status --source stripe --health --limit 5
```

This command provides operational visibility into ingestion runs and source health without requiring a full monitoring dashboard.

**Scheduled ingestion (Celery Beat):**
- Stripe ingestion is scheduled every 4 hours by default (configurable via INGESTION_SCHEDULE_STRIPE_HOURS)
- Spotify ingestion is scheduled every 4 hours by default (configurable via INGESTION_SCHEDULE_SPOTIFY_HOURS)
- Linear ingestion is scheduled every 4 hours by default (configurable via INGESTION_SCHEDULE_LINEAR_HOURS)
- Celery Beat service runs alongside Celery worker in docker-compose.yml
- Schedules are registered via management command: `python manage.py register_schedule`
- Only sources in SOURCE_REGISTRY can be scheduled
- Overlap prevention ensures only one RUNNING run per source at a time

**Registering periodic schedules:**
```bash
cd backend
python manage.py register_schedule
```

This command creates or updates PeriodicTask records in django-celery-beat for all configured sources. It is safe to run multiple times - it will not create duplicate schedules.
