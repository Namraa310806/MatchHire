# Architecture Documentation
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document provides comprehensive architecture documentation including component diagrams, sequence diagrams, data flow, index flow, ranking flow, roadmap, and decision log for the MatchHire search architecture.

---

## Component Diagram

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Web App    │  │  Mobile App  │  │   API Client │  │  Admin Panel │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Gateway                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  AuthN/AuthZ │  │ Rate Limiting│  │ Request Log  │  │ Load Balancer│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Application Layer                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Django REST Framework                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Search Views │  │Autocomplete  │  │Recommendation│              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Service Layer                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Search       │  │ Ranking      │  │ Filtering    │              │  │
│  │  │ Service      │  │ Service      │  │ Service      │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Pagination   │  │ Faceting     │  │ Autocomplete │              │  │
│  │  │ Service      │  │ Service      │  │ Service      │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  │  ┌──────────────┐  ┌──────────────┐                                 │  │
│  │  │Recommendation│  │ Indexing     │                                 │  │
│  │  │ Service      │  │ Service      │                                 │  │
│  │  └──────────────┘  └──────────────┘                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Provider Layer                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Provider Factory                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Elasticsearch│  │ OpenSearch   │  │ PostgreSQL   │  │ Vector Search │  │
│  │ Provider     │  │ Provider     │  │ Provider     │  │ Provider     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐                                                          │  │
│  │ Hybrid       │                                                          │  │
│  │ Provider     │                                                          │  │
│  └──────────────┘                                                          │  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Storage Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Elasticsearch │  │ OpenSearch   │  │ PostgreSQL   │  │ Vector DB    │  │
│  │ Cluster      │  │ Cluster      │  │ Database     │  │ (Pinecone)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │  │
│  │ Redis Cache  │  │ Celery Queue │  │ S3 Storage   │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Background Processing                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Celery       │  │ Embedding    │  │ Match Score  │  │ Index Sync   │  │
│  │ Workers      │  │ Generation  │  │ Calculation  │  │ Service      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagrams

### Search Request Sequence

```
Client                    API Gateway              Django App              Search Service              Provider              Storage
  │                          │                         │                        │                      │
  │─── GET /search/jobs ────>│                         │                        │                      │
  │                          │─── Auth Check ─────────>│                        │                      │
  │                          │<── Auth Valid ──────────│                        │                      │
  │                          │─── Rate Limit Check ────>│                        │                      │
  │                          │<── Rate OK ─────────────│                        │                      │
  │                          │─── Forward Request ─────>│                        │                      │
  │                          │                         │─── Validate Query ────>│                      │
  │                          │                         │<── Valid ──────────────│                      │
  │                          │                         │─── Build Search Query ──>│                      │
  │                          │                         │─── Apply Filters ──────>│                      │
  │                          │                         │─── Apply Ranking ──────>│                      │
  │                          │                         │─── Execute Search ─────>│                      │
  │                          │                         │                        │─── Query ────────────>│
  │                          │                         │                        │                      │
  │                          │                         │                        │<── Results ───────────│
  │                          │                         │<── Search Results ─────│                      │
  │                          │                         │─── Compute Facets ─────>│                      │
  │                          │                         │─── Apply Pagination ────>│                      │
  │                          │                         │<── Paginated Results ───│                      │
  │                          │<── JSON Response ───────│                        │                      │
  │<── Search Results ────────│                         │                        │                      │
```

### Indexing Sequence

```
Django ORM               Signal Handler          Indexing Service          Provider              Storage
    │                          │                         │                      │
    │─── save() ──────────────>│                         │                      │
    │                          │─── post_save Signal ────>│                      │
    │                          │                         │─── Transform Data ────>│
    │                          │                         │─── Add Metadata ──────>│
    │                          │                         │─── Index Document ─────>│
    │                          │                         │                      │─── Index ──────────>│
    │                          │                         │                      │                      │
    │                          │                         │                      │<── Success ──────────│
    │                          │                         │<── Index Result ───────│
    │                          │<── Index Complete ──────│                      │
    │<── save() Complete ───────│                         │                      │
```

### Recommendation Sequence

```
Client                    Django App          Recommendation Service      Vector Provider         Storage
  │                            │                         │                      │
  │─── GET /recommendations ──>│                         │                      │
  │                            │─── Get User Context ────>│                      │
  │                            │<── Context ──────────────│                      │
  │                            │─── Generate Recommendations ─────────────────>│
  │                            │                         │                      │
  │                            │                         │─── Vector Similarity ───────────────>│
  │                            │                         │                      │
  │                            │                         │<── Similar Items ────────────────────│
  │                            │<── Recommendations ──────│                      │
  │                            │─── Apply Filters ──────>│                      │
  │                            │─── Rank Results ────────>│                      │
  │                            │<── Ranked Results ───────│                      │
  │<── Recommendations ────────│                         │                      │
```

---

## Data Flow

### Search Data Flow

```
1. Client Request
   ↓
2. API Gateway
   - Authentication
   - Authorization
   - Rate Limiting
   - Request Logging
   ↓
3. Django API Layer
   - Request Validation
   - Parameter Parsing
   - View Selection
   ↓
4. Service Layer
   - SearchService: Build query
   - FilteringService: Apply filters
   - RankingService: Apply ranking
   - PaginationService: Apply pagination
   - FacetingService: Compute facets
   ↓
5. Provider Layer
   - Provider Selection (via Factory)
   - Query Translation (to provider DSL)
   - Query Execution
   ↓
6. Storage Layer
   - Elasticsearch/OpenSearch: Execute search
   - PostgreSQL: Execute query (if using PG provider)
   - Vector DB: Execute similarity search (if using vector provider)
   ↓
7. Provider Layer
   - Result Parsing
   - Result Normalization
   ↓
8. Service Layer
   - Facet Computation
   - Ranking Application
   - Pagination Application
   - Response Formatting
   ↓
9. Django API Layer
   - Serialization.
   - Response Headers
   ↓
10. API Gateway
    - Response Logging
    ↓
11. Client Response
```

### Indexing Data Flow

```
1. Data Change (CRUD Operation)
   ↓
2. Django ORM
   - Database Update
   ↓
3. Django Signal (post_save/post_delete)
   ↓
4. Indexing Service
   - Document Transformation
   - Metadata Addition
   - Validation
   ↓
5. Celery Task (Async)
   - Task Queue
   - Worker Execution
   ↓
6. Provider Layer
   - Provider Selection
   - Document Translation
   ↓
7. Storage Layer
   - Elasticsearch/OpenSearch: Index document
   - Vector DB: Index vector embedding
   ↓
8. Provider Layer
   - Result Validation
   - Error Handling
   - Retry Logic
   ↓
9. Indexing Service
   - Cache Invalidation
   - Status Update
   ↓
10. Monitoring
    - Logging
    - Metrics
```

---

## Index Flow

### Index Creation Flow

```
1. Define Index Schema
   - Field mappings
   - Analyzer configuration
   - Settings (shards, replicas)
   ↓
2. Create Index
   - Provider.create_index()
   - Apply mappings
   - Apply settings
   ↓
3. Initial Data Load
   - Bulk index existing data
   - Validate indexed data
   ↓
4. Create Alias
   - Point alias to new index
   - Zero-downtime switch
   ↓
5. Monitor
   - Index health
   - Index size
   - Index performance
```

### Index Update Flow

```
1. Data Change Detected
   - Django signal triggered
   ↓
2. Transform Document
   - Map Django model to search document
   - Add metadata (timestamps, etc.)
   ↓
3. Index Document
   - Provider.index_document()
   - Synchronous (critical) or Async (non-critical)
   ↓
4. Validate
   - Check index status
   - Verify document indexed
   ↓
5. Invalidate Cache
   - Remove from Redis cache
   - Update cache keys
   ↓
6. Log
   - Indexing event logged
   - Metrics updated
```

### Index Reindex Flow

```
1. Trigger Reindex
   - Manual trigger or scheduled
   ↓
2. Create New Index
   - New index with new mappings
   - New index name (v2, v3, etc.)
   ↓
3. Bulk Index Data
   - Fetch data from PostgreSQL
   - Transform to search documents
   - Bulk index to new index
   ↓
4. Validate New Index
   - Compare document counts
   - Sample data validation
   - Query validation
   ↓
5. Switch Alias
   - Update alias to point to new index
   - Zero-downtime switch
   ↓
6. Delete Old Index
   - Wait for validation period
   - Delete old index
   ↓
7. Cleanup
   - Remove old snapshots
   - Update monitoring
```

---

## Ranking Flow

### Ranking Pipeline

```
1. Search Results Retrieved
   - From provider (Elasticsearch, etc.)
   ↓
2. Signal Calculation
   - Text Relevance: BM25 score
   - Match Score: Pre-calculated or real-time
   - Recency: Time-based decay
   - Popularity: View count, application count
   - Quality: Completeness, verification
   ↓
3. Signal Normalization
   - Normalize all signals to 0-100 range
   - Linear, logarithmic, or sigmoid normalization
   ↓
4. Weight Application
   - Apply configured weights to each signal
   - Weighted sum or weighted average
   ↓
5. Score Combination
   - Combine weighted signals
   - Final ranking score
   ↓
6. Reordering
   - Sort by final score
   - Apply tie-breaking rules
   ↓
7. Result Return
   - Return ranked results
   - Include ranking explanation (if requested)
```

### Hybrid Ranking Flow (Future)

```
1. Keyword Search
   - Execute keyword search
   - Get BM25 scores
   ↓
2. Vector Search
   - Generate query embedding
   - Execute vector similarity search
   - Get cosine similarity scores
   ↓
3. Score Normalization
   - Normalize keyword scores to 0-100
   - Normalize vector scores to 0-100
   ↓
4. Reciprocal Rank Fusion (RRF)
   - Combine rankings using RRF
   - RRF score = 1/(k + rank_keyword) + 1/(k + rank_vector)
   ↓
5. Final Ranking
   - Sort by RRF score
   - Return combined results
```

---

## Roadmap

### Phase 1: Current State (Complete)
**Timeline:** Q1 2024
**Status:** Complete

**Features:**
- PostgreSQL-based search with Django ORM
- Basic job search with filters
- Resume search with structured data
- Pre-calculated match scores
- Basic recommendations

**Limitations:**
- No full-text search
- No faceted search
- No autocomplete
- No semantic search
- Poor scalability

---

### Phase 2: Elasticsearch Deployment (Next)
**Timeline:** Q2 2024
**Status:** Planned

**Features:**
- Deploy Elasticsearch cluster (3 nodes)
- Implement ElasticsearchProvider
- Create search indexes with mappings
- Implement full-text search with BM25
- Add faceted search with aggregations
- Add autocomplete with completion suggester
- Implement multi-level caching (Redis + Elasticsearch)
- Real-time indexing with Celery
- Index lifecycle management

**Deliverables:**
- Elasticsearch cluster deployed
- Search API endpoints migrated to Elasticsearch
- Faceted search implemented
- Autocomplete implemented
- Caching strategy implemented
- Indexing service implemented

**Success Criteria:**
- Search latency < 100ms (p95)
- Index freshness < 5 seconds
- Cache hit rate > 60%
- Zero downtime migration

---

### Phase 3: Vector Search
**Timeline:** Q3 2024
**Status:** Planned

**Features:**
- Deploy vector database (Pinecone or pgvector)
- Implement VectorSearchProvider
- Generate embeddings for entities (candidates, jobs, resumes)
- Implement semantic search
- Implement HybridProvider (keyword + vector)
- Add similar candidates/jobs recommendations
- Implement reciprocal rank fusion (RRF)
- Add embedding generation pipeline

**Deliverables:**
- Vector database deployed
- Embedding provider implemented
- Semantic search implemented
- Hybrid search implemented
- Similar items recommendations implemented

**Success Criteria:**
- Semantic search latency < 200ms (p95)
- Hybrid search improves relevance by 20%
- Embedding generation throughput > 1000 docs/sec

---

### Phase 4: Advanced Ranking
**Timeline:** Q4 2024
**Status:** Planned

**Features:**
- Implement LLMRankingProvider
- Add user behavior tracking (clicks, dwell time)
- Implement learning-to-rank model
- Add personalization based on user preferences
- Implement A/B testing framework
- Add ranking explainability
- Optimize ranking weights

**Deliverables:**
- LLM ranking provider implemented
- User behavior tracking implemented
- Learning-to-rank model trained
- Personalization implemented
- A/B testing framework implemented

**Success Criteria:**
- CTR improvement > 15%
- Ranking explainability for all results
- A/B testing framework operational

---

### Phase 5: Distributed Search
**Timeline:** Q1 2025
**Status:** Planned

**Features:**
- Multi-region Elasticsearch deployment
- Cross-cluster replication (CCR)
- Geo-based query routing
- Disaster recovery with snapshots
- Implement distributed caching (Redis Cluster)
- Add search analytics dashboard
- Implement search query logging
- Add search performance monitoring

**Deliverables:**
- Multi-region deployment
- Cross-cluster replication configured
- Geo-based routing implemented
- Disaster recovery implemented
- Search analytics dashboard operational

**Success Criteria:**
- Cross-region latency < 300ms
- Disaster recovery RTO < 4 hours
- Search analytics dashboard operational

---

### Phase 6: AI-Powered Search
**Timeline:** Q2 2025
**Status:** Planned

**Features:**
- Implement query understanding with NLP
- Add natural language query processing
- Implement intent detection
- Add query suggestion and correction
- Implement semantic query expansion
- Add conversational search
- Implement search result summarization

**Deliverables:**
- NLP query understanding implemented
- Natural language query processing implemented
- Query suggestion implemented
- Conversational search implemented

**Success Criteria:**
- Natural language query accuracy > 80%
- Query suggestion CTR > 30%
- Conversational search operational

---

## Decision Log

### Decision 1: Search Engine Selection
**Date:** 2024-01-15
**Status:** Decided

**Options Considered:**
1. Elasticsearch
2. OpenSearch
3. Solr
4. PostgreSQL Full-Text Search
5. Algolia (SaaS)

**Decision:** Elasticsearch

**Rationale:**
- Mature and widely adopted
- Rich feature set (full-text, aggregations, vector search)
- Strong community support
- Compatible with OpenSearch (vendor lock-in mitigation)
- Scalable to enterprise scale
- Python client library (elasticsearch-py)

**Alternatives Rejected:**
- OpenSearch: Similar to Elasticsearch, less mature ecosystem
- Solr: Steeper learning curve, less Python-friendly
- PostgreSQL Full-Text Search: Limited features, poor scalability
- Algolia: SaaS vendor lock-in, cost at scale

---

### Decision 2: Provider Interface Design
**Date:** 2024-01-16
**Status:** Decided

**Options Considered:**
1. Abstract base class with interface
2. Protocol class (Python 3.8+)
3. Duck typing (no formal interface)
4. Adapter pattern

**Decision:** Abstract base class with interface

**Rationale:**
- Clear contract for providers
- Type hints for better IDE support
- Enforces implementation of required methods
- Easy to test with mocks
- Compatible with Python 3.7+

**Alternatives Rejected:**
- Protocol class: Requires Python 3.8+
- Duck typing: No enforcement, harder to maintain
- Adapter pattern: More complex than needed

---

### Decision 3: Indexing Strategy
**Date:** 2024-01-17
**Status:** Decided

**Options Considered:**
1. Real-time synchronous indexing
2. Asynchronous with Celery
3. Hybrid (critical sync, non-critical async)
4. Event-driven with message queue

**Decision:** Hybrid (critical sync, non-critical async)

**Rationale:**
- Critical updates (job status, application status) indexed immediately
- Non-critical updates (profile changes) indexed asynchronously
- Balances freshness with performance
- Reduces request latency for non-critical operations
- Celery already in use for other background tasks

**Alternatives Rejected:**
- Real-time synchronous: High latency for all operations
- Asynchronous only: Delay for critical updates
- Event-driven: More complex, overkill for current needs

---

### Decision 4: Caching Strategy
**Date:** 2024-01-18
**Status:** Decided

**Options Considered:**
1. Application-level cache only (Redis)
2. Elasticsearch query cache only
3. Multi-level cache (Redis + Elasticsearch + OS)
4. CDN cache for API responses

**Decision:** Multi-level cache (Redis + Elasticsearch + OS)

**Rationale:**
- Redis for application-level caching (fastest)
- Elasticsearch query cache for repeated queries
- OS cache managed by Elasticsearch (file system cache)
- Reduces load on all layers
- Improves overall performance

**Alternatives Rejected:**
- Application-level only: Higher load on Elasticsearch
- Elasticsearch only: No application-level caching
- CDN cache: Not suitable for dynamic search results

---

### Decision 5: Pagination Strategy
**Date:** 2024-01-19
**Status:** Decided

**Options Considered:**
1. Offset/Limit pagination
2. Cursor-based pagination
3. Keyset pagination
4. Elasticsearch search_after

**Decision:** Support multiple strategies (default: offset/limit, option: search_after)

**Rationale:**
- Offset/Limit: Simple, sufficient for most use cases
- Search_after: Better for deep pagination (avoids deep pagination problem)
- Backward compatible with current implementation
- Allows optimization for specific use cases

**Alternatives Rejected:**
- Offset/Limit only: Deep pagination performance issues
- Cursor-based only: More complex, not always needed
- Keyset pagination: Requires unique sort field, less flexible

---

### Decision 6: Vector Database Selection
**Date:** 2024-01-20
**Status:** Tentative (Phase 3)

**Options Considered:**
1. Pinecone (SaaS)
2. Weaviate (self-hosted)
3. pgvector (PostgreSQL extension)
4. Milvus (self-hosted)
5. Elasticsearch dense_vector

**Decision:** Tentative: Pinecone or pgvector

**Rationale:**
- Pinecone: Managed service, easy deployment, good performance
- pgvector: No additional infrastructure, integrates with PostgreSQL
- Decision to be made based on cost and team expertise

**Alternatives Rejected:**
- Weaviate: Additional infrastructure overhead
- Milvus: Additional infrastructure overhead
- Elasticsearch dense_vector: Less performant than dedicated vector DB

---

### Decision 7: Ranking Strategy
**Date:** 2024-01-21
**Status:** Decided

**Options Considered:**
1. BM25 only
2. Pre-calculated match scores only
3. Hybrid (BM25 + match scores)
4. Learning-to-rank

**Decision:** Hybrid (BM25 + match scores + other signals)

**Rationale:**
- BM25 provides text relevance
- Match scores provide candidate-job compatibility
- Additional signals (recency, popularity) improve ranking
- Configurable weights for different use cases
- Path to learning-to-rank in future

**Alternatives Rejected:**
- BM25 only: No candidate-job compatibility
- Match scores only: No text relevance
- Learning-to-rank: Requires training data, more complex

---

### Decision 8: API Versioning
**Date:** 2024-01-22
**Status:** Decided

**Options Considered:**
1. URL-based versioning (/api/v1/search)
2. Header-based versioning (Accept: application/vnd.api.v1+json)
3. Query parameter versioning (?version=1)
4. No versioning (breaking changes allowed)

**Decision:** URL-based versioning

**Rationale:**
- Clear and explicit
- Easy to cache (URL-based cache keys)
- Standard practice in REST APIs
- Easy to deprecate old versions
- Compatible with API documentation tools

**Alternatives Rejected:**
- Header-based: Less explicit, harder to cache
- Query parameter: Less explicit,容易忽略
- No versioning: Breaking changes disruptive

---

### Decision 9: Index Naming Convention
**Date:** 2024-01-23
**Status:** Decided

**Options Considered:**
1. Entity name only (candidates)
2. Entity + environment (candidates_production)
3. Entity + environment + version (candidates_production_v1)
4. UUID-based (random UUID)

**Decision:** Entity + environment + version with aliases

**Rationale:**
- Clear identification of index purpose
- Environment separation (dev, staging, prod)
- Version support for zero-downtime reindexing
- Aliases for zero-downtime switching
- Easy to manage index lifecycle

**Alternatives Rejected:**
- Entity name only: No environment/version separation
- Entity + environment: No version support
- UUID-based: Not human-readable, hard to manage

---

### Decision 10: Monitoring Strategy
**Date:** 2024-01-24
**Status:** Decided

**Options Considered:**
1. Elasticsearch monitoring only
2. Application monitoring only
3. Full-stack monitoring (Elasticsearch + Application + Infrastructure)
4. Custom monitoring solution

**Decision:** Full-stack monitoring with Prometheus + Grafana

**Rationale:**
- End-to-end visibility
- Standard open-source tools
- Integration with existing infrastructure
- Custom dashboards for search-specific metrics
- Alerting on all layers

**Alternatives Rejected:**
- Elasticsearch only: No application visibility
- Application only: No infrastructure visibility
- Custom solution: Higher maintenance overhead

---

## Summary

The architecture documentation provides:

1. **Component Diagram:**
   - Client layer
   - API gateway
   - Application layer (Django)
   - Service layer
   - Provider layer
   - Storage layer
   - Background processing

2. **Sequence Diagrams:**
   - Search request sequence
   - Indexing sequence
   - Recommendation sequence

3. **Data Flow:**
   - Search data flow (11 steps)
   - Indexing data flow (10 steps)

4. **Index Flow:**
   - Index creation flow
   - Index update flow
   - Index reindex flow

5. **Ranking Flow:**
   - Ranking pipeline (7 steps)
   - Hybrid ranking flow (future)

6. **Roadmap:**
   - Phase 1: Current state (complete)
   - Phase 2: Elasticsearch deployment (Q2 2024)
   - Phase 3: Vector search (Q3 2024)
   - Phase 4: Advanced ranking (Q4 2024)
   - Phase 5: Distributed search (Q1 2025)
   - Phase 6: AI-powered search (Q2 2025)

7. **Decision Log:**
   - 10 key architectural decisions
   - Options considered
   - Rationale for decisions
   - Alternatives rejected

This comprehensive documentation provides a complete view of the search architecture, from components to data flows to future roadmap, enabling engineers to implement and extend the search system effectively.
