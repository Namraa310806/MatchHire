# Engineering Principles

This document outlines the core engineering principles that guide development in the MatchHire project. These principles ensure code quality, maintainability, and scalability.

## Table of Contents

- [Thin Views](#thin-views)
- [Fat Services](#fat-services)
- [Explicit Transactions](#explicit-transactions)
- [Dependency Direction](#dependency-direction)
- [Single Responsibility](#single-responsibility)
- [Fail Fast](#fail-fast)
- [Idempotency](#idempotency)
- [Backward Compatibility](#backward-compatibility)
- [OpenAPI First](#openapi-first)
- [Testing Before Merge](#testing-before-merge)

## Thin Views

### Principle

Views should be thin and handle only HTTP concerns. Business logic belongs in the service layer.

### Why This Matters

- **Testability**: Business logic can be tested without HTTP overhead
- **Reusability**: Same business logic can be called from views, management commands, or Celery tasks
- **Maintainability**: Easier to locate and modify business rules
- **Separation of Concerns**: Clear boundary between HTTP handling and domain logic

### Example

```python
# Good - Thin view
class JobCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRecruiter]
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        job = JobService.create_job(
            recruiter=self.request.user,
            **serializer.validated_data
        )
        serializer.instance = job

# Bad - Fat view with business logic
class JobCreateView(APIView):
    def post(self, request):
        # Business logic in view
        job = Job.objects.create(
            title=request.data['title'],
            recruiter=request.user,
            status=Job.JobStatus.DRAFT
        )
        # More business logic...
        return Response(JobSerializer(job).data)
```

## Fat Services

### Principle

Services should contain business logic. They are the "fat" layer where domain rules live.

### Why This Matters

- **Centralized Logic**: Business rules in one place, not scattered
- **Consistency**: Same logic used regardless of entry point
- **Testability**: Easy to test business rules in isolation
- **Transaction Control**: Services can manage database transactions explicitly

### Example

```python
# Good - Fat service
class MatchingService:
    @classmethod
    @transaction.atomic
    def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
        """Calculate match score with all business logic."""
        skills_score = cls._calculate_skill_score(candidate, job)
        experience_score = cls._calculate_experience_score(candidate, job)
        education_score = cls._calculate_education_score(candidate)
        
        final_score = (
            (skills_score * Decimal('0.60')) +
            (experience_score * Decimal('0.30')) +
            (education_score * Decimal('0.10'))
        )
        
        return JobMatch.objects.create(
            candidate=candidate,
            job=job,
            match_score=final_score,
            # ...
        )
```

## Explicit Transactions

### Principle

Database transactions should be managed explicitly at the service layer for multi-step operations.

### Why This Matters

- **Data Consistency**: Ensures all related changes succeed or fail together
- **Error Recovery**: Automatic rollback on errors
- **Predictable Behavior**: Clear transaction boundaries
- **Debugging**: Easier to trace transaction-related issues

### Example

```python
# Good - Explicit transaction
@classmethod
@transaction.atomic
def create_job_with_requirements(cls, recruiter, title, requirements):
    job = Job.objects.create(recruiter=recruiter, title=title)
    JobRequirement.objects.create(job=job, text=requirements)
    return job

# Bad - No transaction
@classmethod
def create_job_with_requirements(cls, recruiter, title, requirements):
    job = Job.objects.create(recruiter=recruiter, title=title)
    JobRequirement.objects.create(job=job, text=requirements)
    # If second create fails, job is orphaned
    return job
```

## Dependency Direction

### Principle

Dependencies should flow in one direction: from higher-level modules to lower-level modules. Avoid circular dependencies.

### Why This Matters

- **Maintainability**: Clear dependency graph prevents spaghetti code
- **Testability**: Easier to mock and test in isolation
- **Reusability**: Lower-level modules can be reused independently
- **Build System**: Faster builds with clear dependency order

### Dependency Hierarchy

```
Views → Services → Models
  ↓        ↓
Serializers  ↓
           ↓
        Core Utilities
```

### Example

```python
# Good - Correct direction
# apps/jobs/services.py
from apps.matching.services import MatchingService  # Higher level depends on lower level

# Bad - Circular dependency
# apps/matching/services.py
from apps.jobs.services import JobService  # Lower level depends on higher level
# apps/jobs/services.py
from apps.matching.services import MatchingService  # Circular!
```

## Single Responsibility

### Principle

Each module, class, and function should have one reason to change.

### Why This Matters

- **Maintainability**: Easier to understand and modify
- **Testability**: Smaller, focused units are easier to test
- **Reusability**: Single-purpose components are more reusable
- **Debugging**: Easier to locate bugs in focused code

### Example

```python
# Good - Single responsibility
class ResumeService:
    @classmethod
    def parse_resume(cls, resume: Resume) -> StructuredResume:
        """Parse resume file into structured data."""
        pass

class MatchingService:
    @classmethod
    def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
        """Calculate match score."""
        pass

# Bad - Multiple responsibilities
class ResumeService:
    @classmethod
    def parse_resume(cls, resume: Resume) -> StructuredResume:
        """Parse resume."""
        pass
    
    @classmethod
    def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
        """Unrelated responsibility!"""
        pass
```

## Fail Fast

### Principle

Errors should be detected and reported as early as possible.

### Why This Matters

- **Debugging**: Easier to trace errors to their source
- **User Experience**: Faster feedback to users
- **System Stability**: Prevents cascading failures
- **Resource Efficiency**: Avoids wasted processing on invalid data

### Example

```python
# Good - Fail fast
@classmethod
def parse_resume(cls, resume: Resume) -> StructuredResume:
    if not resume.file:
        raise ResumeParsingError("Resume file is missing")
    
    if not resume.file.name.endswith(('.pdf', '.docx')):
        raise ResumeParsingError("Unsupported file format")
    
    # Proceed with parsing
    pass

# Bad - Fail late
@classmethod
def parse_resume(cls, resume: Resume) -> StructuredResume:
    # Proceed without validation
    try:
        # ... parsing logic ...
    except Exception as e:
        # Error discovered late in processing
        raise ResumeParsingError("Parsing failed")
```

## Idempotency

### Principle

Operations should be idempotent - calling them multiple times with the same input produces the same result.

### Why This Matters

- **Reliability**: Safe to retry failed operations
- **Distributed Systems**: Essential for eventual consistency
- **User Experience**: Prevents duplicate actions on retry
- **Testing**: Easier to test and reason about

### Example

```python
# Good - Idempotent
@classmethod
def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
    job_match, created = JobMatch.objects.update_or_create(
        candidate=candidate,
        job=job,
        defaults={'match_score': calculated_score}
    )
    return job_match

# Bad - Not idempotent
@classmethod
def calculate_match(cls, candidate: User, job: Job) -> JobMatch:
    # Creates duplicate on each call
    return JobMatch.objects.create(candidate=candidate, job=job)
```

## Backward Compatibility

### Principle

Changes should not break existing clients. Breaking changes require versioning and migration paths.

### Why This Matters

- **User Trust**: Users can upgrade without fear of breakage
- **Ecosystem**: Third-party integrations remain stable
- **Deployment**: Gradual rollouts possible
- **Support**: Easier to support multiple versions

### Guidelines

- Never remove or rename API fields without deprecation
- Never change API response structure without versioning
- Add new fields as optional when possible
- Use feature flags for major changes
- Provide migration guides for breaking changes

### Example

```python
# Good - Backward compatible
class JobSerializer(serializers.ModelSerializer):
    # New field added as optional
    salary_range = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'salary_range']  # Existing clients ignore new field

# Bad - Breaking change
class JobSerializer(serializers.ModelSerializer):
    # Renamed field - breaks existing clients
    job_title = serializers.CharField(source='title')
    
    class Meta:
        model = Job
        fields = ['id', 'job_title']  # Clients expecting 'title' break
```

## OpenAPI First

### Principle

API changes should be designed with OpenAPI documentation in mind. The API contract is primary.

### Why This Matters

- **Documentation**: API documentation stays in sync with code
- **Client Generation**: Enables automatic client SDK generation
- **Testing**: Contract testing possible
- **Communication**: Clear API contract for frontend/backend teams

### Guidelines

- Use drf-spectacular decorators for complex endpoints
- Add help_text to serializer fields
- Document error responses
- Use appropriate status codes
- Validate OpenAPI schema before merging

### Example

```python
# Good - OpenAPI documented
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
    responses={200: JobSerializer(many=True)}
)
class JobListView(generics.ListAPIView):
    queryset = Job.objects.filter(status=Job.JobStatus.ACTIVE)
    serializer_class = JobSerializer

# Bad - No OpenAPI documentation
class JobListView(generics.ListAPIView):
    queryset = Job.objects.filter(status=Job.JobStatus.ACTIVE)
    serializer_class = JobSerializer
```

## Testing Before Merge

### Principle

No code should be merged without tests. Tests are a first-class citizen.

### Why This Matters

- **Quality**: Catches bugs before production
- **Refactoring**: Safe refactoring with test coverage
- **Documentation**: Tests serve as executable documentation
- **Confidence**: Enables fearless deployment

### Guidelines

- Unit tests for business logic
- Integration tests for service layer
- API tests for endpoints
- Test both success and failure paths
- Aim for >80% coverage on new code

### Example

```python
# Good - Comprehensive tests
class MatchingServiceTests(TestCase):
    def test_calculate_match_with_perfect_skills_match(self):
        """Test match calculation with perfect skills alignment."""
        candidate = self.create_candidate_with_skills(['Python', 'Django'])
        job = self.create_job_with_requirements('Python, Django')
        
        match = MatchingService.calculate_match(candidate, job)
        
        self.assertEqual(match.match_score, Decimal('100.00'))
    
    def test_calculate_match_with_no_skills_match(self):
        """Test match calculation with no skills alignment."""
        candidate = self.create_candidate_with_skills(['Java', 'Spring'])
        job = self.create_job_with_requirements('Python, Django')
        
        match = MatchingService.calculate_match(candidate, job)
        
        self.assertEqual(match.match_score, Decimal('0.00'))

# Bad - No tests
class MatchingService:
    @classmethod
    def calculate_match(cls, candidate, job):
        # Complex logic with no tests
        pass
```

## Additional Principles

### Security First

Security is not an afterthought. Consider security implications in every decision:

- Validate all inputs
- Use parameterized queries
- Implement proper authentication and authorization
- Never log sensitive data
- Follow OWASP guidelines

### Performance Awareness

Write performant code from the start:

- Optimize database queries (select_related, prefetch_related)
- Add indexes for frequently queried fields
- Use caching where appropriate
- Consider pagination for list endpoints
- Profile slow operations

### Documentation as Code

Documentation should be treated as code:

- Keep documentation in version control
- Update documentation with code changes
- Use diagrams for complex flows
- Write clear, concise documentation
- Review documentation in PRs

### YAGNI (You Aren't Gonna Need It)

Don't build features you don't need:

- Build for current requirements
- Avoid over-engineering
- Keep it simple
- Refactor when needed, not before
- Prefer simple solutions over complex ones

## Applying These Principles

### Code Review Checklist

When reviewing code, check for:

- [ ] Views are thin, services are fat
- [ ] Transactions are explicit for multi-step operations
- [ ] Dependencies flow in correct direction
- [ ] Each function has single responsibility
- [ ] Errors fail fast with clear messages
- [ ] Operations are idempotent where appropriate
- [ ] Changes are backward compatible
- [ ] OpenAPI documentation is updated
- [ ] Tests are comprehensive
- [ ] Security is considered
- [ ] Performance is considered

### Architecture Review

When designing architecture:

- [ ] Clear separation of concerns
- [ ] Dependency graph is acyclic
- [ ] Services have well-defined interfaces
- [ ] Data flow is clear and traceable
- [ ] Error handling is consistent
- [ ] Logging is sufficient for debugging
- [ ] Monitoring points are identified

## References

- [Clean Architecture by Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [The Pragmatic Programmer by David Thomas](https://www.amazon.com/Pragmatic-Programmer-journey-mastery/dp/020161622X)
- [Domain-Driven Design by Eric Evans](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
