# Search Indexing Engine

This directory documents the provider-agnostic indexing platform introduced in Phase 5.2.

## Documents

- [Architecture](architecture.md)
- [Lifecycle](lifecycle.md)
- [Synchronization Flow](synchronization-flow.md)
- [Failure Recovery](failure-recovery.md)
- [Management Commands](management-commands.md)
- [Developer Guide](developer-guide.md)
- [Extension Guide](extension-guide.md)

## Scope

The indexing engine is the single source of truth for keeping search providers synchronized with MatchHire domain data.

The engine is intentionally provider-independent and does not embed Elasticsearch-specific assumptions.
