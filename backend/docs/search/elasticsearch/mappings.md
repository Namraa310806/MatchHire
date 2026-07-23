# Elasticsearch Mappings

## Overview

Elasticsearch mappings define the structure and data types of documents in each index. The MatchHire Elasticsearch provider includes production-ready mappings for all entity types.

## Mapping Design Principles

1. **Keyword Fields**: For exact matching, aggregations, and sorting
2. **Text Fields**: For full-text search with analyzers
3. **Multi-Fields**: For different analysis needs on the same field
4. **Nested Objects**: For complex data structures
5. **Placeholders**: For future features (geo, vector search)

## Entity Mappings

### Job Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "job_id": {"type": "keyword"},
        "recruiter_id": {"type": "keyword"},
        "title": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "company_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "location": {"type": "keyword"},
        "employment_type": {"type": "keyword"},
        "experience_level": {"type": "keyword"},
        "description": {"type": "text", "analyzer": "standard"},
        "requirements": {"type": "text", "analyzer": "standard"},
        "responsibilities": {"type": "text", "analyzer": "standard"},
        "salary_min": {"type": "float"},
        "salary_max": {"type": "float"},
        "currency": {"type": "keyword"},
        "is_remote": {"type": "boolean"},
        "status": {"type": "keyword"},
        "closed_at": {"type": "date"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "location_geo": {"type": "geo_point"},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

**Key Features:**
- Multi-field title for autocomplete and exact matching
- Salary range with float type for filtering
- Boolean for remote work filtering
- Date fields for temporal filtering
- Geo point placeholder for location-based search
- Dense vector placeholder for semantic search

### Candidate Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "email": {"type": "keyword"},
        "full_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "headline": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"}
            }
        },
        "bio": {"type": "text", "analyzer": "standard"},
        "current_location": {"type": "keyword"},
        "years_of_experience": {"type": "integer"},
        "skills_text": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"}
            }
        },
        "linkedin_url": {"type": "keyword"},
        "github_url": {"type": "keyword"},
        "portfolio_url": {"type": "keyword"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "is_active": {"type": "boolean"},
        "is_verified": {"type": "boolean"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "location_geo": {"type": "geo_point"},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

**Key Features:**
- Multi-field name for autocomplete
- Integer for experience filtering
- Boolean for status filtering
- Skills text for keyword matching

### Resume Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "resume_id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "version_number": {"type": "integer"},
        "is_current": {"type": "boolean"},
        "raw_text": {"type": "text", "analyzer": "standard"},
        "summary": {"type": "text", "analyzer": "standard"},
        "full_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "email": {"type": "keyword"},
        "phone": {"type": "keyword"},
        "location": {"type": "keyword"},
        "skills": {"type": "keyword"},
        "education": {
            "type": "nested",
            "properties": {
                "institution": {"type": "text"},
                "degree": {"type": "text"},
                "field": {"type": "text"},
                "start_date": {"type": "date"},
                "end_date": {"type": "date"}
            }
        },
        "experience": {
            "type": "nested",
            "properties": {
                "company": {"type": "text"},
                "job_title": {"type": "text"},
                "start_date": {"type": "date"},
                "end_date": {"type": "date"},
                "description": {"type": "text"}
            }
        },
        "projects": {
            "type": "nested",
            "properties": {
                "title": {"type": "text"},
                "description": {"type": "text"},
                "technologies": {"type": "keyword"}
            }
        },
        "certifications": {
            "type": "nested",
            "properties": {
                "name": {"type": "text"},
                "issuer": {"type": "text"},
                "date": {"type": "date"}
            }
        },
        "linkedin_url": {"type": "keyword"},
        "github_url": {"type": "keyword"},
        "portfolio_url": {"type": "keyword"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "location_geo": {"type": "geo_point"},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

**Key Features:**
- Nested objects for education, experience, projects, certifications
- Allows querying nested fields independently
- Supports complex resume structure
- Multi-field name for autocomplete

### Company Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "company_id": {"type": "keyword"},
        "name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "website": {"type": "keyword"},
        "industry": {"type": "keyword"},
        "size": {"type": "keyword"},
        "description": {"type": "text", "analyzer": "standard"},
        "headquarters": {"type": "keyword"},
        "locations": {"type": "keyword"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "is_verified": {"type": "boolean"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "headquarters_geo": {"type": "geo_point"},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

### Recruiter Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "user_id": {"type": "keyword"},
        "email": {"type": "keyword"},
        "full_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "company_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"}
            }
        },
        "company_website": {"type": "keyword"},
        "job_title": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"}
            }
        },
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "is_verified": {"type": "boolean"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

### Skill Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "skill_id": {"type": "keyword"},
        "name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "edge_ngram": {
                    "type": "text",
                    "analyzer": "edge_ngram_analyzer",
                    "search_analyzer": "standard"
                }
            }
        },
        "category": {"type": "keyword"},
        "synonyms": {"type": "keyword"},
        "usage_count": {"type": "integer"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True},
        "vector_embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine"
        }
    }
}
```

### Application Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "application_id": {"type": "keyword"},
        "job_id": {"type": "keyword"},
        "candidate_id": {"type": "keyword"},
        "resume_version_id": {"type": "keyword"},
        "status": {"type": "keyword"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True}
    }
}
```

### Interview Mapping

```python
{
    "properties": {
        "id": {"type": "keyword"},
        "interview_id": {"type": "keyword"},
        "application_id": {"type": "keyword"},
        "job_id": {"type": "keyword"},
        "candidate_id": {"type": "keyword"},
        "scheduled_at": {"type": "date"},
        "interview_type": {"type": "keyword"},
        "status": {"type": "keyword"},
        "searchable_text": {"type": "text", "analyzer": "standard"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "metadata": {"type": "object", "dynamic": True}
    }
}
```

## Field Types

### Keyword Fields
Used for:
- Exact matching
- Aggregations
- Sorting
- Filtering
- IDs and references

### Text Fields
Used for:
- Full-text search
- Fuzzy matching
- Phrase matching
- Highlighting

### Date Fields
Used for:
- Temporal filtering
- Range queries
- Date histograms
- Sorting by time

### Numeric Fields
Used for:
- Range queries
- Mathematical aggregations
- Sorting

### Boolean Fields
Used for:
- Binary filtering
- Status flags
- Feature toggles

### Nested Objects
Used for:
- Complex data structures
- Independent querying of nested fields
- Array of objects

### Geo Point Fields (Placeholder)
Used for:
- Location-based search
- Distance calculations
- Geo aggregations

### Dense Vector Fields (Placeholder)
Used for:
- Semantic search
- Vector similarity
- KNN search

## Multi-Fields

Multi-fields allow different analysis on the same field:

### Example: Title Field
```python
"title": {
    "type": "text",                    # Full-text search
    "fields": {
        "keyword": {"type": "keyword"}, # Exact matching, sorting
        "edge_ngram": {                 # Autocomplete
            "type": "text",
            "analyzer": "edge_ngram_analyzer",
            "search_analyzer": "standard"
        }
    }
}
```

## Dynamic Templates

The `metadata` field is configured as dynamic to allow flexible additional data:

```python
"metadata": {
    "type": "object",
    "dynamic": True
}
```

## Index Settings

Base settings applied to all indices:

```python
{
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "1s",
    "index.max_result_window": 10000
}
```

## Mapping Updates

### Versioned Indices
When updating mappings, create a new versioned index:

```python
provider.create_versioned_index(entity_type="job", switch_alias=True)
```

### Zero-Downtime Switching
Use aliases to switch between index versions:

```python
provider.index_lifecycle.switch_alias(
    entity_type="job",
    old_index="matchhire_job_v1",
    new_index="matchhire_job_v2"
)
```

### Cleanup Old Versions
Remove old index versions after verification:

```python
provider.cleanup_old_indices(entity_type="job", keep_versions=2)
```

## Best Practices

1. **Use keyword fields** for exact matching and aggregations
2. **Use text fields** for full-text search
3. **Use multi-fields** for different analysis needs
4. **Use nested objects** for complex arrays
5. **Version indices** for mapping changes
6. **Use aliases** for zero-downtime deployments
7. **Configure appropriate shard counts** based on data volume
8. **Set appropriate replica counts** for high availability
