# MatchHire

[![CI](https://github.com/your-org/matchhire/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/matchhire/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://docs.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

MatchHire is a verified job aggregation and intelligent matching platform that ingests jobs exclusively from official company career portals. The platform normalizes, scores, and matches opportunities against candidate profiles using a production-grade Django backend with React frontend, PostgreSQL, Redis, Celery, and Nginx.

## 🎯 Features

- **Verified Job Sources**: Jobs ingested only from official company career portals
- **AI-Powered Matching**: Intelligent candidate-job matching with semantic analysis
- **Resume Parsing**: Automated resume extraction and structured data parsing (PDF, DOCX)
- **Role-Based Access Control**: Granular permissions for candidates, recruiters, and admins
- **JWT Authentication**: Secure token-based authentication with cookie storage
- **Interview Management**: Complete interview scheduling and workflow
- **Real-time Notifications**: In-platform notification system
- **Analytics Dashboard**: Comprehensive hiring analytics for recruiters
- **OpenAPI Documentation**: Auto-generated API documentation with Swagger UI
- **Production-Ready**: Docker-based deployment with comprehensive testing

## 🏗️ Architecture

MatchHire follows a service-oriented architecture with clear separation of concerns:

- **Service Layer**: Business logic encapsulated in service classes
- **Thin Views**: Views handle HTTP concerns only
- **Background Processing**: Celery for async operations
- **Request Tracing**: Request ID middleware for distributed logging
- **Explicit Transactions**: Database transactions managed at service layer

For detailed architecture information, see [Architecture Documentation](docs/architecture/system-overview.md).

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/matchhire.git
cd matchhire

# Set up development environment
make setup

# Install pre-commit hooks
make install

# Start the stack
make docker-up

# Run database migrations
make migrate

# Create a superuser (optional)
make createsuperuser
```

### Local Development (Optional)

If you prefer to develop without Docker:

```bash
# Install dependencies locally
make local-install

# Run quality checks locally
make local-check
```

The application will be available at:
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- Swagger UI: http://localhost:8000/api/v1/schema/swagger-ui/

## 📚 Documentation

- **[Developer Guide](docs/development/developer-guide.md)**: Comprehensive setup and development instructions
- **[Architecture Documentation](docs/architecture/system-overview.md)**: System architecture and design decisions
- **[Coding Standards](docs/development/coding-standards.md)**: Code style and best practices
- **[API Documentation](docs/api/)**: API reference (OpenAPI/Swagger)
- **[Deployment Guide](docs/deployment/)**: Production deployment instructions
- **[Architecture Decision Records](docs/adr/)**: Technical decision documentation
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

## 🛠️ Tech Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.1.7 |
| API | Django REST Framework | 3.15.2 |
| Authentication | djangorestframework-simplejwt | 5.5.0 |
| Database | PostgreSQL | Latest |
| Cache/Broker | Redis | 5.2.1 |
| Task Queue | Celery | 5.4.0 |
| Document Processing | PyMuPDF, PyPDF2, python-docx | Latest |
| Machine Learning | scikit-learn, sentence-transformers | Latest |
| API Documentation | drf-spectacular | 0.29.0 |
| WSGI Server | Gunicorn | 23.0.0 |

### Frontend

- React with Vite
- React Router
- TanStack Query
- Tailwind CSS
- Axios

### Infrastructure

- Docker & Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (database)
- Redis (cache & message broker)

## 📁 Project Structure

```
matchhire/
├── backend/                    # Django backend
│   ├── apps/                  # Django applications
│   │   ├── admin/            # Admin and moderation
│   │   ├── analytics/        # Analytics and metrics
│   │   ├── applications/     # Job applications
│   │   ├── interviews/       # Interview management
│   │   ├── jobs/             # Job postings
│   │   ├── matching/         # Matching engine
│   │   ├── notifications/    # Notification system
│   │   ├── resumes/          # Resume management
│   │   └── users/            # User management
│   ├── matchhire_backend/     # Django project configuration
│   │   ├── api/              # API-level views and URLs
│   │   ├── core/             # Cross-cutting concerns
│   │   ├── settings/         # Environment-specific settings
│   │   ├── celery.py         # Celery configuration
│   │   └── urls.py           # Root URL configuration
│   ├── manage.py
│   └── requirements.txt
├── frontend/                  # React frontend
├── docker/                     # Docker configuration files
├── nginx/                      # Nginx configuration
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
│   ├── architecture/          # Architecture documentation
│   ├── adr/                   # Architecture Decision Records
│   ├── api/                   # API documentation
│   ├── deployment/            # Deployment guides
│   ├── development/           # Developer guides
│   └── guides/                # User guides
├── .env.development           # Development environment template
├── .env.production.example    # Production environment template
├── .env.example               # General environment template
├── .gitignore
├── CONTRIBUTING.md            # Contribution guidelines
├── CODE_OF_CONDUCT.md         # Community code of conduct
├── SECURITY.md                # Security policy
├── SUPPORT.md                 # Support information
├── CHANGELOG.md               # Version history
├── ROADMAP.md                 # Project roadmap
├── VISION.md                  # Project vision
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🔧 Development Workflow

MatchHire is a **Docker-first** project. All Django management commands must be executed through Docker Compose.

### Common Commands

```bash
# Show all available commands
make help

# Database migrations
make makemigrations
make migrate

# Run tests
make test
make test-coverage

# Code quality
make format
make lint
make typecheck
make check

# Django shell
make shell

# Create superuser
make createsuperuser

# Check configuration
docker compose exec web python manage.py check

# Generate OpenAPI schema
make docs
```

### Environment Configuration

Environment variables are managed through `.env` files:

- `.env.development`: Local development defaults (tracked in git)
- `.env.production.example`: Production template (tracked in git)
- `.env`: Runtime environment (not tracked, created by developer)

**Important**: Never commit `.env` files with secrets to the repository.

## 🧪 Testing

MatchHire maintains comprehensive test coverage:

```bash
# Run all tests
docker compose exec web python manage.py test

# Run with coverage
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
```

## 🔒 Security

MatchHire includes several security features:

- JWT authentication with short-lived access tokens (15 minutes)
- Refresh token rotation to prevent token theft replay attacks
- Role-Based Access Control (RBAC)
- Rate limiting per endpoint
- Input validation via serializers
- SQL injection prevention via ORM
- XSS prevention via DRF serializers
- httpOnly cookies to prevent XSS token theft
- SameSite=Lax to prevent CSRF attacks

For security policies and vulnerability reporting, see [SECURITY.md](SECURITY.md).

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

### Development Guidelines

1. Follow the [Coding Standards](docs/development/coding-standards.md)
2. Ensure all tests pass before submitting a PR
3. Update documentation for any user-facing changes
4. Follow the [Definition of Done](docs/development/definition-of-done.md)
5. Write descriptive commit messages following conventional commit format

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for information about completed phases, current work, and future plans.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: See [docs/](docs/) for comprehensive documentation
- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/your-org/matchhire/issues)
- **Discussions**: Join discussions at [GitHub Discussions](https://github.com/your-org/matchhire/discussions)
- **Security**: Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))
- **Support**: See [SUPPORT.md](SUPPORT.md) for additional support options

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- All contributors who have helped improve MatchHire
- Open-source projects that make MatchHire possible

## 📌 Project Status

**Current Version**: 1.0.0  
**Status**: Production-Ready  
**Last Updated**: July 2026

For version history, see [CHANGELOG.md](CHANGELOG.md).
