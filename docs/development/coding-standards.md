# MatchHire Coding Standards

This document defines the coding standards for the MatchHire backend. Following these standards ensures code quality, maintainability, and consistency across the codebase.

## Table of Contents

- [Python](#python)
- [Django](#django)
- [Services](#services)
- [Views](#views)
- [Serializers](#serializers)
- [Models](#models)
- [Permissions](#permissions)
- [Transactions](#transactions)
- [Logging](#logging)
- [Exceptions](#exceptions)
- [Type Hints](#type-hints)
- [Documentation](#documentation)
- [Imports](#imports)
- [Naming Conventions](#naming-conventions)
- [Testing](#testing)

## Python

### Why These Standards Matter

Python's flexibility requires discipline to maintain code quality. These standards prevent common bugs, improve readability, and ensure the codebase remains maintainable as it grows.

### PEP 8 Compliance

All code must follow PEP 8 style guidelines:

```python
# Good
def calculate_match_score(candidate: User, job: Job) -> Decimal:
    """Calculate match score between candidate and job."""
    pass

# Bad
def calculate_match_score(candidate,job):
    pass
```

### Line Length

Maximum line length: 100 characters (soft limit), 120 characters (hard limit for URLs/paths).

### String Formatting

Use f-strings for string formatting:

```python
# Good
name = "John"
message = f"Hello, {name}!"

# Bad
message = "Hello, {}!".format(name)
message = "Hello, %s!" % name
```

### Type Annotations

Use type hints for function signatures:

```python
# Good
def get_user(user_id: str) -> Optional[User]:
    pass

# Bad
def get_user(user_id):
    pass
```

### List Comprehensions

Use list comprehensions for simple transformations, use loops for complex logic:

```python
# Good - simple transformation
user_ids = [user.id for user in users]

# Good - complex logic
user_ids = []
for user in users:
    if user.is_active:
        user_ids.append(user.id)
```

## Django

### Why These Standards Matter

Django provides many ways to accomplish the same task. These standards ensure consistency and leverage Django's best practices for performance and security.

### Settings Organization

- Base settings in `settings/base.py`
- Environment-specific settings in `settings/dev.py`, `settings/prod.py`, `settings/test.py`
- Use `get_env()` for environment variables

```python
# Good
from matchhire_backend.core.env import get_env

SECRET_KEY = get_env("SECRET_KEY", default="change-me")

# Bad
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
```

### URL Configuration

- Use namespaced URLs
- Include trailing slashes in patterns
- Use `path()` for simple routes, `re_path()` only when necessary

```python
# Good
urlpatterns = [
    path("api/v1/jobs/", include(("apps.jobs.urls", "jobs"), namespace="jobs")),
]

# Bad
urlpatterns = [
    url(r'^api/v1/jobs/$', include('apps.jobs.urls')),
]
```

### QuerySet Optimization

- Use `select_related()` for foreign keys
- Use `prefetch_related()` for many-to-many and reverse foreign keys
- Use `only()` and `defer()` to limit fields when appropriate
- Use `iterator()` for large result sets

```python
# Good
jobs = Job.objects.select_related("recruiter").prefetch_related("applications").all()

# Bad
jobs = Job.objects.all()  # N+1 queries
```

### Model Managers

Use custom managers for complex queries:

```python
# Good
class JobManager(models.Manager):
    def active(self):
        return self.filter(status=Job.JobStatus.ACTIVE)

class Job(models.Model):
    objects = JobManager()

# Usage
active_jobs = Job.objects.active()

# Bad
active_jobs = Job.objects.filter(status=Job.JobStatus.ACTIVE)
```

## Services

### Why These Standards Matter

The service layer is where business logic lives. Consistent service patterns make code testable, reusable, and maintainable.

### Service Class Structure

- Use class methods for stateless operations
- Use instance methods only when maintaining state is necessary
- Services should not handle HTTP concerns
- Services should return domain objects, not HTTP responses

```python
# Good
class MatchingService:
    @classmethod
    def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
        """Calculate match score between candidate and job."""
        pass

# Bad
class MatchingService:
    def calculate_match(self, request, job_id):
        # Don't handle HTTP in services
        pass
```

### Service Idempotency

Services should be idempotent - calling them multiple times with the same input produces the same result:

```python
# Good
@classmethod
def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
    job_match, created = JobMatch.objects.update_or_create(
        candidate=candidate,
        job=job,
        defaults={'match_score': calculated_score}
    )
    return job_match

# Bad
@classmethod
def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
    # Creates duplicate on each call
    return JobMatch.objects.create(candidate=candidate, job=job)
```

### Service Error Handling

Services should raise domain-specific exceptions:

```python
# Good
class ResumeParsingError(Exception):
    """Raised when resume parsing fails."""

class ResumeService:
    @classmethod
    def parse_resume(cls, resume: Resume) -> StructuredResume:
        if not resume.file:
            raise ResumeParsingError("Resume file is missing")
        # ... parsing logic

# Bad
class ResumeService:
    @classmethod
    def parse_resume(cls, resume: Resume) -> StructuredResume:
        if not resume.file:
            return None  # Silent failure
```

## Views

### Why These Standards Matter

Views are the entry point for API requests. Consistent view patterns ensure proper error handling, authentication, and response formatting.

### View Responsibility

Views should handle HTTP concerns only:
- Request validation
- Authentication/authorization
- Calling services
- Response serialization
- Error handling

```python
# Good
class JobCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRecruiter]
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        job = JobService.create_job(
            recruiter=self.request.user,
            **serializer.validated_data
        )
        serializer.instance = job

# Bad
class JobCreateView(APIView):
    def post(self, request):
        # Business logic in view
        job = Job.objects.create(
            title=request.data['title'],
            recruiter=request.user,
            # ... more logic
        )
        return Response(JobSerializer(job).data)
```

### View Naming

Use descriptive view names that indicate the HTTP method and resource:

```python
# Good
class JobListView(generics.ListAPIView):
    pass

class JobDetailView(generics.RetrieveAPIView):
    pass

class JobCreateView(generics.CreateAPIView):
    pass

# Bad
class Jobs(APIView):
    pass
```

### Response Format

Use consistent response format:

```python
# Good
return Response(
    {"id": job.id, "title": job.title},
    status=status.HTTP_201_CREATED
)

# Bad
return Response(job.__dict__)
```

## Serializers

### Why These Standards Matter

Serializers define the API contract. Consistent serializer patterns ensure clear, type-safe, and well-documented APIs.

### Serializer Validation

Use field-level validation for simple rules, object-level validation for complex rules:

```python
# Good
class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'requirements', 'experience_level']

    def validate_requirements(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Requirements must be at least 10 characters")
        return value

    def validate(self, data):
        if data['experience_level'] == Job.ExperienceLevel.SENIOR and not data.get('requirements'):
            raise serializers.ValidationError("Senior jobs must have requirements")
        return data

# Bad
class JobSerializer(serializers.ModelSerializer):
    # No validation
    pass
```

### Nested Serializers

Use nested serializers for related objects, but be mindful of performance:

```python
# Good - with select_related
class JobSerializer(serializers.ModelSerializer):
    recruiter = RecruiterSerializer(read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'recruiter']

# View should use select_related
queryset = Job.objects.select_related('recruiter').all()
```

### Serializer Documentation

Add help_text to fields for OpenAPI documentation:

```python
# Good
class JobSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        help_text="Job title",
        max_length=200
    )
    requirements = serializers.CharField(
        help_text="Job requirements and qualifications",
        required=False
    )

    class Meta:
        model = Job
        fields = ['id', 'title', 'requirements']
```

## Models

### Why These Standards Matter

Models define the data schema. Consistent model patterns ensure data integrity, proper indexing, and clear relationships.

### Model Fields

Use appropriate field types and add verbose names:

```python
# Good
class Job(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Job Title"
    )
    requirements = models.TextField(
        verbose_name="Job Requirements",
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-created_at']

# Bad
class Job(models.Model):
    title = models.CharField(max_length=200)
    requirements = models.TextField(blank=True)
```

### Model Methods

Add descriptive docstrings to model methods:

```python
# Good
class Job(models.Model):
    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status == self.JobStatus.ACTIVE

    def get_application_count(self) -> int:
        """Get the number of applications for this job."""
        return self.applications.count()

# Bad
class Job(models.Model):
    def is_active(self):
        return self.status == self.JobStatus.ACTIVE
```

### Model Relationships

Use appropriate relationship types and related_name:

```python
# Good
class Job(models.Model):
    recruiter = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='jobs'
    )

class Application(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    candidate = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='applications'
    )

# Bad
class Job(models.Model):
    recruiter = models.ForeignKey('users.User', on_delete=models.CASCADE)
```

### Model Indexes

Add indexes for frequently queried fields:

```python
# Good
class Job(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

# Bad
class Job(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
```

## Permissions

### Why These Standards Matter

Permissions enforce security boundaries. Consistent permission patterns ensure proper access control and prevent unauthorized operations.

### Permission Classes

Use granular permission classes:

```python
# Good
class IsRecruiter(permissions.BasePermission):
    """Allow access only to recruiters."""
    def has_permission(self, request, view):
        return request.user.role == User.Roles.RECRUITER

class IsJobOwner(permissions.BasePermission):
    """Allow access only to the job owner."""
    def has_object_permission(self, request, view, obj):
        return obj.recruiter == request.user

class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsRecruiter, IsJobOwner]

# Bad
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]  # No role check
```

### Permission Naming

Use descriptive permission class names:

```python
# Good
class IsRecruiter(permissions.BasePermission):
    pass

class IsCandidate(permissions.BasePermission):
    pass

class IsAdmin(permissions.BasePermission):
    pass

# Bad
class CustomPerm(permissions.BasePermission):
    pass
```

## Transactions

### Why These Standards Matter

Transactions ensure data consistency. Proper transaction management prevents partial updates and data corruption.

### Explicit Transactions

Use `transaction.atomic()` for multi-step operations:

```python
# Good
from django.db import transaction

@transaction.atomic
def create_job_with_requirements(recruiter, title, requirements):
    job = Job.objects.create(recruiter=recruiter, title=title)
    JobRequirement.objects.create(job=job, text=requirements)
    return job

# Bad
def create_job_with_requirements(recruiter, title, requirements):
    job = Job.objects.create(recruiter=recruiter, title=title)
    JobRequirement.objects.create(job=job, text=requirements)
    return job  # If second create fails, job is orphaned
```

### Transaction in Services

Services should handle their own transactions:

```python
# Good
class JobService:
    @classmethod
    @transaction.atomic
    def create_job(cls, recruiter, **kwargs):
        job = Job.objects.create(recruiter=recruiter, **kwargs)
        # Additional operations
        return job

# Bad - transaction in view
class JobCreateView(generics.CreateAPIView):
    @transaction.atomic
    def post(self, request):
        # Business logic
        pass
```

## Logging

### Why These Standards Matter

Logging is essential for debugging and monitoring. Consistent logging patterns ensure logs are useful and searchable.

### Logger Usage

Use module-level loggers with appropriate log levels:

```python
# Good
import logging

logger = logging.getLogger(__name__)

class JobService:
    @classmethod
    def create_job(cls, recruiter, **kwargs):
        logger.info(f"Creating job for recruiter {recruiter.id}")
        try:
            job = Job.objects.create(recruiter=recruiter, **kwargs)
            logger.info(f"Job {job.id} created successfully")
            return job
        except Exception as e:
            logger.error(f"Failed to create job: {e}", exc_info=True)
            raise

# Bad
print("Creating job")  # Don't use print
```

### Structured Logging

Include context in log messages:

```python
# Good
logger.info(
    "Job created",
    extra={
        'job_id': job.id,
        'recruiter_id': recruiter.id,
        'request_id': request.id
    }
)

# Bad
logger.info("Job created")
```

### Log Levels

Use appropriate log levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Something unexpected happened
- `ERROR`: Error occurred, but application continues
- `CRITICAL`: Serious error, application may not continue

## Exceptions

### Why These Standards Matter

Proper exception handling ensures errors are handled gracefully and provides useful debugging information.

### Custom Exceptions

Create domain-specific exceptions:

```python
# Good
class ResumeParsingError(Exception):
    """Raised when resume parsing fails."""
    pass

class MatchingError(Exception):
    """Raised when matching calculation fails."""
    pass

# Bad
raise Exception("Resume parsing failed")
```

### Exception Handling

Catch specific exceptions, not generic Exception:

```python
# Good
try:
    job = Job.objects.get(id=job_id)
except Job.DoesNotExist:
    logger.error(f"Job {job_id} not found")
    raise

# Bad
try:
    job = Job.objects.get(id=job_id)
except Exception:
    logger.error("Something went wrong")
```

### Exception Propagation

Let exceptions propagate to the exception handler unless you can handle them:

```python
# Good
def process_job(job_id):
    job = Job.objects.get(id=job_id)
    return MatchingService.calculate_match(candidate, job)

# Bad
def process_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
        return MatchingService.calculate_match(candidate, job)
    except Exception:
        pass  # Silent failure
```

## Type Hints

### Why These Standards Matter

Type hints improve code readability, enable IDE support, and catch type errors early.

### Function Signatures

Add type hints to all function signatures:

```python
# Good
def calculate_match_score(candidate: User, job: Job) -> Decimal:
    pass

def get_user(user_id: str) -> Optional[User]:
    pass

# Bad
def calculate_match_score(candidate, job):
    pass
```

### Import Order

Import typing modules at the top:

```python
# Good
from typing import Optional, List, Dict
from decimal import Decimal

def process_jobs(jobs: List[Job]) -> Dict[str, Decimal]:
    pass

# Bad
def process_jobs(jobs):
    from typing import List, Dict
    pass
```

## Documentation

### Why These Standards Matter

Documentation makes code understandable and maintainable. Good documentation reduces onboarding time and prevents misuse.

### Docstrings

Use Google-style docstrings:

```python
# Good
def calculate_match_score(candidate: User, job: Job) -> Decimal:
    """Calculate match score between candidate and job.

    Args:
        candidate: The candidate user.
        job: The job to match against.

    Returns:
        Match score between 0 and 100.

    Raises:
        ResumeParsingError: If candidate resume cannot be parsed.
    """
    pass

# Bad
def calculate_match_score(candidate, job):
    # Calculates match score
    pass
```

### Inline Comments

Add comments for non-obvious logic:

```python
# Good
# Convert days to years using 365.25 to account for leap years
total_years = total_days / 365.25

# Bad
total_years = total_days / 365.25
```

## Imports

### Why These Standards Matter

Consistent import ordering improves readability and reduces merge conflicts.

### Import Order

Group imports in this order:
1. Standard library imports
2. Third-party imports
3. Django imports
4. Local application imports

```python
# Good
import logging
from datetime import timedelta
from typing import Optional

from celery import shared_task
from django.db import models

from apps.users.models import User
from matchhire_backend.core.env import get_env

# Bad
from apps.users.models import User
import logging
from celery import shared_task
```

### Import Style

Use explicit imports over `from module import *`:

```python
# Good
from apps.users.models import User, Job

# Bad
from apps.users.models import *
```

## Naming Conventions

### Why These Standards Matter

Consistent naming makes code predictable and easier to understand.

### Variable Names

Use descriptive, snake_case variable names:

```python
# Good
user_id = "123"
match_score = 85.5
is_active = True

# Bad
uid = "123"
ms = 85.5
active = True
```

### Class Names

Use PascalCase for class names:

```python
# Good
class MatchingService:
    pass

class JobSerializer:
    pass

# Bad
class matching_service:
    pass
```

### Constant Names

Use UPPER_CASE for constants:

```python
# Good
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Bad
max_retry_attempts = 3
default_timeout = 30
```

### Private Methods

Prefix private methods with underscore:

```python
# Good
class MatchingService:
    @classmethod
    def calculate_match(cls, candidate, job):
        skills_score = cls._calculate_skill_score(candidate, job)
        pass

    @classmethod
    def _calculate_skill_score(cls, candidate, job):
        pass

# Bad
class MatchingService:
    @classmethod
    def calculate_match(cls, candidate, job):
        skills_score = cls.calculate_skill_score(candidate, job)
        pass
```

## Testing

### Why These Standards Matter

Tests ensure code correctness and prevent regressions. Consistent test patterns make tests maintainable and reliable.

### Test Organization

Group tests by functionality:

```python
# Good
class JobModelTests(TestCase):
    def test_job_creation(self):
        pass

    def test_job_status_update(self):
        pass

class JobViewTests(APITestCase):
    def test_list_jobs(self):
        pass

    def test_create_job(self):
        pass

# Bad
class JobTests(TestCase):
    def test_1(self):
        pass

    def test_2(self):
        pass
```

### Test Naming

Use descriptive test names that describe what is being tested:

```python
# Good
def test_calculate_match_score_with_perfect_skills_match(self):
    pass

def test_calculate_match_score_with_no_skills_match(self):
    pass

# Bad
def test_match_1(self):
    pass

def test_match_2(self):
    pass
```

### Test Isolation

Each test should be independent:

```python
# Good
def test_job_creation(self):
    job = Job.objects.create(title="Test Job")
    self.assertEqual(job.title, "Test Job")

def test_job_update(self):
    job = Job.objects.create(title="Test Job")
    job.title = "Updated Job"
    job.save()
    self.assertEqual(job.title, "Updated Job")

# Bad - tests depend on each other
def test_job_creation(self):
    self.job = Job.objects.create(title="Test Job")

def test_job_update(self):
    self.job.title = "Updated Job"
    self.job.save()
```

### Test Coverage

Aim for high test coverage, but focus on critical paths:
- Service layer business logic
- Complex view logic
- Permission checks
- Error handling

## Additional Resources

- [PEP 8 Style Guide](https://peps8.org/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/internals/misc/)
- [Django REST Framework Best Practices](https://www.django-rest-framework.org/community/tutorial-quickstart/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
