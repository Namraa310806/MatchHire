# Search Architecture
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines the modular search architecture for the MatchHire platform. The architecture is designed to be provider-agnostic, supporting multiple search backends (Elasticsearch, OpenSearch, PostgreSQL Full-Text Search, Vector Search) while maintaining a consistent API and service layer. The architecture follows clean separation of concerns with distinct layers for API, Services, Providers, Ranking, Filtering, Pagination, Faceting, Autocomplete, and Recommendations.

---

## Architectural Principles

1. **Provider Agnostic:** Core business logic independent of search engine implementation
2. **Interface-Based Design:** Define interfaces, not implementations
3. **Layered Architecture:** Clear separation between API, Service, and Provider layers
4. **Extensibility:** Easy to add new search providers without changing business logic
5. **Performance:** Optimized for low latency and high throughput
6. **Scalability:** Designed for horizontal scaling
7. **Testability:** Each layer independently testable
8. **Observability:** Built-in metrics and logging

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Search Views │  │ Autocomplete │  │ Recommendation│         │
│  │              │  │    Views     │  │    Views     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Search       │  │ Ranking      │  │ Filtering    │         │
│  │ Service      │  │ Service      │  │ Service      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Pagination   │  │ Faceting     │  │ Autocomplete │         │
│  │ Service      │  │ Service      │  │ Service      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Recommendation│  │ Indexing     │                         │
│  │ Service      │  │ Service      │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Provider Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Elasticsearch│  │ OpenSearch   │  │ PostgreSQL   │         │
│  │ Provider     │  │ Provider     │  │ Provider     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Vector Search │  │ Hybrid       │                         │
│  │ Provider     │  │ Provider     │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Elasticsearch │  │ OpenSearch   │  │ PostgreSQL   │         │
│  │ Cluster      │  │ Cluster      │  │ Database     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Vector DB    │  │ Redis Cache  │                         │
│  │ (e.g., Pinecone)│              │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: API Layer

### Purpose
Expose RESTful endpoints for search, autocomplete, and recommendations. Handle request validation, authentication, authorization, and response formatting.

### Components

#### Search Views
- `CandidateSearchView` - Search candidates
- `ResumeSearchView` - Search resumes
- `JobSearchView` - Search jobs
- `CompanySearchView` - Search companies
- `RecruiterSearchView` - Search recruiters
- `SkillSearchView` - Search skills
- `UnifiedSearchView` - Cross-entity search

#### Autocomplete Views
- `CandidateAutocompleteView` - Candidate name/headline completion
- `JobAutocompleteView` - Job title/company completion
- `SkillAutocompleteView` - Skill name completion
- `LocationAutocompleteView` - Location completion

#### Recommendation Views
- `CandidateRecommendationsView` - Job recommendations for candidates
- `JobRecommendationsView` - Candidate recommendations for jobs
- `SimilarCandidatesView` - Similar candidates
- `SimilarJobsView` - Similar jobs
- `RelatedSkillsView` - Related skills
- `TrendingSkillsView` - Trending skills
- `PopularSearchesView` - Popular search queries

### Responsibilities
- Request validation (query parameters, filters, pagination)
- Authentication and authorization
- Rate limiting
- Request/response serialization
- Error handling
- API documentation (OpenAPI/Swagger)

### Technology
- Django REST Framework
- drf-spectacular (OpenAPI documentation)
- Django throttling (rate limiting)

---

## Layer 2: Service Layer

### Purpose
Implement business logic for search operations. Orchestrate provider calls, apply ranking strategies, and compose complex search operations from simpler primitives.

### Components

#### SearchService
**Interface:**
```python
class SearchService(ABC):
    @abstractmethod
    def search(
        self,
        entity_type: str,
        query: str,
        filters: Dict[str, Any],
        sorting: List[SortField],
        pagination: PaginationParams,
    ) -> SearchResult:
        pass
```

**Responsibilities:**
- Execute search queries
- Apply filters
- Apply sorting
- Return paginated results
- Cache results (if configured)

**Implementations:**
- `ElasticsearchSearchService`
- `OpenSearchSearchService`
- `PostgreSQLSearchService`

---

#### RankingService
**Interface:**
```python
class RankingService(ABC):
    @abstractmethod
    def rank(
        self,
        results: List[SearchResult],
        context: RankingContext,
    ) -> List[SearchResult]:
        pass
```

**Responsibilities:**
- Apply ranking algorithms
- Combine multiple ranking signals
- Re-order results based on relevance
- Apply personalization (if configured)

**Ranking Strategies:**
- `MatchScoreRankingStrategy` - Use pre-calculated match scores
- `TFIDFRankingStrategy` - Term frequency-inverse document frequency
- `BM25RankingStrategy` - Best Matching 25
- `LearningToRankStrategy` - ML-based ranking (future)
- `HybridRankingStrategy` - Combine multiple strategies

**Ranking Signals:**
- Text relevance (BM25 score)
- Match score (pre-calculated)
- Recency (creation/update date)
- Popularity (view count, application count)
- User behavior (click-through rate)
- Personalization (user preferences)

---

#### FilteringService
**Interface:**
```python
class FilteringService(ABC):
    @abstractmethod
    def apply_filters(
        self,
        query: SearchQuery,
        filters: Dict[str, Any],
    ) -> SearchQuery:
        pass
```

**Responsibilities:**
- Parse filter parameters
- Build filter queries
- Validate filter values
- Apply access control filters

**Filter Types:**
- Exact match filters
- Range filters (numeric, date)
- Boolean filters
- Multi-select filters (OR logic)
- Nested object filters
- Geo-spatial filters (future)

---

#### PaginationService
**Interface:**
```python
class PaginationService(ABC):
    @abstractmethod
    def paginate(
        self,
        query: SearchQuery,
        params: PaginationParams,
    ) -> PaginatedResult:
        pass
```

**Responsibilities:**
- Apply pagination (offset/limit or cursor-based)
- Return total count
- Return pagination metadata (next, previous, total pages)
- Validate pagination parameters

**Pagination Strategies:**
- `OffsetLimitPagination` - Traditional OFFSET/LIMIT
- `CursorPagination` - Cursor-based for deep pagination
- `SearchAfterPagination` - Elasticsearch search_after

---

#### FacetingService
**Interface:**
```python
class FacetingService(ABC):
    @abstractmethod
    def compute_facets(
        self,
        query: SearchQuery,
        facet_config: FacetConfig,
    ) -> FacetResult:
        pass
```

**Responsibilities:**
- Compute aggregations
- Return facet counts
- Handle nested aggregations
- Apply facet filters

**Facet Types:**
- Term facets (categorical)
- Range facets (numeric, date)
- Histogram facets (buckets)
- Stats facets (min, max, avg, sum)
- Nested facets (nested objects)

---

#### AutocompleteService
**Interface:**
```python
class AutocompleteService(ABC):
    @abstractmethod
    def suggest(
        self,
        field: str,
        prefix: str,
        context: AutocompleteContext,
    ) -> List[Suggestion]:
        pass
```

**Responsibilities:**
- Generate suggestions based on prefix
- Apply context-aware suggestions
- Rank suggestions by frequency/relevance
- Return suggestion metadata

**Autocomplete Strategies:**
- `PrefixCompletionStrategy` - Simple prefix matching
- `FuzzyCompletionStrategy` - Fuzzy matching with typos
- `ContextualCompletionStrategy` - Context-aware suggestions
- `LearningCompletionStrategy` - ML-based suggestions (future)

---

#### RecommendationService
**Interface:**
```python
class RecommendationService(ABC):
    @abstractmethod
    def recommend(
        self,
        entity_type: str,
        entity_id: str,
        context: RecommendationContext,
    ) -> List[Recommendation]:
        pass
```

**Responsibilities:**
- Generate recommendations
- Apply recommendation algorithms
- Filter recommendations (access control, status)
- Rank recommendations

**Recommendation Types:**
- `ContentBasedRecommendation` - Based on item similarity
- `CollaborativeFilteringRecommendation` - Based on user behavior (future)
- `HybridRecommendation` - Combine multiple approaches
- `VectorSimilarityRecommendation` - Based on vector embeddings

---

#### IndexingService
**Interface:**
```python
class IndexingService(ABC):
    @abstractmethod
    def index_document(
        self,
        entity_type: str,
        document: Dict[str, Any],
    ) -> IndexResult:
        pass

    @abstractmethod
    def bulk_index(
        self,
        entity_type: str,
        documents: List[Dict[str, Any]],
    ) -> BulkIndexResult:
        pass

    @abstractmethod
    def delete_document(
        self,
        entity_type: str,
        document_id: str,
    ) -> DeleteResult:
        pass
```

**Responsibilities:**
- Index single documents
- Bulk index documents
- Delete documents from index
- Handle index synchronization
- Retry failed indexing operations

**Indexing Strategies:**
- `RealtimeIndexing` - Index immediately on CRUD
- `BatchIndexing` - Index in batches via Celery
- `EventDrivenIndexing` - Index via event bus (future)

---

## Layer 3: Provider Layer

### Purpose
Abstract search engine implementations. Each provider implements the same interfaces but uses different underlying technologies.

### Base Provider Interface
```python
class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResult:
        pass

    @abstractmethod
    def index(self, document: IndexDocument) -> IndexResult:
        pass

    @abstractmethod
    def bulk_index(self, documents: List[IndexDocument]) -> BulkIndexResult:
        pass

    @abstractmethod
    def delete(self, document_id: str) -> DeleteResult:
        pass

    @abstractmethod
    def aggregate(self, query: AggregationQuery) -> AggregationResult:
        pass

    @abstractmethod
    def suggest(self, query: SuggestionQuery) -> SuggestionResult:
        pass
```

### Provider Implementations

#### ElasticsearchProvider
**Technology:** Elasticsearch 8.x
**Features:**
- Full-text search with BM25
- Complex aggregations
- Nested documents
- Geo-spatial search
- Vector search (dense_vector)
- Percolation (reverse search)
**Use Case:** Primary search engine for most use cases

#### OpenSearchProvider
**Technology:** OpenSearch 2.x
**Features:**
- Same as Elasticsearch (compatible API)
- Additional security features
- ML Commons for vector operations
**Use Case:** Alternative to Elasticsearch, especially for AWS deployments

#### PostgreSQLProvider
**Technology:** PostgreSQL 15+ with pg_trgm
**Features:**
- Full-text search (tsvector)
- Trigram matching (pg_trgm)
- GIN indexes
- Partial indexes
**Use Case:** Lightweight search, small datasets, reduced infrastructure

#### VectorSearchProvider
**Technology:** Pinecone, Weaviate, or pgvector
**Features:**
- Approximate nearest neighbor (ANN) search
- Vector embeddings
- Semantic similarity
**Use Case:** Semantic search, recommendations

#### HybridProvider
**Technology:** Combination of providers
**Features:**
- Hybrid search (keyword + vector)
- Reciprocal rank fusion (RRF)
- Score normalization
**Use Case:** Advanced relevance, semantic + keyword

---

## Layer 4: Storage Layer

### Purpose
Physical storage for search indexes and cached data.

### Components

#### Search Index Storage
- **Elasticsearch Cluster:** Primary search index storage
- **OpenSearch Cluster:** Alternative search index storage
- **PostgreSQL Database:** Full-text search indexes (GIN)

#### Vector Storage
- **Vector Database:** Pinecone, Weaviate, or pgvector
- **Embedding Storage:** Store pre-computed embeddings

#### Cache Storage
- **Redis:** Query result caching, autocomplete cache
- **Memcached:** Alternative cache backend

---

## Data Flow

### Search Request Flow
```
1. Client Request
   ↓
2. API Layer (View)
   - Validate request
   - Authenticate/Authorize
   - Parse query parameters
   ↓
3. Service Layer (SearchService)
   - Build search query
   - Apply filters (FilteringService)
   - Apply ranking (RankingService)
   - Apply pagination (PaginationService)
   ↓
4. Provider Layer (ElasticsearchProvider)
   - Execute search query
   - Return raw results
   ↓
5. Service Layer
   - Compute facets (FacetingService)
   - Apply final ranking
   - Format results
   ↓
6. API Layer
   - Serialize response
   - Return to client
```

### Indexing Flow
```
1. Data Change (CRUD)
   ↓
2. Django Signal
   ↓
3. Service Layer (IndexingService)
   - Transform data to search document
   - Add metadata (timestamps, etc.)
   ↓
4. Provider Layer (ElasticsearchProvider)
   - Index document
   - Handle errors/retries
   ↓
5. Cache Invalidation
   - Invalidate related cache entries
```

### Recommendation Flow
```
1. Client Request
   ↓
2. API Layer (RecommendationView)
   - Validate request
   - Authenticate/Authorize
   ↓
3. Service Layer (RecommendationService)
   - Select recommendation strategy
   - Get candidate entity
   - Generate recommendations
   ↓
4. Provider Layer (VectorSearchProvider or ElasticsearchProvider)
   - Execute similarity search
   - Return candidates
   ↓
5. Service Layer
   - Apply filters (access control, status)
   - Rank recommendations
   ↓
6. API Layer
   - Serialize response
   - Return to client
```

---

## Configuration

### Provider Selection
```python
# settings.py
SEARCH_PROVIDER = "elasticsearch"  # or "opensearch", "postgresql", "hybrid"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire",
        "timeout": 30,
    },
    "opensearch": {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire",
        "timeout": 30,
    },
    "postgresql": {
        "connection": "default",
    },
}
```

### Ranking Configuration
```python
RANKING_CONFIG = {
    "default_strategy": "bm25",
    "strategies": {
        "bm25": {
            "weights": {
                "text_relevance": 1.0,
                "recency": 0.3,
                "popularity": 0.2,
            }
        },
        "match_score": {
            "weights": {
                "match_score": 1.0,
                "recency": 0.2,
            }
        }
    }
}
```

### Cache Configuration
```python
SEARCH_CACHE_CONFIG = {
    "enabled": True,
    "backend": "redis",
    "ttl": {
        "search_results": 300,  # 5 minutes
        "autocomplete": 3600,  # 1 hour
        "facets": 600,  # 10 minutes
    }
}
```

---

## Error Handling

### Error Categories
1. **Validation Errors:** Invalid query parameters
2. **Provider Errors:** Search engine failures
3. **Indexing Errors:** Document indexing failures
4. **Timeout Errors:** Query timeouts
5. **Rate Limit Errors:** Too many requests

### Error Handling Strategy
- **Validation Errors:** Return 400 with error details
- **Provider Errors:** Log error, return 503, retry with backoff
- **Indexing Errors:** Log error, retry via Celery, alert on failure
- **Timeout Errors:** Return partial results or 504
- **Rate Limit Errors:** Return 429 with retry-after header

---

## Observability

### Metrics
- **Search Latency:** p50, p95, p99
- **Search Throughput:** Queries per second
- **Cache Hit Rate:** Cache hit/miss ratio
- **Indexing Latency:** Time to index documents
- **Indexing Errors:** Failed indexing operations
- **Zero-Result Rate:** Percentage of searches with no results
- **Click-Through Rate:** Percentage of searches with clicks

### Logging
- **Search Queries:** Log all search queries (anonymized)
- **Filter Usage:** Log which filters are used
- **Ranking Signals:** Log ranking scores for analysis
- **Provider Errors:** Log all provider errors
- **Indexing Events:** Log all indexing operations

### Tracing
- **Distributed Tracing:** Use OpenTelemetry for request tracing
- **Query Tracing:** Track query execution time per component
- **Provider Tracing:** Track provider call latency

---

## Security

### Access Control
- **Row-Level Security:** Filter results based on user permissions
- **Role-Based Access:** Different search capabilities per role
- **Data Masking:** Mask sensitive fields in search results

### Rate Limiting
- **Global Rate Limit:** Overall search QPS limit
- **Per-User Rate Limit:** Per-user QPS limit
- **Per-Endpoint Rate Limit:** Endpoint-specific limits

### Input Sanitization
- **Query Sanitization:** Remove dangerous characters
- **Filter Validation:** Validate all filter values
- **SQL Injection Prevention:** Use parameterized queries (PostgreSQL provider)

### Audit Logging
- **Search Audit:** Log who searched what
- **Result Access:** Log which results were accessed
- **Data Export:** Log data export operations

---

## Testing Strategy

### Unit Tests
- Test each service in isolation
- Mock provider responses
- Test edge cases and error conditions

### Integration Tests
- Test service-provider integration
- Test with real search engine (test cluster)
- Test indexing synchronization

### Performance Tests
- Load test search endpoints
- Measure latency under load
- Test with large datasets

### Contract Tests
- Test provider interface compliance
- Ensure all providers implement same interface
- Test serialization/deserialization

---

## Migration Path

### Phase 1: PostgreSQL Full-Text Search (Current)
- Use existing Django ORM
- Add GIN indexes for full-text search
- Implement basic faceting

### Phase 2: Elasticsearch/OpenSearch (Next)
- Deploy Elasticsearch cluster
- Implement ElasticsearchProvider
- Migrate indexes to Elasticsearch
- Update API to use SearchService
- Keep PostgreSQL as source of truth

### Phase 3: Vector Search (Future)
- Deploy vector database (Pinecone/pgvector)
- Generate embeddings for entities
- Implement VectorSearchProvider
- Add semantic search capabilities

### Phase 4: Hybrid Search (Future)
- Implement HybridProvider
- Combine keyword + vector search
- Implement reciprocal rank fusion
- Optimize ranking strategies

---

## Summary

The search architecture is designed with the following key characteristics:

1. **Modular:** Clear separation between API, Service, and Provider layers
2. **Extensible:** Easy to add new providers without changing business logic
3. **Provider-Agnostic:** Core logic independent of search engine
4. **Scalable:** Designed for horizontal scaling
5. **Observable:** Built-in metrics, logging, and tracing
6. **Secure:** Access control, rate limiting, audit logging
7. **Testable:** Each layer independently testable
8. **Future-Proof:** Ready for vector search, hybrid search, and ML ranking

The architecture supports multiple search providers (Elasticsearch, OpenSearch, PostgreSQL, Vector DBs) and provides a clear migration path from the current PostgreSQL-based search to a full-featured Elasticsearch deployment with future vector search capabilities.
