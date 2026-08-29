# MatchHire

MatchHire is a verified job aggregation and intelligent job-matching platform.

## Current Implementation Status: Phase 2A

This is Phase 2A of the MatchHire project: core domain models.

**Currently implemented:**
- Django backend with Django REST Framework
- React frontend with Vite
- PostgreSQL and Redis via Docker Compose with health checks
- Health endpoint at `/api/health/` (checks database and Redis connectivity)
- Environment-based configuration (database, Redis, CORS)
- Custom user model with email-based authentication
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
- Comprehensive model tests (39 tests passing)
- Database migrations for all domain models

**Not yet implemented (planned for future phases):**
- Authentication endpoints (JWT, login/register)
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

## Health Endpoint

The health endpoint is available at:

```
GET http://localhost:8000/api/health/
```

Expected response:
```json
{
    "status": "ok"
}
```

## Architecture Notes

- The backend is structured with domain-specific Django apps in the `apps/` directory
- PostgreSQL and Redis are configured with health checks in Docker Compose
- PostgreSQL credentials are configurable via environment variables in both Docker Compose and Django settings
- Environment variables are managed through `python-decouple`
- CORS is configurable via environment variables (CORS_ALLOWED_ORIGINS)
- Django REST Framework is configured with permissive permissions for development
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
- Authentication endpoints (JWT, login/register)
- Job ingestion from verified sources (scraping pipeline)
- Resume upload and parsing
- ML-based job matching (TF-IDF, embeddings, scoring algorithms)
- Celery for async task processing
- Redis caching
- Subscription and payment integration (Razorpay)
- Production deployment with Nginx
