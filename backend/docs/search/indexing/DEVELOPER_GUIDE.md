# Developer Guide - Search Indexing Engine

## Phase 5.2 - Search Indexing Engine

---

## Quick Start

### Basic Usage

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
```

---

## Document Serialization

### Creating a Custom Serializer

```python
from apps.search.indexing.serializers import BaseSerializer
from apps.search.indexing.documents import BaseDocument, EntityType

@dataclass
class CustomDocument(BaseDocument):
    entity_type: EntityType = EntityType.CUSTOM
    # Add your fields here

class CustomSerializer(BaseSerializer):
    @classmethod
    def serialize(cls, instance) -> CustomDocument:
        return CustomDocument(
            id=str(instance.id),
            entity_type=EntityType.CUSTOM,
            version=cls.get_version(),
            # Map instance fields to document fields
            custom_field=instance.field_name,
            metadata=cls.build_metadata(instance),
        )
```

### Serializing with Nested Relationships

```python
class JobSerializer(BaseSerializer):
    @classmethod
    def serialize(cls, job: Job) -> JobDocument:
        # Access related objects
        recruiter_name = job.recruiter.full_name
        
        return JobDocument(
            id=str(job.id),
            entity_type=EntityType.JOB,
            job_id=str(job.id),
            recruiter_id=str(job.recruiter_id),
            recruiter_name=recruiter_name,  # Custom field
            title=job.title,
            company_name=job.company_name,
            # ... other fields
        )
```

---

## Synchronization

### Single Document Sync

```python
from apps.search.indexing.sync_service import SyncService

sync_service = SyncService(provider)
result = sync_service.sync_single_document(document)

if result.status == SyncStatus.COMPLETED:
    print("Sync successful")
elif result.status == SyncStatus.FAILED:
    print(f"Sync failed: {result.error}")
```

### Bulk Document Sync

```python
documents = [doc1, doc2, doc3, ...]

results = sync_service.sync_bulk_documents(documents)

for result in results:
    print(f"{result.document_id}: {result.status}")
```

### Incremental Sync

```python
from datetime import datetime, timedelta

# Sync changes in the last hour
since = datetime.utcnow() - timedelta(hours=1)
progress = sync_service.sync_incremental(EntityType.JOB, since)

print(f"Synced {progress.completed} documents")
print(f"Failed: {progress.failed}")
```

### Full Rebuild

```python
progress = sync_service.sync_full_rebuild(EntityType.JOB)

print(f"Rebuilt {progress.completed} documents")
print(f"Duration: {progress.duration:.2f}s")
```

---

## Index Management

### Creating an Index

```python
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.documents import EntityType

index_manager = IndexManager(provider)

# Create with default settings
index_manager.create_index(EntityType.JOB)

# Create with custom settings
settings = {
    "number_of_shards": 3,
    "number_of_replicas": 1,
}
index_manager.create_index(EntityType.JOB, settings=settings)
```

### Rebuilding an Index

```python
# Delete and recreate
index_manager.rebuild_index(EntityType.JOB)
```

### Checking Health

```python
health = index_manager.health_check(EntityType.JOB)

print(f"Status: {health['status']}")
print(f"Message: {health.get('message', '')}")
```

### Getting Statistics

```python
stats = index_manager.get_statistics(EntityType.JOB)

print(f"Document count: {stats.get('document_count')}")
print(f"Index size: {stats.get('index_size')}")
```

---

## Bulk Indexing

### Creating a Bulk Job

```python
from apps.search.indexing.bulk_indexer import BulkIndexer

bulk_indexer = BulkIndexer(sync_service, chunk_size=50)
job = bulk_indexer.create_job(EntityType.JOB)

print(f"Job ID: {job.job_id}")
```

### Executing with Progress Tracking

```python
def progress_callback(job):
    print(f"Progress: {job.progress_percentage:.1f}%")
    print(f"Speed: {job.documents_per_second:.1f} docs/sec")

job = bulk_indexer.execute_job(job, progress_callback=progress_callback)
```

### Pausing and Resuming

```python
# Pause a running job
job = bulk_indexer.pause_job(job.job_id)

# Resume later
job = bulk_indexer.resume_job(job.job_id)
```

### Canceling a Job

```python
job = bulk_indexer.cancel_job(job.job_id)
```

### Listing Jobs

```python
# List all jobs
jobs = bulk_indexer.list_jobs()

# Filter by status
active_jobs = bulk_indexer.list_jobs(status=BulkIndexStatus.IN_PROGRESS)

# Filter by entity type
job_jobs = bulk_indexer.list_jobs(entity_type=EntityType.JOB)
```

---

## Event Handlers

### Registering Custom Signal Handlers

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=YourModel)
def handle_your_model_save(sender, instance, **kwargs):
    from apps.search.indexing.event_handlers import get_sync_service
    from apps.search.indexing.serializers import YourSerializer
    
    if not should_index_model(instance):
        return
    
    try:
        sync_service = get_sync_service()
        document = YourSerializer.serialize(instance)
        sync_service.sync_single_document(document)
    except Exception as e:
        logger.error(f"Failed to index document: {e}")
```

### Disabling Auto-Indexing

```python
# Via feature flag
SEARCH_FEATURE_FLAGS = {
    "auto_indexing": False,
}

# Or unregister signal handlers
from apps.search.indexing.event_handlers import unregister_indexing_signals
unregister_indexing_signals()
```

---

## Metrics

### Recording Custom Metrics

```python
from apps.search.indexing.metrics import IndexingMetrics

metrics = IndexingMetrics()

# Record operation
metrics.record_index_operation(
    operation="custom_operation",
    entity_type="job",
    duration=1.5,
    success=True,
)

# Record document indexed
metrics.record_document_indexed(entity_type="job", count=10)

# Record provider latency
metrics.record_provider_latency(provider_name="elasticsearch", latency=0.5)
```

### Retrieving Metrics

```python
# Get operation metrics
op_metrics = metrics.get_operation_metrics(operation="index")

# Get document metrics
doc_metrics = metrics.get_document_metrics(entity_type="job")

# Get summary
summary = metrics.get_summary()
print(f"Total indexed: {summary['total_documents_indexed']}")
print(f"Docs/sec: {summary['documents_per_second']:.2f}")
```

---

## Verification

### Verifying Entity Type

```python
from apps.search.indexing.verification import IndexVerifier

verifier = IndexVerifier(index_manager)
report = verifier.verify_entity_type(EntityType.JOB, detailed=True)

print(f"Healthy: {report.is_healthy}")
print(f"Issues: {report.issue_count}")
print(f"Critical: {report.critical_count}")

for issue in report.issues:
    print(f"{issue.issue_type}: {issue.description}")
```

### Verifying All Entity Types

```python
reports = verifier.verify_all_entity_types(detailed=True)

for report in reports:
    print(f"{report.entity_type}: {report.issue_count} issues")

summary = verifier.get_summary(reports)
print(f"Overall healthy: {summary['overall_healthy']}")
```

---

## Error Handling

### Handling Sync Failures

```python
result = sync_service.sync_single_document(document)

if result.status == SyncStatus.FAILED:
    print(f"Failed after {result.retry_count} retries")
    print(f"Error: {result.error}")
    
    # Check dead letter queue
    dead_letter = sync_service.get_dead_letter_queue()
    print(f"Dead letter queue size: {len(dead_letter)}")
```

### Retrying Failed Operations

```python
# Retry all dead letter queue items
results = sync_service.retry_dead_letter_queue()

for result in results:
    print(f"{result.document_id}: {result.status}")
```

### Custom Retry Logic

```python
class CustomSyncService(SyncService):
    def __init__(self, provider, max_retries=5, retry_delay=2):
        super().__init__(provider)
        self.max_retries = max_retries
        self.retry_delay = timedelta(seconds=retry_delay)
```

---

## Testing

### Writing Document Tests

```python
from django.test import TestCase
from apps.search.indexing.documents import CandidateDocument, EntityType

class TestCandidateDocument(TestCase):
    def test_document_creation(self):
        doc = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        self.assertEqual(doc.entity_type, EntityType.CANDIDATE)
        self.assertIn("John Doe", doc.searchable_text)
```

### Writing Serializer Tests

```python
from django.test import TestCase
from apps.users.models import User
from apps.search.indexing.serializers import CandidateSerializer

class TestCandidateSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            role=User.Roles.CANDIDATE,
            full_name="John Doe",
        )
    
    def test_serialize(self):
        document = CandidateSerializer.serialize_from_user(self.user)
        
        self.assertEqual(document.email, self.user.email)
        self.assertEqual(document.full_name, self.user.full_name)
```

### Writing Sync Service Tests

```python
from unittest.mock import Mock
from django.test import TestCase
from apps.search.indexing.sync_service import SyncService

class TestSyncService(TestCase):
    def test_sync_single_document(self):
        provider = Mock()
        sync_service = SyncService(provider)
        
        document = Mock(id="test", entity_type="candidate")
        result = sync_service.sync_single_document(document)
        
        self.assertEqual(result.status, "completed")
```

---

## Best Practices

### 1. Use Feature Flags

```python
from apps.search.config import SearchConfig

if SearchConfig.is_feature_enabled("auto_indexing"):
    # Enable auto-indexing
```

### 2. Handle Errors Gracefully

```python
try:
    result = sync_service.sync_single_document(document)
except SearchError as e:
    logger.error(f"Search error: {e}")
    # Handle error appropriately
```

### 3. Use Appropriate Chunk Sizes

```python
# For small datasets
bulk_indexer = BulkIndexer(sync_service, chunk_size=50)

# For large datasets
bulk_indexer = BulkIndexer(sync_service, chunk_size=200)
```

### 4. Monitor Dead Letter Queue

```python
dead_letter = sync_service.get_dead_letter_queue()
if len(dead_letter) > 100:
    # Alert or take action
    logger.warning(f"Large dead letter queue: {len(dead_letter)}")
```

### 5. Use Checkpoints for Long Jobs

```python
# Checkpoints are automatically saved
# Resume capability is built-in
job = bulk_indexer.resume_job(job.job_id)
```

### 6. Verify After Bulk Operations

```python
# After bulk indexing, verify integrity
report = verifier.verify_entity_type(EntityType.JOB)
if not report.is_healthy:
    # Take corrective action
    pass
```

---

## Troubleshooting

### Debug Mode

```python
import logging
logging.getLogger('apps.search.indexing').setLevel(logging.DEBUG)
```

### Common Issues

**Documents not indexing**:
- Check feature flags
- Verify signal handlers registered
- Check dead letter queue

**Bulk job slow**:
- Reduce chunk size
- Check database performance
- Monitor provider latency

**Verification failures**:
- Run full sync
- Check relationships
- Verify provider connectivity

---

## Performance Tips

### 1. Use Select Related

```python
# Inefficient
users = User.objects.filter(role=User.Roles.CANDIDATE)

# Efficient
users = User.objects.filter(
    role=User.Roles.CANDIDATE
).select_related("candidate_profile")
```

### 2. Use Iterator Pattern

```python
# Inefficient (loads all into memory)
documents = list(queryset)

# Efficient (streams)
documents = queryset.iterator()
```

### 3. Batch Operations

```python
# Inefficient (one by one)
for doc in documents:
    sync_service.sync_single_document(doc)

# Efficient (bulk)
sync_service.sync_bulk_documents(documents)
```

### 4. Tune Chunk Size

```python
# Start with default
chunk_size = 100

# Adjust based on performance
# Smaller chunks = less memory, more overhead
# Larger chunks = more memory, less overhead
```

---

## Extension Examples

### Adding a New Document Type

```python
# 1. Define document
@dataclass
class ProductDocument(BaseDocument):
    entity_type: EntityType = EntityType.PRODUCT
    product_id: str
    name: str
    price: float
    # ...

# 2. Create serializer
class ProductSerializer(BaseSerializer):
    @classmethod
    def serialize(cls, product) -> ProductDocument:
        return ProductDocument(
            id=str(product.id),
            entity_type=EntityType.PRODUCT,
            product_id=str(product.id),
            name=product.name,
            price=float(product.price),
            metadata=cls.build_metadata(product),
        )

# 3. Add to EntityType enum
class EntityType(str, Enum):
    PRODUCT = "product"

# 4. Register signal handler
@receiver(post_save, sender=Product)
def handle_product_save(sender, instance, **kwargs):
    document = ProductSerializer.serialize(instance)
    sync_service.sync_single_document(document)
```

### Custom Sync Logic

```python
class ConditionalSyncService(SyncService):
    def sync_single_document(self, document, retry_count=0):
        # Add custom condition
        if document.metadata.get("skip_indexing"):
            return SyncResult(
                document_id=document.id,
                entity_type=document.entity_type.value,
                status=SyncStatus.COMPLETED,
            )
        
        return super().sync_single_document(document, retry_count)
```

---

## References

- [Indexing README](README.md)
- [Architecture](ARCHITECTURE.md)
- [Search Infrastructure README](../README.md)
- [Provider Registry](../../registry.py)
