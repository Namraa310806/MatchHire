# Synchronization Flow

## Single Document Sync

- Trigger: create/update event.
- Path: event handler -> serializer -> `SyncService.sync_single_document`.
- Behavior: retries up to configured maximum before moving to dead-letter queue.

## Bulk Sync

- Trigger: command or rebuild process.
- Path: iterator -> chunk processor -> `sync_bulk_documents`.
- Behavior: progress updates, checkpoint persistence, optional transaction boundaries.

## Incremental Sync

- Trigger: command with `--since` or default time window.
- Path: `SyncService._get_documents_since` by entity type.
- Behavior: only changed records are serialized and synchronized.

## Full Rebuild Sync

- Trigger: rebuild or repair operation.
- Path: `SyncService._get_all_documents` by entity type.
- Behavior: reserializes full source set and resubmits to provider.
