# ADR 0003: Celery Background Processing

## Status

Accepted

## Context

MatchHire has several CPU-intensive and time-consuming operations that would block HTTP requests if executed synchronously:

- Resume parsing (PDF/DOCX extraction, structured data extraction)
- Match score calculations (especially batch recalculations)
- Notification delivery (external API calls, email sending)
- Analytics aggregation (periodic metric calculations)

Running these operations synchronously would result in poor user experience and potential request timeouts.

## Decision

Implement Celery for asynchronous background task processing with Redis as both broker and result backend.

### Implementation Details

- **Broker**: Redis
- **Result Backend**: Redis
- **Task Autodiscovery**: Enabled for all apps
- **Beat Scheduler**: For periodic tasks
- **Task Location**: `apps/<app>/tasks.py`

### Task Categories

1. **Resume Processing**: CPU-intensive parsing and extraction
2. **Matching**: Batch match score recalculations
3. **Notifications**: Asynchronous notification delivery
4. **Analytics**: Periodic metric aggregation

### Idempotency Design

All tasks are designed to be idempotent:
- Database operations use `update_or_create` patterns
- No side effects from duplicate executions
- Safe to retry failed tasks

### Example

```python
# apps/matching/tasks.py
from celery import shared_task

@shared_task
def recalculate_candidate_matches(candidate_id: str) -> int:
    """Recalculate matches for a candidate. Idempotent."""
    return MatchingService.recalculate_for_candidate(candidate_id)

# View triggers task
class ResumeUploadView(APIView):
    def post(self, request):
        # ... process resume ...
        recalculate_candidate_matches.delay(candidate_id=request.user.id)
        return Response({"status": "processing"})
```

## Alternatives Considered

### Alternative 1: Synchronous Processing

- **Pros**: Simpler, no additional infrastructure
- **Cons**: Blocks HTTP requests, poor UX, request timeouts, no retry mechanism

### Alternative 2: Django Background Tasks

- **Pros**: Django-native, simpler setup
- **Cons**: Not production-grade for high volume, limited monitoring, no distributed processing

### Alternative 3: RQ (Redis Queue)

- **Pros**: Simpler than Celery, good for smaller workloads
- **Cons**: Less feature-rich, no built-in periodic tasks, less mature ecosystem

### Alternative 4: AWS Lambda / Cloud Functions

- **Pros**: Serverless, auto-scaling, pay-per-use
- **Cons**: Cold starts, vendor lock-in, more complex deployment, not Django-native

## Pros

- **Non-Blocking**: HTTP requests return immediately, background work continues
- **Scalability**: Can scale workers independently based on task load
- **Reliability**: Built-in retry mechanisms, task monitoring
- **Periodic Tasks**: Celery Beat for scheduled jobs
- **Mature Ecosystem**: Well-documented, battle-tested, large community
- **Monitoring**: Flower support for task monitoring
- **Distributed**: Can run workers across multiple machines

## Cons

- **Infrastructure Complexity**: Requires Redis broker and result backend
- **Operational Overhead**: Need to monitor workers, handle failures
- **Debugging**: Harder to debug async tasks than synchronous code
- **Memory Usage**: Workers consume memory even when idle
- **Task Result Storage**: Results stored in Redis, can consume memory

## Future Implications

- Consider adding task prioritization for different task types
- May need to implement task routing to specialized workers (e.g., CPU-heavy vs I/O-heavy)
- Consider adding task chains/canvas for complex workflows
- May need to implement task rate limiting for external API calls
- Consider adding task dead letter queues for failed tasks

## Related Decisions

- [ADR 0001: Service Layer Pattern](0001-service-layer.md) - Services are called by both views and Celery tasks
- [ADR 0004: OpenAPI Documentation](0004-openapi.md) - Async endpoints documented with appropriate response codes

## References

- [Celery Documentation](https://docs.celeryq.dev/)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
