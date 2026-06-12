# MatchHire

MatchHire is a verified job aggregation and intelligent matching platform that only ingests jobs from official company career portals and never allows manual posting. It is built to normalize, score, and match opportunities against candidate profiles with a production-minded Django backend, React frontend, PostgreSQL, Redis, Celery, Docker, and Nginx.

## Environment Setup

Environment is centralized through `.env`-style files and Django helper functions. Use `.env.development` for local Docker and development work. Use `.env.production.example` as the template for production secrets and copy it to your deployment-specific production file.

## Development Setup

The development environment uses non-secret defaults for local Docker-based work. The stack expects `SECRET_KEY`, `DEBUG`, database settings, and Redis/Celery values to be present from the active environment file.

## Production Setup

Production settings validate all required secrets before Django starts. Fill in the production environment file with real values, keep it out of git, and load it into Docker or your runtime environment at deployment time.

## Secrets Management

Secrets are never committed. The repository ignores `.env` files by default while allowing safe templates such as `.env.example` and `.env.production.example` to remain tracked. Never store production credentials in the repo.

## Docker Usage

Start the stack with:

```bash
docker compose up --build
```

You can override the active environment file by setting `ENV_FILE` before running Compose.

## Tech Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Backend | Django, Django REST Framework | API and domain logic |
| Auth | djangorestframework-simplejwt, PyJWT | JWT authentication |
| Data | PostgreSQL | Primary database |
| Cache / Broker | Redis | Cache and Celery broker |
| Tasks | Celery | Async processing |
| Scraping | Scrapy, Playwright, PyMuPDF | Official portal ingestion |
| Matching | scikit-learn, sentence-transformers | Ranking and semantic matching |
| Frontend | React, Vite, React Router, Axios, TanStack Query, Tailwind CSS | User interface |
| Containers | Docker, Docker Compose, Nginx | Deployment and reverse proxy |

## Folder Structure

```text
matchhire/
├── backend/
│   ├── apps/
│   │   ├── jobs/
│   │   ├── matching/
│   │   └── users/
│   ├── matchhire_backend/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
├── docker/
├── nginx/
├── scripts/
├── .gitignore
├── README.md
└── docker-compose.yml
```

## Quick Start

```bash
docker compose up --build
```

## Development Workflow

MatchHire is a **Docker-first** project. All Django management commands must be executed through Docker Compose to ensure proper connectivity to the database and Redis services.

### Django Management Commands

Never run `python manage.py ...` directly from Windows. Always use:

```bash
docker compose exec web python manage.py <command>
```

### Common Commands

```bash
# Database migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Run tests
docker compose exec web python manage.py test

# Django shell
docker compose exec web python manage.py shell

# Create superuser
docker compose exec web python manage.py createsuperuser

# Check configuration
docker compose exec web python manage.py check
```

### Development Guidelines

1. Keep business logic in the appropriate Django app under `backend/apps/`.
2. Use the environment files for all secrets and runtime configuration.
3. Run Django through Docker during normal development so database, Redis, Celery, and Nginx stay aligned.
4. Keep public HTTP access behind the Nginx proxy and use the API for all app interactions.
5. Add new backend work before introducing matching UI changes.
