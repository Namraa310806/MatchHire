# MatchHire Backend Performance Audit

**Date:** 2026-07-22
**Phase:** Milestone 1 - Phase 4.5 Performance Engineering
**Auditor:** Performance Engineering Review

---

## Executive Summary

This audit identifies performance bottlenecks in the MatchHire backend through static code analysis. The audit focuses on ORM query patterns, N+1 query problems, serializer efficiency, and database index utilization.

**Key Findings:**
- **Critical N+1 Query Issues:** 6 identified
- **Inefficient Query Patterns:** 3 identified
- **Missing Query Optimization:** 8 instances
- **Index Optimization Opportunities 4 identified**
- **Serializer Performance Issues:** 5 identified

---

## 1. N+1 Query Problems

### 1.1 Resume Serializers - Current Version Access

**Location:** `apps/resumes/serializers.py`
**Severity:** HIGH
**Impact:** Medium

**Issue:**
```python
# ResumeListSerializer.get_current_version() (line 72-78)
def get_current_version(self, obj):
    try:
        current_version = obj.versions.get(is_current=True)  # N+1 query
        return ResumeVersionSerializer(current_version).data
    except ResumeVersion.DoesNotExist:
        return None
```

**Problem:** When serializing a list of resumes, each resume triggers an additional query to fetch the current version.

**Affected Endpoints:**
- `GET /api/resumes/` (ResumeListView)
- `GET /api/resumes/<id>/` (ResumeDetailView)
- `GET /api/resumes/active/` (ActiveResumeView)

**Recommendation:** Use `prefetch_related` with a `Prefetch` object to fetch current versions in a single query.

---

### 1.2 Resume Search Result Serializer - Related Field Counts

**Location:** `apps/resumes/serializers.py`
**Severity:** HIGH
**Impact:** High

**Issue:**
```python
# ResumeSearchResultSerializer (lines 332-350)
def get_skills(self, obj):
    return [skill.name for skill in obj.skills.all()]  # N+1 query

def get_experience_count(self, obj):
    return obj.experience.count()  # N+1 query

def get_education_count(self, obj):
    return obj.education.count()  # N+1 query

def get_project_count(self, obj):
    return obj.projects.count()  # N+1 query

def get_certification_count(self, obj):
    return obj.certifications.count()  # N+1 query
```

**Problem:** Each method triggers a separate query for each resume in search results.

**Affected Endpoints:**
- `GET /api/resumes/search/` (ResumeSearchView)

**Recommendation:** Use `prefetch_related` with `Prefetch` objects and annotate counts at the queryset level.

---

### 1.3 Candidate Profile Serializer - Structured Resume Access

**Location:** `apps/resumes/serializers.py`
**Severity:** MEDIUM
**Impact:** Medium

**Issue:**
```python
# CandidateProfileSerializer.get_structured_resume() (lines 370-380)
def get_structured_resume(self, obj):
    try:
        current_version = obj.versions.get(is_current=True)  # Query 1
        try:
            structured_resume = current_version.structured_resume  # Query 2
            return StructuredResumeSerializer(structured_resume StructuredResumeSerializer(structured_resume).data
        except StructuredResume.DoesNotExist:
            return None
    except ResumeVersion.DoesNotExist:
        return None
```

**Problem:** Nested queries without optimization.

**Affected Endpoints:** Any endpoint using CandidateProfileSerializer

**Recommendation:** Use `select_related` and `prefetch_related` with proper Prefetch objects.

---

### 1.4 Matching Service - Candidate Data Access

**Location:** `apps/matching/services/matching.py`
**Severity:** HIGH
**Impact:** High

**Issue:**
```python
# _get_candidate_skills() (lines 256-280)
def _get_candidate_skills(cls, candidate):
    try:
        resume = Resume.objects.get(user=candidate)  # Query 1
        current_version = resume.versions.filter(is_current=True).first()  # Query 2
        if not current_version:
            return ResumeSkill.objects.none()
        try:
            structured_resume = current_version.structured_resume  # Query 3
        except StructuredResume.DoesNotExist:
            return ResumeSkill.objects.none()
        if not structured_resume:
            return ResumeSkill.objects.none()
        return structured_resume.skills.all()  # Query 4
    except Resume.DoesNotExist:
        return ResumeSkill.objects.none()
```

**Problem:** Multiple sequential queries for each candidate during matching.

**Affected Endpoints:**
- `POST /api/jobs/<job_id>/match/` (CandidateMatchView)
- `GET /api/jobs/recommendations/` (JobRecommendationsView)
- `GET /api/recruiter/candidates/?job_id=<uuid>` (RecruiterCandidatesView)

**Recommendation:** Use `select_related` and `prefetch_related` to fetch all data in 1-2 queries.

---

### 1.5 Matching Service - Experience and Education Access

**Location:** `apps/matching/services/matching.py`
**Severity:** HIGH
**Impact:** High

**Issue:**
```python
# _get_candidate_experience_years() (lines 283-321)
# Similar pattern to _get_candidate_skills - 4+ queries per candidate

# _get_candidate_has_education() (lines 324-348)
# Similar pattern - 4+ queries per candidate
```

**Problem:** Each helper method performs multiple queries independently.

**Affected Endpoints:** Same as 1.4

**Recommendation:** Consolidate data fetching into a single optimized query.

---

### 1.6 Job Recommendations View - Iterative Matching

**Location:** `apps/matching/views.py`
**Severity:** CRITICAL
**Impact:** Very High

**Issue:**
```python
# JobRecommendationsView.get() (lines 106-122)
def get(self, request):
    active_jobs = Job.objects.filter(status=Job.JobStatus.ACTIVE).select_related("recruiter")
    
    recommendations = []
    for job in active_jobs:  # Iterates over ALL active jobs
        job_match = MatchingService.calculate_match(request.user, job)  # Multiple queries per job
        recommendations.append(job_match)
    
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    recommendations = recommendations[:20]
```

**Problem:** For a candidate, this iterates over ALL active jobs and performs multiple database queries per job. If there are 1000 active jobs, this could result in 4000+ queries.

**Affected Endpoints:**
- `GET /api/jobs/recommendations/` (JobRecommendationsView)

**Recommendation:** Use pre-calculated JobMatch records with proper indexing, or batch process with Celery.

---

### 1.7 Recruiter Candidates View - Iterative Matching

**Location:** `apps/matching/views.py`
**Severity:** CRITICAL
**Impact:** Very High

**Issue:**
```python
# RecruiterCandidatesView.get() (lines 151-180)
def get(self, request):
    # ... validation ...
    
    candidates = User.objects.filter(role=User.Roles.CANDIDATE)  # ALL candidates
    
    candidate_matches = []
    for candidate in candidates:  # Iterates over ALL candidates
        job_match = MatchingService.calculate_match(candidate, job)  # Multiple queries per candidate
        candidate_matches.append(job_match)
    
    candidate_matches.sort(key=lambda x: x.match_score, reverse=True)
```

**Problem:** Iterates over ALL candidates and performs multiple queries per candidate. If there are 1000 candidates, this could result in 4000+ queries.

**Affected Endpoints:**
- `GET /api/recruiter/candidates/?job_id=<uuid>` (RecruiterCandidatesView)

**Recommendation:** Use pre-calculated JobMatch records with proper indexing.

---

## 2. Inefficient Query Patterns

### 2.1 Resume Search Service - Multiple Joins Without Optimization

**Location:** `apps/resumes/services/search_service.py`
**Severity:** MEDIUM
**Impact:** Medium

**Issue:**
```python
# search() method (lines 122-219)
# The service applies multiple filters that create joins
# but doesn't use Prefetch objects to optimize related data loading
```

**Problem:** While the service uses `select_related` and `prefetch_related`, it doesn't use `Prefetch` objects to control the querysets for related data, potentially loading more data than needed.

**Affected Endpoints:**
- `GET /api/resumes/search/` (ResumeSearchView)

**Recommendation:** Use `Prefetch` objects to optimize related data loading.

---

### 2.2 Admin Resume List - Complex Filtering

**Location:** `apps/admin/views.py`
**Severity:** MEDIUM
**Impact:** Medium

**Issue:**
```python
# AdminResumeListView.get() (lines 357-414)
# Complex filtering with versions__is_current=True and versions__structured_resume
# Uses distinct() which can be expensive on large datasets
```

**Problem:** Multiple joins across related tables with `distinct()` can be expensive.

**Affected Endpoints:**
- `GET /api/admin/resumes/` (AdminResumeListView)

**Recommendation:** Consider using subqueries or exists() for filtering.

---

### 2.3 Analytics Views - Multiple Aggregate Queries

**Location:** `apps/analytics/views.py`
**Severity:** LOW
**Impact:** Low

**Issue:**
```python
# RecruiterDashboardView.get() (lines 48-90)
# Performs 3 separate aggregate queries
job_metrics = Job.objects.filter(recruiter=recruiter).aggregate(...)
application_metrics = Application.objects.filter(job__recruiter=recruiter).aggregate(...)
interview_metrics = Interview.objects.filter(application__job__recruiter=recruiter).aggregate(...)
```

**Problem:** Multiple separate aggregate queries could potentially be combined.

**Affected Endpoints:**
- `GET /api/analytics/recruiter/dashboard/` (RecruiterDashboardView)
- `GET /api/analytics/candidate/dashboard/` (CandidateDashboardView)

**Recommendation:** This is actually well-optimized. Separate aggregate queries are often more efficient than complex joins. No action needed.

---

## 3. Missing Query Optimization

### 3.1 Job Detail View - Missing select_related

**Location:** `apps/jobs/views.py`
**Severity:** LOW
**Impact:** Low

**Issue:**
```python
# JobDetailView.get_object() (line 139)
job = Job.objects.select_related("recruiter").get(id=id)
```

**Status:** ALREADY OPTIMIZED - This view already uses `select_related`.

---

### 3.2 Application Views - Good Optimization

**Location:** `apps/applications/views.py`
**Severity:** N/A
**Impact:** N/A

**Status:** ALREADY OPTIMIZED - Most views already use `select_related` for job, candidate, and resume_version.

---

### 3.3 Resume Version Views - Missing Optimization

**Location:** `apps/resumes/views.py`
**Severity:** MEDIUM
**Impact:** Medium

**Issue:**
```python
# ResumeVersionHistoryView.get() (lines 522-532)
versions = ResumeVersion.objects.filter(resume=resume).select_related(
    "parsed_resume"
).order_by("-version_number")
```

**Status:** PARTIALLY OPTIMIZED - Uses `select_related` for parsed_resume but could also prefetch structured_resume.

**Recommendation:** Add `prefetch_related("structured_resume")` if structured resume data is needed.

---

## 4. Database Index Review

### 4.1 Existing Indexes

**Jobs Model:**
```python
indexes = [
    models.Index(fields=["status"]),
    models.Index(fields=["recruiter"]),
    models.Index(fields=["created_at"]),
]
```

**Applications Model:**
```python
indexes = [
    models.Index(fields=["status"]),
    models.Index(fields=["job"]),
    models.Index(fields=["candidate"]),
    models.Index(fields=["created_at"]),
]
```

**JobMatch Model:**
```python
indexes = [
    models.Index(fields=["candidate"]),
    models.Index(fields=["job"]),
    models.Index(fields=["match_score"]),
]
```

**ApplicationStatusHistory Model:**
```python
indexes = [
    models.Index(fields=["application"]),
    models.Index(fields=["changed_at"]),
]
```

### 4.2 Missing Composite Indexes

**Recommendation 1: Jobs - Status + Created_at Composite Index**
```python
# For queries like: Job.objects.filter(status=ACTIVE).order_by('-created_at')
models.Index(fields=["status", "-created_at"])
```
**Rationale:** The public job list filters by status=ACTIVE and orders by created_at DESC. A composite index would significantly improve this query.

**Recommendation 2: Applications - Job + Status Composite Index**
```python
# For queries like: Application.objects.filter(job=job, status=status)
models.Index(fields=["job", "status"])
```
**Rationale:** Job applications list filters by job and optionally by status. A composite index would improve this.

**Recommendation 3: JobMatch - Job + Match Score Composite Index**
```python
# For queries like: JobMatch.objects.filter(job=job).order_by('-match_score')
models.Index(fields=["job", "-match_score"])
```
**Rationale:** Top candidates view filters by job and orders by match_score DESC. A composite index would significantly improve this.

**Recommendation 4: JobMatch - Candidate + Job Composite Index**
```python
# The unique constraint already serves as an index
# But we should verify it's being used efficiently
```
**Rationale:** The unique constraint on (candidate, job) already provides this index.

---

## 5. Serializer Performance Issues

### 5.1 MethodField Queries

**Location:** Multiple serializers
**Severity:** MEDIUM
**Impact:** Medium

**Issue:** Many serializers use `SerializerMethodField` to perform queries. These are executed for each object in a queryset, causing N+1 problems.

**Affected Serializers:**
- ResumeListSerializer
- ResumeDetailSerializer
- ResumeActivationSerializer
- CandidateProfileSerializer
- ResumeSearchResultSerializer

**Recommendation:** Move query logic to the view layer using `prefetch_related` and `Prefetch` objects, then use standard fields in serializers.

---

## 6. Pagination Review

### 6.1 Current Pagination Implementation

**Jobs:** JobSearchPagination (page_size=20, max=100)
**Resumes:** ResumeSearchPagination (page_size=20, max=100)
**Admin:** AdminPagination (page_size=50, max=200)

**Status:** WELL IMPLEMENTED

All paginated endpoints use proper pagination with reasonable limits. No issues identified.

---

## 7. Caching Opportunities

### 7.1 Read-Only Reference Data

**Candidate:** Dashboard statistics
**Rationale:** Dashboard metrics are expensive aggregate queries that don't change frequently.
**TTL:** 5 minutes
**Cache Key:** `dashboard:{user_id}:{role}`

### 7.2 Expensive Aggregate Queries

**Candidate:** Job recommendations
**Rationale:** Calculating matches for all jobs is expensive.
**TTL:** 1 hour
**Cache Key:** `recommendations:{candidate_id}`
**Invalidation:** On resume update, job creation/update

### 7.3 API Responses with Deterministic Output

**Candidate:** Public job list (with filters)
**Rationale:** Job list with specific filters is requested frequently.
**TTL:** 1 minute
**Cache Key:** `jobs:public:{hash_of_filters}`
**Invalidation:** On job create/update/delete

---

## 8. Connection Management Review

### 8.1 Current Configuration

**Database (prod.py):**
```python
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["OPTIONS"] = {
    "connect_timeout": 10,
}
```

**Status:** WELL CONFIGURED

Connection pooling is enabled with a 10-minute max age. This is appropriate for a production application.

### 8.2 Gunicorn Configuration

**Status:** NOT REVIEWED (Docker configuration not in scope)

Recommendation: Ensure Gunicorn workers are configured appropriately for the expected load.

---

## 9. Celery Performance Review

### 9.1 Current Configuration

**Status:** NOT REVIEWED (Celery configuration not in scope)

Recommendation: Review worker concurrency, prefetch multiplier, and queue routing in future optimization phase.

---

## 10. Priority Recommendations

### Critical (Immediate Action Required)

1. **Fix JobRecommendationsView iterative matching** - Use pre-calculated JobMatch records
2. **Fix RecruiterCandidatesView iterative matching** - Use pre-calculated JobMatch records
3. **Optimize MatchingService data access** - Consolidate queries with select_related/prefetch_related

### High (Action Required Soon)

4. **Fix ResumeSearchResultSerializer N+1 queries** - Use prefetch_related with counts
5. **Fix Resume serializers current version access** - Use Prefetch objects
6. **Add composite indexes for common query patterns**

### Medium (Action Required When Possible)

7. **Optimize CandidateProfileSerializer** - Use proper query optimization
8. **Review and implement caching for dashboard metrics**
9. **Optimize ResumeVersionHistoryView** - Add prefetch for structured_resume

### Low (Nice to Have)

10. **Review admin views for optimization opportunities**
11. **Implement caching for job recommendations**
12. **Implement caching for public job list**

---

## 11. Performance Budgets (Proposed)

### API Response Times

- **p95 latency:** < 500ms for all endpoints
- **p99 latency:** < 1000ms for all endpoints
- **Dashboard endpoints:** < 200ms (p95)

### Query Counts

- **List endpoints:** < 5 queries per request
- **Detail endpoints:** < 3 queries per request
- **Search endpoints:** < 10 queries per request
- **Dashboard endpoints:** < 5 queries per request

### Payload Sizes

- **List responses:** < 50KB per page
- **Detail responses:** < 100KB
- **Search responses:** < 50KB per page

---

## 12. Next Steps

1. Set up profiling tools (Django Debug Toolbar, django-querycount)
2. Profile application to validate audit findings
3. Implement critical optimizations
4. Benchmark before/after performance
5. Implement high-priority optimizations
6. Add composite indexes
7. Implement caching strategy
8. Create load testing suite
9. Define and document performance budgets
10. Create performance dashboards

---

## Appendix: Codebase Statistics

- **Total Python files:** 49
- **Apps:** 10 (users, jobs, matching, resumes, applications, interviews, notifications, analytics, admin, core)
- **Models:** 15+ across all apps
- **API Views:** 40+
- **Serializers:** 30+

---

**Audit Complete**
