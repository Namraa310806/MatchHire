FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies and create venv in a location that won't be mounted
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Use the venv that was created during build
ENV PATH="/app/.venv/bin:$PATH"

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
