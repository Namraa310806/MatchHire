# Search Indexing Engine

## Phase 5.2 - Search Indexing Engine

**Status:** Complete

---

## Overview

The Search Indexing Engine is a provider-agnostic platform that keeps search providers synchronized with application data. It serves as the single source of truth for document indexing across all search providers (PostgreSQL, Elasticsearch, OpenSearch, Vector Search, Hybrid Search).

---

## Architecture

### Design Principles

1. **Provider Independence**: The indexing engine is completely decoupled from any specific search provider implementation.
2. **Single Source of Truth**: All search providers receive data through this engine.
3. **Event-Driven**: Automatic indexing via Django signals on model changes.
4. **Scalable**: Memory-efficient bulk processing with chunking and progress tracking.
5. **Resilient**: Retry logic, dead-letter queue, and checkpoint-based resume capability.
6. **Observable**: Comprehensive metrics and verification tools.

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Django Models                            │
│  (User, Job, Resume, Application, etc.)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Django Signals
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Event Handlers                              │
│  (post_save, post_delete, pre_save)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Serialization
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Document Serializers                        │
│  (CandidateSerializer, JobSerializer, etc.)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Search Documents
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Search Documents                            │
│  (CandidateDocument, JobDocument, etc.)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Synchronization
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Sync Service                               │
│  (single, bulk, incremental sync)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Index Management
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Index Manager                               │
│  (create, delete, rebuild, refresh, optimize)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Provider Abstraction
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Search Providers                           │
│  (PostgreSQL, Elasticsearch, OpenSearch, etc.)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
apps/search/indexing/
├── __init__.py                      # Package exports
├── documents.py                     # Search document models
├── serializers.py                   # Django model serializers
├── index_manager.py                 # Index management operations
├── sync_service.py                  # Synchronization engine
├── bulk_indexer.py                  # Bulk indexing framework
├── event_handlers.py                # Django signal handlers
├── metrics.py                       # Metrics collection
├── verification.py                  # Integrity verification
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       ├── rebuild_search_index.py  # Rebuild index command
│       ├── sync_search_index.py    # Sync index command
│       ├── verify_search_index.py  # Verify index command
│       └── search_index_status.py  # Status command
└── tests/
    ├── __init__.py
    ├── test_documents.py           # Document tests
    ├── test_serializers.py          # Serializer tests
    ├── test_sync_service.py        # Sync service tests
    ├── test_index_manager.py       # Index manager tests
    └── test_bulk_indexer.py        # Bulk indexer tests
```

---

## Components

### Search Documents

Search documents are provider-independent representations of entities to be indexed. Each document defines:

- **Primary ID**: Unique identifier
- **Entity Type**: Type of entity (candidate, job, resume, etc.)
- **Indexed Fields**: Fields to be indexed
- **Metadata**: Additional metadata
- **Relationships**: Related entity information
- **Searchable Text**: Aggregated text for full-text search
- **Vector Placeholder**: Future vector embedding support

**Document Types:**
- `CandidateDocument`: Candidate profiles
- `ResumeDocument`: Resume versions
- `JobDocument`: Job postings
- `CompanyDocument`: Company information
- `RecruiterDocument`: Recruiter profiles
- `SkillDocument`: Skill taxonomy
- `ApplicationDocument`: Job applications
- `InterviewDocument`: Interview schedules

### Document Serializers

Serializers convert Django models into search documents with:

- **Consistent Serialization**: Uniform document structure
- **Nested Relationships**: Support for related models
- **Version Tracking**: Document version for migrations
- **Metadata Injection**: Automatic metadata population

**Serializer Types:**
- `CandidateSerializer`: User + CandidateProfile → CandidateDocument
- `RecruiterSerializer`: User + RecruiterProfile → RecruiterDocument
- `JobSerializer`: Job → JobDocument
- `ResumeSerializer`: ResumeVersion → ResumeDocument
- `ApplicationSerializer`: Application → ApplicationDocument
- `SkillSerializer`: Skill string → SkillDocument

### Index Manager

The IndexManager provides provider-independent index operations:

- **create_index**: Create a new index
- **delete_index**: Delete an index
- **rebuild_index**: Rebuild from scratch
- **refresh_index**: Make changes visible
- **optimize_index**: Optimize for performance
- **health_check**: Check index health
- **get_statistics**: Get index statistics
- **create_alias**: Create index alias
- **delete_alias**: Delete index alias
- **get_aliases**: List all aliases

### Synchronization Service

The SyncService handles document synchronization:

- **sync_single_document**: Sync one document with retry
- **sync_bulk_documents**: Sync multiple documents
- **sync_incremental**: Sync changes since timestamp
- **sync_full_rebuild**: Full index rebuild
- **delete_document**: Delete from index
- **get_dead_letter_queue**: Get failed syncs
- **retry_dead_letter_queue**: Retry failed syncs

**Features:**
- Automatic retry with exponential backoff
- Dead-letter queue for failed operations
- Progress tracking
- Metrics collection

### Bulk Indexer

The BulkIndexer provides memory-efficient bulk processing:

- **Chunked Processing**: Process documents in configurable chunks
- **Progress Tracking**: Real-time progress updates
- **Transaction Safety**: Optional database transactions
- **Resume Capability**: Checkpoint-based resume
- **Job Management**: Create, pause, cancel, resume jobs

**Features:**
- Memory-efficient iterator pattern
- Checkpoint persistence to disk
- Job status tracking
- Progress callbacks

### Event Handlers

Event handlers use Django signals for automatic indexing:

- **handle_post_save**: Index on create/update
- **handle_post_delete**: Delete from index on delete
- **handle_pre_save**: Track changes for smart re-indexing

**Features:**
- Lightweight signal triggers
- Business logic independence
- Configurable per-entity-type
- Feature flag support

### Metrics Collection

The IndexingMetrics class tracks:

- **Operation Metrics**: Count, duration, success rate per operation
- **Document Metrics**: Indexed count, sync count, failures
- **Queue Metrics**: Queue size, processed count
- **Provider Metrics**: Latency, request count

### Integrity Verification

The IndexVerifier provides comprehensive checks:

- **Missing Documents**: Documents in DB but not in index
- **Extra Documents**: Documents in index but not in DB
- **Version Mismatches**: DB version vs index version
- **Orphaned Documents**: Documents with broken relationships
- **Relationship Consistency**: Foreign key validation

---

## Management Commands

### rebuild_search_index

Rebuild search index for specified entity types.

```bash
# Rebuild all entity types
python manage.py rebuild_search_index --all

# Rebuild specific entity type
python manage.py rebuild_search_index --entity-type job

# Dry run
python manage.py rebuild_search_index --all --dry-run

# With progress
python manage.py rebuild_search_index --all --progress

# Custom chunk size
python manage.py rebuild_search_index --all --chunk-size 50
```

### sync_search_index

Synchronize search index with database changes.

```bash
# Sync all entity types
python manage.py sync_search_index --all

# Sync specific entity type
python manage.py sync_search_index --entity-type job

# Sync changes since timestamp
python manage.py sync_search_index --all --since "2024-01-01T00:00:00"

# Sync recent changes (relative time)
python manage.py sync_search_index --all --since "1h"
python manage.py sync_search_index --all --since "1d"

# Full sync
python manage.py sync_search_index --all --full

# Dry run
python manage.py sync_search_index --all --dry-run
```

### verify_search_index

Verify search index integrity.

```bash
# Verify all entity types
python manage.py verify_search_index --all

# Verify specific entity type
python manage.py verify_search_index --entity-type job

# Detailed verification
python manage.py verify_search_index --all --detailed

# Attempt to fix issues
python manage.py verify_search_index --all --fix
```

### search_index_status

Show search index status.

```bash
# Show status for all entity types
python manage.py search_index_status --all

# Show status for specific entity type
python manage.py search_index_status --entity-type job

# Show detailed metrics
python manage.py search_index_status --all --metrics

# Show bulk indexing jobs
python manage.py search_index_status --all --jobs
```

---

## Configuration

### Django Settings

```python
# Search provider configuration
SEARCH_PROVIDER = "postgresql"

SEARCH_CONFIG = {
    "postgresql": {
        "connection": "default",
    },
}

# Feature flags
SEARCH_FEATURE_FLAGS = {
    "full_text_search": True,
    "auto_indexing": True,
}

# Indexing configuration
INDEXING_CHUNK_SIZE = 100
INDEXING_MAX_RETRIES = 3
INDEXING_RETRY_DELAY = 1  # seconds
```

---

## Usage Examples

### Manual Document Synchronization

```python
from apps.search.registry import get_registry
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.serializers import JobSerializer
from apps.jobs.models import Job

# Get provider and sync service
registry = get_registry()
provider = registry.get_provider()
sync_service = SyncService(provider)

# Serialize and sync a job
job = Job.objects.get(id="job-123")
document = JobSerializer.serialize(job)
result = sync_service.sync_single_document(document)

print(f"Sync status: {result.status}")
```

### Bulk Indexing

```python
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.documents import EntityType

# Create bulk indexer
sync_service = SyncService(provider)
bulk_indexer = BulkIndexer(sync_service, chunk_size=100)

# Create and execute job
job = bulk_indexer.create_job(EntityType.JOB)

def progress_callback(job):
    print(f"Progress: {job.progress_percentage:.1f}%")

job = bulk_indexer.execute_job(job, progress_callback=progress_callback)

print(f"Processed {job.processed_count} documents")
print(f"Failed: {job.failed_count}")
```

### Index Management

```python
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.documents import EntityType

# Create index manager
index_manager = IndexManager(provider)

# Create index
index_manager.create_index(EntityType.JOB)

# Check health
health = index_manager.health_check(EntityType.JOB)
print(f"Health: {health['status']}")

# Get statistics
stats = index_manager.get_statistics(EntityType.JOB)
print(f"Document count: {stats.get('document_count')}")
```

### Integrity Verification

```python
from apps.search.indexing.verification import IndexVerifier
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.documents import EntityType

# Create verifier
index_manager = IndexManager(provider)
verifier = IndexVerifier(index_manager)

# Verify entity type
report = verifier.verify_entity_type(EntityType.JOB, detailed=True)

print(f"Healthy: {report.is_healthy}")
print(f"Issues: {report.issue_count}")
print(f"Critical: {report.critical_count}")
```

---

## Lifecycle

### Document Lifecycle

1. **Creation**: Model created → Django signal → Serialize → Sync to provider
2. **Update**: Model updated → Django signal → Serialize → Sync to provider
3. **Deletion**: Model deleted → Django signal → Delete from provider
4. **Bulk Import**: Bulk indexer → Chunked processing → Sync to provider
5. **Verification**: Periodic verification → Issue detection → Fix if needed

### Index Lifecycle

1. **Create**: IndexManager.create_index → Provider creates index
2. **Populate**: Bulk indexer → Sync service → Provider indexes documents
3. **Maintain**: Event handlers → Sync service → Provider updates documents
4. **Optimize**: IndexManager.optimize_index → Provider optimizes
5. **Rebuild**: IndexManager.rebuild_index → Delete and recreate

---

## Failure Recovery

### Retry Strategy

- **Max Retries**: 3 attempts (configurable)
- **Retry Delay**: 1 second (configurable)
- **Dead-Letter Queue**: Failed operations stored for manual review
- **Retry Command**: `retry_dead_letter_queue()` to retry failed items

### Checkpoint Resume

- **Automatic Checkpoints**: Saved every chunk
- **Disk Persistence**: Checkpoints stored to disk
- **Resume Capability**: Resume interrupted jobs from checkpoint
- **Cleanup**: Automatic cleanup of old checkpoints

### Verification and Repair

- **Missing Documents**: Detected and can be re-synced
- **Extra Documents**: Detected and can be removed
- **Version Mismatches**: Detected and can be updated
- **Relationship Issues**: Detected and reported

---

## Performance Considerations

### Memory Efficiency

- **Iterator Pattern**: Django querysets use iterators for large datasets
- **Chunked Processing**: Configurable chunk size (default: 100)
- **Streaming**: Documents processed one at a time
- **Checkpoint Persistence**: Minimal memory footprint

### Scalability

- **Bulk Operations**: Efficient bulk indexing for large datasets
- **Parallel Processing**: Can be extended with Celery for async processing
- **Provider Abstraction**: Easy to add new providers
- **Horizontal Scaling**: Multiple indexer instances can run in parallel

### Monitoring

- **Metrics**: Comprehensive metrics collection
- **Progress Tracking**: Real-time progress updates
- **Health Checks**: Index health monitoring
- **Status Commands**: Quick status overview

---

## Extension Guide

### Adding a New Document Type

1. **Define Document**: Add to `documents.py`
```python
@dataclass
class NewEntityDocument(BaseDocument):
    entity_type: EntityType = EntityType.NEW_ENTITY
    # Add fields
```

2. **Create Serializer**: Add to `serializers.py`
```python
class NewEntitySerializer(BaseSerializer):
    @classmethod
    def serialize(cls, instance) -> NewEntityDocument:
        # Implement serialization
```

3. **Register EntityType**: Add to `EntityType` enum
```python
class EntityType(str, Enum):
    NEW_ENTITY = "new_entity"
```

4. **Add Signal Handler**: Update `event_handlers.py`
```python
elif isinstance(instance, NewEntity):
    document = NewEntitySerializer.serialize(instance)
    sync_service.sync_single_document(document)
```

### Adding a New Search Provider

1. **Implement Provider Interface**: Extend `SearchProvider` base class
2. **Register Provider**: Add to registry
3. **Implement Index Methods**: Add provider-specific index methods
4. **Test**: Verify with existing indexing engine

---

## Testing

Run tests:

```bash
# Run all indexing tests
python manage.py test apps.search.indexing

# Run specific test file
python manage.py test apps.search.indexing.tests.test_documents

# Run with coverage
coverage run --source='apps.search.indexing' manage.py test apps.search.indexing
coverage report
```

---

## Migration Guide

### From Direct Provider Usage

**Before:**
```python
# Direct Elasticsearch usage
es_client.index(index="jobs", id=job.id, body=job_data)
```

**After:**
```python
# Provider-agnostic indexing
document = JobSerializer.serialize(job)
sync_service.sync_single_document(document)
```

### From Custom Indexing Logic

**Before:**
```python
# Custom indexing logic
def index_job(job):
    data = {
        "title": job.title,
        "company": job.company_name,
        # ...
    }
    es_client.index(index="jobs", id=job.id, body=data)
```

**After:**
```python
# Use indexing engine
document = JobSerializer.serialize(job)
sync_service.sync_single_document(document)
```

---

## Troubleshooting

### Common Issues

**Issue: Documents not appearing in search index**
- Check if auto-indexing is enabled: `SEARCH_FEATURE_FLAGS["auto_indexing"]`
- Verify signal handlers are registered
- Check dead-letter queue for failed syncs

**Issue: Bulk indexing job failed**
- Check job status with `search_index_status --jobs`
- Review error message in job metadata
- Resume job from checkpoint if available

**Issue: Verification shows missing documents**
- Run `sync_search_index --full` to re-sync
- Check for database connectivity issues
- Verify provider is accessible

**Issue: High memory usage during bulk indexing**
- Reduce chunk size: `--chunk-size 50`
- Use iterator pattern (already implemented)
- Process entity types separately

---

## Future Enhancements

### Planned Features

- **Async Processing**: Celery integration for async indexing
- **Real-time Sync**: WebSocket-based real-time updates
- **Vector Embeddings**: Automatic vector generation
- **Hybrid Search**: Combined keyword + vector search
- **Multi-tenant**: Tenant-specific indexing
- **Index Sharding**: Automatic shard management
- **Hot-swapping**: Zero-downtime index updates

### Provider Roadmap

- **Elasticsearch**: Full Elasticsearch provider (Phase 5.3)
- **OpenSearch**: OpenSearch provider
- **Vector Search**: Vector database provider
- **Hybrid Search**: Hybrid search provider

---

## References

- [Search Infrastructure README](../README.md)
- [Developer Guide](../DEVELOPER_GUIDE.md)
- [Provider Registry](../../registry.py)
- [Search Configuration](../../config.py)
