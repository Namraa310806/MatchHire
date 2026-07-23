# Recommendation Architecture
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines the recommendation architecture for the MatchHire platform. Recommendations go beyond search by proactively suggesting relevant items to users based on their profile, behavior, and preferences. The architecture supports multiple recommendation types including candidate recommendations, job recommendations, similar items, and trending/popular content.

---

## Recommendation Types

### 1. Candidate Recommendations for Jobs

**Description:** Recommend candidates to recruiters for their job postings.

**Use Case:** Recruiter views a job and sees recommended candidates.

**Input:**
- Job ID
- Recruiter ID (for access control)
- Context (filters, preferences)

**Output:** List of candidate IDs with recommendation scores.

**Strategy:** Content-based filtering using match scores.

---

### 2. Job Recommendations for Candidates

**Description:** Recommend jobs to candidates based on their profile and resume.

**Use Case:** Candidate sees recommended jobs on dashboard.

**Input:**
- Candidate ID
- Context (location preferences, salary expectations, remote preference)

**Output:** List of job IDs with recommendation scores.

**Strategy:** Content-based filtering using match scores.

---

### 3. Similar Candidates

**Description:** Find candidates similar to a given candidate.

**Use Case:** Recruiter sees a candidate and wants to find similar candidates.

**Input:**
- Candidate ID
- Context (filters)

**Output:** List of similar candidate IDs with similarity scores.

**Strategy:** Content-based filtering using skill/experience similarity.

---

### 4. Similar Jobs

**Description:** Find jobs similar to a given job.

**Use Case:** Candidate views a job and sees similar jobs.

**Input:**
- Job ID
- Context (location, salary range)

**Output:** List of similar job IDs with similarity scores.

**Strategy:** Content-based filtering using title/skills/location similarity.

---

### 5. Related Skills

**Description:** Find skills related to a given skill.

**Use Case:** Candidate views a skill and sees related skills to learn.

**Input:**
- Skill ID or skill name
- Context (category, type)

**Output:** List of related skill IDs with relationship scores.

**Strategy:** Co-occurrence analysis or skill taxonomy.

---

### 6. Trending Skills

**Description:** Identify skills that are trending in popularity.

**Use Case:** Candidate sees trending skills to learn for better job prospects.

**Input:**
- Time window (7 days, 30 days, 90 days)
- Context (category, location)

**Output:** List of skill IDs with trend scores.

**Strategy:** Time-series analysis of skill mentions in jobs/resumes.

---

### 7. Popular Searches

**Description:** Identify popular search queries.

**Use Case:** Candidate sees popular searches to discover job opportunities.

**Input:**
- Time window (7 days, 30 days)
- Context (entity type, user role)

**Output:** List of search queries with frequency counts.

**Strategy:** Query log analysis.

---

## Recommendation Strategies

### Strategy 1: Content-Based Filtering

**Description:** Recommend items similar to items the user has interacted with or based on their profile.

**Algorithm:**
1. Extract features from user profile/item
2. Calculate similarity between user/item and candidate items
3. Rank by similarity score
4. Apply filters and return top N

**Similarity Metrics:**
- Cosine similarity (for vector embeddings)
- Jaccard similarity (for skill sets)
- Euclidean distance (for numeric features)
- Hamming distance (for categorical features)

**Use Cases:**
- Similar candidates
- Similar jobs
- Related skills

**Pros:**
- No cold start problem for items
- Transparent recommendations
- Easy to implement

**Cons:**
- Limited to known features
- No serendipity (only similar items)
- Cold start for new users

---

### Strategy 2: Collaborative Filtering

**Description:** Recommend items based on user behavior patterns.

**Algorithm:**
1. Build user-item interaction matrix
2. Calculate user-user or item-item similarity
3. Recommend items liked by similar users
4. Rank by predicted rating

**Approaches:**
- User-based: Find similar users, recommend their items
- Item-based: Find similar items, recommend items similar to liked items
- Matrix Factorization: SVD, ALS for latent factors

**Use Cases:**
- Job recommendations (future)
- Candidate recommendations (future)

**Pros:**
- Can discover unexpected items
- Improves with more data
- No feature engineering required

**Cons:**
- Cold start problem for new users/items
- Sparsity problem (limited interactions)
- Scalability challenges

---

### Strategy 3: Hybrid Filtering

**Description:** Combine content-based and collaborative filtering.

**Algorithm:**
1. Generate content-based recommendations
2. Generate collaborative filtering recommendations
3. Combine scores (weighted average, rank fusion)
4. Apply final ranking

**Combination Methods:**
- Weighted average: `score = w1 * content_score + w2 * cf_score`
- Rank fusion: `score = 1 / (k + rank_content) + 1 / (k + rank_cf)`
- Cascade: Content-based first, then CF for remaining slots

**Use Cases:**
- Job recommendations (future)
- Candidate recommendations (future)

**Pros:**
- Addresses cold start problem
- Combines strengths of both approaches
- Better accuracy than individual approaches

**Cons:**
- More complex to implement
- Requires tuning of combination weights
- Higher computational cost

---

### Strategy 4: Match Score-Based

**Description:** Use pre-calculated match scores from JobMatch table.

**Algorithm:**
1. Query JobMatch table for candidate-job pairs
2. Filter by job status (active)
3. Sort by match_score
4. Return top N

**Use Cases:**
- Candidate recommendations (current implementation)
- Recruiter candidates (current implementation)

**Pros:**
- Fast (pre-calculated)
- Accurate (deterministic)
- Simple to implement

**Cons:**
- Limited to candidate-job pairs
- Requires match calculation for all pairs
- No personalization beyond match score

---

### Strategy 5: Vector Similarity

**Description:** Use vector embeddings for semantic similarity.

**Algorithm:**
1. Generate embeddings for items
2. Calculate cosine similarity between query embedding and candidate embeddings
3. Rank by similarity score
4. Return top N

**Embedding Models:**
- Sentence-BERT (SBERT)
- OpenAI embeddings
- Cohere embeddings
- Custom trained models

**Use Cases:**
- Similar candidates (future)
- Similar jobs (future)
- Related skills (future)

**Pros:**
- Captures semantic meaning
- Handles synonyms and related concepts
- State-of-the-art performance

**Cons:**
- Requires embedding generation
- Computational cost
- Model maintenance

---

### Strategy 6: Trend Analysis

**Description:** Identify trending items based on temporal patterns.

**Algorithm:**
1. Track item mentions/interactions over time
2. Calculate growth rate
3. Identify items with significant growth
4. Rank by trend score

**Trend Metrics:**
- Growth rate: `(current - previous) / previous`
- Momentum: Weighted growth rate over time windows
- Velocity: Rate of change

**Use Cases:**
- Trending skills
- Popular searches

**Pros:**
- Identifies emerging trends
- Time-aware recommendations
- Simple to implement

**Cons:**
- Requires historical data
- May be noisy
- Limited to trending items

---

## Recommendation Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recommendation API Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Candidate    │  │ Job          │  │ Similar      │         │
│  │ Recomm View  │  │ Recomm View  │  │ Items View   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Related      │  │ Trending     │  │ Popular      │         │
│  │ Skills View  │  │ Skills View  │  │ Searches View│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Recommendation Service Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Content-Based│  │ Collaborative│  │ Hybrid       │         │
│  │ Recomm Service│  │ Filter Service│  │ Recomm Service│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Match Score  │  │ Vector       │  │ Trend        │         │
│  │ Recomm Service│  │ Similarity   │  │ Analysis     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ JobMatch     │  │ Vector DB    │  │ Query Logs   │         │
│  │ Table        │  │ (Embeddings) │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Search Index │  │ Cache        │  │ Analytics DB │         │
│  │ (ES/OS)      │  │ (Redis)      │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommendation Algorithms

### Algorithm 1: Candidate Recommendations for Jobs

**Current Implementation:**
```python
def get_candidate_recommendations(job_id: str, limit: int = 20) -> List[JobMatch]:
    return JobMatch.objects.filter(
        job_id=job_id,
        job__status=Job.JobStatus.ACTIVE
    ).select_related("candidate", "job").order_by("-match_score", "-calculated_at")[:limit]
```

**Future Enhancement (Content-Based):**
```python
def get_candidate_recommendations_enhanced(
    job_id: str,
    candidate_id: str = None,
    filters: Dict = None,
    limit: int = 20
) -> List[Recommendation]:
    # 1. Get job features
    job = get_job_features(job_id)
    
    # 2. Get candidate features (if context provided)
    context_features = get_candidate_features(candidate_id) if candidate_id else None
    
    # 3. Search for candidates with similar skills
    candidates = search_candidates_by_skills(job.required_skills)
    
    # 4. Calculate similarity scores
    for candidate in candidates:
        score = calculate_candidate_job_similarity(candidate, job, context_features)
        candidate.recommendation_score = score
    
    # 5. Apply filters
    if filters:
        candidates = apply_filters(candidates, filters)
    
    # 6. Sort and return
    return sorted(candidates, key=lambda x: x.recommendation_score, reverse=True)[:limit]
```

---

### Algorithm 2: Job Recommendations for Candidates

**Current Implementation:**
```python
def get_job_recommendations(candidate_id: str, limit: int = 20) -> List[JobMatch]:
    return JobMatch.objects.filter(
        candidate_id=candidate_id,
        job__status=Job.JobStatus.ACTIVE
    ).select_related("job", "job__recruiter").order_by("-match_score", "-calculated_at")[:limit]
```

**Future Enhancement (Personalized):**
```python
def get_job_recommendations_enhanced(
    candidate_id: str,
    preferences: Dict = None,
    limit: int = 20
) -> List[Recommendation]:
    # 1. Get candidate profile and resume
    candidate = get_candidate_profile(candidate_id)
    resume = get_candidate_resume(candidate_id)
    
    # 2. Extract candidate features
    skills = extract_skills(resume)
    experience = extract_experience(resume)
    location = candidate.location
    
    # 3. Apply user preferences
    if preferences:
        filters = build_filters_from_preferences(preferences)
    else:
        filters = {}
    
    # 4. Search for matching jobs
    jobs = search_jobs(
        skills=skills,
        experience_level=map_experience(experience),
        location=location,
        filters=filters
    )
    
    # 5. Calculate match scores
    for job in jobs:
        score = calculate_job_match_score(candidate, job)
        job.recommendation_score = score
    
    # 6. Apply personalization boost
    if preferences:
        jobs = apply_personalization_boost(jobs, preferences)
    
    # 7. Sort and return
    return sorted(jobs, key=lambda x: x.recommendation_score, reverse=True)[:limit]
```

---

### Algorithm 3: Similar Candidates

**Implementation:**
```python
def get_similar_candidates(
    candidate_id: str,
    filters: Dict = None,
    limit: int = 10
) -> List[SimilarityResult]:
    # 1. Get source candidate features
    source_candidate = get_candidate_profile(candidate_id)
    source_resume = get_candidate_resume(candidate_id)
    source_skills = extract_skills(source_resume)
    
    # 2. Search for candidates with overlapping skills
    candidates = search_candidates_by_skills(source_skills[:5])  # Top 5 skills
    
    # 3. Calculate similarity scores
    results = []
    for candidate in candidates:
        if candidate.id == candidate_id:
            continue
        
        candidate_resume = get_candidate_resume(candidate.id)
        candidate_skills = extract_skills(candidate_resume)
        
        # Skill overlap (Jaccard similarity)
        skill_overlap = len(set(source_skills) & set(candidate_skills)) / len(set(source_skills) | set(candidate_skills))
        
        # Experience similarity
        exp_similarity = 1 - abs(source_candidate.years_of_experience - candidate.years_of_experience) / 10
        
        # Location similarity
        loc_similarity = 1 if source_candidate.location == candidate.location else 0
        
        # Combined score
        score = (skill_overlap * 0.6) + (exp_similarity * 0.3) + (loc_similarity * 0.1)
        
        results.append(SimilarityResult(
            candidate_id=candidate.id,
            similarity_score=score,
            skill_overlap=skill_overlap,
            shared_skills=list(set(source_skills) & set(candidate_skills))
        ))
    
    # 4. Apply filters
    if filters:
        results = apply_filters(results, filters)
    
    # 5. Sort and return
    return sorted(results, key=lambda x: x.similarity_score, reverse=True)[:limit]
```

---

### Algorithm 4: Similar Jobs

**Implementation:**
```python
def get_similar_jobs(
    job_id: str,
    filters: Dict = None,
    limit: int = 10
) -> List[SimilarityResult]:
    # 1. Get source job features
    source_job = get_job(job_id)
    source_skills = extract_skills(source_job.requirements)
    
    # 2. Search for jobs with similar requirements
    jobs = search_jobs_by_skills(source_skills[:5])  # Top 5 skills
    
    # 3. Calculate similarity scores
    results = []
    for job in jobs:
        if job.id == job_id:
            continue
        
        job_skills = extract_skills(job.requirements)
        
        # Skill overlap (Jaccard similarity)
        skill_overlap = len(set(source_skills) & set(job_skills)) / len(set(source_skills) | set(job_skills))
        
        # Title similarity (Levenshtein distance)
        title_similarity = calculate_string_similarity(source_job.title, job.title)
        
        # Location similarity
        loc_similarity = 1 if source_job.location == job.location else 0
        
        # Employment type similarity
        type_similarity = 1 if source_job.employment_type == job.employment_type else 0
        
        # Combined score
        score = (skill_overlap * 0.5) + (title_similarity * 0.2) + (loc_similarity * 0.2) + (type_similarity * 0.1)
        
        results.append(SimilarityResult(
            job_id=job.id,
            similarity_score=score,
            skill_overlap=skill_overlap,
            shared_skills=list(set(source_skills) & set(job_skills))
        ))
    
    # 4. Apply filters
    if filters:
        results = apply_filters(results, filters)
    
    # 5. Sort and return
    return sorted(results, key=lambda x: x.similarity_score, reverse=True)[:limit]
```

---

### Algorithm 5: Related Skills

**Implementation:**
```python
def get_related_skills(
    skill_name: str,
    context: Dict = None,
    limit: int = 10
) -> List[RelatedSkill]:
    # 1. Get source skill
    source_skill = get_skill(skill_name)
    
    # 2. Find skills that co-occur with source skill
    # Co-occurrence in resumes
    resume_cooccurrence = get_skill_cooccurrence_in_resumes(skill_name)
    # Co-occurrence in jobs
    job_cooccurrence = get_skill_cooccurrence_in_jobs(skill_name)
    
    # 3. Combine co-occurrence scores
    cooccurrence_scores = {}
    for skill, count in resume_cooccurrence.items():
        cooccurrence_scores[skill] = cooccurrence_scores.get(skill, 0) + count * 0.6
    for skill, count in job_cooccurrence.items():
        cooccurrence_scores[skill] = cooccurrence_scores.get(skill, 0) + count * 0.4
    
    # 4. Normalize scores
    max_score = max(cooccurrence_scores.values()) if cooccurrence_scores else 1
    for skill in cooccurrence_scores:
        cooccurrence_scores[skill] /= max_score
    
    # 5. Apply context filters
    if context and context.get('category'):
        cooccurrence_scores = {k: v for k, v in cooccurrence_scores.items() if get_skill_category(k) == context['category']}
    
    # 6. Sort and return
    related_skills = sorted(
        cooccurrence_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [RelatedSkill(name=skill, score=score) for skill, score in related_skills]
```

---

### Algorithm 6: Trending Skills

**Implementation:**
```python
def get_trending_skills(
    time_window: str = "30d",
    context: Dict = None,
    limit: int = 10
) -> List[TrendingSkill]:
    # 1. Calculate time window
    end_date = datetime.now()
    start_date = end_date - timedelta(days=parse_time_window(time_window))
    
    # 2. Get skill mentions in jobs over time window
    job_mentions = get_skill_mentions_in_jobs(start_date, end_date)
    
    # 3. Get skill mentions in previous period for comparison
    previous_start = start_date - timedelta(days=parse_time_window(time_window))
    previous_mentions = get_skill_mentions_in_jobs(previous_start, start_date)
    
    # 4. Calculate growth rate
    trend_scores = {}
    for skill in job_mentions:
        current_count = job_mentions[skill]
        previous_count = previous_mentions.get(skill, 0)
        
        if previous_count > 0:
            growth_rate = (current_count - previous_count) / previous_count
        else:
            growth_rate = current_count  # New skill
        
        trend_scores[skill] = growth_rate
    
    # 5. Apply minimum threshold (at least 5 mentions)
    trend_scores = {k: v for k, v in trend_scores.items() if job_mentions[k] >= 5}
    
    # 6. Apply context filters
    if context and context.get('category'):
        trend_scores = {k: v for k, v in trend_scores.items() if get_skill_category(k) == context['category']}
    
    # 7. Sort and return
    trending_skills = sorted(
        trend_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [TrendingSkill(name=skill, growth_rate=rate, mentions=job_mentions[skill]) for skill, rate in trending_skills]
```

---

### Algorithm 7: Popular Searches

**Implementation:**
```python
def get_popular_searches(
    time_window: str = "7d",
    context: Dict = None,
    limit: int = 10
) -> List[PopularSearch]:
    # 1. Calculate time window
    end_date = datetime.now()
    start_date = end_date - timedelta(days=parse_time_window(time_window))
    
    # 2. Get search queries from query logs
    search_queries = get_search_queries(start_date, end_date)
    
    # 3. Count query frequency
    query_counts = Counter(search_queries)
    
    # 4. Apply context filters
    if context and context.get('entity_type'):
        query_counts = {k: v for k, v inquery_counts.items() if get_query_entity_type(k) == context['entity_type']}
    
    # 5. Sort and return
    popular_searches = query_counts.most_common(limit)
    
    return [PopularSearch(query=query, count=count) for query, count in popular_searches]
```

---

## API Endpoints

### Candidate Recommendations

**Endpoint:** `GET /api/v1/recommendations/candidates`

**Authentication:** Required (Recruiter only)

**Query Parameters:**
- `job_id` - Job ID (required)
- `limit` - Number of recommendations (default: 20, max: 50)
- `strategy` - Recommendation strategy (match_score, content_based, hybrid)

**Example Request:**
```
GET /api/v1/recommendations/candidates?job_id=uuid&limit=20&strategy=match_score
```

**Response Structure:**
```json
{
  "results": [
    {
      "candidate_id": "uuid",
      "candidate_name": "John Doe",
      "match_score": 85.5,
      "recommendation_score": 85.5,
      "matched_skills": ["Python", "Django"],
      "missing_skills": ["PostgreSQL"],
      "experience_years": 5,
      "recommendation_reason": "High skill match (85%)"
    }
  ],
  "job_id": "uuid",
  "job_title": "Senior Python Developer",
  "strategy": "match_score",
  "total": 150,
  "limit": 20
}
```

---

### Job Recommendations

**Endpoint:** `GET /api/v1/recommendations/jobs`

**Authentication:** Required (Candidate only)

**Query Parameters:**
- `candidate_id` - Candidate ID (optional, defaults to current user)
- `limit` - Number of recommendations (default: 20, max: 50)
- `strategy` - Recommendation strategy (match_score, personalized, hybrid)

**Example Request:**
```
GET /api/v1/recommendations/jobs?limit=20&strategy=personalized
```

**Response Structure:**
```json
{
  "results": [
    {
      "job_id": "uuid",
      "job_title": "Senior Python Developer",
      "company_name": "Tech Corp",
      "match_score": 85.5,
      "recommendation_score": 85.5,
      "location": "San Francisco, CA",
      "salary_min": 120000,
      "salary_max": 180000,
      "recommendation_reason": "High match with your skills"
    }
  ],
  "candidate_id": "uuid",
  "strategy": "personalized",
  "total": 75,
  "limit": 20
}
```

---

### Similar Candidates

**Endpoint:** `GET /api/v1/recommendations/similar-candidates`

**Authentication:** Required (Recruiter only)

**Query Parameters:**
- `candidate_id` - Candidate ID (required)
- `limit` - Number of similar candidates (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/recommendations/similar-candidates?candidate_id=uuid&limit=10
```

**Response Structure:**
```json
{
  "results": [
    {
      "candidate_id": "uuid",
      "candidate_name": "Jane Smith",
      "similarity_score": 0.85,
      "skill_overlap": 0.9,
      "shared_skills": ["Python", "Django", "PostgreSQL"],
      "years_of_experience": 5
    }
  ],
  "source_candidate_id": "uuid",
  "source_candidate_name": "John Doe",
  "total": 50,
  "limit": 10
}
```

---

### Similar Jobs

**Endpoint:** `GET /api/v1/recommendations/similar-jobs`

**Authentication:** Required (Candidate only)

**Query Parameters:**
- `job_id` - Job ID (required)
- `limit` - Number of similar jobs (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/recommendations/similar-jobs?job_id=uuid&limit=10
```

**Response Structure:**
```json
{
  "results": [
    {
      "job_id": "uuid",
      "job_title": "Python Backend Developer",
      "company_name": "Startup Inc",
      "similarity_score": 0.85,
      "skill_overlap": 0.8,
      "shared_skills": ["Python", "Django"],
      "location": "San Francisco, CA"
    }
  ],
  "source_job_id": "uuid",
  "source_job_title": "Senior Python Developer",
  "total": 30,
  "limit": 10
}
```

---

### Related Skills

**Endpoint:** `GET /api/v1/recommendations/related-skills`

**Authentication:** Required (all roles)

**Query Parameters:**
- `skill` - Skill name (required)
- `limit` - Number of related skills (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/recommendations/related-skills?skill=Python&limit=10
```

**Response Structure:**
```json
{
  "results": [
    {
      "skill_name": "Django",
      "relationship_score": 0.9,
      "cooccurrence_count": 500
    },
    {
      "skill_name": "Flask",
      "relationship_score": 0.8,
      "cooccurrence_count": 350
    }
  ],
  "source_skill": "Python",
  "total": 25,
  "limit": 10
}
```

---

### Trending Skills

**Endpoint:** `GET /api/v1/recommendations/trending-skills`

**Authentication:** Required (all roles)

**Query Parameters:**
- `time_window` - Time window (7d, 30d, 90d, default: 30d)
- `limit` - Number of trending skills (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/recommendations/trending-skills?time_window=30d&limit=10
```

**Response Structure:**
```json
{
  "results": [
    {
      "skill_name": "Rust",
      "growth_rate": 2.5,
      "current_mentions": 150,
      "previous_mentions": 60
    },
    {
      "skill_name": "Go",
      "growth_rate": 1.8,
      "current_mentions": 200,
      "previous_mentions": 110
    }
  ],
  "time_window": "30d",
  "total": 50,
  "limit": 10
}
```

---

### Popular Searches

**Endpoint:** `GET /api/v1/recommendations/popular-searches`

**Authentication:** Required (all roles)

**Query Parameters:**
- `time_window` - Time window (7d, 30d, default: 7d)
- `limit` - Number of popular searches (default: 10, max: 50)

**Example Request:**
```
GET /api/v1/recommendations/popular-searches?time_window=7d&limit=10
```

**Response Structure:**
```json
{
  "results": [
    {
      "query": "Python developer",
      "count": 500,
      "entity_type": "job"
    },
    {
      "query": "remote software engineer",
      "count": 350,
      "entity_type": "job"
    }
  ],
  "time_window": "7d",
  "total": 100,
  "limit": 10
}
```

---

## Caching Strategy

### Cache Keys
- `recommendations:candidates:{job_id}:{strategy}` - Candidate recommendations for job
- `recommendations:jobs:{candidate_id}:{strategy}` - Job recommendations for candidate
- `recommendations:similar_candidates:{candidate_id}` - Similar candidates
- `recommendations:similar_jobs:{job_id}` - Similar jobs
- `recommendations:related_skills:{skill_name}` - Related skills
- `recommendations:trending_skills:{time_window}` - Trending skills
- `recommendations:popular_searches:{time_window}` - Popular searches

### Cache TTL
- Candidate recommendations: 5 minutes
- Job recommendations: 5 minutes
- Similar candidates: 10 minutes
- Similar jobs: 10 minutes
- Related skills: 1 hour
- Trending skills: 15 minutes
- Popular searches: 15 minutes

### Cache Invalidation
- On job update: Invalidate candidate recommendations for that job
- On candidate profile update: Invalidate job recommendations for that candidate
- On resume update: Invalidate job recommendations and similar candidates
- On skill data update: Invalidate related skills and trending skills

---

## Performance Optimization

### Pre-computation
- Pre-compute match scores for all candidate-job pairs (current implementation)
- Pre-compute skill co-occurrence matrix daily
- Pre-compute trending skills hourly

### Batch Processing
- Batch recommendation generation for all users (nightly)
- Batch similarity calculations for all items (weekly)

### Lazy Loading
- Generate recommendations on first request
- Cache results for subsequent requests

### Parallel Processing
- Calculate similarities in parallel
- Use Celery for background recommendation generation

---

## Evaluation Metrics

### Offline Metrics
- **Precision@K:** Percentage of relevant recommendations in top K
- **Recall@K:** Percentage of relevant items found in top K
- **NDCG@K:** Normalized discounted cumulative gain
- **MAP:** Mean average precision
- **AUC:** Area under ROC curve

### Online Metrics
- **Click-Through Rate (CTR):** Percentage of recommendations clicked
- **Conversion Rate:** Percentage of recommendations that led to action (apply, hire)
- **Dwell Time:** Time spent viewing recommendations
- **User Satisfaction:** Post-recommendation surveys

---

## Summary

The recommendation architecture defines:

1. **7 Recommendation Types:**
   - Candidate recommendations for jobs
   - Job recommendations for candidates
   - Similar candidates
   - Similar jobs
   - Related skills
   - Trending skills
   - Popular searches

2. **6 Recommendation Strategies:**
   - Content-based filtering
   - Collaborative filtering
   - Hybrid filtering
   - Match score-based (current)
   - Vector similarity (future)
   - Trend analysis

3. **7 Recommendation Algorithms:**
   - Candidate recommendations (current + enhanced)
   - Job recommendations (current + enhanced)
   - Similar candidates
   - Similar jobs
   - Related skills
   - Trending skills
   - Popular searches

4. **7 API Endpoints:**
   - Candidate recommendations
   - Job recommendations
   - Similar candidates
   - Similar jobs
   - Related skills
   - Trending skills
   - Popular searches

5. **Additional Features:**
   - Caching strategy
   - Performance optimization
   - Evaluation metrics
   - Cache invalidation

The recommendation architecture is designed to be extensible, supporting current match score-based recommendations while providing a clear path to advanced content-based, collaborative filtering, and vector similarity approaches.
