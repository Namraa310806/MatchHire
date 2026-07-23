# Signal Reference

## Overview

Ranking signals are reusable scoring components that calculate scores for documents based on specific criteria. Each signal implements a consistent interface and can be combined in the ranking pipeline.

## Signal Interface

All signals extend `BaseSignal` and implement:

```python
class BaseSignal(ABC):
    @property
    def signal_type(self) -> SignalType:
        """Return the signal type."""
        pass
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate score for a document."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if signal is enabled."""
        pass
    
    def get_weight(self) -> float:
        """Get the signal weight."""
        pass
```

## Core Signals

### LexicalSignal

**Type**: `SignalType.LEXICAL`

**Purpose**: Calculate lexical relevance based on text matching and provider scores.

**Scoring Logic**:
- Uses provider's `_score` if available
- Falls back to field matching (title, description, skills, etc.)
- Bonus for exact matches in title field

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import LexicalSignal

signal = LexicalSignal()
score = signal.score(
    document={"id": "1", "title": "Software Engineer", "_score": 5.0},
    context={"query": "engineer"},
)
```

**Use Cases**:
- General text search relevance
- Query-document matching
- Title/description scoring

---

### MetadataSignal

**Type**: `SignalType.METADATA`

**Purpose**: Score documents based on structured metadata field matching.

**Scoring Logic**:
- Matches document fields against filter criteria
- Bonus for rich metadata (category, tags, industry, etc.)
- Supports exact match and list matching

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import MetadataSignal

signal = MetadataSignal()
score = signal.score(
    document={"id": "1", "category": "Technology", "tags": ["Python"]},
    context={"filters": {"category": "Technology"}},
)
```

**Use Cases**:
- Category-based filtering
- Tag matching
- Industry filtering

---

### BusinessRuleSignal

**Type**: `SignalType.BUSINESS_RULE`

**Purpose**: Apply boosts and penalties based on business rules.

**Scoring Logic**:
- Checks for pinned results (+10.0)
- Checks for promoted content (+5.0)
- Checks for priority companies (+3.0)
- Checks for blocked content (-100.0)

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import BusinessRuleSignal

signal = BusinessRuleSignal()
score = signal.score(
    document={"id": "1", "company_name": "Priority Corp"},
    context={"business_rules": {"priority_companies": ["Priority Corp"]}},
)
```

**Use Cases**:
- Pinned results
- Promoted content
- Priority company boosting
- Blocked content filtering

---

### FreshnessSignal

**Type**: `SignalType.FRESHNESS`

**Purpose**: Score documents based on recency with exponential decay.

**Scoring Logic**:
- Calculates age from date field
- Applies exponential decay: `exp(-decay * (age / scale))`
- Higher scores for newer documents

**Parameters**:
- `date_field`: Field containing date (default: "created_at")
- `scale_days`: Decay scale in days (default: 30)
- `decay`: Decay factor (default: 0.5)

**Example**:
```python
from apps.search.ranking.signals import FreshnessSignal, SignalConfig

config = SignalConfig(
    params={"date_field": "posted_at", "scale_days": 7, "decay": 0.3}
)
signal = FreshnessSignal(config=config)
score = signal.score(
    document={"id": "1", "posted_at": "2024-01-15T00:00:00Z"},
    context={},
)
```

**Use Cases**:
- Job freshness scoring
- Recent content prioritization
- Time-based ranking

---

### PopularitySignal

**Type**: `SignalType.POPULARITY`

**Purpose**: Score documents based on engagement metrics.

**Scoring Logic**:
- View count: `log1p(view_count) * 0.5`
- Application count: `log1p(application_count) * 1.0`
- Save count: `log1p(save_count) * 0.8`
- Click count: `log1p(click_count) * 0.3`

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import PopularitySignal

signal = PopularitySignal()
score = signal.score(
    document={
        "id": "1",
        "view_count": 1000,
        "application_count": 50,
        "save_count": 20,
    },
    context={},
)
```

**Use Cases**:
- Popular content boosting
- Engagement-based ranking
- Trending content

---

### QualitySignal

**Type**: `SignalType.QUALITY`

**Purpose**: Score documents based on quality indicators.

**Scoring Logic**:
- Verified status: +2.0
- Featured status: +1.5
- Premium status: +1.0
- Completeness: `completeness * 0.05`

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import QualitySignal

signal = QualitySignal()
score = signal.score(
    document={
        "id": "1",
        "is_verified": True,
        "is_featured": True,
        "completeness": 80,
    },
    context={},
)
```

**Use Cases**:
- Quality-based ranking
- Verified content prioritization
- Premium content boosting

## Domain-Specific Signals

### SkillOverlapSignal

**Type**: `SignalType.SKILL_OVERLAP`

**Purpose**: Calculate skill overlap between requirements and available skills.

**Scoring Logic**:
- Jaccard similarity: `|intersection| / |union|`
- Bonus for exact match: +0.2
- Range: [0, 1.2]

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import SkillOverlapSignal

signal = SkillOverlapSignal()
score = signal.score(
    document={"id": "1", "skills": ["Python", "JavaScript", "SQL"]},
    context={"required_skills": ["Python", "JavaScript", "SQL"]},
)
```

**Use Cases**:
- Candidate-job skill matching
- Resume skill matching
- Skill gap analysis

---

### ExperienceOverlapSignal

**Type**: `SignalType.EXPERIENCE_OVERLAP`

**Purpose**: Calculate experience level compatibility.

**Scoring Logic**:
- Ratio: `min(available / required, 2.0)`
- Normalized: `ratio / 2.0`
- Range: [0, 1]

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import ExperienceOverlapSignal

signal = ExperienceOverlapSignal()
score = signal.score(
    document={"id": "1", "experience_years": 5},
    context={"required_experience": 5},
)
```

**Use Cases**:
- Experience matching
- Overqualification handling
- Underqualification detection

---

### EducationOverlapSignal

**Type**: `SignalType.EDUCATION_OVERLAP`

**Purpose**: Calculate education level compatibility.

**Scoring Logic**:
- Hierarchy: high_school < associate < bachelor < master < phd
- Full score if meets or exceeds requirement
- Partial credit for close matches

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import EducationOverlapSignal

signal = EducationOverlapSignal()
score = signal.score(
    document={"id": "1", "education_level": "master"},
    context={"required_education": "bachelor"},
)
```

**Use Cases**:
- Education requirement matching
- Degree level filtering
- Educational background scoring

---

### LocationProximitySignal

**Type**: `SignalType.LOCATION_PROXIMITY`

**Purpose**: Calculate geographic proximity.

**Scoring Logic**:
- Exact match: 1.0
- Same city: 0.8
- Same region: 0.5
- No match: 0.0

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import LocationProximitySignal

signal = LocationProximitySignal()
score = signal.score(
    document={"id": "1", "location": "San Francisco, CA"},
    context={"required_location": "San Francisco, CA"},
)
```

**Use Cases**:
- Location-based ranking
- Remote work filtering
- Geographic proximity

---

### SalaryCompatibilitySignal

**Type**: `SignalType.SALARY_COMPATIBILITY`

**Purpose**: Calculate salary range compatibility.

**Scoring Logic**:
- In range: 1.0
- Below range: partial credit based on difference
- Above range: partial credit based on difference

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import SalaryCompatibilitySignal

signal = SalaryCompatibilitySignal()
score = signal.score(
    document={"id": "1", "salary": 80000},
    context={"min_salary": 70000, "max_salary": 90000},
)
```

**Use Cases**:
- Salary range matching
- Compensation compatibility
- Salary expectation alignment

---

### EmploymentTypeCompatibilitySignal

**Type**: `SignalType.EMPLOYMENT_TYPE_COMPATIBILITY`

**Purpose**: Match employment type preferences.

**Scoring Logic**:
- Exact match: 1.0
- No match: 0.0

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import EmploymentTypeCompatibilitySignal

signal = EmploymentTypeCompatibilitySignal()
score = signal.score(
    document={"id": "1", "employment_type": "full-time"},
    context={"preferred_employment_types": ["full-time", "contract"]},
)
```

**Use Cases**:
- Employment type filtering
- Work preference matching
- Contract vs full-time

---

### CompanyPreferenceSignal

**Type**: `SignalType.COMPANY_PREFERENCE`

**Purpose**: Apply company preferences.

**Scoring Logic**:
- Preferred company: +1.0
- Blocked company: -1.0
- Neutral: 0.0

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import CompanyPreferenceSignal

signal = CompanyPreferenceSignal()
score = signal.score(
    document={"id": "1", "company_name": "Preferred Corp"},
    context={"preferred_companies": ["Preferred Corp"]},
)
```

**Use Cases**:
- Company preference ranking
- Blocked company filtering
- Employer branding

---

### RecruiterPreferenceSignal

**Type**: `SignalType.RECRUITER_PREFERENCE`

**Purpose**: Apply recruiter-specific preferences.

**Scoring Logic**:
- Same recruiter: +1.0
- Same team: +0.5
- Neutral: 0.0

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import RecruiterPreferenceSignal

signal = RecruiterPreferenceSignal()
score = signal.score(
    document={"id": "1", "recruiter_id": "recruiter-123"},
    context={"recruiter_id": "recruiter-123"},
)
```

**Use Cases**:
- Recruiter-specific ranking
- Team-based filtering
- Internal candidate prioritization

---

### ProfileCompletenessSignal

**Type**: `SignalType.PROFILE_COMPLETENESS`

**Purpose**: Score based on profile completeness.

**Scoring Logic**:
- Uses pre-calculated completeness if available
- Calculates based on required fields
- Range: [0, 1]

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import ProfileCompletenessSignal

signal = ProfileCompletenessSignal()
score = signal.score(
    document={"id": "1", "completeness": 80},
    context={},
)
```

**Use Cases**:
- Profile quality ranking
- Incomplete profile filtering
- Onboarding completion tracking

---

### CandidateActivitySignal

**Type**: `SignalType.CANDIDATE_ACTIVITY`

**Purpose**: Score based on recent candidate activity.

**Scoring Logic**:
- Last active decay: `exp(-days_since / 30) * 2.0`
- Recent applications: `min(recent_applications * 0.5, 2.0)`
- Profile views: `log1p(profile_views) * 0.3`

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import CandidateActivitySignal

signal = CandidateActivitySignal()
score = signal.score(
    document={
        "id": "1",
        "last_active_at": "2024-01-15T00:00:00Z",
        "recent_applications": 5,
        "profile_views": 100,
    },
    context={},
)
```

**Use Cases**:
- Active candidate prioritization
- Engagement-based ranking
- Inactive candidate filtering

---

### JobFreshnessSignal

**Type**: `SignalType.JOB_FRESHNESS`

**Purpose**: Score job postings based on recency.

**Scoring Logic**:
- ≤ 1 day: 1.0
- ≤ 7 days: 0.8
- ≤ 14 days: 0.6
- ≤ 30 days: 0.4
- ≤ 60 days: 0.2
- > 60 days: 0.1
- Urgent jobs get 7-day boost

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import JobFreshnessSignal

signal = JobFreshnessSignal()
score = signal.score(
    document={"id": "1", "posted_at": "2024-01-15T00:00:00Z"},
    context={},
)
```

**Use Cases**:
- Job freshness ranking
- Urgent job prioritization
- Stale job filtering

---

### ApplicationHistorySignal

**Type**: `SignalType.APPLICATION_HISTORY`

**Purpose**: Score based on historical application patterns.

**Scoring Logic**:
- Already applied: -0.5
- Previously viewed: +0.3
- Similar companies: +0.5
- Neutral: 0.0

**Parameters**: None

**Example**:
```python
from apps.search.ranking.signals import ApplicationHistorySignal

signal = ApplicationHistorySignal()
score = signal.score(
    document={"id": "1"},
    context={
        "user_id": "user-123",
        "applied_jobs": ["job-1", "job-2"],
        "viewed_jobs": ["job-3"],
    },
)
```

**Use Cases**:
- Duplicate application prevention
- View history personalization
- Company affinity scoring

## Signal Configuration

All signals can be configured with `SignalConfig`:

```python
from apps.search.ranking.signals import SignalConfig

config = SignalConfig(
    enabled=True,
    weight=2.0,
    normalization="min_max",
    params={"custom_param": "value"},
)

signal = YourSignal(config=config)
```

## Creating Custom Signals

To create a custom signal:

1. Extend `BaseSignal`
2. Implement `score()` method
3. Set `signal_type` property
4. Register in pipeline

```python
from apps.search.ranking.signals import BaseSignal, SignalType, SignalConfig

class CustomSignal(BaseSignal):
    @property
    def signal_type(self) -> SignalType:
        return SignalType.CUSTOM
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        # Custom scoring logic
        value = document.get("custom_field", 0)
        return float(value)
```

## Signal Best Practices

### Performance

- Cache expensive calculations
- Use efficient data structures
- Avoid complex regex in hot paths
- Pre-compute when possible

### Accuracy

- Validate input data
- Handle missing fields gracefully
- Use appropriate normalization
- Test with real data

### Maintainability

- Document scoring logic
- Use descriptive parameter names
- Provide examples in docstrings
- Include unit tests

### Integration

- Follow signal interface
- Use standard context keys
- Return float scores
- Handle errors gracefully
