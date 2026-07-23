# Extension Guide

## Overview

The recommendation engine is designed for easy extension. This guide provides detailed instructions for extending the engine with new components.

## Adding New Recommendation Types

### Step 1: Define the Recommendation Type

```python
from apps.search.recommendations.candidate_recommendations import CandidateRecommendationGenerator
from apps.search.query_engine import SearchExecutionContext

class CustomCandidateRecommendation(CandidateRecommendationGenerator):
    def generate(self, job_id: str, context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters=self._build_filters(context),
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": "custom_type",
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        return result.results
    
    def _build_filters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Custom filter logic
        return {}
```

### Step 2: Register with Provider

```python
from apps.search.recommendations.providers import CandidateRecommendationProvider

class CustomCandidateProvider(CandidateRecommendationProvider):
    def generate_candidates(self, entity_id: str, context: Dict[str, Any], limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        generator = CustomCandidateRecommendation(self._query_engine)
        return generator.generate(entity_id, context, limit)

# Register the provider
registry = RecommendationRegistry()
registry.register_provider(CustomCandidateProvider(query_engine))
```

## Adding New Strategies

### Step 1: Define the Strategy

```python
from apps.search.recommendations.strategies import RecommendationStrategy, StrategyConfig

class CustomStrategy(RecommendationStrategy):
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.CONTENT_BASED
    
    def generate_candidates(self, entity_id: str, context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        # Custom candidate generation logic
        candidates = []
        # ... generate candidates ...
        return candidates
```

### Step 2: Use the Strategy

```python
# Use standalone
strategy = CustomStrategy(config)
candidates = strategy.generate_candidates(entity_id, context, limit)

# Use in composition
composition = StrategyComposition([CustomStrategy(), ContentBasedStrategy()])
candidates = composition.compose(entity_id, context, limit, method="weighted")
```

## Adding New Signals

### Step 1: Define the Signal

```python
from apps.search.ranking.signals import BaseSignal, SignalConfig

class CustomSignal(BaseSignal):
    @property
    def signal_type(self) -> SignalType:
        return SignalType.METADATA
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        # Custom scoring logic
        score = 0.0
        # ... calculate score ...
        return score
```

### Step 2: Register with Ranking Pipeline

```python
from apps.search.ranking.pipeline import RankingPipeline

pipeline = RankingPipeline()
pipeline.register_signal("custom_signal", CustomSignal())
```

### Step 3: Add to Pipeline Stage

```python
from apps.search.ranking.pipeline import PipelineStage

stage = PipelineStage(
    name="custom_signals",
    signals=["custom_signal"],
    weights={"custom_signal": 1.0},
)
pipeline.add_stage(stage)
```

## Adding New Diversifiers

### Step 1: Define the Diversifier

```python
from apps.search.recommendations.diversification import Diversifier, DiversificationConfig, DiversificationType

class CustomDiversifier(Diversifier):
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.DEDUPLICATION
    
    def diversify(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Custom diversification logic
        diversified = []
        # ... diversify candidates ...
        return diversified
```

### Step 2: Add to Diversification Engine

```python
from apps.search.recommendations.diversification import DiversificationEngine

engine = DiversificationEngine()
engine.add_diversifier(CustomDiversifier())
```

## Adding New Explanation Types

### Step 1: Define the Explanation Generator

```python
from apps.search.recommendations.explanation import ExplanationGenerator, RecommendationExplanation, ExplanationType

class CustomExplanationGenerator(ExplanationGenerator):
    def generate(self, candidate: Dict[str, Any], context: Dict[str, Any]) -> RecommendationExplanation:
        item_id = candidate.get("id", "")
        
        # Custom explanation logic
        primary_reason = "Custom reason"
        secondary_reasons = ["Reason 1", "Reason 2"]
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.WHY_RECOMMENDED,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=0.8,
        )
```

### Step 2: Add to Explanation Builder

```python
from apps.search.recommendations.explanation import ExplanationBuilder

builder = ExplanationBuilder()
builder.add_explanation_generator(ExplanationType.WHY_RECOMMENDED, CustomExplanationGenerator())
```

## Adding New Learning Hooks

### Step 1: Define the Learning Hook

```python
from apps.search.recommendations.learning_hooks import RecommendationLearningHook, FeedbackEvent, FeedbackType

class CustomLearningHook(RecommendationLearningHook):
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.CLICK
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        # Custom feedback processing logic
        # Update user preferences
        # Adjust strategy weights
        # Update ML models
        pass
```

### Step 2: Register with Learning Hook Registry

```python
from apps.search.recommendations.learning_hooks import LearningHookRegistry

registry = LearningHookRegistry()
registry.register_hook(CustomLearningHook())
```

## Adding Custom Pipeline Stages

### Step 1: Define the Stage Logic

```python
def custom_stage_logic(candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Custom stage logic
    processed = []
    for candidate in candidates:
        # Process candidate
        processed.append(candidate)
    return processed
```

### Step 2: Add to Pipeline

```python
from apps.search.recommendations.pipeline import PipelineStage, PipelineStageType

stage = PipelineStage(
    name="custom_stage",
    stage_type=PipelineStageType.FILTERING,
    enabled=True,
    config={"custom_param": "value"},
)

pipeline.add_stage(stage)
```

## Integrating Collaborative Filtering

### Step 1: Use the Collaborative Filtering Hook

```python
from apps.search.recommendations.learning_hooks import CollaborativeFilteringHook

hook = CollaborativeFilteringHook()
registry = LearningHookRegistry()
registry.register_hook(hook)
```

### Step 2: Process Feedback

```python
from apps.search.recommendations.learning_hooks import FeedbackEvent, FeedbackType

event = FeedbackEvent(
    event_type=FeedbackType.VIEW,
    user_id="user_123",
    item_id="item_456",
    recommendation_id="rec_789",
    timestamp=datetime.now(),
    context={},
    metadata={},
)

registry.process_feedback(event)
```

### Step 3: Get Similar Users/Items

```python
# Get similar users
similar_users = hook.get_similar_users("user_123", limit=10)

# Get similar items
similar_items = hook.get_similar_items("item_456", limit=10)
```

## Integrating ML Models

### Step 1: Use the ML Recommendation Hook

```python
from apps.search.recommendations.learning_hooks import MLRecommendationHook

hook = MLRecommendationHook()
registry = LearningHookRegistry()
registry.register_hook(hook)
```

### Step 2: Load Pre-trained Model

```python
hook.load_model("path/to/model.pkl")
```

### Step 3: Train Model

```python
training_data = [
    {"user_id": "user_1", "item_id": "item_1", "label": 1},
    # ... more data ...
]

hook.train_model(training_data)
```

### Step 4: Use Embeddings

```python
# Get item embedding
embedding = hook.get_embedding("item_123")

# Compute similarity
similarity = hook.compute_similarity("item_1", "item_2")
```

## Custom Configuration

### Step 1: Define Custom Config

```python
from apps.search.recommendations.config import RecommendationConfig

class CustomRecommendationConfig(RecommendationConfig):
    def __init__(self):
        super().__init__()
        self.custom_param = "value"
        self.enable_custom_feature = True
```

### Step 2: Use Custom Config

```python
config = CustomRecommendationConfig()
engine = RecommendationEngine(
    query_engine=query_engine,
    ranking_pipeline=ranking_pipeline,
    recommendation_registry=registry,
    config=config.to_dict(),
)
```

## Testing Extensions

### Unit Tests

```python
import pytest
from apps.search.recommendations.signals import CustomSignal

def test_custom_signal():
    signal = CustomSignal()
    document = {"id": "test", "field": "value"}
    context = {}
    score = signal.score(document, context)
    assert 0 <= score <= 1
```

### Integration Tests

```python
def test_custom_strategy_integration():
    strategy = CustomStrategy()
    candidates = strategy.generate_candidates("entity_123", {}, 10)
    assert isinstance(candidates, list)
```

## Best Practices

### 1. Follow Existing Patterns

Study existing implementations and follow the same patterns:
- Use abstract base classes
- Implement required methods
- Follow naming conventions
- Use type hints

### 2. Provide Configuration

Make your extension configurable:
- Use config classes
- Provide sensible defaults
- Document configuration options

### 3. Handle Errors Gracefully

- Use try-except blocks
- Log errors appropriately
- Provide fallback behavior
- Don't crash the pipeline

### 4. Monitor Performance

- Track execution time
- Monitor resource usage
- Profile bottlenecks
- Optimize hot paths

### 5. Write Tests

- Write unit tests
- Write integration tests
- Test edge cases
- Test error conditions

### 6. Document Your Code

- Add docstrings
- Document parameters
- Document return values
- Provide examples

## Common Extension Patterns

### Plugin Pattern

```python
class Plugin:
    def __init__(self, config):
        self.config = config
    
    def execute(self, data):
        # Plugin logic
        return processed_data

class PluginRegistry:
    def __init__(self):
        self.plugins = []
    
    def register(self, plugin):
        self.plugins.append(plugin)
    
    def execute_all(self, data):
        for plugin in self.plugins:
            data = plugin.execute(data)
        return data
```

### Strategy Pattern

```python
class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class ConcreteStrategy(Strategy):
    def execute(self, data):
        # Implementation
        return result

class Context:
    def __init__(self, strategy):
        self.strategy = strategy
    
    def execute(self, data):
        return self.strategy.execute(data)
```

### Observer Pattern

```python
class Observer(ABC):
    @abstractmethod
    def update(self, event):
        pass

class Subject:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.update(event)
```

## Future Extension Points

The architecture is ready for:

- **Graph-based Recommendations**: Add network analysis components
- **Time-series Recommendations**: Add temporal pattern recognition
- **Multi-objective Optimization**: Add Pareto optimization
- **Reinforcement Learning**: Add RL-based recommendation
- **Federated Learning**: Add privacy-preserving learning
- **Explainable AI**: Add XAI techniques
- **Causal Inference**: Add causal recommendation models
