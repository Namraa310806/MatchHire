# Indexing Lifecycle

## 1. Source Update

A domain model changes in applications such as users, jobs, resumes, or applications.

## 2. Trigger

Django signals call indexing event handlers as lightweight triggers.

## 3. Serialization

The relevant serializer converts model state into a provider-independent search document.

## 4. Synchronization

`SyncService` executes single-document sync with retry and dead-letter fallback.

## 5. Provider Write

The provider receives a normalized document payload via `document.to_dict()`.

## 6. Observability

Shared indexing metrics record throughput, durations, success/failure rates, and queue behavior.
