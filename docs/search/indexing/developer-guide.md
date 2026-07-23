# Developer Guide

## Adding a New Entity Document

1. Define a new document dataclass in `documents.py`.
2. Add an entity enum value in `EntityType`.
3. Implement a serializer in `serializers.py`.
4. Add sync retrieval paths in `SyncService` and `BulkIndexer` iterators.
5. Add tests for document shape and serializer behavior.

## Document Versioning

Each serializer emits `version` from `BaseSerializer.DOCUMENT_VERSION`.

When shape changes require migration logic:

1. Bump document version.
2. Keep provider consumption backward compatible where needed.
3. Rebuild affected entity indexes.

## Testing Focus

- Document schema and `to_dict` output.
- Serializer correctness with nested relationships.
- Retry and dead-letter behavior in sync service.
- Bulk chunking, checkpoint, and resume paths.
- Management command behavior for dry-run and operational modes.
