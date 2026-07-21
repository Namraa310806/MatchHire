# MatchHire Developer Guide

This guide helps developers set up, understand, and work with the MatchHire backend codebase.

## Table of Contents

- [Repository Setup](#repository-setup)
- [Running Locally](#running-locally)
- [Docker Workflow](#docker-workflow)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Database Migrations](#database-migrations)
- [Celery](#celery)
- [Debugging](#debugging)
- [Swagger/OpenAPI](#swaggeropenapi)
- [OpenAPI Generation](#openapi-generation)
- [Repository Structure](#repository-structure)

## Repository Setup

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- A code editor (VS Code, PyCharm, etc.)

### Cloning the Repository

```bash
git clone <repository-url>
cd matchhire
```

### Initial Setup

1. Copy the development environment file:
```bash
cp .env.development .env
```

2. Build and start the containers:
```bash
docker compose up --build
```

3. Run database migrations:
```bash
docker compose exec web python manage.py migrate
```

4. Create a superuser (optional):
```bash
docker compose exec web python manage.py createsuperuser
```

## Running Locally

MatchHire is a **Docker-first** project. All development work should be done through Docker Compose to ensure proper connectivity to database, Redis, Celery, and Nginx services.

### Starting the Stack

```bash
docker compose up --build
```

### Stopping the Stack

```bash
docker compose down
```

### Stopping with Volume Cleanup

```bash
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f celery-worker
```

## Docker Workflow

### Service Architecture

The Docker Compose setup includes:

- **web**: Django application server (Gunicorn in production, development server in dev)
- **celery-worker**: Celery background task workers
- **celery-beat**: Celery periodic task scheduler
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy and static file server
- **frontend**: React frontend development server

### Common Docker Commands

```bash
# Rebuild a specific service
docker compose up --build web

# Execute commands in the web container
docker compose exec web python manage.py <command>

# Access Django shell
docker compose exec web python manage.py shell

# Access database shell
docker compose exec db psql -U matchhire -d matchhire

# Access Redis CLI
docker compose exec redis redis-cli
```

### Container Management

```bash
# View running containers
docker compose ps

# Restart a service
docker compose restart web

# Remove stopped containers
docker compose rm
```

## Environment Variables

MatchHire uses environment variables for configuration. Environment files are never committed to git.

### Environment Files

- `.env.development`: Local development defaults (tracked in git)
- `.env.production.example`: Production template (tracked in git)
- `.env`: Runtime environment (not tracked, created by developer)

### Switching Environment Files

```bash
# Use production environment
ENV_FILE=.env.production docker compose up
```

### Key Environment Variables

#### Database

```bash
DB_NAME=matchhire
DB_USER=matchhire
DB_PASSWORD=matchhire
DB_HOST=db
DB_PORT=5432
```

#### Django

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Redis/Celery

```bash
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### CORS

```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Adding New Environment Variables

1. Add the variable to `.env.development` with a safe default
2. Add the variable to `.env.production.example` without a value
3. Access the variable in code using `matchhire_backend.core.env.get_env()`

```python
from matchhire_backend.core.env import get_env

MY_VAR = get_env("MY_VAR", default="default_value")
```

## Running Tests

MatchHire uses Django's built-in test framework with SQLite in-memory database for test runs.

### Running All Tests

```bash
docker compose exec web python manage.py test
```

### Running Specific App Tests

```bash
docker compose exec web python manage.py test apps.users
docker compose exec web python manage.py test apps.matching
```

### Running Specific Test Class

```bash
docker compose exec web python manage.py test apps.matching.tests.MatchingServiceTests
```

### Running Specific Test Method

```bash
docker compose exec web python manage.py test apps.matching.tests.MatchingServiceTests.test_calculate_match
```

### Test Options

```bash
# Verbose output
docker compose exec web python manage.py test --verbosity=2

# Keep test database
docker compose exec web python manage.py test --keepdb

# Parallel execution (with pytest-django)
docker compose exec web pytest
```

### Test Coverage

```bash
# Install coverage in container
docker compose exec web pip install coverage

# Run coverage
docker compose exec web coverage run --source='.' manage.py test

# Generate report
docker compose exec web coverage report
docker compose exec web coverage html
```

## Database Migrations

MatchHire uses Django migrations for database schema management.

### Creating Migrations

```bash
# Create migrations for an app
docker compose exec web python manage.py makemigrations <app_name>

# Create migrations for all apps
docker compose exec web python manage.py makemigrations
```

### Reviewing Migrations

```bash
# Show pending migrations
docker compose exec web python manage.py showmigrations

# Show SQL for a migration
docker compose exec web python manage.py sqlmigrate <app_name> <migration_number>
```

### Applying Migrations

```bash
# Apply all migrations
docker compose exec web python manage.py migrate

# Apply migrations for a specific app
docker compose exec web python manage.py migrate <app_name>
```

### Rolling Back Migrations

```bash
# Roll back one migration
docker compose exec web python manage.py migrate <app_name> <previous_migration>

# Roll back all migrations for an app
docker compose exec web python manage.py migrate <app_name> zero
```

### Migration Best Practices

1. Always review generated migrations before committing
2. Write descriptive migration names: `python manage.py makemigrations --name add_user_role_field`
3. Avoid data migrations in schema migrations
4. Test migrations on a copy of production data before deploying
5. Never modify committed migrations

## Celery

MatchHire uses Celery for background task processing.

### Celery Services

- **celery-worker**: Executes background tasks
- **celery-beat**: Schedules periodic tasks

### Monitoring Celery

```bash
# View worker logs
docker compose logs -f celery-worker

# View beat logs
docker compose logs -f celery-beat
```

### Running Celery Tasks Manually

```bash
# Access Django shell
docker compose exec web python manage.py shell

# Import and run task
from apps.matching.tasks import recalculate_candidate_matches
result = recalculate_candidate_matches.delay(candidate_id="user-id")
```

### Inspecting Tasks

```bash
# Access Django shell
docker compose exec web python manage.py shell

# Check task status
from celery.result import AsyncResult
task = AsyncResult("task-id")
task.status  # PENDING, STARTED, SUCCESS, FAILURE
task.result  # Task result if successful
```

### Flower (Optional)

To add Flower for Celery monitoring:

1. Add Flower to requirements.txt:
```
flower==2.0.1
```

2. Add Flower service to docker-compose.yml:
```yaml
flower:
  build: ./backend
  command: celery -A matchhire_backend flower
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
```

3. Access Flower at http://localhost:5555

## Debugging

### Django Debug Mode

Debug mode is controlled by the `DEBUG` environment variable:

```bash
# .env file
DEBUG=True
```

### Debugging in VS Code

1. Install the Python extension
2. Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/manage.py",
      "args": ["runserver", "0.0.0.0:8000"],
      "django": true,
      "justMyCode": true
    }
  ]
}
```

Note: For Docker-based debugging, use remote debugging or add breakpoints and use `docker compose exec web python manage.py shell` for interactive debugging.

### Logging

MatchHire uses structured logging with request IDs:

```python
import logging

logger = logging.getLogger("matchhire")

logger.info("User logged in", extra={"request_id": request.id})
logger.error("Failed to process resume", exc_info=True)
```

View logs:
```bash
docker compose logs -f web
```

### Common Debugging Scenarios

#### Database Connection Issues

```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db

# Test database connection
docker compose exec web python manage.py dbshell
```

#### Celery Task Not Running

```bash
# Check worker status
docker compose ps celery-worker

# Check worker logs
docker compose logs celery-worker

# Check Redis connection
docker compose exec redis redis-cli ping
```

#### Migration Conflicts

```bash
# Show migration conflicts
docker compose exec web python manage.py makemigrations --merge

# Or fake migration if needed
docker compose exec web python manage.py migrate --fake
```

## Swagger/OpenAPI

MatchHire uses drf-spectacular for OpenAPI documentation.

### Accessing Swagger UI

In development, Swagger UI is available at:
```
http://localhost:8000/api/v1/schema/swagger-ui/
```

### Accessing ReDoc

In development, ReDoc is available at:
```
http://localhost:8000/api/v1/schema/redoc/
```

### Downloading OpenAPI Schema

```bash
# Download JSON schema
docker compose exec web python manage.py spectacular --color --file schema.openapi.json

# Download YAML schema
docker compose exec web python manage.py spectacular --color --file schema.openapi.yml --format yaml
```

## OpenAPI Generation

OpenAPI schema is automatically generated from code. No manual schema maintenance is required.

### Customizing Schema

Add decorators to views or serializers:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    summary="List jobs",
    description="Retrieve a paginated list of active jobs",
    parameters=[
        OpenApiParameter(
            name="search",
            description="Search query for job title",
            required=False,
            type=str
        )
    ],
    responses={200: JobSerializer}
)
class JobListView(generics.ListAPIView):
    queryset = Job.objects.filter(status=Job.JobStatus.ACTIVE)
    serializer_class = JobSerializer
```

### Schema Validation

Validate that the schema is correct:

```bash
docker compose exec web python manage.py spectacular --validate
```

## Repository Structure

```
matchhire/
├── backend/
│   ├── apps/                    # Django apps
│   │   ├── admin/              # Admin and moderation
│   │   ├── analytics/          # Analytics and metrics
│   │   ├── applications/       # Job applications
│   │   ├── core/               # Core utilities (empty, uses matchhire_backend/core)
│   │   ├── interviews/         # Interview management
│   │   ├── jobs/               # Job postings
│   │   ├── matching/           # Matching engine
│   │   ├── notifications/      # Notification system
│   │   ├── resumes/            # Resume management
│   │   └── users/              # User management and auth
│   ├── matchhire_backend/      # Django project configuration
│   │   ├── api/                # API-level views and URLs
│   │   ├── core/               # Cross-cutting concerns
│   │   │   ├── apps.py
│   │   │   ├── env.py          # Environment configuration
│   │   │   ├── exceptions.py   # Custom exception handling
│   │   │   ├── middleware.py   # Custom middleware
│   │   │   ├── security_audit.py
│   │   │   ├── startup_checks.py
│   │   │   ├── throttling.py
│   │   │   └── validators.py
│   │   ├── settings/           # Environment-specific settings
│   │   │   ├── base.py         # Base settings
│   │   │   ├── dev.py          # Development settings
│   │   │   ├── prod.py         # Production settings
│   │   │   └── test.py         # Test settings
│   │   ├── asgi.py
│   │   ├── celery.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   ├── requirements.txt
│   └── schema.yml              # Database schema (Prisma format)
├── frontend/                   # React frontend
├── docker/                      # Docker configuration files
├── nginx/                       # Nginx configuration
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
│   ├── architecture/            # Architecture documentation
│   ├── adr/                    # Architecture Decision Records
│   ├── api/                    # API documentation
│   ├── deployment/             # Deployment guides
│   ├── development/            # Developer guides
│   └── guides/                 # User guides
├── .env.development            # Development environment template
├── .env.production.example     # Production environment template
├── .env.example                # General environment template
├── .gitignore
├── docker-compose.yml
├── Makefile
└── README.md
```

### App Structure

Each Django app follows this structure:

```
apps/<app_name>/
├── __init__.py
├── admin.py                   # Django admin configuration
├── apps.py                    # App configuration
├── migrations/                 # Database migrations
├── models.py                  # Database models
├── permissions.py             # Custom permissions
├── serializers.py             # DRF serializers
├── services/                  # Business logic (service layer)
│   └── <service_name>.py
├── signals.py                 # Django signals
├── tasks.py                   # Celery tasks
├── tests.py                   # Tests
├── urls.py                    # URL routing
└── views.py                   # API views
```

### Adding a New Django App

```bash
# Create the app
docker compose exec web python manage.py startapp apps/<app_name>

# Add to apps/<app_name>/services/ directory
mkdir -p backend/apps/<app_name>/services

# Add to INSTALLED_APPS in matchhire_backend/settings/base.py
```

## Common Development Tasks

### Adding a New API Endpoint

1. Add URL in `apps/<app>/urls.py`
2. Create view in `apps/<app>/views.py`
3. Create serializer in `apps/<app>/serializers.py`
4. Add business logic to `apps/<app>/services/`
5. Add tests in `apps/<app>/tests.py`
6. Test the endpoint

### Adding a New Celery Task

1. Create task in `apps/<app>/tasks.py`
2. Use `@shared_task` decorator
3. Make task idempotent
4. Add tests for the task
5. Trigger task from view or signal

### Adding a New Model Field

1. Add field to model in `apps/<app>/models.py`
2. Create migration: `docker compose exec web python manage.py makemigrations <app>`
3. Review migration
4. Apply migration: `docker compose exec web python manage.py migrate`
5. Update serializer if needed
6. Update tests

### Adding Environment Configuration

1. Add variable to `.env.development`
2. Add variable to `.env.production.example`
3. Access via `get_env()` in `matchhire_backend/core/env.py`
4. Add validation in `matchhire_backend/core/startup_checks.py` if critical

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <pid> /F
```

### Docker Container Won't Start

```bash
# Check container logs
docker compose logs <service>

# Rebuild container
docker compose up --build <service>

# Remove volumes and restart
docker compose down -v
docker compose up --build
```

### Permission Denied Errors

```bash
# On Windows, ensure Docker Desktop is running with proper permissions
# Check Docker Desktop settings > Resources > File sharing
```

### Tests Failing Due to Database

```bash
# Ensure test database is clean
docker compose exec web python manage.py test --keepdb=False

# Check for migration issues
docker compose exec web python manage.py showmigrations
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [MatchHire Architecture](../architecture/system-overview.md)
- [Architecture Decision Records](../adr/)
