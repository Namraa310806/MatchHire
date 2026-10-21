#!/bin/bash
set -e

cd backend

echo "Running ruff linting..."
uv run ruff check .

echo "Running ruff formatting check..."
uv run ruff format --check .

echo "Running mypy type checking..."
uv run mypy config api

echo "Running pytest..."
uv run pytest

echo "All checks passed!"
