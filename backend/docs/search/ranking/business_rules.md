# Business Rules

## Overview

The Business Rules Engine provides a configurable system for applying ranking boosts, penalties, and filters based on business logic. Rules can pin results, hide content, promote jobs, block candidates, and apply custom boosts.

## Rule Types

### PinnedResultRule

**Purpose**: Pin specific results to the top of search results.

**Parameters**:
- `document_ids`: List of document IDs to pin
- `position`: Position to pin at (default: 0)

**Effect**: +100.0 ranking boost, sets `_pinned` flag

**Example**:
```python
from apps.search.ranking.business_rules import PinnedResultRule

rule = PinnedResultRule(
    name="pin_featured_jobs",
    document_ids=["job-1", "job-2"],
    position=0,
)
```

**Use Cases**:
- Featured job pinning
- Important candidate highlighting
- Priority content placement

---

### HiddenResultRule

**Purpose**: Hide specific results from search results.

**Parameters**:
- `document_ids`: List of document IDs to hide
- `reason`: Reason for hiding (default: "Hidden by business rule")

**Effect**: -1000.0 ranking boost, sets `_hidden` flag, filters from results

**Example**:
```python
from apps.search.ranking.business_rules import HiddenResultRule

rule = HiddenResultRule(
    name="hide_filled_jobs",
    document_ids=["job-1", "job-2"],
    reason="Position already filled",
)
```

**Use Cases**:
- Filled job hiding
- Inactive candidate filtering
- Content moderation

---

### PromotedJobRule

**Purpose**: Promote specific jobs in search results.

**Parameters**:
- `job_ids`: List of job IDs to promote
- `boost_amount`: Boost amount (default: 5.0)
- `promotion_reason`: Reason for promotion

**Effect**: +boost_amount ranking boost, sets `_promoted` flag

**Example**:
```python
from apps.search.ranking.business_rules import PromotedJobRule

rule = PromotedJobRule(
    name="promote_sponsored_jobs",
    job_ids=["job-1", "job-2"],
    boost_amount=5.0,
    promotion_reason="Sponsored job",
)
```

**Use Cases**:
- Sponsored job promotion
- Featured employer highlighting
- Premium content boosting

---

### BlockedCandidateRule

**Purpose**: Block specific candidates from search results.

**Parameters**:
- `candidate_ids`: List of candidate IDs to block
- `block_reason`: Reason for blocking (default: "Blocked candidate")

**Effect**: -1000.0 ranking boost, sets `_blocked` flag, filters from results

**Example**:
```python
from apps.search.ranking.business_rules import BlockedCandidateRule

rule = BlockedCandidateRule(
    name="block_spam_candidates",
    candidate_ids=["cand-1", "cand-2"],
    block_reason="Spam activity detected",
)
```

**Use Cases**:
- Spam candidate filtering
- Policy violation blocking
- Inactive user filtering

---

### PriorityCompanyRule

**Purpose**: Boost results from priority companies.

**Parameters**:
- `company_names`: List of priority company names
- `boost_amount`: Boost amount (default: 3.0)

**Effect**: +boost_amount ranking boost, sets `_priority_company` flag

**Example**:
```python
from apps.search.ranking.business_rules import PriorityCompanyRule

rule = PriorityCompanyRule(
    name="priority_tech_companies",
    company_names=["Google", "Microsoft", "Amazon"],
    boost_amount=3.0,
)
```

**Use Cases**:
- Priority employer boosting
- Partner company highlighting
- Premium employer promotion

---

### SponsoredRule

**Purpose**: Mark and boost sponsored content.

**Parameters**:
- `sponsored_ids`: List of sponsored item IDs
- `boost_amount`: Boost amount (default: 2.0)

**Effect**: +boost_amount ranking boost, sets `_sponsored` flag

**Example**:
```python
from apps.search.ranking.business_rules import SponsoredRule

rule = SponsoredRule(
    name="sponsored_content",
    sponsored_ids=["job-1", "job-2"],
    boost_amount=2.0,
)
```

**Use Cases**:
- Sponsored job promotion
- Ad placement
- Monetization

---

### ManualBoostRule

**Purpose**: Apply manual boosts based on custom field patterns.

**Parameters**:
- `field`: Field to match
- `value_pattern`: Pattern to match (supports regex)
- `boost_amount`: Boost amount (default: 1.0)

**Effect**: +boost_amount ranking boost, sets `_manual_boost` flag

**Example**:
```python
from apps.search.ranking.business_rules import ManualBoostRule

rule = ManualBoostRule(
    name="boost_senior_roles",
    field="title",
    value_pattern="Senior.*",
    boost_amount=2.0,
)
```

**Use Cases**:
- Senior role boosting
- Specific skill promotion
- Custom field-based boosting

---

### CustomRule

**Purpose**: Apply custom business logic with user-defined functions.

**Parameters**:
- `match_function`: Function to check if rule matches
- `apply_function`: Function to apply rule effects

**Effect**: Custom based on functions

**Example**:
```python
from apps.search.ranking.business_rules import CustomRule

def match_senior_engineers(document, context):
    title = document.get("title", "")
    return "Senior" in title and "Engineer" in title

def apply_boost(document, context):
    document["_custom_boost"] = True
    document["_ranking_boost"] = document.get("_ranking_boost", 0) + 3.0
    return document

rule = CustomRule(
    name="boost_senior_engineers",
    match_function=match_senior_engineers,
    apply_function=apply_boost,
)
```

**Use Cases**:
- Complex business logic
- Multi-field conditions
- Custom scoring

## Rule Priority

Rules are executed in priority order:

```python
from apps.search.ranking.business_rules import RulePriority

rule = PinnedResultRule(
    name="pin_urgent",
    document_ids=["job-1"],
    priority=RulePriority.CRITICAL,  # Executes first
)
```

**Priority Levels**:
- `CRITICAL` (0): Highest priority
- `HIGH` (1): High priority
- `MEDIUM` (2): Medium priority (default)
- `LOW` (3): Lowest priority

## BusinessRulesEngine

### Basic Usage

```python
from apps.search.ranking.business_rules import BusinessRulesEngine

engine = BusinessRulesEngine()

# Add rules
engine.add_rule(pin_rule)
engine.add_rule(promote_rule)
engine.add_rule(block_rule)

# Apply rules to results
results = [
    {"id": "job-1", "title": "Software Engineer"},
    {"id": "job-2", "title": "Data Scientist"},
]
context = {}

modified_results, applied_rules = engine.apply_rules(results, context)
```

### Rule Management

```python
# Get rule by name
rule = engine.get_rule("pin_urgent")

# Get rules by type
pinned_rules = engine.get_rules_by_type(RuleType.PINNED_RESULT)

# Enable/disable rules
engine.enable_rule("pin_urgent")
engine.disable_rule("pin_urgent")

# Remove rule
engine.remove_rule("pin_urgent")

# Validate rules
issues = engine.validate_rules()
```

### RuleBuilder

Convenient builder for creating rules:

```python
from apps.search.ranking.business_rules import RuleBuilder

# Pinned rule
pin_rule = RuleBuilder.pinned(
    name="pin_featured",
    document_ids=["job-1"],
    position=0,
)

# Hidden rule
hide_rule = RuleBuilder.hidden(
    name="hide_filled",
    document_ids=["job-2"],
    reason="Position filled",
)

# Promoted rule
promote_rule = RuleBuilder.promoted(
    name="promote_sponsored",
    job_ids=["job-3"],
    boost=5.0,
)

# Blocked rule
block_rule = RuleBuilder.blocked(
    name="block_spam",
    candidate_ids=["cand-1"],
    reason="Spam",
)

# Priority company rule
priority_rule = RuleBuilder.priority_company(
    name="priority_tech",
    company_names=["Google", "Microsoft"],
    boost=3.0,
)

# Sponsored rule
sponsored_rule = RuleBuilder.sponsored(
    name="sponsored_jobs",
    sponsored_ids=["job-4"],
    boost=2.0,
)

# Manual boost rule
boost_rule = RuleBuilder.manual_boost(
    name="boost_senior",
    field="title",
    value_pattern="Senior.*",
    boost=2.0,
)
```

## Rule Execution

### Execution Order

1. Rules sorted by priority (lower value = higher priority)
2. Each rule checked against document
3. Matching rules applied in order
4. Conflicts resolved by priority
5. Hidden results filtered out
6. Results re-sorted by final score

### Conflict Resolution

When multiple rules apply to the same document:

- Higher priority rules execute first
- Boosts are cumulative
- Negative boosts (blocking) override positive boosts
- Hidden status cannot be overridden

### Rule Effects

**Document Metadata Added**:
- `_ranking_boost`: Total boost from rules
- `_applied_rules`: List of applied rule names
- `_pinned`: Pinned flag (if pinned)
- `_pin_position`: Pin position (if pinned)
- `_hidden`: Hidden flag (if hidden)
- `_hidden_reason`: Reason for hiding (if hidden)
- `_promoted`: Promoted flag (if promoted)
- `_blocked`: Blocked flag (if blocked)
- `_priority_company`: Priority company flag (if applicable)
- `_sponsored`: Sponsored flag (if sponsored)
- `_manual_boost`: Manual boost flag (if applicable)

## Best Practices

### Rule Design

- Use descriptive rule names
- Provide clear reasons for hiding/blocking
- Set appropriate priority levels
- Document rule purpose

### Performance

- Use specific document IDs when possible
- Avoid complex regex in match conditions
- Cache expensive rule calculations
- Limit number of active rules

### Maintainability

- Validate rules before deployment
- Monitor rule application rates
- Review rule effectiveness regularly
- Remove unused rules

### Safety

- Test rules in staging environment
- Use rule priority to prevent conflicts
- Monitor for unintended side effects
- Have rollback plan for rule changes

## Monitoring

### Track Rule Application

```python
modified_results, applied_rules = engine.apply_rules(results, context)

# Applied rules info contains:
# - rule_name
# - rule_type
# - document_id
# - priority
```

### Rule Statistics

```python
# Get all rules
all_rules = engine.get_all_rules()

# Count rules by type
from collections import Counter
rule_types = Counter(rule.rule_type for rule in all_rules)

# Count enabled rules
enabled_rules = sum(1 for rule in all_rules if rule.enabled)
```

## Common Patterns

### Time-Based Rules

```python
from datetime import datetime, timedelta

class TimeBasedRule(BusinessRule):
    def matches(self, document, context):
        posted_date = document.get("posted_at")
        if not posted_date:
            return False
        
        posted = datetime.fromisoformat(posted_date)
        days_since = (datetime.now() - posted_date).days
        
        return days_since <= 7  # Last 7 days
```

### User-Based Rules

```python
class UserPreferenceRule(BusinessRule):
    def matches(self, document, context):
        user_id = context.get("user_id")
        preferred_companies = context.get("preferred_companies", [])
        
        company = document.get("company_name")
        return company in preferred_companies
```

### Composite Conditions

```python
class CompositeRule(BusinessRule):
    def matches(self, document, context):
        # Multiple conditions
        has_skill = "Python" in document.get("skills", [])
        is_senior = "Senior" in document.get("title", "")
        is_verified = document.get("is_verified", False)
        
        return has_skill and is_senior and is_verified
```

## Troubleshooting

### Rules Not Applying

**Symptoms**: Rules not affecting results

**Solutions**:
- Check rule is enabled
- Verify rule priority
- Check match condition logic
- Verify document IDs match
- Check for rule conflicts

### Unexpected Filtering

**Symptoms**: Results disappearing unexpectedly

**Solutions**:
- Check for hidden rules
- Verify blocked rules
- Check rule priority
- Review rule conditions
- Monitor applied rules

### Performance Issues

**Symptoms**: Slow ranking with rules

**Solutions**:
- Reduce number of rules
- Optimize match conditions
- Use specific document IDs
- Cache rule results
- Profile slow rules

### Rule Conflicts

**Symptoms**: Inconsistent ranking

**Solutions**:
- Review rule priorities
- Check for conflicting boosts
- Use rule validation
- Monitor rule application
- Test rule combinations
