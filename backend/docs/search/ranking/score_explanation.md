# Score Explanation

## Overview

The Score Explanation system provides detailed, explainable ranking for every search result. Each result exposes how its ranking score was calculated, including individual signal contributions, applied boosts, and business rules.

## Explanation Components

### SignalContribution

Represents the contribution of a single signal to the final score.

**Fields**:
- `signal_name`: Name of the signal
- `signal_type`: Type of signal (lexical, metadata, etc.)
- `raw_score`: Original score from signal
- `normalized_score`: Score after normalization
- `weight`: Weight applied to the signal
- `contribution`: Final contribution to total score
- `metadata`: Additional signal-specific metadata

**Example**:
```python
{
    "signal_name": "skill_overlap",
    "signal_type": "skill_overlap",
    "raw_score": 0.8,
    "normalized_score": 0.8,
    "weight": 2.0,
    "contribution": 1.6,
    "metadata": {}
}
```

---

### BoostExplanation

Represents a boost applied to a document.

**Fields**:
- `boost_type`: Type of boost (ranking_boost, freshness, etc.)
- `boost_amount`: Amount of boost applied
- `reason`: Reason for the boost
- `source`: Source of the boost (pipeline, business rule, etc.)
- `applied_at`: Timestamp when boost was applied
- `metadata`: Additional boost-specific metadata

**Example**:
```python
{
    "boost_type": "ranking_boost",
    "boost_amount": 5.0,
    "reason": "Priority company",
    "source": "business_rules",
    "applied_at": "2024-01-15T10:30:00Z",
    "metadata": {}
}
```

---

### BusinessRuleExplanation

Represents a business rule applied to a document.

**Fields**:
- `rule_name`: Name of the business rule
- `rule_type`: Type of rule (pinned, hidden, promoted, etc.)
- `action`: Action taken (pin, hide, promote, block, boost)
- `priority`: Priority level of the rule
- `effect`: Effect on ranking score
- `reason`: Reason for rule application
- `metadata`: Additional rule-specific metadata

**Example**:
```python
{
    "rule_name": "priority_company",
    "rule_type": "priority_company",
    "action": "boost",
    "priority": 1,
    "effect": 3.0,
    "reason": "Company is in priority list",
    "metadata": {}
}
```

---

### RankingBreakdown

Complete breakdown of how a ranking score was calculated.

**Fields**:
- `document_id`: ID of the document
- `final_score`: Final ranking score
- `original_score`: Original score from provider
- `signal_contributions`: List of signal contributions
- `boosts`: List of applied boosts
- `business_rules`: List of applied business rules
- `ranking_position`: Final ranking position
- `metadata`: Additional metadata (pinned, hidden, promoted, etc.)

**Example**:
```python
{
    "document_id": "job-123",
    "final_score": 8.5,
    "original_score": 5.0,
    "signal_contributions": [
        {
            "signal_name": "lexical",
            "signal_type": "lexical",
            "raw_score": 5.0,
            "normalized_score": 1.0,
            "weight": 1.0,
            "contribution": 1.0
        },
        {
            "signal_name": "skill_overlap",
            "signal_type": "skill_overlap",
            "raw_score": 0.8,
            "normalized_score": 0.8,
            "weight": 2.0,
            "contribution": 1.6
        }
    ],
    "boosts": [
        {
            "boost_type": "ranking_boost",
            "boost_amount": 3.0,
            "reason": "Priority company",
            "source": "business_rules"
        }
    ],
    "business_rules": [
        {
            "rule_name": "priority_company",
            "rule_type": "priority_company",
            "action": "boost",
            "priority": 1,
            "effect": 3.0,
            "reason": "Company is in priority list"
        }
    ],
    "ranking_position": 1,
    "metadata": {
        "priority_company": true
    }
}
```

## Usage

### Basic Explanation

```python
from apps.search.ranking.explanation import ScoreExplanation

explanation = ScoreExplanation()

# Create breakdown for a single document
document = {
    "id": "job-123",
    "_ranking_score": 8.5,
    "_score": 5.0,
    "_ranking_signals": {
        "lexical": 1.0,
        "skill_overlap": 1.6,
    },
    "_ranking_boost": 3.0,
    "_applied_rules": ["priority_company"],
}
context = {"query": "engineer", "required_skills": ["Python"]}

breakdown = explanation.create_breakdown(document, context)
```

### Explain All Results

```python
# Explain all search results
results = [
    {"id": "job-123", "_ranking_score": 8.5, ...},
    {"id": "job-124", "_ranking_score": 7.2, ...},
]

breakdowns = explanation.explain_results(results, context)

# Get breakdown for specific document
breakdown = explanation.get_breakdown("job-123")
```

### Using ExplanationBuilder

```python
from apps.search.ranking.explanation import ExplanationBuilder

builder = ExplanationBuilder()

# Build for single document
breakdown = builder.build_for_document(document, context)

# Build for all results
breakdowns = builder.build_for_results(results, context)

# Format for API
api_format = builder.format_for_api(breakdown)

# Format for UI
ui_format = builder.format_for_ui(breakdown)

# Format for logs
log_format = builder.format_for_logs(breakdown)
```

## Output Formats

### API Format

JSON format suitable for API responses:

```python
{
    "document_id": "job-123",
    "score": {
        "final": 8.5,
        "original": 5.0,
        "delta": 3.5
    },
    "signals": [
        {
            "name": "lexical",
            "type": "lexical",
            "contribution": 1.0,
            "weight": 1.0
        },
        {
            "name": "skill_overlap",
            "type": "skill_overlap",
            "contribution": 1.6,
            "weight": 2.0
        }
    ],
    "boosts": [
        {
            "type": "ranking_boost",
            "amount": 3.0,
            "reason": "Priority company"
        }
    ],
    "business_rules": [
        {
            "name": "priority_company",
            "type": "priority_company",
            "action": "boost",
            "effect": 3.0
        }
    ],
    "position": 1
}
```

### UI Format

Simplified format for UI display:

```python
{
    "document_id": "job-123",
    "score": 8.5,
    "top_factors": [
        {
            "name": "skill_overlap",
            "impact": "positive",
            "value": 1.6
        },
        {
            "name": "lexical",
            "impact": "positive",
            "value": 1.0
        }
    ],
    "boosts_applied": 1,
    "rules_applied": 1,
    "is_pinned": false,
    "is_promoted": false,
    "is_sponsored": false
}
```

### Log Format

Text format for logging:

```
Document: job-123
Final Score: 8.5000
Original Score: 5.0000
Signal Contributions:
  - lexical: 1.0000 (weight: 1.0)
  - skill_overlap: 1.6000 (weight: 2.0)
Boosts:
  - ranking_boost: +3.0000 (Priority company)
Business Rules:
  - priority_company: boost (effect: 3.0000)
```

## Analysis Methods

### RankingBreakdown Methods

```python
breakdown = explanation.get_breakdown("job-123")

# Get total signal contribution
total_signal = breakdown.get_total_signal_contribution()

# Get total boost
total_boost = breakdown.get_total_boost()

# Get total business rule effect
total_rule_effect = breakdown.get_total_business_rule_effect()

# Get top N signals
top_signals = breakdown.get_top_signals(n=3)
```

### Summary Statistics

```python
builder = ExplanationBuilder()
breakdowns = builder.build_for_results(results, context)

# Get summary statistics
stats = builder.get_summary_statistics(breakdowns)

# Statistics include:
# - total_documents
# - total_signal_contribution
# - total_boost
# - total_business_rule_effect
# - average_signal_contribution
# - average_boost
# - signal_usage
# - rule_usage
# - most_used_signals
# - most_used_rules
```

## Enabling/Disabling Explanation

```python
explanation = ScoreExplanation()

# Enable explanation
explanation.enable()

# Disable explanation
explanation.disable()

# Check if enabled
if explanation.is_enabled():
    # Generate explanations
    breakdown = explanation.create_breakdown(document, context)
```

## Performance Considerations

### Caching

Explanation data is cached per document:

```python
# Explanation is cached when created
breakdown = explanation.create_breakdown(document, context)

# Subsequent calls return cached breakdown
cached_breakdown = explanation.get_breakdown("job-123")
```

### Selective Explanation

Enable explanation only when needed:

```python
# Disable for production (performance)
explanation.disable()

# Enable for debugging
explanation.enable()
```

### Lazy Explanation

Generate explanations only for top results:

```python
# Explain only top 10 results
top_results = results[:10]
breakdowns = explanation.explain_results(top_results, context)
```

## Best Practices

### API Responses

Include explanation in API responses when requested:

```python
def search_results(request):
    results = execute_search(request)
    
    if request.GET.get("explain"):
        explanation = ScoreExplanation()
        breakdowns = explanation.explain_results(results, context)
        return {"results": results, "explanations": breakdowns}
    else:
        return {"results": results}
```

### UI Display

Show simplified explanation in UI:

```python
# Use UI format for display
ui_format = builder.format_for_ui(breakdown)

# Display top factors
for factor in ui_format["top_factors"]:
    print(f"{factor['name']}: {factor['impact']} ({factor['value']})")
```

### Debugging

Use log format for debugging:

```python
# Use log format for debugging
log_format = builder.format_for_logs(breakdown)
logger.debug(log_format)
```

### Admin Access

Provide full explanation only to admin users:

```python
if user.is_admin:
    full_breakdown = builder.format_for_api(breakdown)
else:
    simplified_breakdown = builder.format_for_ui(breakdown)
```

## Monitoring

### Track Explanation Generation

```python
# Track explanation generation rate
explanation_count = 0

def generate_explanation(document, context):
    global explanation_count
    explanation_count += 1
    return explanation.create_breakdown(document, context)
```

### Monitor Signal Usage

```python
# Track which signals are most used
signal_usage = {}

for breakdown in breakdowns.values():
    for signal in breakdown.signal_contributions:
        signal_name = signal.signal_name
        signal_usage[signal_name] = signal_usage.get(signal_name, 0) + 1
```

### Monitor Rule Application

```python
# Track which rules are most applied
rule_usage = {}

for breakdown in breakdowns.values():
    for rule in breakdown.business_rules:
        rule_name = rule.rule_name
        rule_usage[rule_name] = rule_usage.get(rule_name, 0) + 1
```

## Troubleshooting

### Missing Explanation Data

**Symptoms**: Explanation missing signal contributions

**Solutions**:
- Verify explanation is enabled
- Check document has `_ranking_signals`
- Verify document has `_ranking_score`
- Check pipeline execution completed

### Inconsistent Scores

**Symptoms**: Final score doesn't match sum of contributions

**Solutions**:
- Check for rounding errors
- Verify all signals are included
- Check for missing boosts
- Verify business rule effects

### Performance Issues

**Symptoms**: Slow search with explanation enabled

**Solutions**:
- Disable explanation in production
- Generate explanation only for top results
- Cache explanation data
- Use simplified formats

### Missing Metadata

**Symptoms**: Explanation missing metadata (pinned, promoted, etc.)

**Solutions**:
- Verify business rules applied
- Check document has rule flags
- Verify rule execution order
- Check for rule conflicts
