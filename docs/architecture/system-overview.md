# MatchHire System Architecture

## Project Overview

MatchHire is a verified job aggregation and intelligent matching platform that ingests jobs exclusively from official company career portals. The platform normalizes, scores, and matches opportunities against candidate profiles using a production-minded Django backend with React frontend, PostgreSQL, Redis, Celery, and Nginx.

### Core Value Proposition

- **Verified Job Sources Only**: Jobs are ingested only from official company career portals, never manual postings
- **Intelligent Matching**: AI-powered candidate-job matching using semantic analysis and structured resume data
- **Production-Grade Engineering**: Built with enterprise-grade patterns including service layers, background processing, and comprehensive testing

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx Reverse Proxy                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌──────▼──────┐  ┌──────────▼─────────┐
│  React Frontend │  │ Django API  │  │   Django Admin     │
│   (Vite/React)  │  │  (DRF/JWT)  │  │                    │
└────────────────┘  └──────┬──────┘  └────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼────┐ ┌─────▼─────┐ ┌───▼────────┐
     │ PostgreSQL  │ │   Redis    │ │   Celery   │
     │   Database  │ │  Cache/Broker│ │  Workers   │
     └─────────────┘ └───────────┘ └────────────┘
```

## Django Apps Structure

The backend is organized into domain-specific Django apps under `backend/apps/`:

### Core Apps

- **`users`**: User management, authentication, and role-based access control (RBAC)
  - Custom user model with role-based permissions
  - JWT authentication with cookie-based token storage
  - Profile management for candidates and recruiters

- **`jobs`**: Job posting and management
  - Job CRUD operations
  - Job status lifecycle (draft, active, closed, archived)
  - Employment type and experience level categorization

- **`resumes`**: Resume upload, parsing, and management
  - Multi-format resume upload (PDF, DOCX)
  - Resume parsing with structured data extraction
  - Resume versioning and history tracking

- **`matching`**: AI-powered candidate-job matching
  - Deterministic matching algorithm with weighted scoring
  - Match score calculation (skills 60%, experience 30%, education 10%)
  - Recommendation generation and caching

- **`applications`**: Job application workflow
  - Application submission and tracking
  - Application status lifecycle
  - Application history and analytics

- **`interviews`**: Interview scheduling and management
  - Interview creation and scheduling
  - Interview status tracking
  - Interview feedback collection

- **`notifications`**: Notification system
  - Real-time notification delivery
  - Notification preferences
  - Notification history

- **`analytics`**: Dashboard and analytics
  - Application metrics
  - Hiring pipeline analytics
  - Performance reporting

- **`admin`**: Admin and moderation
  - Content moderation
  - User management
  - System administration

### Framework Apps

- **`core`** (in `matchhire_backend/core/`): Cross-cutting concerns
  - Environment configuration and validation
  - Custom exception handling
  - Request ID middleware for distributed tracing
  - Security validators and startup checks
  - Throttling configuration

## Service Layer

MatchHire follows a service layer pattern to separate business logic from views:

### Service Organization

Services are located in `apps/<app>/services/` directories:

- **`matching/services/matching.py`**: `MatchingService` class
  - Calculates match scores between candidates and jobs
  - Handles skill, experience, and education scoring
  - Provides batch recalculation methods

- **`resumes/services/`**: Resume parsing and processing services
- **`applications/services/`**: Application workflow services
- **`notifications/services/`**: Notification delivery services

### Service Layer Principles

- **Fat Services, Thin Views**: Business logic resides in services, not views
- **Deterministic Behavior**: Services produce consistent outputs for given inputs
- **Idempotency**: Service methods can be safely retried
- **Transaction Management**: Services handle database transactions explicitly

## Request Lifecycle

### HTTP Request Flow

```
1. Nginx receives request
   ↓
2. Nginx routes to Django (web container)
   ↓
3. Django middleware chain:
   - SecurityMiddleware
   - CorsMiddleware
   - SessionMiddleware
   - RequestIDMiddleware (generates unique request ID)
   - CommonMiddleware
   - CsrfViewMiddleware
   - AuthenticationMiddleware (JWT validation)
   - MessageMiddleware
   - XFrameOptionsMiddleware
   ↓
4. URL routing (api/v1/)
   ↓
5. View receives request
   ↓
6. View calls service layer
   ↓
7. Service executes business logic
   ↓
8. Service returns data to view
   ↓
9. View serializes response
   ↓
10. Response middleware chain
   ↓
11. Nginx returns response to client
```

### Request ID Tracking

Every request receives a unique `X-Request-ID` header generated by `RequestIDMiddleware`. This ID is:

- Added to all log entries via `RequestIDFilter`
- Included in error responses
- Enables distributed tracing across services

## Authentication Flow

### JWT Authentication Architecture

MatchHire uses JWT (JSON Web Tokens) with cookie-based storage:

### Token Lifecycle

```
1. User Login
   ↓
2. Server validates credentials
   ↓
3. Server generates JWT access token (15 min lifetime)
   ↓
4. Server generates JWT refresh token (7 day lifetime)
   ↓
5. Tokens stored in httpOnly cookies
   ↓
6. Access token sent with each request
   ↓
7. Middleware validates token on each request
   ↓
8. Expired access tokens refreshed using refresh token
   ↓
9. Refresh tokens rotated on each refresh
   ↓
10. Old refresh tokens blacklisted after rotation
```

### Authentication Components

- **`apps/users/authentication.py`**: Custom JWT authentication backend
  - Cookie-based token extraction
  - Token validation
  - User resolution from token

- **`apps/users/rbac.py`**: Role-based access control
  - Role definitions (CANDIDATE, RECRUITER, ADMIN)
  - Permission checks
  - Role-based view decorators

### Security Features

- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days
- Refresh token rotation on each use
- Token blacklisting after rotation
- httpOnly cookies prevent XSS
- SameSite=Lax prevents CSRF
- Secure flag in production

## Background Processing

### Celery Architecture

MatchHire uses Celery for asynchronous task processing:

### Task Categories

- **Resume Parsing**: CPU-intensive resume extraction and parsing
- **Matching Calculations**: Batch match score recalculations
- **Notifications**: Asynchronous notification delivery
- **Analytics**: Periodic metric aggregation

### Celery Configuration

- **Broker**: Redis
- **Result Backend**: Redis
- **Task Autodiscovery**: Enabled for all apps
- **Beat Scheduler**: For periodic tasks

### Task Implementation

Tasks are defined in `apps/<app>/tasks.py`:

- **`matching/tasks.py`**: Match recalculation tasks
- **notifications/tasks.py`**: Notification delivery tasks
- **resumes/tasks.py`**: Resume parsing tasks

### Task Execution Flow

```
1. View triggers task via .delay() or .apply_async()
   ↓
2. Task serialized and sent to Redis broker
   ↓
3. Celery worker picks up task from broker
   ↓
4. Worker executes task with Django app context
   ↓
5. Task result stored in Redis backend
   ↓
6. View can poll for task result or use callbacks
```

### Idempotency

All Celery tasks are designed to be idempotent:
- Re-running a task produces the same final state
- Database operations use `update_or_create` patterns
- No side effects from duplicate executions

## Notification Flow

### Notification Architecture

MatchHire implements a real-time notification system:

### Notification Types

- Application status updates
- Interview scheduling
- Match recommendations
- System announcements

### Notification Delivery

```
1. Event occurs (e.g., application submitted)
   ↓
2. Signal handler triggers notification creation
   ↓
3. Notification record created in database
   ↓
4. Celery task enqueued for delivery
   ↓
5. Task delivers notification via configured channels
   ↓
6. Notification marked as delivered
   ↓
7. Frontend polls or receives push notification
```

### Notification Components

- **`apps/notifications/models.py`**: Notification data model
- **`apps/notifications/services/`**: Notification delivery services
- **`apps/notifications/tasks.py`**: Asynchronous notification delivery
- **`apps/notifications/signals.py`**: Event-driven notification triggers

## Analytics Flow

### Analytics Architecture

MatchHire provides comprehensive analytics for recruiters and administrators:

### Metric Categories

- Application funnel metrics
- Hiring pipeline analytics
- Match score distributions
- Time-to-hire metrics
- Source attribution

### Data Collection

```
1. User actions emit signals
   ↓
2. Signal handlers record analytics events
   ↓
3. Events aggregated in periodic Celery tasks
   ↓
4. Aggregated metrics stored in database
   ↓
5. Analytics endpoints query aggregated data
   ↓
6. Frontend visualizes metrics
```

### Analytics Components

- **`apps/analytics/models.py`**: Analytics data models
- **`apps/analytics/services/`**: Metric calculation services
- **`apps/analytics/tasks.py`**: Periodic aggregation tasks

## Deployment Overview

### Container Architecture

MatchHire uses Docker Compose for local development and production deployment:

### Services

- **web**: Django application server (Gunicorn)
- **celery-worker**: Celery background task workers
- **celery-beat**: Celery periodic task scheduler
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy and static file server
- **frontend**: React frontend development server

### Environment Configuration

Environment-specific configuration via `.env` files:

- `.env.development`: Local development defaults
- `.env.production.example`: Production template
- `.env`: Runtime environment (not committed)

### Deployment Layers

```
1. Infrastructure Layer
   - Docker containers
   - Network isolation
   - Volume persistence

2. Application Layer
   - Django web server
   - Celery workers
   - Beat scheduler

3. Data Layer
   - PostgreSQL database
   - Redis cache/broker
   - Static/media file storage

4. Proxy Layer
   - Nginx reverse proxy
   - SSL termination
   - Static file serving
```

## Security Architecture

### Security Layers

1. **Network Security**
   - Nginx as reverse proxy
   - CORS configuration
   - Rate limiting per endpoint

2. **Application Security**
   - JWT authentication
   - Role-based access control
   - Request validation
   - SQL injection prevention (ORM)

3. **Data Security**
   - Environment-based secrets management
   - Password validation
   - Secure cookie flags
   - httpOnly cookies

4. **Operational Security**
   - Request ID tracking
   - Comprehensive logging
   - Security audit logs
   - Startup validation checks

### Security Components

- **`matchhire_backend/core/security_audit.py`**: Security audit functions
- **`matchhire_backend/core/validators.py`**: Input validation
- **`matchhire_backend/core/startup_checks.py`**: Runtime security validation
- **`matchhire_backend/core/throttling.py`**: Rate limiting configuration

## API Architecture

### RESTful API Design

MatchHire exposes a RESTful API via Django REST Framework:

### API Versioning

- URL path versioning: `/api/v1/`
- Current version: v1
- Backward compatibility maintained

### API Documentation

- **OpenAPI/Swagger**: Generated via drf-spectacular
- **Schema Endpoint**: `/api/v1/schema/`
- **Swagger UI**: Available in development
- **ReDoc**: Available in development

### API Structure

```
/api/v1/
├── auth/              # Authentication endpoints
├── users/             # User management
├── profiles/          # Profile management
├── resumes/           # Resume operations
├── jobs/              # Job management
├── applications/      # Application workflow
├── matching/          # Matching and recommendations
├── interviews/        # Interview management
├── notifications/     # Notification management
├── analytics/         # Analytics endpoints
└── admin/             # Admin endpoints
```

### API Features

- JWT authentication
- Pagination (PageNumberPagination)
- Rate limiting (per-endpoint throttling)
- Exception handling with custom error responses
- Request ID tracking
- OpenAPI schema generation

## Testing Architecture

### Test Organization

Tests are located in `apps/<app>/tests.py`:

### Test Categories

- Unit tests: Individual component testing
- Integration tests: Service layer testing
- API tests: Endpoint testing
- Operational tests: System health and configuration

### Test Configuration

- SQLite in-memory database for test runs
- Throttling disabled during tests
- Test-specific settings in `settings/test.py`

### Test Coverage

The backend maintains comprehensive test coverage across all apps and services.

## Technology Stack Summary

### Backend

- **Framework**: Django 5.1.7
- **API**: Django REST Framework 3.15.2
- **Authentication**: djangorestframework-simplejwt 5.5.0, PyJWT 2.9.0
- **Database**: PostgreSQL (psycopg2-binary 2.9.10)
- **Cache/Broker**: Redis 5.2.1
- **Task Queue**: Celery 5.4.0
- **Document Processing**: PyMuPDF 1.25.2, PyPDF2 3.0.1, python-docx 1.1.2
- **Machine Learning**: scikit-learn 1.6.1, sentence-transformers 3.4.1
- **Web Scraping**: Scrapy 2.12.0, Playwright 1.50.0
- **API Documentation**: drf-spectacular 0.29.0
- **Configuration**: python-decouple 3.8
- **WSGI Server**: Gunicorn 23.0.0

### Frontend

- **Framework**: React with Vite
- **Routing**: React Router
- **HTTP Client**: Axios
- **State Management**: TanStack Query
- **Styling**: Tailwind CSS

### Infrastructure

- **Containers**: Docker, Docker Compose
- **Reverse Proxy**: Nginx
- **Process Management**: Gunicorn (production), Django development server (local)

## Data Models Overview

### Core Entities

- **User**: Custom user model with roles (candidate, recruiter, admin)
- **Job**: Job postings with requirements and metadata
- **Resume**: User resumes with versioning
- **StructuredResume**: Parsed resume data (skills, experience, education)
- **Application**: Job applications with status tracking
- **Interview**: Scheduled interviews with feedback
- **Notification**: User notifications with delivery status
- **JobMatch**: Calculated match scores between candidates and jobs

### Relationships

- User → Resume (one-to-one)
- Resume → ResumeVersion (one-to-many)
- ResumeVersion → StructuredResume (one-to-one)
- StructuredResume → Skills/Experience/Education (one-to-many)
- User → Application (one-to-many)
- Job → Application (one-to-many)
- User → JobMatch (one-to-many)
- Job → JobMatch (one-to-many)
- Application → Interview (one-to-many)

## Scalability Considerations

### Horizontal Scaling

- **Web Servers**: Stateless design allows multiple web instances
- **Celery Workers**: Can scale workers independently based on task load
- **Database**: PostgreSQL supports read replicas for scaling reads
- **Cache**: Redis supports clustering for high availability

### Performance Optimizations

- Database query optimization with select_related/prefetch_related
- Redis caching for frequently accessed data
- Asynchronous processing for CPU-intensive operations
- Pagination to limit response sizes
- Database indexing on frequently queried fields

### Monitoring and Observability

- Request ID tracking for distributed tracing
- Structured logging with request correlation
- Health check endpoints for orchestration
- Celery task monitoring
- Error tracking via exception handlers

## Future Architecture Considerations

### Potential Enhancements

- **Message Queue**: Replace Redis with RabbitMQ or Kafka for complex workflows
- **Read Replicas**: Add PostgreSQL read replicas for analytics queries
- **CDN**: Offload static assets to CDN for global distribution
- **Search Engine**: Integrate Elasticsearch for advanced job search
- **Microservices**: Consider service extraction for independent scaling
- **Event Sourcing**: Implement event sourcing for audit trail and replayability
