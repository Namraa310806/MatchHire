# Multi-stage production Dockerfile for MatchHire Backend
# Optimized for security, size, and performance

# Stage 1: Base builder
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base as dependencies

WORKDIR /app

# Copy requirements files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt --no-cache-dir

# Stage 3: Development
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir \
    black \
    ruff \
    mypy \
    django-stubs \
    djangorestframework-stubs \
    types-redis \
    types-PyYAML \
    pre-commit \
    coverage

# Copy application code
COPY . .

# Stage 4: Production
FROM base as production

WORKDIR /app

# Copy only runtime dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r matchhire && useradd -r -g matchhire matchhire && \
    chown -R matchhire:matchhire /app

# Switch to non-root user
USER matchhire

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/', timeout=5)" || exit 1

# Run with gunicorn
CMD ["gunicorn", "matchhire_backend.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keepalive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# Stage 5: Celery Worker
FROM production as celery-worker

# Override CMD for Celery
CMD ["celery", "-A", "matchhire_backend.celery", "worker", \
     "--loglevel=info", \
     "--concurrency=4", \
     "--max-tasks-per-child=1000"]

# Stage 6: Celery Beat
FROM production as celery-beat

# Override CMD for Celery Beat
CMD ["celery", "-A", "matchhire_backend.celery", "beat", \
     "--loglevel=info", \
     "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]

# Stage 7: Minimal (for testing)
FROM python:3.11-slim as minimal

WORKDIR /app

# Copy only essential files for testing
COPY requirements.txt ./
COPY matchhire_backend/ ./matchhire_backend/
COPY apps/ ./apps/

# Install minimal dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
