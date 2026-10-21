# MatchHire

MatchHire is a job aggregation and matching platform for India's Tier-2/3 freshers. The platform automatically fetches job listings from official company sources, matches them to user profiles, and provides a curated feed of relevant opportunities.

## Project Structure

```
matchhire/
├── backend/        # Django + DRF backend
├── frontend/       # React frontend (placeholder)
├── docker/         # Docker configuration
├── scripts/        # Utility scripts
├── docs/           # Documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Python 3.12 (for local development without Docker)
- uv (Python package manager) - install with: `pip install uv`

## Quick Start

### Using Docker Compose (Recommended)

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start all services:
   ```bash
   docker compose up --build
   ```

3. The backend will be available at `http://localhost:8000`

### Local Development

1. Navigate to backend:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables (copy `.env.example` to `.env` and configure)

4. Run migrations:
   ```bash
   uv run python manage.py migrate
   ```

5. Start the development server:
   ```bash
   uv run python manage.py runserver
   ```

## Running Tests

Run all checks (linting, type checking, tests):

**Linux/Mac:**
```bash
./scripts/check.sh
```

**Windows:**
```bash
scripts\check.bat
```

Or run individually:

```bash
cd backend

# Linting
uv run ruff check .

# Type checking
uv run mypy config api

# Tests
uv run pytest
```

## Health Check

Verify the service is running:

```bash
curl http://localhost:8000/api/health/
```

Expected response:
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

## Development

### Backend Stack

- Django 6.x
- Django REST Framework
- PostgreSQL 15
- Redis 7
- Celery + Celery Beat
- Python 3.12

### Dependency Management

We use `uv` for dependency management. It provides fast dependency resolution and installation.

### Settings

Django settings are split into:
- `config.settings.base` - Common settings
- `config.settings.development` - Development overrides
- `config.settings.test` - Test configuration
- `config.settings.production` - Production settings

Environment variable: `DJANGO_SETTINGS_MODULE`

## Documentation

- [Technical Decisions](docs/DECISIONS.md)
- [Project Rules](CLAUDE.md)

## License

To be determined.
