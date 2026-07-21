# MatchHire Backend Configuration

This directory contains the Django project configuration and cross-cutting concerns.

## Structure

```
matchhire_backend/
├── __init__.py
├── api/                        # API-level views and URLs
│   ├── urls.py
│   └── views.py
├── asgi.py                     # ASGI configuration
├── celery.py                   # Celery configuration
├── core/                       # Cross-cutting concerns
│   ├── apps.py                 # Core app configuration
│   ├── env.py                  # Environment configuration
│   ├── exceptions.py           # Custom exception handling
│   ├── middleware.py           # Custom middleware
│   ├── security_audit.py       # Security audit functions
│   ├── startup_checks.py       # Startup validation checks
│   ├── throttling.py           # Rate limiting configuration
│   └── validators.py           # Input validators
├── settings/                   # Environment-specific settings
│   ├── base.py                 # Base settings
│   ├── dev.py                  # Development settings
│   ├── prod.py                 # Production settings
│   └── test.py                 # Test settings
├── urls.py                     # Root URL configuration
└── wsgi.py                     # WSGI configuration
```

## Core Module

The `core/` module contains cross-cutting concerns used across all apps:

### env.py
Environment configuration using `python-decouple`. Provides `get_env()` helper for accessing environment variables with defaults and type casting.

### exceptions.py
Custom exception handling for consistent error responses across the API.

### middleware.py
Custom middleware including:
- Request ID generation for distributed tracing
- Request ID filter for logging

### security_audit.py
Security audit functions for validating configuration and detecting security issues.

### startup_checks.py
Startup validation checks to ensure required configuration is present before Django starts.

### throttling.py
Rate limiting configuration for different endpoint types.

### validators.py
Custom validators for input validation.

## Settings Module

The `settings/` module contains environment-specific settings:

### base.py
Base settings shared across all environments. Includes:
- Database configuration
- Installed apps
- Middleware
- REST framework configuration
- JWT settings
- CORS configuration
- Logging configuration

### dev.py
Development-specific settings that override base settings.

### prod.py
Production-specific settings with security hardening.

### test.py
Test-specific settings (SQLite in-memory database, throttling disabled).

## API Module

The `api/` module contains API-level views and URLs:
- Health check endpoints
- Version endpoint
- Root API routing

## When to Add Files

- **core/**: When adding cross-cutting concerns used by multiple apps
- **settings/**: When adding environment-specific configuration
- **api/**: When adding API-level endpoints (health, version, etc.)

## Dependencies

The `matchhire_backend` module should not depend on specific apps. Apps depend on `matchhire_backend`, not the other way around.
