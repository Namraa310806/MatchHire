# Search Requirements
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines comprehensive search requirements for each searchable entity in the MatchHire platform. For every entity, we specify searchable fields, filterable fields, sortable fields, faceted fields, autocomplete fields, ranking fields, and future semantic fields.

---

## Entity: Candidate

### Searchable Fields (Full-Text Search)
- `full_name` - Candidate name
- `headline` - Professional headline
- `bio` - Professional summary
- `skills_text` - Comma-separated skills
- `current_location` - Current location

**Search Strategy:**
- Multi-field search with field boosting
- Name and headline: higher boost (2.0)
- Bio and skills: medium boost (1.5)
- Location: lower boost (1.0)

### Filterable Fields (Exact/Range)
- `years_of_experience` - Range filter (min, max)
- `resume_uploaded` - Boolean filter (has resume)
- `date_joined` - Date range filter
- `updated_at` - Date range filter
- `current_location` - Exact match (for filtering, not search)

### Sortable Fields
- `date_joined` - Account creation date
- `updated_at` - Last profile update
- `years_of_experience` - Experience level
- `full_name` - Alphabetical
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `years_of_experience` - Range buckets (0-1, 1-3, 3-5, 5-10, 10+)
- `resume_uploaded` - Boolean (Yes/No)
- `current_location` - Top 20 locations
- `skills` - Top 50 skills (derived from skills_text)

### Autocomplete Fields
- `full_name` - Name completion
- `headline` - Headline completion
- `current_location` - Location completion

### Ranking Fields (Signals)
- **Profile Completeness:** (0-100) Based on filled fields
- **Activity Score:** (0-100) Based on recent activity
- **Experience Level:** (0-100) Based on years_of_experience
- **Skill Count:** (0-100) Number of skills
- **Recency:** (0-100) Based on updated_at
- **Match Score:** (0-100) Pre-calculated from JobMatch (context-dependent)

### Future Semantic Fields
- `skills_embeddings` - Vector embeddings for skills
- `bio_embedding` - Vector embedding for bio
- `headline_embedding` - Vector embedding for headline
- `semantic_profile` - Combined semantic representation

---

## Entity: Resume

### Searchable Fields (Full-Text Search)
- `full_name` - Candidate name
- `summary` - Professional summary
- `skills.name` - Skill names (nested)
- `experience.company` - Company names (nested)
- `experience.job_title` - Job titles (nested)
- `experience.description` - Job descriptions (nested)
- `education.institution` - Institution names (nested)
- `education.degree` - Degrees (nested)
- `education.field_of_study` - Fields of study (nested)
- `projects.title` - Project titles (nested)
- `projects.description` - Project descriptions (nested)
- `certifications.name` - Certification names (nested)
- `certifications.issuer` - Issuer names (nested)

**Search Strategy:**
- Cross-field search with different boost levels
- Skills and job titles: highest boost (3.0)
- Company and institution names: high boost (2.0)
- Summaries and descriptions: medium boost (1.5)
- Projects and certifications: lower boost (1.0)

### Filterable Fields (Exact/Range)
- `location` - Exact match
- `skills.name` - Multi-select filter (OR logic)
- `experience.company` - Multi-select filter (OR logic)
- `experience.job_title` - Multi-select filter (OR logic)
- `education.degree` - Multi-select filter (OR logic)
- `education.institution` - Multi-select filter (OR logic)
- `experience.start_date` - Date range filter
- `experience.end_date` - Date range filter
- `education.end_year` - Range filter (graduation year)
- `certifications.issue_date` - Date range filter
- `created_at` - Date range filter
- `updated_at` - Date range filter

### Sortable Fields
- `created_at` - Resume creation date
- `updated_at` - Last update date
- `full_name` - Alphabetical
- `experience_years` - Total years of experience (calculated)
- `education_count` - Number of education entries
- `skill_count` - Number of skills
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `location` - Top 20 locations
- `skills.name` - Top 50 skills
- `experience.company` - Top 20 companies
- `experience.job_title` - Top 20 job titles
- `education.degree` - Degree types (Bachelor, Master, PhD, etc.)
- `education.institution` - Top 20 institutions
- `experience_years` - Range buckets (0-1, 1-3, 3-5, 5-10, 10+)
- `certifications.name` - Top 20 certifications

### Autocomplete Fields
- `full_name` - Name completion
- `skills.name` - Skill completion
- `experience.company` - Company completion
- `experience.job_title` - Job title completion
- `education.institution` - Institution completion
- `location` - Location completion

### Ranking Fields (Signals)
- **Skill Relevance:** (0-100) Match with required skills
- **Experience Relevance:** (0-100) Match with experience requirements
- **Education Quality:** (0-100) Based on degree level and institution
- **Recency:** (0-100) Based on updated_at
- **Completeness:** (0-100) Based on filled sections
- **Match Score:** (0-100) Pre-calculated from JobMatch (context-dependent)

### Future Semantic Fields
- `summary_embedding` - Vector embedding for summary
- `skills_embeddings` - Vector embeddings for each skill
- `experience_embeddings` - Vector embeddings for experience descriptions
- `semantic_resume` - Combined semantic representation

---

## Entity: Job

### Searchable Fields (Full-Text Search)
- `title` - Job title
- `company_name` - Company name
- `description` - Job description
- `requirements` - Job requirements
- `responsibilities` - Job responsibilities
- `location` - Job location

**Search Strategy:**
- Multi-field search with field boosting
- Title: highest boost (3.0)
- Company name: high boost (2.0)
- Requirements: medium-high boost (1.8)
- Responsibilities: medium boost (1.5)
- Description: medium-low boost (1.2)
- Location: lower boost (1.0)

### Filterable Fields (Exact/Range)
- `employment_type` - Exact match (full_time, part_time, contract, internship)
- `experience_level` - Exact match (entry, junior, mid, senior, lead)
- `is_remote` - Boolean filter
- `salary_min` - Range filter (min salary)
- `salary_max` - Range filter (max salary)
- `currency` - Exact match (USD, EUR, etc.)
- `location` - Exact match
- `status` - Exact match (active, draft, closed)
- `created_at` - Date range filter
- `updated_at` - Date range filter
- `closed_at` - Date range filter

### Sortable Fields
- `created_at` - Creation date
- `updated_at` - Last update date
- `salary_min` - Minimum salary
- `salary_max` - Maximum salary
- `title` - Alphabetical
- `company_name` - Alphabetical
- `match_score` - Pre-calculated match score (context-dependent)
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `employment_type` - All employment types with counts
- `experience_level` - All experience levels with counts
- `is_remote` - Boolean (Yes/No) with counts
- `location` - Top 20 locations with counts
- `salary_range` - Custom buckets (0-50k, 50k-100k, 100k-150k, 150k+)
- `company_name` - Top 20 companies with counts
- `currency` - All currencies with counts

### Autocomplete Fields
- `title` - Job title completion
- `company_name` - Company completion
- `location` - Location completion
- `requirements` - Skill/requirement completion

### Ranking Fields (Signals)
- **Recency:** (0-100) Based on created_at (newer = higher)
- **Salary Competitiveness:** (0-100) Compared to market average
- **Match Score:** (0-100) Pre-calculated from JobMatch (context-dependent)
- **Application Count:** (0-100) Inverse (fewer applications = higher)
- **Company Quality:** (0-100) Based on company verification and rating
- **Urgency:** (0-100) Based on days since posting

### Future Semantic Fields
- `title_embedding` - Vector embedding for job title
- `description_embedding` - Vector embedding for description
- `requirements_embedding` - Vector embedding for requirements
- `semantic_job` - Combined semantic representation

---

## Entity: Company

### Searchable Fields (Full-Text Search)
- `name` - Company name
- `description` - Company description
- `industry` - Industry sector

**Search Strategy:**
- Name: highest boost (3.0)
- Description: medium boost (1.5)
- Industry: medium boost (1.5)

### Filterable Fields (Exact/Range)
- `industry` - Exact match
- `company_size` - Exact match (startup, small, medium, large, enterprise)
- `verified` - Boolean filter
- `headquarters` - Exact match
- `locations` - Multi-select filter (office locations)
- `created_at` - Date range filter
- `updated_at` - Date range filter

### Sortable Fields
- `name` - Alphabetical
- `created_at` - First job posting date
- `updated_at` - Last job posting date
- `active_jobs_count` - Number of active jobs
- `total_jobs_count` - Total job postings
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `industry` - All industries with counts
- `company_size` - All size categories with counts
- `verified` - Boolean (Yes/No) with counts
- `headquarters` - Top 20 locations with counts
- `active_jobs_count` - Range buckets (0, 1-5, 6-10, 11-20, 20+)

### Autocomplete Fields
- `name` - Company name completion
- `industry` - Industry completion

### Ranking Fields (Signals)
- **Job Activity:** (0-100) Based on active_jobs_count
- **Verification Status:** (0-100) Verified companies ranked higher
- **Recency:** (0-100) Based on updated_at
- **Company Size:** (0-100) Larger companies ranked higher (configurable)

### Future Semantic Fields
- `description_embedding` - Vector embedding for description
- `industry_embedding` - Vector embedding for industry
- `semantic_company` - Combined semantic representation

---

## Entity: Recruiter

### Searchable Fields (Full-Text Search)
- `full_name` - Recruiter name
- `company_name` - Company name
- `job_title` - Recruiter's job title

**Search Strategy:**
- Name: highest boost (2.0)
- Company name: high boost (1.5)
- Job title: medium boost (1.0)

### Filterable Fields (Exact/Range)
- `company_name` - Exact match
- `verified_company` - Boolean filter
- `job_title` - Exact match
- `date_joined` - Date range filter
- `updated_at` - Date range filter

### Sortable Fields
- `full_name` - Alphabetical
- `company_name` - Alphabetical
- `date_joined` - Account creation date
- `updated_at` - Last profile update
- `active_jobs_count` - Number of active jobs (derived)
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `company_name` - Top 20 companies with counts
- `verified_company` - Boolean (Yes/No) with counts
- `job_title` - Top 20 job titles with counts

### Autocomplete Fields
- `full_name` - Name completion
- `company_name` - Company completion

### Ranking Fields (Signals)
- **Job Activity:** (0-100) Based on active job count
- **Verification Status:** (0-100) Verified companies ranked higher
- **Recency:** (0-100) Based on updated_at

### Future Semantic Fields
- `profile_embedding` - Combined semantic representation

---

## Entity: Skill

### Searchable Fields (Full-Text Search)
- `name` - Skill name
- `aliases` - Alternative names

**Search Strategy:**
- Name: highest boost (3.0)
- Aliases: high boost (2.0)

### Filterable Fields (Exact/Range)
- `category` - Exact match (frontend, backend, devops, etc.)
- `type` - Exact match (hard, soft, tool, language)
- `resume_count` - Range filter (minimum resume count)
- `job_count` - Range filter (minimum job count)

### Sortable Fields
- `name` - Alphabetical
- `resume_count` - Number of resumes with skill
- `job_count` - Number of jobs requiring skill
- `popularity_score` - Calculated popularity
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `category` - All categories with counts
- `type` - All types with counts
- `popularity_score` - Range buckets (low, medium, high)

### Autocomplete Fields
- `name` - Skill name completion
- `aliases` - Alias completion

### Ranking Fields (Signals)
- **Popularity:** (0-100) Based on resume_count and job_count
- **Trendiness:** (0-100) Based on recent growth (future)
- **Category Relevance:** (0-100) Based on category importance

### Future Semantic Fields
- `name_embedding` - Vector embedding for skill name
- `related_skills_embeddings` - Vector embeddings for related skills

---

## Entity: Application

### Searchable Fields (Full-Text Search)
- `candidate.full_name` - Candidate name (via join)
- `candidate.headline` - Candidate headline (via join)
- `job.title` - Job title (via join)
- `job.company_name` - Company name (via join)

**Search Strategy:**
- Candidate name: high boost (2.0)
- Job title: high boost (2.0)
- Company name: medium boost (1.5)
- Candidate headline: medium boost (1.5)

### Filterable Fields (Exact/Range)
- `status` - Exact match (submitted, under_review, shortlisted, rejected, hired)
- `candidate_id` - Exact match
- `job_id` - Exact match
- `recruiter_id` - Exact match (derived)
- `created_at` - Date range filter
- `updated_at` - Date range filter

### Sortable Fields
- `created_at` - Application date
- `updated_at` - Last status change
- `status` - Status (alphabetical)
- `match_score` - Pre-calculated match score (via JobMatch)
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `status` - All statuses with counts
- `job.title` - Top 20 job titles with counts
- `job.company_name` - Top 20 companies with counts

### Autocomplete Fields
- `candidate.full_name` - Candidate name completion
- `job.title` - Job title completion

### Ranking Fields (Signals)
- **Match Score:** (0-100) Pre-calculated from JobMatch
- **Recency:** (0-100) Based on created_at
- **Status Priority:** (0-100) Based on status (hired > shortlisted > under_review > submitted > rejected)

### Future Semantic Fields
- None planned (applications are transactional, not content-rich)

---

## Entity: Interview

### Searchable Fields (Full-Text Search)
- `candidate.full_name` - Candidate name (via join)
- `job.title` - Job title (via join)
- `location` - Interview location/platform

**Search Strategy:**
- Candidate name: high boost (2.0)
- Job title: high boost (2.0)
- Location: medium boost (1.0)

### Filterable Fields (Exact/Range)
- `status` - Exact match (scheduled, completed, cancelled, no_show)
- `interview_type` - Exact match (video, phone, in_person)
- `candidate_id` - Exact match (derived)
- `job_id` - Exact match (derived)
- `recruiter_id` - Exact match (derived)
- `scheduled_at` - Date range filter
- `created_at` - Date range filter

### Sortable Fields
- `scheduled_at` - Scheduled date/time
- `created_at` - Creation date
- `status` - Status (alphabetical)
- `relevance` - Search relevance score (default)

### Faceted Fields (Aggregations)
- `status` - All statuses with counts
- `interview_type` - All types with counts
- `scheduled_at` - Date histogram (by day/week/month)

### Autocomplete Fields
- `candidate.full_name` - Candidate name completion
- `job.title` - Job title completion
- `location` - Location completion

### Ranking Fields (Signals)
- **Urgency:** (0-100) Based on scheduled_at (sooner = higher)
- **Status Priority:** (0-100) Based on status (scheduled > completed > cancelled > no_show)

### Future Semantic Fields
- None planned (interviews are transactional, not content-rich)

---

## Cross-Entity Search Requirements

### Unified Search
- **Query:** Free-text search across multiple entity types
- **Entity Type Filter:** Restrict search to specific entity types
- **Result Grouping:** Group results by entity type
- **Result Count:** Limit results per entity type

### Example Unified Search Query
```
GET /api/search/unified?q=Python developer&entity_type=candidate,job
```

### Response Structure
```json
{
  "candidates": {
    "total": 150,
    "results": [...]
  },
  "jobs": {
    "total": 75,
    "results": [...]
  },
  "resumes": {
    "total": 200,
    "results": [...]
  }
}
```

---

## Advanced Search Features

### Boolean Operators
- **AND:** `Python AND Django` (both terms must match)
- **OR:** `Python OR Django` (either term must match)
- **NOT:** `Python NOT Java` (exclude Java)
- **Grouping:** `(Python OR Django) AND REST`

### Phrase Search
- **Exact Phrase:** `"senior developer"` (exact phrase match)
- **Proximity:** `"senior developer"~5` (within 5 words)

### Wildcard Search
- **Single Character:** `Pytho?` (matches Python, Pythox)
- **Multiple Characters:** `Py*` (matches Python, PyTorch, Pygame)

### Fuzzy Search
- **Edit Distance:** `Python~1` (matches Python, Pythn, Pythoh)
- **Configurable:** Edit distance 0-2

### Range Queries
- **Numeric:** `salary_min:[50000 TO *)`
- **Date:** `created_at:[2024-01-01 TO 2024-12-31]`
- **Exclusive:** `salary_min:[50000 TO 100000}`

### Boosting
- **Term Boost:** `Python^2 Django` (Python weighted 2x)
- **Field Boost:** `title:Python^3 description:Python`
- **Function Boost:** Boost based on recency, popularity, etc.

---

## Search Performance Requirements

### Latency Targets
- **Simple Search:** < 100ms (p95)
- **Complex Search:** < 300ms (p95)
- **Faceted Search:** < 500ms (p95)
- **Autocomplete:** < 50ms (p95)

### Throughput Targets
- **Search QPS:** 1000 queries per second
- **Index QPS:** 100 documents per second
- **Concurrent Users:** 500 simultaneous search users

### Result Size Limits
- **Default Page Size:** 20 results
- **Max Page Size:** 100 results
- **Max Result Depth:** 3 levels of nested objects

---

## Search Quality Requirements

### Relevance Metrics
- **Click-Through Rate (CTR):** > 20%
- **Zero-Result Rate:** < 5%
- **First Result CTR:** > 30%
- **Top-3 Result CTR:** > 60%

### Coverage Metrics
- **Index Freshness:** < 5 seconds lag
- **Index Completeness:** 100% of active documents indexed
- **Search Coverage:** 100% of searchable fields indexed

---

## Summary

This document defines comprehensive search requirements for 8 core entities:

1. **Candidate:** 5 searchable fields, 6 filterable fields, 5 sortable fields, 4 faceted fields, 3 autocomplete fields, 6 ranking signals
2. **Resume:** 13 searchable fields, 11 filterable fields, 7 sortable fields, 8 faceted fields, 6 autocomplete fields, 6 ranking signals
3. **Job:** 6 searchable fields, 10 filterable fields, 7 sortable fields, 7 faceted fields, 4 autocomplete fields, 6 ranking signals
4. **Company:** 3 searchable fields, 7 filterable fields, 6 sortable fields, 5 faceted fields, 2 autocomplete fields, 4 ranking signals
5. **Recruiter:** 3 searchable fields, 5 filterable fields, 6 sortable fields, 3 faceted fields, 2 autocomplete fields, 3 ranking signals
6. **Skill:** 2 searchable fields, 4 filterable fields, 5 sortable fields, 3 faceted fields, 2 autocomplete fields, 3 ranking signals
7. **Application:** 4 searchable fields, 6 filterable fields, 6 sortable fields, 3 faceted fields, 2 autocomplete fields, 3 ranking signals
8. **Interview:** 3 searchable fields, 7 filterable fields, 5 sortable fields, 3 faceted fields, 3 autocomplete fields, 2 ranking signals

Additionally, the document specifies:
- Cross-entity unified search requirements
- Advanced search features (boolean, phrase, wildcard, fuzzy, range, boosting)
- Performance requirements (latency, throughput, result size)
- Quality requirements (relevance, coverage)

These requirements serve as the foundation for designing the search architecture, index strategy, and ranking strategy.
