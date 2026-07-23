# Failure Recovery

## Retry Strategy

`SyncService` retries failed single-document operations with bounded attempts and delay.

## Dead-Letter Queue

After retries are exhausted, failed operations are captured in an in-memory dead-letter queue placeholder.

`sync_search_index --retry-dead-letter` can trigger retry attempts for queued failures.

## Bulk Job Resume

`BulkIndexer` persists per-job checkpoints and can resume paused or failed jobs using the saved position.

## Verification and Repair

`verify_search_index --fix` performs best-effort repair by re-running full sync for unhealthy entity types.

## Operational Guidance

- Use incremental sync first for low-disruption recovery.
- Use full rebuild for severe divergence or schema migrations.
- Run verification after any bulk backfill.
