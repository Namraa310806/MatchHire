# Search Domain Model
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

The search domain model defines all searchable entities in the MatchHire platform, their relationships, and how they map to search documents. This model serves as the foundation for designing search indexes, APIs, and ranking strategies.

---

## Core Searchable Entities

### 1. Candidate

**Description:** A user account with candidate role, representing a job seeker.

**Source Model:** `User` (role=candidate) + `CandidateProfile`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Primary key
  - `email` (email) - Contact email
  - `full_name` (text) - Candidate name
  - `headline` (text) - Professional headline
- **Profile:**
  - `bio` (text) - Professional summary
  - `current_location` (text) - Current location
  - `years_of_experience` (integer) - Total years of experience
  - `skills_text` (text) - Comma-separated skills
- **Links:**
  - `linkedin_url` (url) - LinkedIn profile
  - `github_url` (url) - GitHub profile
  - `portfolio_url` (url) - Portfolio website
- **Metadata:**
  - `resume_uploaded` (boolean) - Has uploaded resume
  - `date_joined` (date) - Account creation date
  - `updated_at` (date) - Last profile update

**Relationships:**
- One-to-One with `Resume`
- One-to-Many with `Application`
- One-to-Many with `JobMatch`

---

### 2. Resume

**Description:** Structured resume data extracted from uploaded files.

**Source Model:** `Resume` + `ResumeVersion` (is_current=True) + `StructuredResume`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Resume container ID
  - `candidate_id` (UUID) - Owner user ID
  - `candidate_email` (email) - Owner email
- **Contact:**
  - `full_name` (text) - Extracted name
  - `email` (email) - Extracted email
  - `phone` (text) - Extracted phone
  - `location` (text) - Extracted location
- **Content:**
  - `summary` (text) - Professional summary
- **Skills** (nested array):
  - `name` (keyword) - Skill name
  - `experience_years` (integer) - Years of experience with skill (future)
- **Experience** (nested array):
  - `company` (text) - Company name
  - `job_title` (text) - Job title
  - `start_date` (date) - Employment start
  - `end_date` (date) - Employment end
  - `description` (text) - Job description
  - `location` (text) - Job location (future)
- **Education** (nested array):
  - `institution` (text) - School/university name
  - `degree` (text) - Degree obtained
  - `field_of_study` (text) - Major/concentration
  - `start_year` (integer) - Start year
  - `end_year` (integer) - Graduation year
  - `description` (text) - Additional details
- **Projects** (nested array):
  - `title` (text) - Project name
  - `description` (text) - Project description
  - `github_url` (url) - GitHub repository
  - `project_url` (url) - Live project URL
- **Certifications** (nested array):
  - `name` (text) - Certification name
  - `issuer` (text) - Issuing organization
  - `issue_date` (date) - Issue date
- **Links:**
  - `linkedin_url` (url) - LinkedIn profile
  - `github_url` (url) - GitHub profile
  - `portfolio_url` (url) - Portfolio website
- **Metadata:**
  - `version_number` (integer) - Current version number
  - `created_at` (date) - Resume creation date
  - `updated_at` (date) - Last update date

**Relationships:**
- Many-to-One with `Candidate`
- One-to-Many with `ResumeSkill`
- One-to-Many with `ResumeExperience`
- One-to-Many with `ResumeEducation`
- One-to-Many with `ResumeProject`
- One-to-Many with `ResumeCertification`

---

### 3. Job

**Description:** Job posting created by recruiters.

**Source Model:** `Job`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Primary key
  - `recruiter_id` (UUID) - Recruiter user ID
  - `recruiter_email` (email) - Recruiter email
- **Basic:**
  - `title` (text) - Job title
  - `company_name` (text) - Company name
  - `location` (text) - Job location
- **Details:**
  - `description` (text) - Job description
  - `requirements` (text) - Job requirements
  - `responsibilities` (text) - Job responsibilities
- **Attributes:**
  - `employment_type` (keyword) - full_time, part_time, contract, internship
  - `experience_level` (keyword) - entry, junior, mid, senior, lead
  - `is_remote` (boolean) - Remote work option
- **Compensation:**
  - `salary_min` (decimal) - Minimum salary
  - `salary_max` (decimal) - Maximum salary
  - `currency` (keyword) - Currency code (USD, EUR, etc.)
- **Status:**
  - `status` (keyword) - draft, active, closed
  - `created_at` (date) - Creation date
  - `updated_at` (date) - Last update date
  - `closed_at` (date) - Closure date (if closed)

**Relationships:**
- Many-to-One with `Recruiter`
- One-to-Many with `Application`
- One-to-Many with `JobMatch`

---

### 4. Company

**Description:** Organization that posts jobs. Derived from recruiter profiles and job postings.

**Source Model:** `RecruiterProfile` + `Job` (aggregated)

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Company ID (derived from recruiter profile or company entity)
  - `name` (text) - Company name
- **Details:**
  - `website` (url) - Company website
  - `description` (text) - Company description (future)
  - `industry` (keyword) - Industry sector (future)
  - `company_size` (keyword) - Company size (future)
- **Location:**
  - `headquarters` (text) - Headquarters location (future)
  - `locations` (keyword array) - Office locations (future)
- **Aggregated Metrics:**
  - `active_jobs_count` (integer) - Number of active job postings
  - `total_jobs_count` (integer) - Total job postings
  - `verified` (boolean) - Company verification status
- **Metadata:**
  - `created_at` (date) - First job posting date
  - `updated_at` (date) - Last job posting date

**Relationships:**
- One-to-Many with `Recruiter`
- One-to-Many with `Job`

---

### 5. Recruiter

**Description:** A user account with recruiter role, representing a hiring professional.

**Source Model:** `User` (role=recruiter) + `RecruiterProfile`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Primary key
  - `email` (email) - Contact email
  - `full_name` (text) - Recruiter name
- **Profile:**
  - `company_name` (text) - Company name
  - `company_website` (url) - Company website
  - `job_title` (text) - Recruiter's job title
  - `verified_company` (boolean) - Company verification status
- **Metadata:**
  - `date_joined` (date) - Account creation date
  - `updated_at` (date) - Last profile update

**Relationships:**
- Many-to-One with `Company`
- One-to-Many with `Job`
- One-to-Many with `Application` (via jobs)

---

### 6. Skill

**Description:** Individual skill extracted from resumes and job requirements.

**Source Model:** `ResumeSkill` + derived from `Job.requirements`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Skill ID
  - `name` (keyword) - Skill name (normalized)
  - `aliases` (keyword array) - Alternative names (e.g., "JS", "JavaScript")
- **Category:**
  - `category` (keyword) - Skill category (frontend, backend, devops, etc.) (future)
  - `type` (keyword) - Skill type (hard, soft, tool, language) (future)
- **Metrics:**
  - `resume_count` (integer) - Number of resumes with this skill
  - `job_count` (integer) - Number of jobs requiring this skill
  - `popularity_score` (float) - Calculated popularity (future)
- **Relationships:**
  - `related_skills` (keyword array) - Related skills (future)
  - `parent_skill` (keyword) - Parent skill in hierarchy (future)
- **Metadata:**
  - `created_at` (date) - First occurrence
  - `updated_at` (date) - Last update

**Relationships:**
- Many-to-Many with `Resume`
- Many-to-Many with `Job`

---

### 7. Application

**Description:** Job application submitted by candidates.

**Source Model:** `Application`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Primary key
  - `candidate_id` (UUID) - Candidate user ID
  - `job_id` (UUID) - Job ID
  - `recruiter_id` (UUID) - Recruiter user ID (derived)
- **Details:**
  - `status` (keyword) - submitted, under_review, shortlisted, rejected, hired
  - `resume_version_id` (UUID) - Resume version used
- **Metadata:**
  - `created_at` (date) - Application date
  - `updated_at` (date) - Last status change

**Relationships:**
- Many-to-One with `Candidate`
- Many-to-One with `Job`
- Many-to-One with `ResumeVersion`
- One-to-Many with `ApplicationStatusHistory`

---

### 8. Interview

**Description:** Scheduled interviews for applications.

**Source Model:** `Interview`

**Search Document Fields:**
- **Identity:**
  - `id` (UUID) - Primary key
  - `application_id` (UUID) - Application ID
  - `candidate_id` (UUID) - Candidate user ID (derived)
  - `job_id` (UUID) - Job ID (derived)
  - `recruiter_id` (UUID) - Recruiter user ID (derived)
- **Details:**
  - `status` (keyword) - scheduled, completed, cancelled, no_show
  - `interview_type` (keyword) - video, phone, in_person
  - `location` (text) - Interview location or platform
  - `scheduled_at` (date) - Scheduled date/time
- **Metadata:**
  - `created_at` (date) - Creation date
  - `updated_at` (date) - Last update

**Relationships:**
- Many-to-One with `Application`
- Many-to-One with `Recruiter` (created_by)

---

## Entity Relationships

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Candidate │─────────│   Resume    │─────────│ ResumeSkill │
│   (User)    │   1:1   │             │   1:N    │             │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │
       │ 1:N                   │ 1:N
       │                       │
       v                       v
┌─────────────┐         ┌─────────────┐
│ Application │─────────│ResumeExp    │
│             │   N:1   │             │
└─────────────┘         └─────────────┘
       │ 1:N                   │ 1:N
       │                       │
       v                       v
┌─────────────┐         ┌─────────────┐
│    Job      │         │ResumeEdu    │
│             │         │             │
└─────────────┘         └─────────────┘
       │ N:1
       │
       v
┌─────────────┐
│  Recruiter  │
│   (User)    │
└─────────────┘
```

---

## Search Document Mappings

### Document Types vs Source Models

| Search Document | Source Model(s) | Cardinality | Primary Key |
|----------------|-----------------|-------------|-------------|
| candidate | User + CandidateProfile | 1:1 | user.id |
| resume | Resume + ResumeVersion + StructuredResume | 1:1 | resume.id |
| job | Job | 1:1 | job.id |
| company | RecruiterProfile + Job (aggregated) | N:1 | company_name (or future company.id) |
| recruiter | User + RecruiterProfile | 1:1 | user.id |
| skill | ResumeSkill + Job.requirements | N:1 | skill.name (normalized) |
| application | Application | 1:1 | application.id |
| interview | Interview | 1:1 | interview.id |

---

## Field Type Mappings

### Django Model → Search Engine Field Types

| Django Field | Elasticsearch Type | PostgreSQL Full-Text | Notes |
|--------------|-------------------|---------------------|-------|
| UUIDField | keyword | - | Exact match only |
| CharField | text + keyword | text | Text for search, keyword for sorting/aggregation |
| TextField | text | text | Full-text search |
| EmailField | keyword | - | Exact match |
| URLField | keyword | - | Exact match |
| BooleanField | boolean | - | Boolean filter |
| IntegerField | integer | - | Range queries |
| DecimalField | double | - | Range queries |
| DateField | date | - | Range queries |
| DateTimeField | date | - | Range queries |
| ForeignKey | keyword (join field) | - | Parent/child relationships |
| ManyToMany | nested object | - | Nested documents |
| JSONField | object | - | Structured data |

---

## Nested Object Structures

### Resume Skills (Nested)
```json
{
  "skills": [
    {
      "name": "Python",
      "experience_years": 3
    },
    {
      "name": "Django",
      "experience_years": 2
    }
  ]
}
```

### Resume Experience (Nested)
```json
{
  "experience": [
    {
      "company": "Tech Corp",
      "job_title": "Senior Developer",
      "start_date": "2020-01-01",
      "end_date": "2023-12-31",
      "description": "Led backend development..."
    }
  ]
}
```

### Resume Education (Nested)
```json
{
  "education": [
    {
      "institution": "MIT",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "start_year": 2016,
      "end_year": 2020
    }
  ]
}
```

---

## Future Entity Extensions

### Planned Entities (Not Yet Implemented)

1. **Skill Taxonomy**
   - Skill hierarchy (parent/child relationships)
   - Skill categories
   - Skill synonyms and aliases
   - Skill relevance scores

2. **Company Entity**
   - Dedicated Company model (not derived)
   - Company verification workflow
   - Company reviews/ratings
   - Company culture attributes

3. **Search Query Log**
   - Track all search queries
   - Query frequency analysis
   - Zero-result detection
   - Query suggestion learning

4. **Search Analytics**
   - Click-through tracking
   - Result position analysis
   - User engagement metrics
   - A/B testing framework

5. **User Preferences**
   - Saved searches
   - Search alerts
   - Location preferences
   - Salary preferences
   - Remote work preference

---

## Cross-Entity Search Patterns

### Unified Search (Future)
Ability to search across multiple entity types simultaneously:

- **Query:** "Python developer"
- **Results:**
  - Candidates with Python skills
  - Jobs requiring Python
  - Resumes mentioning Python
  - Companies hiring Python developers

### Entity Type Filtering
- `?entity_type=candidate,job` - Search specific entity types
- `?entity_type=all` - Search all entities (default)

---

## Data Synchronization

### Source of Truth
- **Primary Database:** PostgreSQL (Django ORM)
- **Search Index:** Elasticsearch/OpenSearch (future)
- **Cache:** Redis (for hot data)

### Synchronization Strategy
1. **Real-time:** Sync on CRUD operations (via signals)
2. **Batch:** Periodic full reindex (for consistency)
3. **Event-driven:** Celery tasks for async indexing

### Indexing Triggers
- Candidate profile update → Reindex candidate
- Resume upload/parse → Reindex resume
- Job create/update → Reindex job
- Application status change → Reindex application
- Interview schedule → Reindex interview

---

## Summary

The search domain model defines 8 core searchable entities:
1. **Candidate** - Job seekers
2. **Resume** - Structured resume data
3. **Job** - Job postings
4. **Company** - Organizations
5. **Recruiter** - Hiring professionals
6. **Skill** - Technical and soft skills
7. **Application** - Job applications
8. **Interview** - Scheduled interviews

Each entity maps to one or more Django models and includes comprehensive field definitions for search, filtering, sorting, and ranking. The model supports nested objects for complex data structures and is designed for future extensibility with skill taxonomies, company entities, and search analytics.
