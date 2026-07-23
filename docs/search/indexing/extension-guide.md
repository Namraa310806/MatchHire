# Extension Guide

## Adding a New Search Provider

1. Implement provider methods behind the existing search provider contract.
2. Register provider in the search registry.
3. Keep document schema provider-independent.
4. Validate lifecycle support through `IndexManager` operations.

## Required Behaviors

- Accept canonical document payloads from `document.to_dict()`.
- Support single-document index/delete operations.
- Expose health/statistics methods where feasible.

## Optional Behaviors

- Alias management for zero-downtime swaps.
- Bulk-native provider APIs (the engine can still chunk and stream).
- Provider-specific latency instrumentation hooks.

## Elasticsearch Readiness

Phase 5.3 should only require:

- Elasticsearch provider implementation.
- Provider registration and config selection.
- Provider-focused integration tests.

No business logic changes should be needed in domain apps.
