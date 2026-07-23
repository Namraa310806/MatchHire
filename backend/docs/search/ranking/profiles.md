# Ranking Profiles

## Overview

Ranking profiles are pre-configured ranking configurations optimized for specific search scenarios. Each profile defines signal weights, pipeline stages, and normalization methods tailored to a particular use case.

## Available Profiles

### RecruiterSearchProfile

**Purpose**: Optimized for recruiters searching for candidates.

**Focus**: Skill matching, experience, education, and candidate activity.

**Stages**:
1. **Lexical Relevance** (weight: 1.0)
   - LexicalSignal
   - Normalization: min_max

2. **Skill Matching** (weights: skill_overlap=2.0, experience_overlap=1.5, education_overlap=1.0)
   - SkillOverlapSignal
   - ExperienceOverlapSignal
   - EducationOverlapSignal
   - Normalization: min_max

3. **Candidate Quality** (weights: profile_completeness=1.0, candidate_activity=1.5, quality=1.0)
   - ProfileCompletenessSignal
   - CandidateActivitySignal
   - QualitySignal
   - Normalization: min_max

4. **Business Rules** (weight: 3.0)
   - BusinessRuleSignal
   - Normalization: none

**Metadata**:
- Primary focus: skill_matching
- Secondary focus: candidate_quality
- Target entity: candidate

**Use Case**: Recruiters finding the best candidates for open positions.

---

### CandidateSearchProfile

**Purpose**: Optimized for candidates searching for jobs.

**Focus**: Job matching, location, salary, and job freshness.

**Stages**:
1. **Lexical Relevance** (weight: 1.0)
   - LexicalSignal
   - Normalization: min_max

2. **Job Matching** (weights: skill_overlap=2.0, location_proximity=1.5, salary_compatibility=1.0, employment_type_compatibility=0.5)
   - SkillOverlapSignal
   - LocationProximitySignal
   - SalaryCompatibilitySignal
   - EmploymentTypeCompatibilitySignal
   - Normalization: min_max

3. **Job Quality** (weights: job_freshness=1.5, quality=1.0, popularity=0.5)
   - JobFreshnessSignal
   - QualitySignal
   - PopularitySignal
   - Normalization: min_max

4. **Preferences** (weights: company_preference=1.0, application_history=0.5)
   - CompanyPreferenceSignal
   - ApplicationHistorySignal
   - Normalization: none

5. **Business Rules** (weight: 3.0)
   - BusinessRuleSignal
   - Normalization: none

**Metadata**:
- Primary focus: job_matching
- Secondary focus: job_quality
- Target entity: job

**Use Case**: Candidates finding relevant job opportunities.

---

### JobDiscoveryProfile

**Purpose**: Optimized for job discovery and exploration.

**Focus**: Freshness, popularity, and diversity.

**Stages**:
1. **Relevance** (weights: lexical=1.0, metadata=0.5)
   - LexicalSignal
   - MetadataSignal
   - Normalization: min_max

2. **Engagement** (weights: popularity=2.0, quality=1.0)
   - PopularitySignal
   - QualitySignal
   - Normalization: logistic

3. **Freshness** (weights: job_freshness=2.0, freshness=1.0)
   - JobFreshnessSignal
   - FreshnessSignal
   - Normalization: min_max

4. **Business Rules** (weight: 2.0)
   - BusinessRuleSignal
   - Normalization: none

**Metadata**:
- Primary focus: engagement
- Secondary focus: freshness
- Target entity: job
- Diversity weight: 0.3

**Use Case**: Users exploring and discovering new job opportunities.

---

### ResumeSearchProfile

**Purpose**: Optimized for searching resumes and CVs.

**Focus**: Skills, experience, and education matching.

**Stages**:
1. **Content Matching** (weight: 1.5)
   - LexicalSignal
   - Normalization: min_max

2. **Skill Experience** (weights: skill_overlap=2.5, experience_overlap=2.0, education_overlap=1.0)
   - SkillOverlapSignal
   - ExperienceOverlapSignal
   - EducationOverlapSignal
   - Normalization: min_max

3. **Resume Quality** (weights: profile_completeness=1.0, quality=1.5)
   - ProfileCompletenessSignal
   - QualitySignal
   - Normalization: min_max

4. **Activity** (weight: 1.0)
   - CandidateActivitySignal
   - Normalization: min_max

5. **Business Rules** (weight: 2.0)
   - BusinessRuleSignal
   - Normalization: none

**Metadata**:
- Primary focus: skill_experience
- Secondary focus: resume_quality
- Target entity: resume

**Use Case**: Recruiters searching for candidates based on resume content.

---

### AdminSearchProfile

**Purpose**: Comprehensive search with full diagnostics for admin use.

**Focus**: All signals enabled for debugging and analysis.

**Stages**:
1. **All Signals** (weights: various)
   - LexicalSignal (1.0)
   - MetadataSignal (0.5)
   - SkillOverlapSignal (1.0)
   - ExperienceOverlapSignal (1.0)
   - EducationOverlapSignal (0.5)
   - LocationProximitySignal (0.5)
   - SalaryCompatibilitySignal (0.5)
   - FreshnessSignal (0.5)
   - PopularitySignal (0.5)
   - QualitySignal (0.5)
   - ProfileCompletenessSignal (0.5)
   - CandidateActivitySignal (0.5)
   - JobFreshnessSignal (0.5)
   - Normalization: min_max

2. **Business Rules** (weight: 5.0)
   - BusinessRuleSignal
   - Normalization: none

**Pipeline Configuration**:
- Diagnostics enabled: true
- Parallel scoring enabled: true
- Cache disabled: false

**Metadata**:
- Primary focus: comprehensive
- Diagnostics enabled: true
- Target entity: all

**Use Case**: Admin debugging, analysis, and comprehensive search.

## Profile Registry

### Basic Usage

```python
from apps.search.ranking.profiles import RankingProfileRegistry

registry = RankingProfileRegistry()

# Get default profile
profile = registry.get_default_profile()

# Get profile by name
profile = registry.get_profile("candidate_search")

# Get profile by type
from apps.search.ranking.profiles import ProfileType
profile = registry.get_profile_by_type(ProfileType.CANDIDATE_SEARCH)

# List all profiles
profiles = registry.list_profiles()

# Get all profiles
all_profiles = registry.get_all_profiles()
```

### Profile Management

```python
# Set default profile
registry.set_default_profile("recruiter_search")

# Register custom profile
from apps.search.ranking.profiles import RankingProfile, ProfileType
custom_profile = RankingProfile(
    name="custom_profile",
    profile_type=ProfileType.CUSTOM,
    description="Custom profile for specific use case",
)
registry.register_profile(custom_profile)

# Unregister profile
registry.unregister_profile("custom_profile")
```

## Custom Profiles

### Using ProfileBuilder

```python
from apps.search.ranking.profiles import ProfileBuilder, ProfileType
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

builder = ProfileBuilder(
    name="custom_profile",
    profile_type=ProfileType.CANDIDATE_SEARCH,
)

builder.with_description("Custom profile for specific use case")

# Add custom stage
stage = PipelineStage(
    name="custom_stage",
    signals=["lexical", "skill_overlap"],
    weights={"lexical": 1.0, "skill_overlap": 2.0},
    normalization=NormalizationMethod.MIN_MAX,
)
builder.add_stage(stage)

# Set pipeline config
from apps.search.ranking.pipeline import PipelineConfig
config = PipelineConfig(
    enable_parallel_scoring=True,
    cache_enabled=True,
)
builder.with_pipeline_config(config)

# Set metadata
builder.with_metadata({
    "primary_focus": "custom_matching",
    "target_entity": "job",
})

# Build profile
profile = builder.build()

# Register profile
registry.register_profile(profile)
```

### Extending Existing Profiles

```python
from apps.search.ranking.profiles import CandidateSearchProfile

# Get existing profile
base_profile = CandidateSearchProfile()

# Copy and modify
custom_profile = RankingProfile(
    name="custom_candidate_search",
    profile_type=base_profile.profile_type,
    description="Modified candidate search profile",
    stages=base_profile.stages.copy(),
    metadata=base_profile.metadata.copy(),
)

# Add custom stage
custom_stage = PipelineStage(
    name="custom_boost",
    signals=["custom_signal"],
    weights={"custom_signal": 3.0},
)
custom_profile.stages.append(custom_stage)

# Register
registry.register_profile(custom_profile)
```

## Profile Selection

### Automatic Selection

```python
def select_profile(entity_type: str, user_type: str) -> str:
    """Select appropriate profile based on context."""
    
    if entity_type == "candidate" and user_type == "recruiter":
        return "recruiter_search"
    elif entity_type == "job" and user_type == "candidate":
        return "candidate_search"
    elif entity_type == "job" and user_type == "admin":
        return "job_discovery"
    elif entity_type == "resume":
        return "resume_search"
    elif user_type == "admin":
        return "admin_search"
    else:
        return registry.get_default_profile().name
```

### Context-Based Selection

```python
def select_profile_by_context(context: Dict[str, Any]) -> str:
    """Select profile based on search context."""
    
    use_case = context.get("use_case")
    entity_type = context.get("entity_type")
    
    if use_case == "job_discovery":
        return "job_discovery"
    elif use_case == "resume_search":
        return "resume_search"
    elif entity_type == "candidate":
        return "recruiter_search"
    elif entity_type == "job":
        return "candidate_search"
    else:
        return "candidate_search"  # Default
```

## Profile Comparison

| Profile | Primary Focus | Entity Type | Signal Count | Diagnostics |
|---------|--------------|-------------|--------------|-------------|
| RecruiterSearch | Skill Matching | Candidate | 7 | No |
| CandidateSearch | Job Matching | Job | 9 | No |
| JobDiscovery | Engagement | Job | 5 | No |
| ResumeSearch | Skill Experience | Resume | 6 | No |
| AdminSearch | Comprehensive | All | 13 | Yes |

## Profile Tuning

### Adjusting Signal Weights

```python
profile = registry.get_profile("candidate_search")

# Find stage to modify
stage = profile.get_stage("job_matching")

# Adjust weights
stage.weights["skill_overlap"] = 2.5  # Increase skill importance
stage.weights["location_proximity"] = 1.0  # Decrease location importance
```

### Adding Custom Stages

```python
profile = registry.get_profile("candidate_search")

# Add new stage
new_stage = PipelineStage(
    name="personalization",
    signals=["company_preference", "application_history"],
    weights={"company_preference": 1.5, "application_history": 1.0},
    normalization=NormalizationMethod.MIN_MAX,
)

profile.stages.append(new_stage)
```

### Changing Normalization

```python
profile = registry.get_profile("recruiter_search")

# Find stage
stage = profile.get_stage("skill_matching")

# Change normalization
stage.normalization = NormalizationMethod.LOGISTIC
```

## A/B Testing Profiles

### Test Profile Setup

```python
# Create test profile variant
test_profile = RankingProfile(
    name="candidate_search_v2",
    profile_type=ProfileType.CANDIDATE_SEARCH,
    description="Test profile with adjusted weights",
    stages=base_profile.stages.copy(),
)

# Modify weights
test_profile.get_stage("job_matching").weights["skill_overlap"] = 3.0

# Register test profile
registry.register_profile(test_profile)
```

### Traffic Splitting

```python
import random

def select_profile_for_ab_test(user_id: str) -> str:
    """Select profile for A/B testing."""
    
    hash_value = hash(user_id) % 100
    
    if hash_value < 50:
        return "candidate_search"  # Control
    else:
        return "candidate_search_v2"  # Test
```

## Best Practices

### Profile Design

- Focus on specific use cases
- Limit number of stages (3-5 optimal)
- Use appropriate normalization per signal
- Document profile purpose and focus

### Signal Weighting

- Assign weights based on business importance
- Balance weights to prevent signal dominance
- Test weight combinations with A/B testing
- Monitor signal contribution over time

### Performance

- Disable diagnostics in production profiles
- Enable caching for frequently used profiles
- Use parallel scoring for CPU-intensive signals
- Profile slow profiles

### Maintainability

- Use descriptive profile names
- Document profile changes
- Version profile configurations
- Monitor profile effectiveness

## Monitoring

### Profile Usage Tracking

```python
# Track profile usage
profile_usage = {}

def track_profile_usage(profile_name: str):
    profile_usage[profile_name] = profile_usage.get(profile_name, 0) + 1

# Get usage statistics
def get_profile_statistics():
    return {
        "total_searches": sum(profile_usage.values()),
        "profile_distribution": profile_usage,
        "most_used_profile": max(profile_usage.items(), key=lambda x: x[1])[0],
    }
```

### Profile Performance

```python
# Track profile performance
profile_performance = {}

def track_profile_performance(profile_name: str, latency_ms: float):
    if profile_name not in profile_performance:
        profile_performance[profile_name] = []
    profile_performance[profile_name].append(latency_ms)

def get_profile_performance(profile_name: str):
    latencies = profile_performance.get(profile_name, [])
    if not latencies:
        return {}
    
    return {
        "avg_latency_ms": sum(latencies) / len(latencies),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "p50_latency_ms": sorted(latencies)[len(latencies) // 2],
    }
```

## Troubleshooting

### Profile Not Working

**Symptoms**: Profile not affecting results

**Solutions**:
- Verify profile is registered
- Check profile is selected
- Verify stages are enabled
- Check signal registration
- Review profile configuration

### Unexpected Rankings

**Symptoms**: Rankings different from expected

**Solutions**:
- Review signal weights
- Check normalization methods
- Verify business rules
- Monitor signal contributions
- Test with sample data

### Performance Issues

**Symptoms**: Slow ranking with specific profile

**Solutions**:
- Profile stage execution times
- Reduce signal count
- Enable caching
- Disable diagnostics
- Optimize slow signals
