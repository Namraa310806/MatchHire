# Django Apps

This directory contains Django applications that implement the core business logic of MatchHire.

## App Structure

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

## Apps

### admin
Admin and moderation features for platform management.

### analytics
Dashboard and analytics for recruiters and administrators.

### applications
Job application workflow and management.

### core
Core utilities (currently empty, uses matchhire_backend/core).

### interviews
Interview scheduling and management.

### jobs
Job posting and management.

### matching
AI-powered candidate-job matching engine.

### notifications
Real-time notification system.

### resumes
Resume upload, parsing, and management.

### users
User management, authentication, and role-based access control.

## Adding a New App

When adding a new Django app:

1. Create the app:
```bash
docker compose exec web python manage.py startapp apps/<app_name>
```

2. Add services directory:
```bash
mkdir -p backend/apps/<app_name>/services
```

3. Add to INSTALLED_APPS in `matchhire_backend/settings/base.py`:
```python
INSTALLED_APPS = [
    # ...
    'apps.<app_name>.apps.<AppName>Config',
]
```

4. Add URL routing in `matchhire_backend/api/urls.py`:
```python
path('<app_name>/', include(('apps.<app_name>.urls', '<app_name>'), namespace='<app_name>')),
```

## Dependencies

Apps should depend on lower-level modules only:
- Views depend on Services
- Services depend on Models
- Avoid circular dependencies

## When to Add Files

- **models.py**: When adding new database entities
- **serializers.py**: When adding or modifying API endpoints
- **views.py**: When adding new API endpoints
- **services/**: When adding business logic
- **tasks.py**: When adding background processing
- **permissions.py**: When adding custom permission classes
- **signals.py**: When responding to Django model events
- **tests.py**: Always add tests for new functionality

## Testing

Each app should have comprehensive tests in `tests.py`:
- Unit tests for models and services
- Integration tests for service layer
- API tests for views and endpoints
