# Search API Design
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines the standard search API endpoints for the MatchHire platform. The API design follows RESTful principles with consistent query formats, filtering, sorting, pagination, aggregations, faceting, and response structures across all entity types.

---

## API Design Principles

1. **RESTful:** Follow REST conventions for resource-based URLs
2. **Consistent:** Uniform query parameter naming across endpoints
3. **Composable:** Support complex queries with composable filters
4. **Efficient:** Support field selection, pagination, and aggregations
5. **Extensible:** Easy to add new filters, sorts, and aggregations
6. **Versioned:** API versioning for backward compatibility
7. **Documented:** OpenAPI/Swagger documentation for all endpoints

---

## Base URL Structure

```
/api/v1/search/{entity_type}
```

### Entity Types
- `candidates` - Search candidates
- `resumes` - Search resumes
- `jobs` - Search jobs
- `companies` - Search companies
- `recruiters` - Search recruiters
- `skills` - Search skills
- `applications` - Search applications
- `interviews` - Search interviews
- `unified` - Cross-entity search

---

## Standard Query Parameters

### Search Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Full-text search query | `q=Python developer` |
| `fields` | string | Fields to search (comma-separated) | `fields=title,description` |
| `operator` | string | Boolean operator (AND/OR) | `operator=AND` |

### Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `filter[{field}]` | string | Filter by field value | `filter[status]=active` |
| `filter[{field}][op]` | string | Filter with operator | `filter[salary_min][gte]=50000` |
| `filter[{field}][in]` | string | Filter with multiple values | `filter[employment_type][in]=full_time,contract` |

### Operators
- `eq` - Equal (default)
- `ne` - Not equal
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `in` - In list
- `nin` - Not in list
- `contains` - Contains substring
- `icontains` - Contains substring (case-insensitive)
- `exists` - Field exists
- `nexists` - Field does not exist

### Sort Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `sort` | string | Sort field (prefix with - for desc) | `sort=-created_at` |
| `sort` | string | Multiple sort fields (comma-separated) | `sort=-match_score,created_at` |

### Pagination Parameters

| Parameter | Type | Description | Default | Max |
|-----------|------|-------------|---------|-----|
| `page` | integer | Page number (1-based) | 1 | - |
| `page_size` | integer | Results per page | 20 | 100 |
| `cursor` | string | Cursor for cursor-based pagination | - | - |

### Aggregation Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `aggregate` | string | Fields to aggregate | `aggregate=employment_type,experience_level` |
| `aggregate[{field}][type]` | string | Aggregation type | `aggregate[salary_range][type]=range` |

### Facet Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facet` | string | Fields to facet | `facet=location,skills` |
| `facet[{field}][size]` | integer | Number of facet values | `facet[skills][size]=50` |

### Field Selection Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `fields` | string | Fields to return (comma-separated) | `fields=id,title,company_name` |
| `exclude_fields` | string | Fields to exclude | `exclude_fields=description,requirements` |

### Ranking Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking_strategy` | string | Ranking strategy | `ranking_strategy=hybrid` |
| `explain` | boolean | Return ranking explanation | `explain=true` |

---

## Endpoint Specifications

### 1. Candidate Search

**Endpoint:** `GET /api/v1/search/candidates`

**Authentication:** Required (Recruiter only)

**Query Parameters:**
- `q` - Full-text search across name, headline, bio, skills, location
- `filter[years_of_experience][gte]` - Minimum years of experience
- `filter[years_of_experience][lte]` - Maximum years of experience
- `filter[resume_uploaded]` - Has uploaded resume (true/false)
- `filter[current_location]` - Current location
- `sort` - Sort by created_at, updated_at, years_of_experience, full_name, relevance
- `facet` - Facet by years_of_experience, resume_uploaded, current_location, skills

**Example Request:**
```
GET /api/v1/search/candidates?q=Python developer&filter[years_of_experience][gte]=3&sort=-match_score&page=1&page_size=20
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "headline": "Senior Python Developer",
      "bio": "Experienced developer...",
      "current_location": "San Francisco, CA",
      "years_of_experience": 5,
      "skills_text": "Python, Django, PostgreSQL",
      "resume_uploaded": true,
      "match_score": 85.5,
      "_ranking": {
        "final_score": 85.5,
        "signal_scores": {
          "bm25": 60.0,
          "match_score": 80.0,
          "recency": 70.0
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "abc123",
    "previous_cursor": null
  },
  "facets": {
    "years_of_experience": {
      "0-1": 10,
      "1-3": 30,
      "3-5": 50,
      "5-10": 40,
      "10+": 20
    },
    "resume_uploaded": {
      "true": 130,
      "false": 20
    },
    "current_location": {
      "San Francisco, CA": 40,
      "New York, NY": 35,
      "Austin, TX": 25
    }
  },
  "aggregations": {
    "avg_years_of_experience": 4.5,
    "total_with_resume": 130
  }
}
```

---

### 2. Resume Search

**Endpoint:** `GET /api/v1/search/resumes`

**Authentication:** Required (Recruiter only)

**Query Parameters:**
- `q` - Full-text search across all resume fields
- `filter[skills][in]` - Skills (comma-separated, OR logic)
- `filter[location]` - Location
- `filter[experience.company]` - Company name
- `filter[experience.job_title]` - Job title
- `filter[education.degree]` - Degree
- `filter[education.institution]` - Institution
- `filter[certifications.name]` - Certification name
- `sort` - Sort by created_at, updated_at, full_name, experience_years, relevance
- `facet` - Facet by location, skills, experience.company, education.degree

**Example Request:**
```
GET /api/v1/search/resumes?q=Python&filter[skills][in]=Python,Django&filter[location]=San Francisco&sort=-experience_years
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "candidate_id": "uuid",
      "candidate_email": "john@example.com",
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "location": "San Francisco, CA",
      "summary": "Senior Python developer with 5 years experience...",
      "skills": [
        {
          "name": "Python",
          "experience_years": 5
        },
        {
          "name": "Django",
          "experience_years": 3
        }
      ],
      "experience": [
        {
          "company": "Tech Corp",
          "job_title": "Senior Developer",
          "start_date": "2020-01-01",
          "end_date": "2023-12-31",
          "description": "Led backend development..."
        }
      ],
      "education": [
        {
          "institution": "MIT",
          "degree": "Bachelor of Science",
          "field_of_study": "Computer Science",
          "start_year": 2016,
          "end_year": 2020
        }
      ],
      "match_score": 85.5
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 200,
    "total_pages": 10
  },
  "facets": {
    "location": {
      "San Francisco, CA": 50,
      "New York, NY": 40
    },
    "skills": {
      "Python": 150,
      "Django": 100,
      "PostgreSQL": 80
    }
  }
}
```

---

### 3. Job Search

**Endpoint:** `GET /api/v1/search/jobs`

**Authentication:** Required (all roles)

**Query Parameters:**
- `q` - Full-text search across title, company_name, description, requirements, location
- `filter[employment_type]` - Employment type (full_time, part_time, contract, internship)
- `filter[experience_level]` - Experience level (entry, junior, mid, senior, lead)
- `filter[is_remote]` - Remote work (true/false)
- `filter[salary_min][gte]` - Minimum salary
- `filter[salary_max][lte]` - Maximum salary
- `filter[currency]` - Currency (USD, EUR, etc.)
- `filter[location]` - Location
- `filter[status]` - Status (active, draft, closed)
- `sort` - Sort by created_at, updated_at, salary_min, salary_max, title, relevance
- `facet` - Facet by employment_type, experience_level, is_remote, location, salary_range, company_name

**Example Request:**
```
GET /api/v1/search/jobs?q=Python developer&filter[employment_type]=full_time&filter[is_remote]=true&sort=-created_at
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "recruiter_id": "uuid",
      "recruiter_email": "recruiter@example.com",
      "title": "Senior Python Developer",
      "company_name": "Tech Corp",
      "location": "San Francisco, CA",
      "description": "We are looking for a senior Python developer...",
      "requirements": "Python, Django, PostgreSQL, 5+ years experience",
      "responsibilities": "Design and implement backend systems...",
      "employment_type": "full_time",
      "experience_level": "senior",
      "is_remote": true,
      "salary_min": 120000,
      "salary_max": 180000,
      "currency": "USD",
      "status": "active",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "match_score": 85.5
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 75,
    "total_pages": 4
  },
  "facets": {
    "employment_type": {
      "full_time": 50,
      "part_time": 15,
      "contract": 8,
      "internship": 2
    },
    "experience_level": {
      "entry": 10,
      "junior": 20,
      "mid": 25,
      "senior": 15,
      "lead": 5
    },
    "is_remote": {
      "true": 40,
      "false": 35
    },
    "salary_range": {
      "0-50k": 5,
      "50k-100k": 20,
      "100k-150k": 30,
      "150k+": 20
    }
  }
}
```

---

### 4. Company Search

**Endpoint:** `GET /api/v1/search/companies`

**Authentication:** Required (all roles)

**Query Parameters:**
- `q` - Full-text search across name, description, industry
- `filter[industry]` - Industry sector
- `filter[company_size]` - Company size (startup, small, medium, large, enterprise)
- `filter[verified]` - Verification status (true/false)
- `filter[headquarters]` - Headquarters location
- `sort` - Sort by name, created_at, updated_at, active_jobs_count, total_jobs_count
- `facet` - Facet by industry, company_size, verified, headquarters

**Example Request:**
```
GET /api/v1/search/companies?q=Tech&filter[industry]=Technology&filter[verified]=true
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Tech Corp",
      "website": "https://techcorp.com",
      "description": "Leading technology company...",
      "industry": "Technology",
      "company_size": "large",
      "headquarters": "San Francisco, CA",
      "locations": ["San Francisco, CA", "New York, NY", "London, UK"],
      "verified": true,
      "active_jobs_count": 25,
      "total_jobs_count": 100,
      "created_at": "2020-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  },
  "facets": {
    "industry": {
      "Technology": 30,
      "Finance": 10,
      "Healthcare": 8
    },
    "company_size": {
      "startup": 15,
      "small": 10,
      "medium": 15,
      "large": 8,
      "enterprise": 2
    }
  }
}
```

---

### 5. Recruiter Search

**Endpoint:** `GET /api/v1/search/recruiters`

**Authentication:** Required (Candidate only)

**Query Parameters:**
- `q` - Full-text search across name, company_name, job_title
- `filter[company_name]` - Company name
- `filter[verified_company]` - Verification status (true/false)
- `filter[job_title]` - Job title
- `sort` - Sort by full_name, company_name, date_joined, updated_at, active_jobs_count
- `facet` - Facet by company_name, verified_company, job_title

**Example Request:**
```
GET /api/v1/search/recruiters?q=John&filter[verified_company]=true
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "email": "recruiter@example.com",
      "full_name": "John Smith",
      "company_name": "Tech Corp",
      "company_website": "https://techcorp.com",
      "job_title": "Senior Technical Recruiter",
      "verified_company": true,
      "active_jobs_count": 15,
      "date_joined": "2021-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 30,
    "total_pages": 2
  },
  "facets": {
    "company_name": {
      "Tech Corp": 10,
      "Startup Inc": 8,
      "Enterprise LLC": 12
    },
    "verified_company": {
      "true": 25,
      "false": 5
    }
  }
}
```

---

### 6. Skill Search

**Endpoint:** `GET /api/v1/search/skills`

**Authentication:** Required (all roles)

**Query Parameters:**
- `q` - Full-text search across name, aliases
- `filter[category]` - Skill category (frontend, backend, devops, etc.)
- `filter[type]` - Skill type (hard, soft, tool, language)
- `filter[resume_count][gte]` - Minimum resume count
- `filter[job_count][gte]` - Minimum job count
- `sort` - Sort by name, resume_count, job_count, popularity_score
- `facet` - Facet by category, type, popularity_score

**Example Request:**
```
GET /api/v1/search/skills?q=Python&filter[category]=backend&sort=-popularity_score
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Python",
      "aliases": ["py", "python3"],
      "category": "backend",
      "type": "language",
      "resume_count": 5000,
      "job_count": 1000,
      "popularity_score": 95.5,
      "related_skills": ["Django", "Flask", "FastAPI"],
      "parent_skill": null,
      "created_at": "2020-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  },
  "facets": {
    "category": {
      "backend": 40,
      "frontend": 30,
      "devops": 20,
      "data": 10
    },
    "type": {
      "language": 50,
      "framework": 30,
      "tool": 15,
      "soft": 5
    }
  }
}
```

---

### 7. Application Search

**Endpoint:** `GET /api/v1/search/applications`

**Authentication:** Required (role-based access)

**Query Parameters:**
- `q` - Full-text search across candidate name, job title, company name
- `filter[status]` - Application status (submitted, under_review, shortlisted, rejected, hired)
- `filter[candidate_id]` - Candidate ID
- `filter[job_id]` - Job ID
- `filter[recruiter_id]` - Recruiter ID
- `filter[created_at][gte]` - Minimum creation date
- `filter[created_at][lte]` - Maximum creation date
- `sort` - Sort by created_at, updated_at, status, match_score
- `facet` - Facet by status, job.title, company_name

**Example Request:**
```
GET /api/v1/search/applications?filter[status]=shortlisted&filter[recruiter_id]=uuid&sort=-match_score
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "candidate_id": "uuid",
      "job_id": "uuid",
      "recruiter_id": "uuid",
      "candidate_full_name": "John Doe",
      "job_title": "Senior Python Developer",
      "company_name": "Tech Corp",
      "status": "shortlisted",
      "resume_version_id": "uuid",
      "match_score": 85.5,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-16T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  },
  "facets": {
    "status": {
      "submitted": 20,
      "under_review": 15,
      "shortlisted": 10,
      "rejected": 5
    },
    "job_title": {
      "Senior Python Developer": 15,
      "Junior Developer": 10,
      "Tech Lead": 5
    }
  }
}
```

---

### 8. Interview Search

**Endpoint:** `GET /api/v1/search/interviews`

**Authentication:** Required (role-based access)

**Query Parameters:**
- `q` - Full-text search across candidate name, job title, location
- `filter[status]` - Interview status (scheduled, completed, cancelled, no_show)
- `filter[interview_type]` - Interview type (video, phone, in_person)
- `filter[candidate_id]` - Candidate ID
- `filter[job_id]` - Job ID
- `filter[recruiter_id]` - Recruiter ID
- `filter[scheduled_at][gte]` - Minimum scheduled date
- `filter[scheduled_at][lte]` - Maximum scheduled date
- `sort` - Sort by scheduled_at, created_at, status
- `facet` - Facet by status, interview_type, scheduled_at (date histogram)

**Example Request:**
```
GET /api/v1/search/interviews?filter[status]=scheduled&filter[recruiter_id]=uuid&sort=scheduled_at
```

**Response Structure:**
```json
{
  "results": [
    {
      "id": "uuid",
      "application_id": "uuid",
      "candidate_id": "uuid",
      "job_id": "uuid",
      "recruiter_id": "uuid",
      "candidate_full_name": "John Doe",
      "job_title": "Senior Python Developer",
      "status": "scheduled",
      "interview_type": "video",
      "location": "Zoom",
      "scheduled_at": "2024-01-20T14:00:00Z",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 25,
    "total_pages": 2
  },
  "facets": {
    "status": {
      "scheduled": 15,
      "completed": 8,
      "cancelled": 2
    },
    "interview_type": {
      "video": 15,
      "phone": 5,
      "in_person": 5
    },
    "scheduled_at": {
      "2024-01-20": 5,
      "2024-01-21": 3,
      "2024-01-22": 7
    }
  }
}
```

---

### 9. Unified Search

**Endpoint:** `GET /api/v1/search/unified`

**Authentication:** Required (all roles)

**Query Parameters:**
- `q` - Full-text search across all entity types
- `entity_type` - Entity types to search (comma-separated, default: all)
- `per_entity_limit` - Results per entity type (default: 10, max: 50)
- `sort` - Sort by relevance (default)
- `facet` - Facet by entity_type

**Example Request:**
```
GET /api/v1/search/unified?q=Python developer&entity_type=candidate,job&per_entity_limit=10
```

**Response Structure:**
```json
{
  "results": {
    "candidates": {
      "total": 150,
      "results": [
        {
          "id": "uuid",
          "entity_type": "candidate",
          "full_name": "John Doe",
          "headline": "Senior Python Developer",
          "match_score": 85.5
        }
      ]
    },
    "jobs": {
      "total": 75,
      "results": [
        {
          "id": "uuid",
          "entity_type": "job",
          "title": "Senior Python Developer",
          "company_name": "Tech Corp",
          "match_score": 85.5
        }
      ]
    },
    "resumes": {
      "total": 200,
      "results": [...]
    }
  },
  "pagination": {
    "per_entity_limit": 10,
    "total": 425
  },
  "facets": {
    "entity_type": {
      "candidates": 150,
      "jobs": 75,
      "resumes": 200
    }
  }
}
```

---

## Autocomplete Endpoints

### Candidate Autocomplete

**Endpoint:** `GET /api/v1/autocomplete/candidates`

**Query Parameters:**
- `q` - Prefix to complete
- `field` - Field to complete (full_name, headline, current_location)
- `size` - Number of suggestions (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/autocomplete/candidates?q=Joh&field=full_name&size=10
```

**Response Structure:**
```json
{
  "suggestions": [
    {
      "value": "John Doe",
      "field": "full_name",
      "score": 95.5,
      "metadata": {
        "id": "uuid",
        "headline": "Senior Python Developer"
      }
    },
    {
      "value": "John Smith",
      "field": "full_name",
      "score": 90.0,
      "metadata": {
        "id": "uuid",
        "headline": "Junior Developer"
      }
    }
  ]
}
```

### Job Autocomplete

**Endpoint:** `GET /api/v1/autocomplete/jobs`

**Query Parameters:**
- `q` - Prefix to complete
- `field` - Field to complete (title, company_name, location)
- `size` - Number of suggestions (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/autocomplete/jobs?q=Pyt&field=title&size=10
```

### Skill Autocomplete

**Endpoint:** `GET /api/v1/autocomplete/skills`

**Query Parameters:**
- `q` - Prefix to complete
- `size` - Number of suggestions (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/autocomplete/skills?q=Pyt&size=10
```

### Location Autocomplete

**Endpoint:** `GET /api/v1/autocomplete/locations`

**Query Parameters:**
- `q` - Prefix to complete
- `size` - Number of suggestions (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/autocomplete/locations?q=San&size=10
```

---

## Error Responses

### Validation Error (400)
```json
{
  "error": "validation_error",
  "message": "Invalid query parameters",
  "details": {
    "filter[salary_min]": "Must be a number",
    "page_size": "Must be between 1 and 100"
  }
}
```

### Not Found (404)
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### Unauthorized (401)
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### Forbidden (403)
```json
{
  "error": "forbidden",
  "message": "You do not have permission to access this resource"
}
```

### Rate Limit Exceeded (429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded",
  "retry_after": 60
}
```

### Internal Server Error (500)
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred"
}
```

---

## Response Headers

### Standard Headers
- `Content-Type: application/json`
- `X-Request-ID: uuid` - Request identifier for tracing
- `X-Response-Time: ms` - Response time in milliseconds
- `X-Rate-Limit-Remaining: 100` - Remaining rate limit
- `X-Rate-Limit-Reset: 1234567890` - Rate limit reset timestamp

### Pagination Headers
- `X-Total-Count: 150` - Total number of results
- `X-Total-Pages: 8` - Total number of pages
- `X-Page: 1` - Current page number
- `X-Page-Size: 20` - Page size

---

## API Versioning

### Version Strategy
- URL-based versioning: `/api/v1/search/...`
- Backward compatibility maintained within major versions
- Breaking changes require new major version

### Version Lifecycle
- **v1:** Current version (stable)
- **v2:** Next version (in development)
- **v0:** Deprecated (scheduled for removal)

---

## Rate Limiting

### Rate Limits
- **Authenticated Users:** 100 requests/minute
- **Unauthenticated Users:** 10 requests/minute (if public endpoints exist)
- **Autocomplete:** 50 requests/minute
- **Unified Search:** 50 requests/minute

### Rate Limit Headers
- `X-Rate-Limit-Limit: 100` - Rate limit
- `X-Rate-Limit-Remaining: 95` - Remaining requests
- `X-Rate-Limit-Reset: 1234567890` - Reset timestamp

---

## Summary

The Search API Design defines:

1. **9 Search Endpoints:**
   - Candidates, Resumes, Jobs, Companies, Recruiters, Skills, Applications, Interviews, Unified

2. **4 Autocomplete Endpoints:**
   - Candidates, Jobs, Skills, Locations

3. **Standard Query Parameters:**
   - Search, Filter, Sort, Pagination, Aggregation, Facet, Field Selection, Ranking

4. **Consistent Response Structure:**
   - Results array
   - Pagination metadata
   - Facets/aggregations
   - Ranking explanation (optional)

5. **Error Handling:**
   - Standard error responses
   - Validation errors
   - Rate limiting

6. **Additional Features:**
   - API versioning
   - Rate limiting
   - Response headers
   - Request tracing

The API design is RESTful, consistent, and extensible, with clear documentation for all endpoints and parameters.
