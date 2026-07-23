# Index Strategy
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines the index strategy for all searchable entities in the MatchHire platform. For each entity, we specify primary keys, indexed fields, composite indexes, full-text fields, keyword fields, nested fields, and future vector fields. The strategy is designed for Elasticsearch/OpenSearch but is applicable to other search engines.

---

## Index Naming Convention

### Pattern
`{entity_type}_{environment}_{version}`

### Examples
- `candidate_production_v1`
- `resume_production_v1`
- `job_production_v1`
- `candidate_staging_v1`
- `candidate_development_v1`

### Index Aliases
- `{entity_type}_read` - Points to current production index for read operations
- `{entity_type}_write` - Points to current production index for write operations
- `{entity_type}_latest` - Points to latest index (including staging)

---

## Entity: Candidate

### Index Name
`candidate_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "email": {
    "type": "keyword"
  },
  "full_name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      },
      "ngram": {
        "type": "text",
        "analyzer": "ngram_analyzer"
      }
    },
    "analyzer": "standard"
  }
}
```

#### Profile Fields
```json
{
  "headline": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "bio": {
    "type": "text",
    "analyzer": "standard"
  },
  "current_location": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "years_of_experience": {
    "type": "integer"
  },
  "skills_text": {
    "type": "text",
    "analyzer": "comma_analyzer"
  }
}
```

#### Link Fields
```json
{
  "linkedin_url": {
    "type": "keyword"
  },
  "github_url": {
    "type": "keyword"
  },
  "portfolio_url": {
    "type": "keyword"
  }
}
```

#### Metadata Fields
```json
{
  "resume_uploaded": {
    "type": "boolean"
  },
  "date_joined": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `email + updated_at` - For filtering by email and sorting by recency
- `resume_uploaded + years_of_experience` - For filtering by resume status and experience

### Full-Text Search Fields
- `full_name` - With ngram analyzer for partial matching
- `headline` - Standard analyzer
- `bio` - Standard analyzer
- `skills_text` - Comma-separated analyzer

### Keyword Fields (for Aggregations/Sorting)
- `full_name.keyword` - For sorting alphabetically
- `headline.keyword` - For sorting
- `current_location.keyword` - For faceting
- `email` - For exact matching

### Future Vector Fields
```json
{
  "skills_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "bio_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "headline_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Resume

### Index Name
`resume_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "candidate_id": {
    "type": "keyword"
  },
  "candidate_email": {
    "type": "keyword"
  }
}
```

#### Contact Fields
```json
{
  "full_name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "email": {
    "type": "keyword"
  },
  "phone": {
    "type": "keyword"
  },
  "location": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  }
}
```

#### Content Fields
```json
{
  "summary": {
    "type": "text",
    "analyzer": "standard"
  }
}
```

#### Nested: Skills
```json
{
  "skills": {
    "type": "nested",
    "properties": {
      "name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "experience_years": {
        "type": "integer"
      }
    }
  }
}
```

#### Nested: Experience
```json
{
  "experience": {
    "type": "nested",
    "properties": {
      "company": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "job_title": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "start_date": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "end_date": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "description": {
        "type": "text",
        "analyzer": "standard"
      },
      "location": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      }
    }
  }
}
```

#### Nested: Education
```json
{
  "education": {
    "type": "nested",
    "properties": {
      "institution": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "degree": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "field_of_study": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "start_year": {
        "type": "integer"
      },
      "end_year": {
        "type": "integer"
      },
      "description": {
        "type": "text",
        "analyzer": "standard"
      }
    }
  }
}
```

#### Nested: Projects
```json
{
  "projects": {
    "type": "nested",
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "description": {
        "type": "text",
        "analyzer": "standard"
      },
      "github_url": {
        "type": "keyword"
      },
      "project_url": {
        "type": "keyword"
      }
    }
  }
}
```

#### Nested: Certifications
```json
{
  "certifications": {
    "type": "nested",
    "properties": {
      "name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "issuer": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        },
        "analyzer": "standard"
      },
      "issue_date": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      }
    }
  }
}
```

#### Metadata Fields
```json
{
  "version_number": {
    "type": "integer"
  },
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `candidate_id + updated_at` - For filtering by candidate and sorting by recency
- `version_number + candidate_id` - For getting current version

### Full-Text Search Fields
- `full_name` - Standard analyzer
- `summary` - Standard analyzer
- `skills.name` - Nested, standard analyzer
- `experience.company` - Nested, standard analyzer
- `experience.job_title` - Nested, standard analyzer
- `experience.description` - Nested, standard analyzer
- `education.institution` - Nested, standard analyzer
- `education.degree` - Nested, standard analyzer
- `projects.title` - Nested, standard analyzer
- `projects.description` - Nested, standard analyzer
- `certifications.name` - Nested, standard analyzer

### Keyword Fields (for Aggregations/Sorting)
- `full_name.keyword` - For sorting
- `location.keyword` - For faceting
- `skills.name.keyword` - For nested aggregations
- `experience.company.keyword` - For nested aggregations
- `experience.job_title.keyword` - For nested aggregations
- `education.degree.keyword` - For nested aggregations
- `education.institution.keyword` - For nested aggregations

### Future Vector Fields
```json
{
  "summary_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "skills_embeddings": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "experience_embeddings": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Job

### Index Name
`job_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "recruiter_id": {
    "type": "keyword"
  },
  "recruiter_email": {
    "type": "keyword"
  }
}
```

#### Basic Fields
```json
{
  "title": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      },
      "ngram": {
        "type": "text",
        "analyzer": "ngram_analyzer"
      }
    },
    "analyzer": "standard"
  },
  "company_name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "location": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  }
}
```

#### Details Fields
```json
{
  "description": {
    "type": "text",
    "analyzer": "standard"
  },
  "requirements": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "responsibilities": {
    "type": "text",
    "analyzer": "standard"
  }
}
```

#### Attributes Fields
```json
{
  "employment_type": {
    "type": "keyword"
  },
  "experience_level": {
    "type": "keyword"
  },
  "is_remote": {
    "type": "boolean"
  }
}
```

#### Compensation Fields
```json
{
  "salary_min": {
    "type": "double"
  },
  "salary_max": {
    "type": "double"
  },
  "currency": {
    "type": "keyword"
  }
}
```

#### Status Fields
```json
{
  "status": {
    "type": "keyword"
  },
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "closed_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `status + created_at` - For filtering active jobs and sorting by recency
- `recruiter_id + status` - For filtering recruiter's active jobs
- `employment_type + experience_level` - For faceted navigation
- `salary_min + salary_max` - For salary range queries

### Full-Text Search Fields
- `title` - With ngram analyzer for autocomplete
- `company_name` - Standard analyzer
- `description` - Standard analyzer
- `requirements` - Standard analyzer with keyword subfield
- `responsibilities` - Standard analyzer
- `location` - Standard analyzer

### Keyword Fields (for Aggregations/Sorting)
- `title.keyword` - For sorting
- `company_name.keyword` - For faceting
- `location.keyword` - For faceting
- `employment_type` - For filtering and faceting
- `experience_level` - For filtering and faceting
- `status` - For filtering
- `currency` - For filtering

### Future Vector Fields
```json
{
  "title_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "description_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "requirements_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Company

### Index Name
`company_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  }
}
```

#### Details Fields
```json
{
  "website": {
    "type": "keyword"
  },
  "description": {
    "type": "text",
    "analyzer": "standard"
  },
  "industry": {
    "type": "keyword"
  },
  "company_size": {
    "type": "keyword"
  }
}
```

#### Location Fields
```json
{
  "headquarters": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "locations": {
    "type": "keyword"
  }
}
```

#### Metrics Fields
```json
{
  "active_jobs_count": {
    "type": "integer"
  },
  "total_jobs_count": {
    "type": "integer"
  },
  "verified": {
    "type": "boolean"
  }
}
```

#### Metadata Fields
```json
{
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `verified + active_jobs_count` - For filtering verified companies with jobs
- `industry + company_size` - For faceted navigation

### Full-Text Search Fields
- `name` - Standard analyzer
- `description` - Standard analyzer
- `headquarters` - Standard analyzer

### Keyword Fields (for Aggregations/Sorting)
- `name.keyword` - For sorting
- `industry` - For faceting
- `company_size` - For faceting
- `verified` - For filtering

### Future Vector Fields
```json
{
  "description_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "industry_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Recruiter

### Index Name
`recruiter_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "email": {
    "type": "keyword"
  },
  "full_name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  }
}
```

#### Profile Fields
```json
{
  "company_name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "company_website": {
    "type": "keyword"
  },
  "job_title": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "verified_company": {
    "type": "boolean"
  }
}
```

#### Metadata Fields
```json
{
  "date_joined": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `verified_company + updated_at` - For filtering verified recruiters

### Full-Text Search Fields
- `full_name` - Standard analyzer
- `company_name` - Standard analyzer
- `job_title` - Standard analyzer

### Keyword Fields (for Aggregations/Sorting)
- `full_name.keyword` - For sorting
- `company_name.keyword` - For faceting
- `job_title.keyword` - For faceting
- `verified_company` - For filtering

### Future Vector Fields
```json
{
  "profile_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Skill

### Index Name
`skill_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "name": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      },
      "ngram": {
        "type": "text",
        "analyzer": "ngram_analyzer"
      }
    },
    "analyzer": "standard"
  },
  "aliases": {
    "type": "keyword"
  }
}
```

#### Category Fields
```json
{
  "category": {
    "type": "keyword"
  },
  "type": {
    "type": "keyword"
  }
}
```

#### Metrics Fields
```json
{
  "resume_count": {
    "type": "integer"
  },
  "job_count": {
    "type": "integer"
  },
  "popularity_score": {
    "type": "double"
  }
}
```

#### Relationship Fields
```json
{
  "related_skills": {
    "type": "keyword"
  },
  "parent_skill": {
    "type": "keyword"
  }
}
```

#### Metadata Fields
```json
{
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `category + popularity_score` - For faceted navigation with sorting
- `resume_count + job_count` - For popularity-based sorting

### Full-Text Search Fields
- `name` - With ngram analyzer for autocomplete
- `aliases` - Keyword for exact matching

### Keyword Fields (for Aggregations/Sorting)
- `name.keyword` - For sorting
- `category` - For faceting
- `type` - For faceting

### Future Vector Fields
```json
{
  "name_embedding": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  },
  "related_skills_embeddings": {
    "type": "dense_vector",
    "dims": 384,
    "index": true,
    "similarity": "cosine"
  }
}
```

---

## Entity: Application

### Index Name
`application_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "candidate_id": {
    "type": "keyword"
  },
  "job_id": {
    "type": "keyword"
  },
  "recruiter_id": {
    "type": "keyword"
  }
}
```

#### Details Fields
```json
{
  "status": {
    "type": "keyword"
  },
  "resume_version_id": {
    "type": "keyword"
  }
}
```

#### Metadata Fields
```json
{
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `candidate_id + status + created_at` - For filtering candidate applications by status
- `job_id + status + created_at` - For filtering job applications by status
- `recruiter_id + status + created_at` - For filtering recruiter applications by status

### Full-Text Search Fields
- None (applications are transactional, not content-rich)

### Keyword Fields (for Aggregations/Sorting)
- `status` - For filtering and faceting
- `candidate_id` - For filtering
- `job_id` - For filtering

### Future Vector Fields
- None planned

---

## Entity: Interview

### Index Name
`interview_production_v1`

### Primary Key
- `id` (UUID) - Document ID

### Field Mappings

#### Identity Fields
```json
{
  "id": {
    "type": "keyword"
  },
  "application_id": {
    "type": "keyword"
  },
  "candidate_id": {
    "type": "keyword"
  },
  "job_id": {
    "type": "keyword"
  },
  "recruiter_id": {
    "type": "keyword"
  }
}
```

#### Details Fields
```json
{
  "status": {
    "type": "keyword"
  },
  "interview_type": {
    "type": "keyword"
  },
  "location": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    },
    "analyzer": "standard"
  },
  "scheduled_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

#### Metadata Fields
```json
{
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  },
  "updated_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

### Composite Indexes
- `candidate_id + scheduled_at` - For filtering candidate interviews by date
- `job_id + status + scheduled_at` - For filtering job interviews by status and date
- `recruiter_id + scheduled_at` - For filtering recruiter interviews by date

### Full-Text Search Fields
- `location` - Standard analyzer

### Keyword Fields (for Aggregations/Sorting)
- `status` - For filtering and faceting
- `interview_type` - For filtering and faceting
- `location.keyword` - For faceting

### Future Vector Fields
- None planned

---

## Custom Analyzers

### Standard Analyzer
```json
{
  "standard": {
    "type": "standard",
    "stopwords": "_english_"
  }
}
```

### Ngram Analyzer (for Autocomplete)
```json
{
  "ngram_analyzer": {
    "type": "custom",
    "tokenizer": "ngram_tokenizer",
    "filter": [
      "lowercase",
      "asciifolding"
    ]
  },
  "ngram_tokenizer": {
    "type": "edge_ngram",
    "min_gram": 2,
    "max_gram": 20,
    "token_chars": [
      "letter",
      "digit"
    ]
  }
}
```

### Comma Analyzer (for Skills)
```json
{
  "comma_analyzer": {
    "type": "custom",
    "tokenizer": "comma_tokenizer",
    "filter": [
      "lowercase",
      "asciifolding"
    ]
  },
  "comma_tokenizer": {
    "type": "pattern",
    "pattern": ",\\s*"
  }
}
```

---

## Index Settings

### Number of Shards
- **Small datasets (< 100K docs):** 1 shard
- **Medium datasets (100K - 1M docs):** 3-5 shards
- **Large datasets (1M - 10M docs):** 5-10 shards
- **Very large datasets (> 10M docs):** 10-20 shards

### Number of Replicas
- **Development:** 0 replicas
- **Staging:** 1 replica
- **Production:** 2 replicas

### Refresh Interval
- **Development:** 1s (immediate)
- **Staging:** 5s
- **Production:** 30s (for better indexing throughput)

### Indexing Buffer Size
- **Default:** 10% of JVM heap
- **High Throughput:** 20% of JVM heap

---

## Index Lifecycle Management

### Hot Phase (0-7 days)
- **Purpose:** Active indexing and searching
- **Settings:** High refresh interval, more replicas
- **Actions:** Real-time indexing, active search

### Warm Phase (7-30 days)
- **Purpose:** Less frequent updates, still searchable
- **Settings:** Lower refresh interval, fewer replicas
- **Actions:** Reduced indexing, still searchable

### Cold Phase (30-90 days)
- **Purpose:** Archive, rarely searched
- **Settings:** Minimal replicas, compressed
- **Actions:** Read-only, compressed storage

### Delete Phase (> 90 days)
- **Purpose:** Cleanup
- **Settings:** N/A
- **Actions:** Delete index

---

## Reindexing Strategy

### Full Reindex
- **Trigger:** Major schema changes, data migration
- **Strategy:** Create new index, reindex data, switch alias
- **Downtime:** Zero (using index aliases)

### Incremental Reindex
- **Trigger:** Field mapping changes
- **Strategy:** Update by query, reindex affected documents
- **Downtime:** Zero

### Rolling Reindex
- **Trigger:** Large dataset updates
- **Strategy:** Reindex in batches, maintain old index until complete
- **Downtime:** Zero

---

## Summary

This index strategy defines comprehensive mappings for 8 core entities:

1. **Candidate:** 15 fields, 3 composite indexes, 3 vector fields
2. **Resume:** 20+ fields (including nested), 2 composite indexes, 3 vector fields
3. **Job:** 15 fields, 4 composite indexes, 3 vector fields
4. **Company:** 10 fields, 2 composite indexes, 2 vector fields
5. **Recruiter:** 8 fields, 1 composite index, 1 vector field
6. **Skill:** 10 fields, 2 composite indexes, 2 vector fields
7. **Application:** 7 fields, 3 composite indexes, 0 vector fields
8. **Interview:** 9 fields, 3 composite indexes, 0 vector fields

The strategy includes:
- Custom analyzers for different use cases (standard, ngram, comma)
- Proper field types (text, keyword, nested, dense_vector)
- Composite indexes for common query patterns
- Future vector fields for semantic search
- Index lifecycle management
- Reindexing strategies for zero-downtime updates

This index strategy is designed for Elasticsearch/OpenSearch but is applicable to other search engines with minor adjustments.
