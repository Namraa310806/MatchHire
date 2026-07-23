# Indexing Architecture

## Core Principles

- Provider independent document model.
- Single synchronization pipeline for all providers.
- Event-triggered indexing with business logic isolation.
- Bulk and incremental indexing paths share common serialization contracts.

## Package Layout

- `backend/apps/search/indexing/documents.py`: Canonical search document schema.
- `backend/apps/search/indexing/serializers.py`: Django model to document mapping.
- `backend/apps/search/indexing/index_manager.py`: Index lifecycle abstraction.
- `backend/apps/search/indexing/sync_service.py`: Sync engine.
- `backend/apps/search/indexing/bulk_indexer.py`: Chunked bulk framework.
- `backend/apps/search/indexing/event_handlers.py`: Signal triggers.
- `backend/apps/search/indexing/verification.py`: Integrity checks.
- `backend/apps/search/indexing/metrics.py`: Indexing telemetry.

## Provider Contract

Providers are accessed via `apps.search.registry.get_registry().get_provider()`.

The indexing engine delegates through capability checks such as:

- `index_document`
- `delete_document`
- `create_index`
- `delete_index`
- `refresh_index`
- `optimize_index`
- `health_check`
- `get_index_statistics`
- alias helpers

If a provider does not implement an optional capability, the indexing layer preserves safe defaults.
