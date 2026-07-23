.PHONY: help setup install format lint typecheck test check docs clean run docker-up docker-down verify local-install local-format local-lint local-typecheck local-test local-check

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Set up development environment
	@echo "Setting up development environment..."
	@cp .env.example .env
	@echo "Environment file created from .env.example"
	@echo "Run 'make install' to install pre-commit hooks"

install: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install
	@echo "Pre-commit hooks installed successfully"

format: ## Format code with Black and Ruff (Docker)
	@echo "Formatting code..."
	@docker compose exec web black backend/
	@docker compose exec web ruff format backend/
	@echo "Code formatted successfully"

lint: ## Run linting with Ruff (Docker)
	@echo "Running linters..."
	@docker compose exec web ruff check backend/
	@echo "Linting completed successfully"

typecheck: ## Run type checking with mypy (Docker)
	@echo "Running type checker..."
	@docker compose exec web mypy backend/
	@echo "Type checking completed successfully"

test: ## Run all tests (Docker)
	@echo "Running tests..."
	@docker compose exec web python manage.py test
	@echo "Tests completed successfully"

test-coverage: ## Run tests with coverage (Docker)
	@echo "Running tests with coverage..."
	@docker compose exec web coverage run --source='.' manage.py test
	@docker compose exec web coverage report
	@echo "Coverage report generated"

check: format lint typecheck test ## Run all quality checks (format, lint, typecheck, test) - Docker
	@echo "All quality checks passed!"

verify: ## Run comprehensive quality verification (format, lint, typecheck, Django checks, tests)
	@echo "Running comprehensive quality verification..."
	@docker compose exec web black --check backend/
	@docker compose exec web ruff check backend/
	@docker compose exec web ruff format --check backend/
	@docker compose exec web mypy backend/
	@docker compose exec web python manage.py check --deploy
	@docker compose exec web python manage.py test
	@echo "All quality verification checks passed!"

docs: ## Generate OpenAPI schema
	@echo "Generating OpenAPI schema..."
	@docker compose exec web python manage.py spectacular --color --file schema.openapi.json
	@echo "OpenAPI schema generated"

clean: ## Clean up cache and temporary files
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup completed"

run: ## Start the development stack
	docker compose up --build

docker-up: ## Start Docker containers
	docker compose up --build -d

docker-down: ## Stop Docker containers
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

shell: ## Open shell in web container
	docker compose exec web sh

migrate: ## Run database migrations
	docker compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker compose exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	docker compose exec web python manage.py createsuperuser

shell-plus: ## Open Django shell_plus
	docker compose exec web python manage.py shell_plus

collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

# Local development commands (non-Docker)
local-install: ## Install development dependencies locally
	@echo "Installing development dependencies..."
	@pip install -r backend/requirements.txt
	@echo "Dependencies installed successfully"

local-format: ## Format code locally (Black and Ruff)
	@echo "Formatting code locally..."
	@cd backend && black .
	@cd backend && ruff format .
	@echo "Code formatted successfully"

local-lint: ## Run linting locally (Ruff)
	@echo "Running linters locally..."
	@cd backend && ruff check .
	@echo "Linting completed successfully"

local-typecheck: ## Run type checking locally (mypy)
	@echo "Running type checker locally..."
	@cd backend && mypy .
	@echo "Type checking completed successfully"

local-test: ## Run tests locally
	@echo "Running tests locally..."
	@cd backend && python manage.py test
	@echo "Tests completed successfully"

local-check: local-format local-lint local-typecheck local-test ## Run all quality checks locally
	@echo "All quality checks passed!"

local-verify: ## Run comprehensive quality verification locally
	@echo "Running comprehensive quality verification locally..."
	@cd backend && black --check .
	@cd backend && ruff check .
	@cd backend && ruff format --check .
	@cd backend && mypy .
	@cd backend && python manage.py check --deploy
	@cd backend && python manage.py test
	@echo "All quality verification checks passed!"
