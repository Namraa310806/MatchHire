# MatchHire

MatchHire is a verified job aggregation and intelligent job-matching platform.

## Current Implementation Status: Phase 1B

This is Phase 1B of the MatchHire project: development infrastructure hardening.

**Currently implemented:**
- Django backend with Django REST Framework
- React frontend with Vite
- PostgreSQL and Redis via Docker Compose with health checks
- Health endpoint at `/api/health/` (checks database and Redis connectivity)
- Environment-based configuration (database, Redis, CORS)
- Basic test suite
- Centralized Redis configuration for future Celery integration

**Not yet implemented (planned for future phases):**
- Authentication and user management
- Job scraping and ingestion
- Resume upload and parsing
- Matching engine (TF-IDF, embeddings)
- Company and job models
- Recruiter functionality
- Subscriptions and payments (Razorpay)
- Celery async tasks
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
│   │   └── health/      # Health check app
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

- The backend is structured to support future Django apps in the `apps/` directory
- PostgreSQL and Redis are configured with health checks in Docker Compose
- PostgreSQL credentials are configurable via environment variables in both Docker Compose and Django settings
- Environment variables are managed through `python-decouple`
- CORS is configurable via environment variables (CORS_ALLOWED_ORIGINS)
- Django REST Framework is configured with permissive permissions for development
- Redis configuration is centralized in settings.py for future Celery integration

## Future Phases

The following features are planned for implementation in future phases:

- User authentication and authorization
- Job ingestion from verified sources
- Resume parsing and analysis
- ML-based job matching (TF-IDF, embeddings)
- Company and recruiter management
- Subscription and payment integration
- Celery for async task processing
- Production deployment with Nginx
