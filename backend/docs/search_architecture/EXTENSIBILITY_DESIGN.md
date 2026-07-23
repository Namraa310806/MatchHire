# Extensibility Design
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document ensures the search architecture is extensible to support multiple search providers (Elasticsearch, OpenSearch, PostgreSQL Full-Text Search, Vector Search, Hybrid Search, LLM-based Ranking, and Embeddings) without changing business logic. The design uses interface-based abstractions to decouple business logic from provider implementations.

---

## Extensibility Principles

1. **Interface-Based Design:** Define interfaces, not implementations
2. **Provider Agnostic:** Business logic independent of search engine
3. **Plug-and-Play:** Easy to add new providers
4. **Configuration-Driven:** Provider selection via configuration
5. **Backward Compatible:** New providers don't break existing code
6. **Testable:** Each provider independently testable
7. **Observable:** Consistent metrics across providers

---

## Provider Interface Design

### Base Search Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class SearchProvider(ABC):
    """
    Abstract base class for all search providers.
    All providers must implement this interface.
    """
    
    @abstractmethod
    def search(
        self,
        index: str,
        query: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        sorting: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        Execute a search query.
        
        Args:
            index: Index name to search
            query: Search query DSL
            filters: Filter criteria
            sorting: Sort criteria
            pagination: Pagination parameters
            
        Returns:
            SearchResult with hits, total, aggregations
        """
        pass
    
    @abstractmethod
    def index_document(
        self,
        index: str,
        document_id: str,
        document: Dict[str, Any],
    ) -> IndexResult:
        """
        Index a single document.
        
        Args:
            index: Index name
            document_id: Document ID
            document: Document data
            
        Returns:
            IndexResult with success status
        """
        pass
    
    @abstractmethod
    def bulk_index(
        self,
        index: str,
        documents: List[Dict[str, Any]],
    ) -> BulkIndexResult:
        """
        Bulk index documents.
        
        Args:
            index: Index name
            documents: List of documents with _id field
            
        Returns:
            BulkIndexResult with success/error counts
        """
        pass
    
    @abstractmethod
    def delete_document(
        self,
        index: str,
        document_id: str,
    ) -> DeleteResult:
        """
        Delete a document.
        
        Args:
            index: Index name
            document_id: Document ID
            
        Returns:
            DeleteResult with success status
        """
        pass
    
    @abstractmethod
    def aggregate(
        self,
        index: str,
        aggregations: Dict[str, Any],
        query: Optional[Dict[str, Any]] = None,
    ) -> AggregationResult:
        """
        Execute aggregations.
        
        Args:
            index: Index name
            aggregations: Aggregation DSL
            query: Optional query to filter aggregation scope
            
        Returns:
            AggregationResult with aggregation buckets
        """
        pass
    
    @abstractmethod
    def suggest(
        self,
        index: str,
        field: str,
        prefix: str,
        size: int = 10,
    ) -> SuggestionResult:
        """
        Generate autocomplete suggestions.
        
        Args:
            index: Index name
            field: Field to suggest from
            prefix: Prefix to complete
            size: Number of suggestions
            
        Returns:
            SuggestionResult with suggestions
        """
        pass
    
    @abstractmethod
    def create_index(
        self,
        index: str,
        mappings: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
    ) -> CreateIndexResult:
        """
        Create an index with mappings and settings.
        
        Args:
            index: Index name
            mappings: Field mappings
            settings: Index settings
            
        Returns:
            CreateIndexResult with success status
        """
        pass
    
    @abstractmethod
    def delete_index(
        self,
        index: str,
    ) -> DeleteIndexResult:
        """
        Delete an index.
        
        Args:
            index: Index name
            
        Returns:
            DeleteIndexResult with success status
        """
        pass
    
    @abstractmethod
    def health(self) -> HealthStatus:
        """
        Check provider health.
        
        Returns:
            HealthStatus with cluster/node health information
        """
        pass
```

---

## Provider Implementations

### Elasticsearch Provider

```python
from elasticsearch import Elasticsearch

class ElasticsearchProvider(SearchProvider):
    """
    Elasticsearch implementation of SearchProvider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.client = Elasticsearch(
            hosts=config.get('hosts', ['http://localhost:9200']),
            timeout=config.get('timeout', 30),
        )
    
    def search(self, index: str, query: Dict[str, Any], 
               filters: Optional[Dict[str, Any]] = None,
               sorting: Optional[List[Dict[str, Any]]] = None,
               pagination: Optional[Dict[str, Any]] = None) -> SearchResult:
        # Build Elasticsearch query DSL
        es_query = self._build_query(query, filters, sorting, pagination)
        
        # Execute search
        response = self.client.search(index=index, body=es_query)
        
        # Parse response
        return self._parse_search_response(response)
    
    def _build_query(self, query: Dict[str, Any], filters: Optional[Dict[str, Any]],
                   sorting: Optional[List[Dict[str, Any]]],
                   pagination: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        # Build Elasticsearch-specific query DSL
        es_query = {
            "query": query,
        }
        
        if filters:
            es_query["query"] = {
                "bool": {
                    "must": [query],
                    "filter": self._build_filters(filters)
                }
            }
        
        if sorting:
            es_query["sort"] = sorting
        
        if pagination:
            es_query["from"] = pagination.get("from", 0)
            es_query["size"] = pagination.get("size", 20)
        
        return es_query
    
    # ... implement other methods
```

---

### OpenSearch Provider

```python
from opensearchpy import OpenSearch

class OpenSearchProvider(SearchProvider):
    """
    OpenSearch implementation of SearchProvider.
    Compatible with Elasticsearch API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.client = OpenSearch(
            hosts=config.get('hosts', ['http://localhost:9200']),
            timeout=config.get('timeout', 30),
        )
    
    # OpenSearch API is compatible with Elasticsearch
    # Can reuse most Elasticsearch implementation
    def search(self, index: str, query: Dict[str, Any], 
               filters: Optional[Dict[str, Any]] = None,
               sorting: Optional[List[Dict[str, Any]]] = None,
               pagination: Optional[Dict[str, Any]] = None) -> SearchResult:
        # Same implementation as Elasticsearch
        # OpenSearch is API-compatible
        pass
    
    # ... implement other methods
```

---

### PostgreSQL Full-Text Search Provider

```python
from django.db import connection

class PostgreSQLProvider(SearchProvider):
    """
    PostgreSQL Full-Text Search implementation of SearchProvider.
    Uses GIN indexes and tsvector for full-text search.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.connection_name = config.get('connection', 'default')
    
    def search(self, index: str, query: Dict[str, Any], 
               filters: Optional[Dict[str, Any]] = None,
               sorting: Optional[List[Dict[str, Any]]] = None,
               pagination: Optional[List[Dict[str, Any]] = None) -> SearchResult:
        # Build PostgreSQL full-text search query
        sql, params = self._build_query(index, query, filters, sorting, pagination)
        
        # Execute query
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        
        # Parse response
        return self._parse_search_response(rows)
    
    def _build_query(self, index: str, query: Dict[str, Any], 
                    filters: Optional[Dict[str, Any]],
                    sorting: Optional[List[Dict[str, Any]]],
                    pagination: Optional[Dict[str, Any]]) -> tuple:
        # Build PostgreSQL-specific SQL with tsvector
        # Use to_tsquery for full-text search
        # Use GIN indexes for performance
        pass
    
    # ... implement other methods
```

---

### Vector Search Provider

```python
import pinecone  # or weaviate, pgvector

class VectorSearchProvider(SearchProvider):
    """
    Vector Search implementation of SearchProvider.
    Uses vector embeddings for semantic similarity search.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.client = pinecone.init(
            api_key=config.get('api_key'),
            environment=config.get('environment')
        )
        self.index_name = config.get('index_name')
    
    def search(self, index: str, query: Dict[str, Any], 
               filters: Optional[Dict[str, Any]] = None,
               sorting: Optional[List[Dict[str, Any]]] = None,
               pagination: Optional[List[Dict[str, Any]] = None) -> SearchResult:
        # Vector search uses embedding query
        query_vector = query.get('vector')
        
        # Execute vector similarity search
        response = self.client.query(
            index_name=self.index_name,
            vector=query_vector,
            top_k=pagination.get('size', 20) if pagination else 20,
            filter=filters if filters else None,
        )
        
        # Parse response
        return self._parse_search_response(response)
    
    def index_document(self, index: str, document_id: str, 
                     document: Dict[str, Any]) -> IndexResult:
        # Index document with vector embedding
        vector = document.get('vector')
        
        self.client.upsert(
            index_name=self.index_name,
            vectors=[{
                'id': document_id,
                'values': vector,
                'metadata': {k: v for k, v in document.items() if k != 'vector'}
            }]
        )
        
        return IndexResult(success=True)
    
    # ... implement other methods
```

---

### Hybrid Search Provider

```python
class HybridSearchProvider(SearchProvider):
    """
    Hybrid Search implementation combining keyword and vector search.
    Uses Reciprocal Rank Fusion (RRF) to combine results.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.keyword_provider = self._create_provider(config['keyword_provider'])
        self.vector_provider = self._create_provider(config['vector_provider'])
        self.rrf_k = config.get('rrf_k', 60)
    
    def search(self, index: str, query: Dict[str, Any], 
               filters: Optional[Dict[str, Any]] = None,
               sorting: Optional[List[Dict[str, Any]]] = None,
               pagination: Optional[List[Dict[str, Any]] = None) -> SearchResult:
        # Execute keyword search
        keyword_results = self.keyword_provider.search(
            index, query, filters, sorting, pagination
        )
        
        # Execute vector search
        vector_results = self.vector_provider.search(
            index, query, filters, sorting, pagination
        )
        
        # Combine results using RRF
        combined_results = self._reciprocal_rank_fusion(
            keyword_results, vector_results, self.rrf_k
        )
        
        return combined_results
    
    def _reciprocal_rank_fusion(
        self, 
        keyword_results: SearchResult, 
        vector_results: SearchResult,
        k: int = 60
    ) -> SearchResult:
        """
        Combine results using Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank) for each ranking source)
        """
        # Build score map
        score_map = {}
        
        # Add keyword search scores
        for rank, hit in enumerate(keyword_results.hits):
            doc_id = hit['id']
            score_map[doc_id] = score_map.get(doc_id, 0) + 1 / (k + rank + 1)
        
        # Add vector search scores
        for rank, hit in enumerate(vector_results.hits):
            doc_id = hit['id']
            score_map[doc_id] = score_map.get(doc_id, 0) + 1 / (k + rank + 1)
        
        # Sort by combined score
        sorted_results = sorted(
            score_map.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Return combined results
        return SearchResult(
            hits=[hit for hit, score in sorted_results],
            total=len(sorted_results)
        )
    
    # ... implement other methods
```

---

## Provider Factory

```python
class ProviderFactory:
    """
    Factory for creating search provider instances.
    """
    
    _providers = {
        'elasticsearch': ElasticsearchProvider,
        'opensearch': OpenSearchProvider,
        'postgresql': PostgreSQLProvider,
        'vector': VectorSearchProvider,
        'hybrid': HybridSearchProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> SearchProvider:
        """
        Create a search provider instance.
        
        Args:
            provider_type: Type of provider (elasticsearch, opensearch, etc.)
            config: Provider configuration
            
        Returns:
            SearchProvider instance
        """
        provider_class = cls._providers.get(provider_type)
        
        if provider_class is None:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return provider_class(config)
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type):
        """
        Register a custom provider.
        
        Args:
            provider_type: Provider type name
            provider_class: Provider class implementing SearchProvider
        """
        cls._providers[provider_type] = provider_class
```

---

## Configuration-Based Provider Selection

```python
# settings.py

SEARCH_CONFIG = {
    'default_provider': 'elasticsearch',
    'providers': {
        'elasticsearch': {
            'hosts': ['http://localhost:9200'],
            'timeout': 30,
            'index_prefix': 'matchhire',
        },
        'opensearch': {
            'hosts': ['http://localhost:9200'],
            'timeout': 30,
            'index_prefix': 'matchhire',
        },
        'postgresql': {
            'connection': 'default',
        },
        'vector': {
            'api_key': 'your-api-key',
            'environment': 'us-west1-gcp',
            'index_name': 'matchhire-vectors',
        },
        'hybrid': {
            'keyword_provider': 'elasticsearch',
            'vector_provider': 'vector',
            'rrf_k': 60,
        }
    },
    'entity_providers': {
        'candidate': 'elasticsearch',
        'resume': 'elasticsearch',
        'job': 'elasticsearch',
        'company': 'elasticsearch',
        'recruiter': 'elasticsearch',
        'skill': 'elasticsearch',
        'application': 'postgresql',
        'interview': 'postgresql',
    }
}

# Get provider instance
def get_provider(entity_type: str = None) -> SearchProvider:
    """
    Get configured search provider.
    
    Args:
        entity_type: Optional entity type for entity-specific provider
        
    Returns:
        SearchProvider instance
    """
    if entity_type:
        provider_type = SEARCH_CONFIG['entity_providers'].get(entity_type)
    else:
        provider_type = SEARCH_CONFIG['default_provider']
    
    config = SEARCH_CONFIG['providers'][provider_type]
    return ProviderFactory.create_provider(provider_type, config)
```

---

## LLM-Based Ranking Extensibility

### Ranking Provider Interface

```python
class RankingProvider(ABC):
    """
    Abstract base class for ranking providers.
    """
    
    @abstractmethod
    def rank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank search results.
        
        Args:
            results: Search results to rank
            query: Original search query
            context: Additional context (user preferences, etc.)
            
        Returns:
            Ranked results with scores
        """
        pass
```

### LLM Ranking Provider

```python
class LLMRankingProvider(RankingProvider):
    """
    LLM-based ranking provider.
    Uses language models to rerank search results.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.model_name = config.get('model_name', 'gpt-4')
        self.api_key = config.get('api_key')
    
    def rank(self, results: List[Dict[str, Any]], query: str,
             context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Prepare ranking prompt
        prompt = self._build_ranking_prompt(results, query, context)
        
        # Call LLM API
        scores = self._call_llm(prompt)
        
        # Add scores to results
        for result, score in zip(results, scores):
            result['_llm_score'] = score
        
        # Sort by LLM score
        ranked_results = sorted(results, key=lambda x: x['_llm_score'], reverse=True)
        
        return ranked_results
    
    def _build_ranking_prompt(self, results: List[Dict[str, Any]], 
                            query: str, context: Optional[Dict[str, Any]]) -> str:
        # Build prompt for LLM to rank results
        prompt = f"Rank the following search results for query: '{query}'\n\n"
        
        for i, result in enumerate(results):
            prompt += f"{i+1}. {result.get('title', result.get('name', ''))}\n"
            prompt += f"   {result.get('description', '')}\n\n"
        
        prompt += "Return rankings as a comma-separated list of result numbers."
        
        return prompt
    
    def _call_llm(self, prompt: str) -> List[float]:
        # Call OpenAI API or other LLM provider
        # Parse response to extract rankings
        # Convert rankings to scores
        pass
```

---

## Embedding Extensibility

### Embedding Provider Interface

```python
class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    """
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding
        """
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: Texts to embed
            
        Returns:
            List of vector embeddings
        """
        pass
```

### OpenAI Embedding Provider

```python
import openai

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.model = config.get('model', 'text-embedding-ada-002')
        self.api_key = config.get('api_key')
        openai.api_key = self.api_key
    
    def generate_embedding(self, text: str) -> List[float]:
        response = openai.Embedding.create(
            input=text,
            model=self.model
        )
        return response['data'][0]['embedding']
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        response = openai.Embedding.create(
            input=texts,
            model=self.model
        )
        return [item['embedding'] for item in response['data']]
```

### Sentence-BERT Embedding Provider

```python
from sentence_transformers import SentenceTransformer

class SentenceBertEmbeddingProvider(EmbeddingProvider):
    """
    Sentence-BERT embedding provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.model_name = config.get('model_name', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(self.model_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]
```

---

## Embedding Configuration

```python
# settings.py

EMBEDDING_CONFIG = {
    'default_provider': 'sentence_bert',
    'providers': {
        'openai': {
            'model': 'text-embedding-ada-002',
            'api_key': 'your-api-key',
        },
        'sentence_bert': {
            'model_name': 'all-MiniLM-L6-v2',
        },
        'cohere': {
            'model': 'embed-english-v3.0',
            'api_key': 'your-api-key',
        }
    },
    'entity_embeddings': {
        'candidate': {
            'fields': ['headline', 'bio', 'skills_text'],
            'provider': 'sentence_bert',
        },
        'resume': {
            'fields': ['summary'],
            'provider': 'sentence_bert',
        },
        'job': {
            'fields': ['title', 'description', 'requirements'],
            'provider': 'sentence_bert',
        },
    }
}

def get_embedding_provider(entity_type: str = None) -> EmbeddingProvider:
    """
    Get configured embedding provider.
    """
    if entity_type:
        provider_type = EMBEDDING_CONFIG['entity_embeddings'][entity_type]['provider']
    else:
        provider_type = EMBEDDING_CONFIG['default_provider']
    
    config = EMBEDDING_CONFIG['providers'][provider_type]
    return EmbeddingProviderFactory.create_provider(provider_type, config)
```

---

## Migration Path Between Providers

### Phase 1: PostgreSQL Only (Current)
- Provider: PostgreSQLProvider
- Features: Basic full-text search with icontains
- Limitations: No faceting, no autocomplete, poor performance

### Phase 2: Elasticsearch (Next)
- Provider: ElasticsearchProvider
- Features: Full-text search, aggregations, autocomplete
- Migration: 
  1. Deploy Elasticsearch cluster
  2. Implement ElasticsearchProvider
  3. Create indexes with mappings
  4. Reindex data from PostgreSQL
  5. Update configuration to use ElasticsearchProvider
  6. Keep PostgreSQL as source of truth

### Phase 3: Add Vector Search (Future)
- Provider: HybridProvider (Elasticsearch + Vector)
- Features: Semantic search, hybrid ranking
- Migration:
  1. Deploy vector database (Pinecone/pgvector)
  2. Implement VectorSearchProvider
  3. Generate embeddings for entities
  4. Implement HybridProvider
  5. Update configuration to use HybridProvider
  6. A/B test hybrid vs keyword-only

### Phase 4: Add LLM Ranking (Future)
- Provider: ElasticsearchProvider + LLMRankingProvider
- Features: ML-based reranking
- Migration:
  1. Implement LLMRankingProvider
  2. Integrate with ranking service
  3. A/B test LLM ranking vs baseline
  4. Gradually roll out to production

---

## Testing Strategy

### Provider Testing

#### Unit Tests
```python
def test_elasticsearch_provider():
    """Test Elasticsearch provider implementation."""
    provider = ElasticsearchProvider({'hosts': ['http://localhost:9200']})
    
    # Test search
    result = provider.search('test_index', {'match_all': {}})
    assert result.total >= 0
    
    # Test index
    provider.index_document('test_index', 'doc1', {'title': 'Test'})
    
    # Test delete
    provider.delete_document('test_index', 'doc1')
```

#### Integration Tests
```python
def test_provider_switching():
    """Test switching between providers."""
    # Test with Elasticsearch
    es_provider = ProviderFactory.create_provider('elasticsearch', es_config)
    es_result = es_provider.search('test_index', query)
    
    # Test with PostgreSQL
    pg_provider = ProviderFactory.create_provider('postgresql', pg_config)
    pg_result = pg_provider.search('test_index', query)
    
    # Results should be similar (not identical)
    assert len(es_result.hits) == len(pg_result.hits)
```

#### Contract Tests
```python
def test_provider_contract():
    """Test that all providers implement the interface correctly."""
    providers = [
        ElasticsearchProvider(es_config),
        OpenSearchProvider(os_config),
        PostgreSQLProvider(pg_config),
    ]
    
    for provider in providers:
        # All providers must implement search
        result = provider.search('test_index', {'match_all': {}})
        assert hasattr(result, 'hits')
        assert hasattr(result, 'total')
        
        # All providers must implement index_document
        provider.index_document('test_index', 'doc1', {'title': 'Test'})
        
        # All providers must implement delete_document
        provider.delete_document('test_index', 'doc1')
```

---

## Summary

The extensibility design ensures:

1. **Interface-Based Design:**
   - SearchProvider interface for all search providers
   - RankingProvider interface for ranking providers
   - EmbeddingProvider interface for embedding providers

2. **Multiple Provider Implementations:**
   - ElasticsearchProvider (full-featured search)
   - OpenSearchProvider (Elasticsearch-compatible)
   - PostgreSQLProvider (lightweight search)
   - VectorSearchProvider (semantic search)
   - HybridProvider (keyword + vector)

3. **Provider Factory:**
   - Factory pattern for provider creation
   - Configuration-based provider selection
   - Entity-specific provider configuration

4. **LLM-Based Ranking:**
   - RankingProvider interface
   - LLMRankingProvider implementation
   - Integration with ranking service

5. **Embedding Support:**
   - EmbeddingProvider interface
   - OpenAI, Sentence-BERT, Cohere implementations
   - Configuration-based provider selection

6. **Migration Path:**
   - Clear phases from PostgreSQL → Elasticsearch → Hybrid → LLM
   - Zero-downtime migration using index aliases
   - A/B testing for validation

7. **Testing Strategy:**
   - Unit tests for each provider
   - Integration tests for provider switching
   - Contract tests for interface compliance

The extensibility design ensures that the search architecture can support multiple search providers, ranking strategies, and embedding models without changing business logic, providing a clear path for future enhancements.
