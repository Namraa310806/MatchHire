# ADR 0001: Service Layer Pattern

## Status

Accepted

## Context

MatchHire is a complex domain with business logic spread across multiple Django apps (users, jobs, matching, applications, etc.). As the application grew, we needed a consistent pattern for organizing business logic to avoid:

- Business logic leaking into views and serializers
- Difficulty testing business rules in isolation
- Code duplication across different endpoints
- Unclear separation of concerns

## Decision

Implement a service layer pattern where business logic is encapsulated in service classes located in `apps/<app>/services/` directories.

### Implementation

- Each Django app has an optional `services/` directory
- Services are implemented as classes with class methods for stateless operations
- Views call services to execute business logic
- Services handle database transactions explicitly
- Services return domain objects, not HTTP responses

### Example

```python
# apps/matching/services/matching.py
class MatchingService:
    @classmethod
    def calculate_match(cls, candidate, job) -> JobMatch:
        # Business logic for matching
        pass

# View calls service
class MatchListView(APIView):
    def get(self, request):
        matches = MatchingService.get_candidate_matches(request.user)
        return Response(MatchSerializer(matches, many=True).data)
```

## Alternatives Considered

### Alternative 1: Business Logic in Views

- **Pros**: Simpler for small applications, less boilerplate
- **Cons**: Views become bloated, hard to test, violates single responsibility

### Alternative 2: Business Logic in Models

- **Pros**: Keeps logic close to data, Django's "fat models" pattern
- **Cons**: Models become god classes, couples data access to business rules, harder to test

### Alternative 3: Domain-Driven Design with Aggregates

- **Pros**: Clear domain boundaries, rich domain model
- **Cons**: Higher complexity, steeper learning curve, may be overkill for this project

## Pros

- **Separation of Concerns**: Clear separation between HTTP handling (views) and business logic (services)
- **Testability**: Services can be tested independently of Django's request/response cycle
- **Reusability**: Same service method can be called from views, management commands, or Celery tasks
- **Maintainability**: Business logic is centralized and easier to locate
- **Transaction Control**: Services can explicitly manage database transactions
- **Idempotency**: Easier to design idempotent service methods for safe retries

## Cons

- **Additional Layer**: More boilerplate and indirection
- **Learning Curve**: Developers must understand the pattern
- **Potential Over-engineering**: For simple CRUD operations, services may feel unnecessary

## Future Implications

- Services may need to be extracted into separate packages if the application grows into microservices
- Service interfaces should remain stable to avoid breaking changes across the codebase
- Consider adding service interfaces/protocols for better type safety and mocking in tests

## Related Decisions

- [ADR 0003: Celery Background Processing](0003-celery-background-processing.md) - Services are used by both views and Celery tasks
- [ADR 0005: Role-Based Access Control](0005-rbac.md) - Services enforce business-level authorization

## References

- Martin Fowler's Service Layer pattern
- Django's "Fat Models, Thin Views" anti-pattern discussion
