# Indexing Architecture

## Phase 5.2 - Search Indexing Engine

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   REST API   │  │   GraphQL    │  │   WebHooks   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Business Logic Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Services   │  │   Views      │  │  Signals     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Data Access Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Models     │  │   Queries    │  │  Serializers │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Indexing Engine Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Documents  │  │  Serializers │  │  Sync Engine │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Index Manager│  │ Bulk Indexer │  │   Metrics    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Provider Abstraction Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Registry   │  │ Base Provider│  │   Config     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  Search Provider Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  PostgreSQL  │  │ Elasticsearch │  │  OpenSearch  │        │
│  └──────────────┘  └──────────────┘  └──────┬───────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │Vector Search │  │ Hybrid Search │  │  Future...   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Interactions

### Document Indexing Flow

```
1. Model Save
   ↓
2. Django Signal (post_save)
   ↓
3. Event Handler
   ↓
4. Document Serializer
   ↓
5. Search Document
   ↓
6. Sync Service
   ↓
7. Index Manager
   ↓
8. Search Provider
```

### Bulk Indexing Flow

```
1. Management Command
   ↓
2. Bulk Indexer (create job)
   ↓
3. Document Iterator (memory-efficient)
   ↓
4. Chunk Processing
   ↓
5. Sync Service (bulk)
   ↓
6. Progress Callback
   ↓
7. Checkpoint Save
   ↓
8. Repeat until complete
```

### Verification Flow

```
1. Management Command
   ↓
2. Index Verifier
   ↓
3. Get DB Documents
   ↓
4. Get Index Documents
   ↓
5. Compare (missing, extra, versions)
   ↓
6. Check Relationships
   ↓
7. Generate Report
   ↓
8. Optional Fix
```

---

## Data Models

### Search Document Structure

```python
@dataclass
class BaseDocument:
    id: str                          # Unique identifier
    entity_type: EntityType          # Type of entity
    version: int                     # Document version
    created_at: Optional[datetime]   # Creation timestamp
    updated_at: Optional[datetime]   # Update timestamp
    metadata: Dict[str, Any]          # Additional metadata
    vector_embedding: Optional[List[float]]  # Future vector support
```

### Entity-Specific Documents

Each entity type extends BaseDocument with specific fields:

- **CandidateDocument**: user_id, email, full_name, headline, bio, skills, etc.
- **JobDocument**: job_id, recruiter_id, title, company_name, description, salary, etc.
- **ResumeDocument**: resume_id, user_id, version_number, skills, experience, etc.
- **ApplicationDocument**: application_id, job_id, candidate_id, status, etc.

---

## Synchronization Patterns

### Event-Driven Synchronization

**Trigger**: Django signals on model changes

**Flow**:
1. Model saved/deleted
2. Signal handler triggered
3. Document serialized
4. Sync service called
5. Provider updated

**Benefits**:
- Automatic synchronization
- Real-time updates
- Minimal latency

**Considerations**:
- Signal handler performance
- Error handling (non-blocking)
- Feature flag support

### Bulk Synchronization

**Trigger**: Management command or scheduled task

**Flow**:
1. Job created
2. Documents fetched (iterator)
3. Chunked processing
4. Progress tracking
5. Checkpointing

**Benefits**:
- Memory efficient
- Resumable
- Progress tracking

**Considerations**:
- Chunk size tuning
- Transaction safety
- Checkpoint management

### Incremental Synchronization

**Trigger**: Scheduled task or manual command

**Flow**:
1. Timestamp filter applied
2. Changed documents fetched
3. Synced to provider
4. Metrics recorded

**Benefits**:
- Efficient for large datasets
- Reduced load
- Fast sync times

**Considerations**:
- Timestamp accuracy
- Change tracking
- Missed updates detection

---

## Error Handling Strategy

### Retry Logic

```
1. Sync Attempt
   ↓ (failure)
2. Wait (retry_delay)
   ↓
3. Retry (max_retries)
   ↓ (failure)
4. Dead-Letter Queue
```

**Configuration**:
- `max_retries`: 3 (default)
- `retry_delay`: 1 second (default)

**Dead-Letter Queue**:
- Failed operations stored
- Manual review possible
- Retry command available

### Checkpoint Recovery

```
1. Job Interrupted
   ↓
2. Checkpoint Saved
   ↓
3. Resume Command
   ↓
4. Load Checkpoint
   ↓
5. Continue from Last Position
```

**Benefits**:
- Resume interrupted jobs
- No duplicate work
- Progress preservation

---

## Performance Optimization

### Memory Efficiency

**Techniques**:
- Django queryset iterators
- Chunked processing
- Streaming document generation
- Minimal in-memory state

**Configuration**:
- `chunk_size`: 100 (default)
- Tunable per job

### Scalability

**Approaches**:
- Horizontal scaling (multiple indexer instances)
- Async processing (Celery integration)
- Provider-specific optimizations
- Connection pooling

### Monitoring

**Metrics**:
- Operation counts and durations
- Document sync rates
- Failure rates
- Provider latencies
- Queue sizes

---

## Security Considerations

### Access Control

- Provider credentials secured
- Feature flag gating
- Permission checks on commands
- Audit logging

### Data Privacy

- Sensitive field filtering
- Metadata sanitization
- Provider-specific privacy controls
- Compliance support

---

## Extensibility Points

### Adding New Document Types

1. Define document class
2. Create serializer
3. Add to EntityType enum
4. Register signal handler
5. Add to verification

### Adding New Providers

1. Implement SearchProvider interface
2. Register in registry
3. Add provider-specific methods
4. Test with indexing engine
5. Update documentation

### Custom Sync Logic

1. Extend SyncService
2. Override sync methods
3. Add custom retry logic
4. Implement custom metrics
5. Register custom handlers

---

## Deployment Considerations

### Production Configuration

```python
# Feature flags
SEARCH_FEATURE_FLAGS = {
    "full_text_search": True,
    "auto_indexing": True,
}

# Indexing settings
INDEXING_CHUNK_SIZE = 100
INDEXING_MAX_RETRIES = 3
INDEXING_RETRY_DELAY = 1

# Checkpoint settings
INDEXING_CHECKPOINT_DIR = "/var/lib/search_indexing/checkpoints"
INDEXING_CHECKPOINT_RETENTION_DAYS = 7
```

### Monitoring Setup

- Metrics collection enabled
- Health check endpoints
- Alert on high failure rates
- Monitor dead-letter queue size

### Backup Strategy

- Database backups include indexed data
- Provider-specific backup procedures
- Checkpoint backup for resume capability
- Configuration versioning

---

## Migration Path

### From Direct Provider Usage

**Phase 1**: Implement indexing engine (current)
**Phase 2**: Migrate existing indexing logic
**Phase 3**: Add Elasticsearch provider
**Phase 4**: Switch to Elasticsearch
**Phase 5**: Remove direct provider usage

### Backward Compatibility

- PostgreSQL provider maintains compatibility
- Existing APIs unchanged
- Gradual migration possible
- Feature flags for rollout

---

## Testing Strategy

### Unit Tests

- Document serialization
- Sync service operations
- Index manager operations
- Bulk indexer job management

### Integration Tests

- End-to-end indexing
- Provider integration
- Signal handler integration
- Management commands

### Performance Tests

- Bulk indexing throughput
- Memory usage profiling
- Provider latency measurement
- Concurrent operation testing

---

## Troubleshooting Guide

### Common Issues

**Documents not indexed**:
- Check auto-indexing feature flag
- Verify signal handlers registered
- Check dead-letter queue

**Bulk job failed**:
- Review job status
- Check error messages
- Resume from checkpoint

**Verification failures**:
- Run full sync
- Check provider connectivity
- Review relationship integrity

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('apps.search.indexing').setLevel(logging.DEBUG)
```

---

## Future Architecture Evolution

### Planned Enhancements

1. **Async Processing**: Celery integration
2. **Real-time Sync**: WebSocket updates
3. **Vector Embeddings**: Automatic generation
4. **Hybrid Search**: Combined keyword + vector
5. **Multi-tenant**: Tenant isolation
6. **Index Sharding**: Automatic management

### Scalability Improvements

1. **Distributed Indexing**: Multiple workers
2. **Load Balancing**: Provider selection
3. **Caching**: Document cache
4. **Batch Optimization**: Dynamic chunk sizing

### Monitoring Enhancements

1. **Distributed Tracing**: Request tracing
2. **Advanced Metics**: Custom metrics
3. **Alerting**: Automated alerts
4. **Dashboards**: Real-time monitoring
