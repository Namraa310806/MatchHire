# MatchHire

MatchHire is a verified job aggregation and intelligent job-matching platform.

## Current Implementation Status: Phase 3D

This is Phase 3D of the MatchHire project: Authentication Hardening & Authorization Boundary.

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
- Django admin interfaces for all models (Job admin is read-only to preserve source-only ingestion)
- Comprehensive test suite (183 tests passing)
- Database migrations for all domain models
- Development seed data management command for local development
- Authorization boundary documented (see `backend/apps/users/AUTHORIZATION_BOUNDARY.md`)

**Not yet implemented (planned for future phases):**
- Job scraping and ingestion pipeline
- Resume upload and parsing
- Matching engine (TF-IDF, embeddings, scoring algorithms)
- Celery async tasks
- Redis caching
- Payment integration (Razorpay)
- Production deployment

## Technology Stack

- **Backend:** Python, Django 4.2.7, Django REST Framework 3.14.0
- **Frontend:** React with Vite
- **Database:** PostgreSQL 15
- **Cache/Message Broker:** Redis 7
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

## Starting PostgreSQL and Redis

Start the infrastructure services using Docker Compose:

```bash
docker-compose up -d
```

To check service status:
```bash
docker-compose ps
```

To stop services:
```bash
docker-compose down
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

- Phase 2B: Indexes, constraints, and performance optimization
- Job ingestion from verified sources (scraping pipeline)
- Resume upload and parsing
- ML-based job matching (TF-IDF, embeddings, scoring algorithms)
- Celery for async task processing
- Redis caching
- Subscription and payment integration (Razorpay)
- Production deployment with Nginx
