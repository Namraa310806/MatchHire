# Ranking Strategy
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document defines the ranking architecture for the MatchHire platform. Ranking determines the order of search results based on relevance to the user's query and context. The strategy includes multiple ranking signals, weighting strategies, and ranking algorithms for different use cases.

---

## Ranking Principles

1. **Relevance First:** Primary ranking based on query relevance
2. **Context Awareness:** Adjust ranking based on user context (role, preferences)
3. **Multi-Signal:** Combine multiple ranking signals for better results
4. **Configurable:** Weights adjustable per use case
5. **Explainable:** Ranking decisions should be transparent
6. **Performance:** Ranking algorithms must be fast (< 50ms)
7. **Fairness:** Avoid bias in ranking results

---

## Ranking Signals

### Text Relevance Signals

#### BM25 Score
- **Description:** Best Matching 25 algorithm for text relevance
- **Source:** Elasticsearch/OpenSearch BM25 calculation
- **Range:** 0-∞ (typically 0-20)
- **Normalization:** Sigmoid to 0-100
- **Weight:** High (1.0 - 2.0 depending on field)

#### Field Boosting
- **Description:** Boost specific fields higher than others
- **Example:** Title boosted 3x, description 1x
- **Source:** Query configuration
- **Range:** 1.0-3.0 multiplier
- **Weight:** Applied before BM25

#### Phrase Matching
- **Description:** Boost results with exact phrase matches
- **Source:** Phrase query analysis
- **Range:** Boolean (yes/no) or boost factor
- **Weight:** 1.5x boost for phrase matches

---

### Match Score Signals

#### Pre-Calculated Match Score
- **Description:** Candidate-job match score from JobMatch table
- **Source:** MatchingService.calculate_match()
- **Range:** 0-100
- **Components:**
  - Skills score (60%)
  - Experience score (30%)
  - Education score (10%)
- **Weight:** High (1.0 - 2.0)

#### Skill Overlap
- **Description:** Percentage of matching skills
- **Source:** Real-time skill comparison
- **Range:** 0-100
- **Calculation:** (matched_skills / total_required_skills) * 100
- **Weight:** Medium (0.5 - 1.0)

#### Experience Match
- **Description:** How well experience matches requirements
- **Source:** Experience comparison
- **Range:** 0-100
- **Calculation:** Based on years of experience vs requirements
- **Weight:** Medium (0.5 - 1.0)

---

### Temporal Signals

#### Recency
- **Description:** How recent the document was created/updated
- **Source:** created_at / updated_at fields
- **Range:** 0-100
- **Calculation:** Exponential decay based on age
- **Formula:** `100 * exp(-age_in_days / decay_constant)`
- **Decay Constant:** 30 days for jobs, 90 days for candidates
- **Weight:** Low to Medium (0.2 - 0.5)

#### Freshness
- **Description:** How recently the document was indexed
- **Source:** Index timestamp
- **Range:** 0-100
- **Calculation:** Linear decay over time
- **Weight:** Low (0.1 - 0.3)

---

### Popularity Signals

#### View Count
- **Description:** Number of times document was viewed
- **Source:** Analytics tracking
- **Range:** 0-∞
- **Normalization:** Logarithmic to 0-100
- **Weight:** Low (0.1 - 0.3)

#### Application Count (Jobs)
- **Description:** Number of applications received
- **Source:** Application table
- **Range:** 0-∞
- **Normalization:** Inverse (fewer applications = higher score)
- **Weight:** Low (0.1 - 0.3)

#### Match Count (Candidates)
- **Description:** Number of job matches
- **Source:** JobMatch table
- **Range:** 0-∞
- **Normalization:** Logarithmic to 0-100
- **Weight:** Low (0.1 - 0.3)

---

### Quality Signals

#### Profile Completeness (Candidates)
- **Description:** Percentage of profile fields filled
- **Source:** CandidateProfile analysis
- **Range:** 0-100
- **Calculation:** (filled_fields / total_fields) * 100
- **Weight:** Medium (0.3 - 0.5)

#### Resume Completeness (Resumes)
- **Description:** Percentage of resume sections filled
- **Source:** StructuredResume analysis
- **Range:** 0-100
- **Calculation:** (filled_sections / total_sections) * 100
- **Weight:** Medium (0.3 - 0.5)

#### Job Detail Completeness (Jobs)
- **Description:** Percentage of job fields filled
- **Source:** Job analysis
- **Range:** 0-100
- **Calculation:** (filled_fields / total_fields) * 100
- **Weight:** Medium (0.3 - 0.5)

#### Company Verification
- **Description:** Whether company is verified
- **Source:** RecruiterProfile.verified_company
- **Range:** Boolean (0 or 100)
- **Weight:** Medium (0.5 - 1.0)

---

### User Behavior Signals

#### Click-Through Rate
- **Description:** Percentage of searches that resulted in clicks
- **Source:** Search analytics
- **Range:** 0-100
- **Calculation:** (clicks / impressions) * 100
- **Weight:** Medium (0.3 - 0.5)

#### Position Clicks
- **Description:** Average position of clicks
- **Source:** Search analytics
- **Range:** 1-∞ (lower is better)
- **Normalization:** Inverse to 0-100
- **Weight:** Medium (0.3 - 0.5)

#### Dwell Time
- **Description:** Average time spent on result
- **Source:** Search analytics
- **Range:** 0-∞ seconds
- **Normalization:** Logarithmic to 0-100
- **Weight:** Low (0.1 - 0.3)

---

### Personalization Signals

#### User Preferences
- **Description:** Match with user's stated preferences
- **Source:** User profile settings
- **Range:** 0-100
- **Calculation:** Preference matching algorithm
- **Weight:** Medium (0.3 - 0.5)

#### Search History
- **Description:** Relevance based on past searches
- **Source:** Search query logs
- **Range:** 0-100
- **Calculation:** Similarity to past successful queries
- **Weight:** Low (0.2 - 0.4)

#### Location Proximity
- **Description:** Distance from user's location
- **Source:** Geo-location data
- **Range:** 0-100
- **Calculation:** Inverse distance decay
- **Weight:** Medium (0.3 - 0.5)

---

### Semantic Signals (Future)

#### Vector Similarity
- **Description:** Cosine similarity of embeddings
- **Source:** Vector embeddings
- **Range:** 0-1 (cosine similarity)
- **Normalization:** Multiply by 100
- **Weight:** High (1.0 - 2.0)

#### Semantic Relevance
- **Description:** ML-based relevance score
- **Source:** Learning-to-rank model
- **Range:** 0-100
- **Weight:** High (1.0 - 2.0)

---

## Ranking Strategies

### Strategy 1: BM25 Ranking (Default)

**Use Case:** General keyword search

**Signals:**
- BM25 score (weight: 1.0)
- Field boosting (applied before BM25)
- Recency (weight: 0.3)

**Formula:**
```
final_score = (bm25_score * 1.0) + (recency_score * 0.3)
```

**Configuration:**
```json
{
  "strategy": "bm25",
  "weights": {
    "bm25": 1.0,
    "recency": 0.3
  }
}
```

---

### Strategy 2: Match Score Ranking

**Use Case:** Candidate-job matching

**Signals:**
- Match score (weight: 1.0)
- Recency (weight: 0.2)
- Profile completeness (weight: 0.3)

**Formula:**
```
final_score = (match_score * 1.0) + (recency_score * 0.2) + (completeness_score * 0.3)
```

**Configuration:**
```json
{
  "strategy": "match_score",
  "weights": {
    "match_score": 1.0,
    "recency": 0.2,
    "completeness": 0.3
  }
}
```

---

### Strategy 3: Hybrid Ranking

**Use Case:** Advanced relevance with multiple signals

**Signals:**
- BM25 score (weight: 0.6)
- Match score (weight: 0.4)
- Recency (weight: 0.2)
- Popularity (weight: 0.1)
- Quality (weight: 0.2)

**Formula:**
```
final_score = (bm25_score * 0.6) + (match_score * 0.4) + (recency_score * 0.2) + (popularity_score * 0.1) + (quality_score * 0.2)
```

**Configuration:**
```json
{
  "strategy": "hybrid",
  "weights": {
    "bm25": 0.6,
    "match_score": 0.4,
    "recency": 0.2,
    "popularity": 0.1,
    "quality": 0.2
  }
}
```

---

### Strategy 4: Personalized Ranking

**Use Case:** Personalized search results

**Signals:**
- BM25 score (weight: 0.5)
- User preferences (weight: 0.3)
- Search history (weight: 0.2)
- Location proximity (weight: 0.2)

**Formula:**
```
final_score = (bm25_score * 0.5) + (preference_score * 0.3) + (history_score * 0.2) + (proximity_score * 0.2)
```

**Configuration:**
```json
{
  "strategy": "personalized",
  "weights": {
    "bm25": 0.5,
    "preferences": 0.3,
    "history": 0.2,
    "proximity": 0.2
  }
}
```

---

### Strategy 5: Semantic Ranking (Future)

**Use Case:** Semantic search with vector embeddings

**Signals:**
- Vector similarity (weight: 0.7)
- BM25 score (weight: 0.3)
- Recency (weight: 0.2)

**Formula:**
```
final_score = (vector_similarity * 0.7) + (bm25_score * 0.3) + (recency_score * 0.2)
```

**Configuration:**
```json
{
  "strategy": "semantic",
  "weights": {
    "vector_similarity": 0.7,
    "bm25": 0.3,
    "recency": 0.2
  }
}
```

---

### Strategy 6: Learning-to-Rank (Future)

**Use Case:** ML-based ranking optimization

**Signals:**
- ML model score (weight: 1.0)
- (Model internally combines all signals)

**Formula:**
```
final_score = ml_model_score
```

**Configuration:**
```json
{
  "strategy": "learning_to_rank",
  "model": "xgboost_ranking_v1",
  "weights": {
    "model_score": 1.0
  }
}
```

---

## Entity-Specific Ranking

### Candidate Ranking

**Primary Strategy:** Hybrid Ranking

**Signals:**
- BM25 score (weight: 0.5)
- Match score (context-dependent, weight: 0.5)
- Profile completeness (weight: 0.3)
- Recency (weight: 0.2)
- Activity score (weight: 0.2)

**Configuration:**
```json
{
  "entity": "candidate",
  "strategy": "hybrid",
  "weights": {
    "bm25": 0.5,
    "match_score": 0.5,
    "completeness": 0.3,
    "recency": 0.2,
    "activity": 0.2
  }
}
```

---

### Resume Ranking

**Primary Strategy:** Hybrid Ranking

**Signals:**
- BM25 score (weight: 0.6)
- Skill overlap (weight: 0.4)
- Experience match (weight: 0.3)
- Resume completeness (weight: 0.3)
- Recency (weight: 0.2)

**Configuration:**
```json
{
  "entity": "resume",
  "strategy": "hybrid",
  "weights": {
    "bm25": 0.6,
    "skill_overlap": 0.4,
    "experience_match": 0.3,
    "completeness": 0.3,
    "recency": 0.2
  }
}
```

---

### Job Ranking

**Primary Strategy:** Hybrid Ranking

**Signals:**
- BM25 score (weight: 0.6)
- Match score (context-dependent, weight: 0.5)
- Recency (weight: 0.4)
- Salary competitiveness (weight: 0.2)
- Company verification (weight: 0.3)
- Application count (inverse, weight: 0.1)

**Configuration:**
```json
{
  "entity": "job",
  "strategy": "hybrid",
  "weights": {
    "bm25": 0.6,
    "match_score": 0.5,
    "recency": 0.4,
    "salary_competitiveness": 0.2,
    "company_verification": 0.3,
    "application_count": -0.1
  }
}
```

---

### Company Ranking

**Primary Strategy:** Popularity-Based Ranking

**Signals:**
- BM25 score (weight: 0.5)
- Active jobs count (weight: 0.4)
- Company verification (weight: 0.5)
- Recency (weight: 0.2)

**Configuration:**
```json
{
  "entity": "company",
  "strategy": "popularity",
  "weights": {
    "bm25": 0.5,
    "active_jobs": 0.4,
    "verification": 0.5,
    "recency": 0.2
  }
}
```

---

### Recruiter Ranking

**Primary Strategy:** Activity-Based Ranking

**Signals:**
- BM25 score (weight: 0.5)
- Active jobs count (weight: 0.4)
- Company verification (weight: 0.5)
- Recency (weight: 0.2)

**Configuration:**
```json
{
  "entity": "recruiter",
  "strategy": "activity",
  "weights": {
    "bm25": 0.5,
    "active_jobs": 0.4,
    "verification": 0.5,
    "recency": 0.2
  }
}
```

---

### Skill Ranking

**Primary Strategy:** Popularity-Based Ranking

**Signals:**
- BM25 score (weight: 0.3)
- Popularity score (weight: 0.6)
- Trendiness (weight: 0.4)

**Configuration:**
```json
{
  "entity": "skill",
  "strategy": "popularity",
  "weights": {
    "bm25": 0.3,
    "popularity": 0.6,
    "trendiness": 0.4
  }
}
```

---

### Application Ranking

**Primary Strategy:** Status-Based Ranking

**Signals:**
- Match score (weight: 1.0)
- Status priority (weight: 0.5)
- Recency (weight: 0.3)

**Status Priority:**
- Hired: 100
- Shortlisted: 80
- Under Review: 60
- Submitted: 40
- Rejected: 0

**Configuration:**
```json
{
  "entity": "application",
  "strategy": "status_priority",
  "weights": {
    "match_score": 1.0,
    "status_priority": 0.5,
    "recency": 0.3
  }
}
```

---

### Interview Ranking

**Primary Strategy:** Urgency-Based Ranking

**Signals:**
- Urgency (weight: 1.0)
- Status priority (weight: 0.5)

**Urgency Calculation:**
- Scheduled within 24 hours: 100
- Scheduled within 3 days: 80
- Scheduled within 7 days: 60
- Scheduled within 30 days: 40
- Scheduled > 30 days: 20

**Status Priority:**
- Scheduled: 100
- Completed: 60
- Cancelled: 20
- No Show: 0

**Configuration:**
```json
{
  "entity": "interview",
  "strategy": "urgency",
  "weights": {
    "urgency": 1.0,
    "status_priority": 0.5
  }
}
```

---

## Ranking Algorithm Implementation

### Score Normalization

All signals are normalized to 0-100 range before weighting.

#### Linear Normalization
```
normalized_score = (value - min) / (max - min) * 100
```

#### Logarithmic Normalization
```
normalized_score = log(value + 1) / log(max + 1) * 100
```

#### Sigmoid Normalization
```
normalized_score = 100 / (1 + exp(-k * (value - x0)))
```

#### Inverse Normalization
```
normalized_score = 100 - (value / max * 100)
```

---

### Score Combination

#### Weighted Sum
```
final_score = sum(signal_score * signal_weight for all signals)
```

#### Weighted Average
```
final_score = sum(signal_score * signal_weight for all signals) / sum(signal_weights)
```

#### Reciprocal Rank Fusion (RRF)
```
final_score = sum(1 / (k + rank) for all ranking sources)
```

#### Max Pooling
```
final_score = max(signal_scores)
```

---

### Ranking Pipeline

```
1. Calculate individual signal scores
   ↓
2. Normalize signal scores to 0-100
   ↓
3. Apply weights to normalized scores
   ↓
4. Combine weighted scores
   ↓
5. Apply final normalization
   ↓
6. Sort by final score
   ↓
7. Return ranked results
```

---

## Ranking Configuration

### Default Configuration
```python
# settings.py
RANKING_CONFIG = {
    "default_strategy": "hybrid",
    "strategies": {
        "bm25": {
            "weights": {
                "bm25": 1.0,
                "recency": 0.3
            }
        },
        "match_score": {
            "weights": {
                "match_score": 1.0,
                "recency": 0.2,
                "completeness": 0.3
            }
        },
        "hybrid": {
            "weights": {
                "bm25": 0.6,
                "match_score": 0.4,
                "recency": 0.2,
                "popularity": 0.1,
                "quality": 0.2
            }
        }
    },
    "entity_strategies": {
        "candidate": "hybrid",
        "resume": "hybrid",
        "job": "hybrid",
        "company": "popularity",
        "recruiter": "activity",
        "skill": "popularity",
        "application": "status_priority",
        "interview": "urgency"
    }
}
```

---

## Ranking Explainability

### Explanation Format
```json
{
  "document_id": "uuid",
  "final_score": 85.5,
  "signal_scores": {
    "bm25": 60.0,
    "match_score": 80.0,
    "recency": 70.0,
    "completeness": 90.0
  },
  "signal_weights": {
    "bm25": 0.6,
    "match_score": 0.4,
    "recency": 0.2,
    "completeness": 0.3
  },
  "weighted_scores": {
    "bm25": 36.0,
    "match_score": 32.0,
    "recency": 14.0,
    "completeness": 27.0
  },
  "ranking_strategy": "hybrid"
}
```

### API Endpoint
```
GET /api/search/candidates?q=Python&explain=true
```

---

## Ranking Performance

### Performance Targets
- **Ranking Latency:** < 50ms (p95)
- **Signal Calculation:** < 10ms per signal
- **Score Combination:** < 5ms
- **Total Ranking Time:** < 50ms

### Optimization Strategies
- **Pre-calculation:** Pre-calculate expensive signals (match scores, completeness)
- **Caching:** Cache signal scores for frequently accessed documents
- **Parallel Calculation:** Calculate signals in parallel
- **Early Termination:** Skip low-priority signals for low-relevance results

---

## Ranking A/B Testing

### Test Metrics
- **Click-Through Rate (CTR):** Percentage of searches with clicks
- **Dwell Time:** Average time spent on results
- **Zero-Result Rate:** Percentage of searches with no results
- **User Satisfaction:** Post-search surveys

### Test Framework
- **Control Group:** Current ranking strategy
- **Test Group:** New ranking strategy
- **Traffic Split:** 50/50 (configurable)
- **Duration:** 1-4 weeks depending on traffic

---

## Ranking Monitoring

### Metrics to Track
- **Signal Distribution:** Distribution of individual signal scores
- **Weight Effectiveness:** Impact of each weight on final ranking
- **Strategy Performance:** Performance of each ranking strategy
- **User Feedback:** User ratings of search results

### Alerts
- **Zero-Result Rate > 10%:** Alert on poor ranking
- **CTR < 15%:** Alert on poor relevance
- **Ranking Latency > 100ms:** Alert on performance degradation

---

## Summary

The ranking strategy defines:

1. **8 Categories of Ranking Signals:**
   - Text relevance (BM25, field boosting, phrase matching)
   - Match score (pre-calculated, skill overlap, experience match)
   - Temporal (recency, freshness)
   - Popularity (view count, application count, match count)
   - Quality (completeness, verification)
   - User behavior (CTR, position clicks, dwell time)
   - Personalization (preferences, history, location)
   - Semantic (vector similarity, ML relevance)

2. **6 Ranking Strategies:**
   - BM25 (default)
   - Match Score
   - Hybrid
   - Personalized
   - Semantic (future)
   - Learning-to-Rank (future)

3. **Entity-Specific Rankings:**
   - Candidate: Hybrid
   - Resume: Hybrid
   - Job: Hybrid
   - Company: Popularity-based
   - Recruiter: Activity-based
   - Skill: Popularity-based
   - Application: Status-based
   - Interview: Urgency-based

4. **Implementation Details:**
   - Score normalization methods
   - Score combination methods
   - Ranking pipeline
   - Configuration format
   - Explainability format
   - Performance targets
   - A/B testing framework
   - Monitoring and alerts

The ranking strategy is designed to be configurable, performant, and explainable, with clear paths for future enhancements including semantic search and ML-based ranking.
