# Search Architecture Audit
## Phase 5.0 - Current State Analysis

**Date:** 2026-07-23
**Phase:** Search Architecture & Domain Design
**Status:** Complete

---

## Executive Summary

The MatchHire platform currently implements basic search functionality using Django ORM queries. The system supports job search, resume search, and matching-based recommendations. However, the current implementation lacks full-text search capabilities, advanced filtering, faceted search, autocomplete, and semantic search features. This audit documents the current state to inform the design of a scalable, future-proof search architecture.

---

## Current Search Endpoints

### 1. Job Search
**Endpoint:** `GET /api/jobs/`
**View:** `PublicJobListView`
**Authentication:** Required (all roles)

#### Search Capabilities
- **Full-text search:** Across `title`, `company_name`, `description` using `icontains`
- **Filters:**
  - `location` (case-insensitive partial match)
  - `employment_type` (exact match: full_time, part_time, contract, internship)
  - `experience_level` (exact match: entry, junior, mid, senior, lead)
  - `is_remote` (boolean)
  - `salary_min` (jobs where `salary_max >= requested_salary_min`)
  - `salary_max` (jobs where `salary_min <= requested_salary_max`)
- **Sorting:** `created_at`, `-created_at`, `salary_min`, `-salary_min`, `salary_max`, `-salary_max`
- **Pagination:** `JobSearchPagination` (default: 20, max: 100)
- **Scope:** Only ACTIVE jobs (no draft or closed jobs)

#### Database Query Pattern
```python
queryset = Job.objects.filter(status=Job.JobStatus.ACTIVE)
queryset = queryset.filter(
    Q(title__icontains=q) | Q(company_name__icontains=q) | Q(description__icontains=q)
)
queryset = queryset.select_related("recruiter")
queryset = queryset.order_by(ordering)
```

#### Current Indexes
- `status` (B-tree)
- `recruiter` (B-tree)
- `created_at` (B-tree)

---

### 2. Resume Search
**Endpoint:** `GET /api/resumes/search/`
**View:** `ResumeSearchView`
**Authentication:** Required (Recruiter only)

#### Search Capabilities
- **Filters:**
  - `skill` (multiple, case-insensitive partial match, OR logic)
  - `location` (case-insensitive partial match)
  - `company` (case-insensitive partial match on experience.company)
  - `education` (case-insensitive partial match on degree OR institution)
  - `certification` (case-insensitive partial match on name OR issuer)
- **Sorting:** `name`, `-name`, `created_at`, `-created_at`
- **Pagination:** `ResumeSearchPagination` (default: 20, max: 100)
- **Scope:** Only current resume versions (`is_current=True`)

#### Database Query Pattern
```python
queryset = StructuredResume.objects.filter(resume_version__is_current=True)
queryset = queryset.filter(
    Q(skills__name__icontains=skill) | ...
)
queryset = queryset.select_related("resume_version", "resume_version__resume")
queryset = queryset.prefetch_related("skills", "education", "experience", "projects", "certifications")
queryset = queryset.distinct()
```

#### Current Indexes
- No dedicated indexes on resume search fields
- Relies on foreign key indexes from relationships

---

### 3. Job Recommendations
**Endpoint:** `GET /api/jobs/recommendations/`
**View:** `JobRecommendationsView`
**Authentication:** Required (Candidate only)

#### Search Capabilities
- **Ranking:** Pre-calculated `match_score` from JobMatch table
- **Scope:** Top 20 ACTIVE jobs
- **Caching:** Redis cache with TTL (via CacheService)
- **Ordering:** `-match_score`, `-calculated_at`

#### Database Query Pattern
```python
recommendations = JobMatch.objects.filter(
    candidate=request.user,
    job__status=Job.JobStatus.ACTIVE
).select_related("job", "job__recruiter").order_by("-match_score", "-calculated_at")[:20]
```

#### Current Indexes
- `candidate` (B-tree)
- `job` (B-tree)
- `match_score` (B-tree)

---

### 4. Matching Candidates
**Endpoint:** `GET /api/recruiter/candidates/?job_id=<uuid>`
**View:** `RecruiterCandidatesView`
**Authentication:** Required (Recruiter only)

#### Search Capabilities
- **Ranking:** Pre-calculated `match_score` from JobMatch table
- **Scope:** All candidates for specified job
- **Ordering:** `-match_score`, `-calculated_at`

#### Database Query Pattern
```python
candidate_matches = JobMatch.objects.filter(job=job).select_related("candidate").order_by("-match_score", "-calculated_at")
```

#### Current Indexes
- Same as JobMatch table

---

### 5. Application Filtering
**Endpoint:** `GET /api/jobs/<job_id>/applications/`
**View:** `JobApplicationsListView`
**Authentication:** Required (Recruiter owner only)

#### Search Capabilities
- **Filter:** `status` (exact match)
- **Scope:** All applications for specified job
- **Ordering:** `-created_at`

#### Database Query Pattern
```python
applications = Application.objects.filter(job=job)
if status_filter:
    applications = applications.filter(status=status_filter)
applications = applications.select_related("job", "candidate", "resume_version").order_by("-created_at")
```

#### Current Indexes
- `status` (B-tree)
- `job` (B-tree)
- `candidate` (B-tree)
- `created_at` (B-tree)

---

## Current ORM Usage

### Query Optimization Techniques Used
1. **select_related:** For ForeignKey relationships (1-to-1, many-to-1)
   - Reduces queries from N+1 to 1 for foreign keys
   - Used in: Job, Application, JobMatch, Resume queries

2. **prefetch_related:** For ManyToMany and reverse ForeignKey relationships
   - Loads related objects in 2 queries instead of N+1
   - Used in: Resume search (skills, education, experience, projects, certifications)

3. **Prefetch with custom querysets:** For optimized related data loading
   - Used in: ResumeListView for current versions

4. **distinct():** To avoid duplicates from joins
   - Used in: Resume search (multiple joins can create duplicates)

5. **iterator():** For memory-efficient large result sets
   - Used in: MatchingService for batch operations

### Query Patterns
- **Q objects:** For complex OR/AND logic
- **icontains:** For case-insensitive partial matching
- **exact:** For exact field matching
- **gte/lte:** For range queries (salary)

---

## Current Indexes

### Job Model
```python
indexes = [
    models.Index(fields=["status"]),
    models.Index(fields=["recruiter"]),
    models.Index(fields=["created_at"]),
]
```

### Application Model
```python
indexes = [
    models.Index(fields=["status"]),
    models.Index(fields=["job"]),
    models.Index(fields=["candidate"]),
    models.Index(fields=["created_at"]),
]
```

### JobMatch Model
```python
indexes = [
    models.Index(fields=["candidate"]),
    models.Index(fields=["job"]),
    models.Index(fields=["match_score"]),
]
```

### Resume Models
- **Resume:** No explicit indexes (relies on unique constraint on user)
- **ResumeVersion:** No explicit indexes
- **StructuredResume:** No explicit indexes
- **ResumeSkill:** No explicit indexes
- **ResumeEducation:** No explicit indexes
- **ResumeExperience:** No explicit indexes

### Missing Critical Indexes
1. **Composite indexes** for common query patterns (e.g., status + created_at)
2. **Full-text search indexes** (PostgreSQL GIN indexes)
3. **Trigram indexes** for fuzzy matching
4. **Covering indexes** to include frequently accessed columns
5. **Partial indexes** for frequently filtered subsets (e.g., is_current=True)

---

## Current Bottlenecks

### 1. No Full-Text Search
- **Issue:** `icontains` queries cannot use standard B-tree indexes efficiently
- **Impact:** Linear scan of table for text searches
- **Severity:** High (degrades with data volume)

### 2. No Faceted Search
- **Issue:** Cannot compute aggregations (count by category, ranges)
- **Impact:** No filter navigation UI, poor UX
- **Severity:** Medium (UX limitation)

### 3. No Autocomplete
- **Issue:** No prefix search or suggestion capabilities
- **Impact:** Poor search experience, higher query latency
- **Severity:** Medium (UX limitation)

### 4. No Semantic Search
- **Issue:** Cannot search by meaning, only by keywords
- **Impact:** Missed relevant results, poor matching
- **Severity:** High (relevance limitation)

### 5. No Fuzzy Matching
- **Issue:** Exact/partial matching only, no typo tolerance
- **Impact:** Zero results for minor spelling errors
- **Severity:** Medium (UX limitation)

### 6. Skill Extraction from Free Text
- **Issue:** Job skills parsed from comma-separated text
- **Impact:** Fragile, cannot handle natural language requirements
- **Severity:** High (data quality issue)

### 7. No Cross-Entity Search
- **Issue:** Cannot search across jobs, resumes, companies simultaneously
- **Impact:** Limited discovery capabilities
- **Severity:** Medium (feature limitation)

### 8. No Search Analytics
- **Issue:** No tracking of search queries, clicks, conversions
- **Impact:** Cannot optimize search relevance
- **Severity:** Low (optimization limitation)

### 9. No Personalization
- **Issue:** Same results for all users with same query
- **Impact:** Poor relevance for individual users
- **Severity:** Medium (relevance limitation)

### 10. No Search History
- **Issue:** Cannot re-run previous searches or see trends
- **Impact:** Poor UX, no learning from user behavior
- **Severity:** Low (UX limitation)

---

## Current Limitations

### Functional Limitations
1. **Single-entity search only:** Cannot search jobs + resumes together
2. **No nested filters:** Cannot combine filters with AND/OR logic
3. **No range filters:** Only salary ranges supported
4. **No geo-spatial search:** Location is text only, no distance calculations
5. **No date range filters:** Cannot filter by date ranges
6. **No multi-sort:** Can only sort by one field at a time
7. **No result highlighting:** Cannot highlight matched terms
8. **No search suggestions:** No query completion or correction
9. **No "did you mean":** No spelling correction
10. **No related results:** No "similar jobs" or "similar candidates"

### Performance Limitations
1. **Linear text search:** icontext requires full table scan
2. **No query caching:** Only recommendations are cached
3. **No result caching:** Every search hits database
4. **No search result pagination optimization:** OFFSET/LIMIT pattern
5. **No parallel query execution:** All queries sequential

### Scalability Limitations
1. **Single database:** No read replicas for search queries
2. **No horizontal scaling:** Search tied to primary database
3. **No background indexing:** All indexing synchronous
4. **No incremental updates:** Full reindex on changes
5. **No distributed search:** Cannot shard search data

### Relevance Limitations
1. **Simple keyword matching:** No TF-IDF, BM25, or relevance scoring
2. **No field boosting:** All fields weighted equally
3. **No custom ranking:** Only pre-calculated match scores
4. **No learning:** No ML-based relevance optimization
5. **No user feedback:** No click-through learning

---

## Current Matching Engine

### MatchingService Architecture
- **Location:** `apps/matching/services/matching.py`
- **Approach:** Deterministic rule-based matching
- **Signals:**
  - Skills (60% weight)
  - Experience (30% weight)
  - Education (10% weight)

### Skill Matching
- **Extraction:** Comma-separated parsing from `job.requirements` text
- **Matching:** Case-insensitive, exact match
- **Score:** Percentage of matched skills

### Experience Matching
- **Calculation:** Sum of days from all experience entries / 365.25
- **Requirements:** Predefined years per experience level
- **Score:** 100% if meets or exceeds, partial otherwise

### Education Matching
- **Check:** Binary (has education or not)
- **Score:** 100% or 0%

### Technical Debt
1. **Skill extraction fragile:** Cannot handle natural language
2. **No skill normalization:** "Python" vs "python" vs "PYTHON"
3. **No skill hierarchy:** Cannot match "Django" to "Python"
4. **No skill synonyms:** Cannot match "JS" to "JavaScript"
5. **No experience validation:** Assumes all experience is relevant
6. **No education quality:** PhD = High School in current model

---

## Current Caching Strategy

### CacheService
- **Implementation:** Redis-backed caching
- **TTL Configuration:**
  - `job_recommendations`: Configurable TTL
- **Usage:**
  - Job recommendations cached per candidate
  - Cache key: `job_recommendations:{user_id}`
- **Invalidation:**
  - Time-based (TTL)
  - No manual invalidation on data changes

### Cache Misses
- Job search: Not cached
- Resume search: Not cached
- Application filtering: Not cached
- Matching candidates: Not cached

---

## Security Considerations

### Current Security
1. **Authentication:** Required for all search endpoints
2. **Authorization:** Role-based access control
3. **Data filtering:** Users only see data they're authorized to see
4. **Input validation:** Search length validation, ordering validation
5. **SQL injection:** Protected by Django ORM

### Security Gaps
1. **No search rate limiting:** Only general API rate limiting
2. **No search query sanitization:** Logs may contain sensitive data
3. **No search result filtering:** No PII masking in search results
4. **No search audit logging:** No tracking of who searched what

---

## Observability

### Current Metrics
- Business metrics tracked:
  - `track_job_creation()`
  - `track_resume_upload()`
  - `track_application_submission()`
  - `track_interview_scheduled()`

### Missing Metrics
- Search query volume
- Search query latency (p50, p95, p99)
- Search result count distribution
- Zero-result rate
- Click-through rate
- Search result position clicks
- Cache hit/miss ratio

---

## Summary

### Strengths
1. Clean separation of concerns (service layer)
2. Query optimization with select_related/prefetch_related
3. Pre-calculated match scores for recommendations
4. Basic caching for recommendations
5. Role-based access control
6. Input validation

### Weaknesses
1. No full-text search capabilities
2. No faceted search or aggregations
3. No autocomplete or suggestions
4. No semantic search or vector similarity
5. Limited ranking (only match scores)
6. Poor scalability (single database)
7. No search analytics or observability
8. Fragile skill extraction from free text

### Recommendations
1. Implement dedicated search engine (Elasticsearch/OpenSearch)
2. Add full-text search with proper indexing
3. Implement faceted search with aggregations
4. Add autocomplete with prefix search
5. Implement semantic search with vector embeddings
6. Add comprehensive search analytics
7. Implement search result caching
8. Improve skill extraction with NLP
9. Add search rate limiting and audit logging
10. Design for horizontal scaling

---

## Next Steps

This audit informs the design of the new search architecture in the following documents:
1. Search Domain Model
2. Search Requirements
3. Search Architecture
4. Index Strategy
5. Ranking Strategy
6. Search API Design
7. Recommendation Architecture
8. Scalability Review
9. Extensibility Design
