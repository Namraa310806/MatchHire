# Extension Guide

## Overview

This guide explains how to extend the ranking system with custom signals, fusion algorithms, business rules, and profiles. The ranking system is designed to be extensible without modifying core architecture.

## Adding Custom Signals

### Step 1: Create Signal Class

Extend `BaseSignal` and implement the required methods:

```python
from apps.search.ranking.signals import BaseSignal, SignalType, SignalConfig
from typing import Dict, Any

class CustomSignal(BaseSignal):
    """Custom signal for specific scoring logic."""
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.CUSTOM
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate custom score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Score value (higher is better)
        """
        # Custom scoring logic
        value = document.get("custom_field", 0)
        
        # Apply custom logic
        if context.get("custom_condition"):
            value *= 2.0
        
        return float(value)
```

### Step 2: Register Signal

Register the signal in the pipeline:

```python
from apps.search.ranking.pipeline import RankingPipeline

pipeline = RankingPipeline()

# Register signal
custom_signal = CustomSignal()
pipeline.register_signal("custom_signal", custom_signal)
```

### Step 3: Add to Profile Stage

Add the signal to a profile stage:

```python
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

stage = PipelineStage(
    name="custom_stage",
    signals=["custom_signal"],
    weights={"custom_signal": 2.0},
    normalization=NormalizationMethod.MIN_MAX,
)

profile.stages.append(stage)
```

### Step 4: Test Signal

Create unit tests for the signal:

```python
import unittest
from apps.search.ranking.signals import BaseSignal

class TestCustomSignal(unittest.TestCase):
    def setUp(self):
        self.signal = CustomSignal()
    
    def test_score_basic(self):
        document = {"custom_field": 10}
        context = {}
        score = self.signal.score(document, context)
        self.assertEqual(score, 10.0)
    
    def test_score_with_condition(self):
        document = {"custom_field": 10}
        context = {"custom_condition": True}
        score = self.signal.score(document, context)
        self.assertEqual(score, 20.0)
```

## Adding Custom Fusion Algorithms

### Step 1: Create Fusion Class

Extend `FusionAlgorithm` and implement the `fuse` method:

```python
from apps.search.ranking.hybrid import FusionAlgorithm, StrategyResult

class CustomFusion(FusionAlgorithm):
    """Custom fusion algorithm."""
    
    def fuse(self, strategy_results: List[StrategyResult]) -> List[SearchResult]:
        """
        Fuse results using custom logic.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        # Custom fusion logic
        all_results = {}
        
        for strategy_result in strategy_results:
            for result in strategy_result.results:
                doc_id = result.document_id
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document_id": doc_id,
                        "document": result.document,
                        "scores": [],
                    }
                all_results[doc_id]["scores"].append(result.score)
        
        # Calculate fused scores
        fused_results = []
        for doc_id, data in all_results.items():
            # Custom score combination
            fused_score = sum(data["scores"]) / len(data["scores"])
            
            fused_result = SearchResult(
                document_id=doc_id,
                score=fused_score,
                rank=0,
                source="custom_fusion",
                document=data["document"],
            )
            fused_results.append(fused_result)
        
        # Sort and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for rank, result in enumerate(fused_results, start=1):
            result.rank = rank
        
        return fused_results
```

### Step 2: Register Fusion Algorithm

```python
from apps.search.ranking.hybrid import HybridSearchEngine

engine = HybridSearchEngine(provider_registry)

# Set custom fusion
custom_fusion = CustomFusion()
engine.set_fusion_algorithm(custom_fusion)
```

### Step 3: Test Fusion

```python
import unittest
from apps.search.ranking.hybrid import SearchResult, StrategyResult

class TestCustomFusion(unittest.TestCase):
    def setUp(self):
        self.fusion = CustomFusion()
    
    def test_fusion_single_strategy(self):
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="test"),
        ]
        strategy_result = StrategyResult(
            strategy_name="test",
            results=results,
            total=1,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result])
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].document_id, "doc1")
```

## Adding Custom Business Rules

### Step 1: Create Rule Class

Extend `BusinessRule` and implement matching and application logic:

```python
from apps.search.ranking.business_rules import BusinessRule, RuleType

class CustomRule(BusinessRule):
    """Custom business rule."""
    
    def __init__(self, name: str, custom_param: str):
        super().__init__(
            name=name,
            rule_type=RuleType.CUSTOM,
            description="Custom rule for specific logic",
        )
        self.custom_param = custom_param
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if rule matches document."""
        # Custom matching logic
        field_value = document.get("custom_field", "")
        return self.custom_param in field_value
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule to document."""
        # Custom application logic
        document["_custom_rule_applied"] = True
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + 2.0
        return document
```

### Step 2: Register Rule

```python
from apps.search.ranking.business_rules import BusinessRulesEngine

engine = BusinessRulesEngine()

# Register custom rule
custom_rule = CustomRule(
    name="boost_featured",
    custom_param="featured",
)
engine.add_rule(custom_rule)
```

### Step 3: Test Rule

```python
import unittest
from apps.search.ranking.business_rules import BusinessRule

class TestCustomRule(unittest.TestCase):
    def setUp(self):
        self.rule = CustomRule("test", "featured")
    
    def test_matches(self):
        document = {"custom_field": "featured_job"}
        self.assertTrue(self.rule.matches(document, {}))
    
    def test_apply(self):
        document = {"custom_field": "featured_job"}
        result = self.rule.apply(document, {})
        self.assertTrue(result.get("_custom_rule_applied"))
        self.assertGreater(result.get("_ranking_boost", 0), 0)
```

## Adding Custom Profiles

### Step 1: Create Profile Class

Extend `RankingProfile` with custom configuration:

```python
from apps.search.ranking.profiles import RankingProfile, ProfileType
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

class CustomProfile(RankingProfile):
    """Custom ranking profile."""
    
    def __init__(self):
        # Define custom stages
        stages = [
            PipelineStage(
                name="custom_stage_1",
                signals=["lexical", "custom_signal"],
                weights={"lexical": 1.0, "custom_signal": 2.0},
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="custom_stage_2",
                signals=["quality"],
                weights={"quality": 1.5},
                normalization=NormalizationMethod.LOGISTIC,
            ),
        ]
        
        super().__init__(
            name="custom_profile",
            profile_type=ProfileType.CUSTOM,
            description="Custom profile for specific use case",
            stages=stages,
            metadata={
                "primary_focus": "custom_matching",
                "target_entity": "job",
            },
        )
```

### Step 2: Register Profile

```python
from apps.search.ranking.profiles import RankingProfileRegistry

registry = RankingProfileRegistry()

# Register custom profile
custom_profile = CustomProfile()
registry.register_profile(custom_profile)
```

### Step 3: Use Profile

```python
# Get custom profile
profile = registry.get_profile("custom_profile")

# Use in pipeline
pipeline = RankingPipeline()
for stage in profile.stages:
    pipeline.add_stage(stage)
```

## Adding Custom Normalization Methods

### Step 1: Create Normalization Function

```python
from apps.search.ranking.pipeline import ScoreNormalizer

def custom_normalization(scores: List[float], **kwargs) -> List[float]:
    """
    Custom normalization method.
    
    Args:
        scores: List of scores to normalize
        **kwargs: Method-specific parameters
        
    Returns:
        Normalized scores
    """
    if not scores:
        return []
    
    # Custom normalization logic
    # Example: Square root normalization
    import math
    return [math.sqrt(abs(score)) for score in scores]
```

### Step 2: Use in Pipeline

```python
# Apply custom normalization in stage
stage = PipelineStage(
    name="custom_stage",
    signals=["custom_signal"],
    weights={"custom_signal": 1.0},
    normalization=NormalizationMethod.NONE,  # Use custom
)

# Apply custom normalization manually
scores = [1.0, 4.0, 9.0]
normalized = custom_normalization(scores)
```

## Adding Custom Search Strategies

### Step 1: Create Strategy Class

Extend `SearchStrategy` and implement the search method:

```python
from apps.search.ranking.hybrid import SearchStrategy, StrategyResult, SearchResult

class CustomStrategy(SearchStrategy):
    """Custom search strategy."""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("custom_strategy", weight)
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute custom search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        import time
        
        start_time = time.time()
        
        # Custom search logic
        response = provider.search(
            entity_type=entity_type,
            query=query,
            filters=context.get("filters"),
            sort=context.get("sort"),
            pagination=context.get("pagination"),
            fields=context.get("fields"),
        )
        
        took_ms = (time.time() - start_time) * 1000
        
        # Convert to SearchResult objects
        results = []
        for rank, doc in enumerate(response.get("results", []), start=1):
            # Custom scoring logic
            custom_score = self._calculate_custom_score(doc, context)
            
            result = SearchResult(
                document_id=doc.get("id", ""),
                score=custom_score,
                rank=rank,
                source=self.name,
                document=doc,
                metadata={"custom_score": custom_score},
            )
            results.append(result)
        
        return StrategyResult(
            strategy_name=self.name,
            results=results,
            total=response.get("total", 0),
            took_ms=took_ms,
        )
    
    def _calculate_custom_score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate custom score."""
        # Custom scoring logic
        return document.get("_score", 0.0) * 1.5
```

### Step 2: Register Strategy

```python
from apps.search.ranking.hybrid import HybridSearchEngine

engine = HybridSearchEngine(provider_registry)

# Register custom strategy
custom_strategy = CustomStrategy(weight=1.5)
engine.register_strategy(custom_strategy)
```

## Adding Custom Learning Hooks

### Step 1: Create Hook Class

Extend `LearningHook` and implement feedback processing:

```python
from apps.search.ranking.learning_hooks import LearningHook, FeedbackEvent, FeedbackType

class CustomLearningHook(LearningHook):
    """Custom learning hook for specific feedback type."""
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._custom_metrics = {}
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """Process custom feedback."""
        if not self.enabled:
            return
        
        if event.feedback_type == FeedbackType.CUSTOM:
            self._feedback_events.append(event)
            
            # Custom processing logic
            doc_id = event.document_id
            self._custom_metrics[doc_id] = self._custom_metrics.get(doc_id, 0) + 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get custom feedback summary."""
        return {
            "total_feedback": len(self._feedback_events),
            "custom_metrics": self._custom_metrics,
        }
```

### Step 2: Register Hook

```python
from apps.search.ranking.learning_hooks import LearningHookRegistry

registry = LearningHookRegistry()

# Register custom hook
custom_hook = CustomLearningHook()
registry.register_hook("custom_hook", custom_hook)
```

## Best Practices for Extensions

### Signal Development

- Keep signals focused and single-purpose
- Use efficient data structures and algorithms
- Handle missing data gracefully
- Document scoring logic clearly
- Write comprehensive unit tests
- Profile performance before deployment

### Fusion Algorithm Development

- Test with various result sets
- Handle edge cases (empty results, single result)
- Document fusion logic clearly
- Compare with existing algorithms
- Monitor performance impact

### Business Rule Development

- Use descriptive rule names
- Provide clear reasons for actions
- Set appropriate priority levels
- Test rule interactions
- Monitor rule application rates
- Document rule purpose

### Profile Development

- Focus on specific use cases
- Limit number of stages (3-5 optimal)
- Use appropriate normalization
- Test with real data
- Monitor profile performance
- Document profile differences

### General Extension Guidelines

- Follow existing patterns and conventions
- Maintain backward compatibility
- Add comprehensive documentation
- Write unit tests
- Profile performance
- Monitor in production
- Version custom extensions

## Testing Extensions

### Unit Testing

```python
import unittest

class TestCustomExtension(unittest.TestCase):
    def setUp(self):
        self.extension = CustomExtension()
    
    def test_basic_functionality(self):
        # Test basic functionality
        result = self.extension.method(input_data)
        self.assertEqual(result, expected_output)
    
    def test_edge_cases(self):
        # Test edge cases
        result = self.extension.method(edge_case_input)
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        # Test error handling
        with self.assertRaises(ValueError):
            self.extension.method(invalid_input)
```

### Integration Testing

```python
def test_custom_signal_in_pipeline():
    """Test custom signal in full pipeline."""
    pipeline = RankingPipeline()
    pipeline.register_signal("custom", CustomSignal())
    
    stage = PipelineStage(
        name="test",
        signals=["custom"],
        weights={"custom": 1.0},
    )
    pipeline.add_stage(stage)
    
    results = [{"id": "1", "custom_field": 10}]
    context = {}
    
    ranked, _ = pipeline.execute(results, context)
    assert len(ranked) == 1
    assert "_ranking_score" in ranked[0]
```

### Performance Testing

```python
import time

def test_custom_signal_performance():
    """Test custom signal performance."""
    signal = CustomSignal()
    
    start = time.time()
    for i in range(1000):
        signal.score({"custom_field": i}, {})
    
    duration = time.time() - start
    assert duration < 1.0  # Should complete in < 1 second
```

## Deployment Checklist

### Before Deploying Extensions

- [ ] Code reviewed by team
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance benchmarked
- [ ] Documentation complete
- [ ] Backward compatibility verified
- [ ] Monitoring configured
- [ ] Rollback plan prepared

### After Deployment

- [ ] Monitor performance metrics
- [ ] Monitor error rates
- [ ] Monitor cache hit rates
- [ ] Review signal contributions
- [ ] Review rule application rates
- [ ] Collect user feedback
- [ ] Adjust configuration if needed
