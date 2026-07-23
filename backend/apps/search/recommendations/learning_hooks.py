"""
Learning Hooks for Recommendations.

This module provides interfaces for future ML-based recommendations.
These hooks allow the system to learn from user interactions and
improve recommendations over time without requiring redesign.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


class FeedbackType(Enum):
    """Types of feedback for learning."""
    CLICK = "click"
    APPLICATION = "application"
    HIRE = "hire"
    BOOKMARK = "bookmark"
    IGNORE = "ignore"
    RECRUITER_ACTION = "recruiter_action"
    VIEW = "view"
    SAVE = "save"


@dataclass
class FeedbackEvent:
    """
    A feedback event for learning.
    
    Contains information about a user interaction with a recommendation.
    """
    
    event_type: FeedbackType
    user_id: str
    item_id: str
    recommendation_id: str
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "recommendation_id": self.recommendation_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }


class RecommendationLearningHook(ABC):
    """
    Abstract base class for recommendation learning hooks.
    
    Each hook handles a specific type of user feedback for learning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the learning hook.
        
        Args:
            config: Hook configuration
        """
        self._config = config or {}
        self._enabled = True
    
    @property
    def feedback_type(self) -> FeedbackType:
        """Get the feedback type."""
        return FeedbackType.CLICK
    
    @abstractmethod
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process a feedback event.
        
        Args:
            event: Feedback event to process
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if hook is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the hook."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the hook."""
        self._enabled = False


class ClickHook(RecommendationLearningHook):
    """
    Click feedback hook.
    
    Tracks when users click on recommendations to learn preferences.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.CLICK
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process click feedback.
        
        Args:
            event: Click feedback event
        """
        # In a real implementation, this would:
        # 1. Update user preferences based on clicked items
        # 2. Track click-through rates
        # 3. Adjust recommendation weights
        # 4. Store for collaborative filtering
        
        # For now, this is an interface for future implementation
        pass


class ApplicationHook(RecommendationLearningHook):
    """
    Application feedback hook.
    
    Tracks when users apply to jobs recommended to them.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.APPLICATION
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process application feedback.
        
        Args:
            event: Application feedback event
        """
        # In a real implementation, this would:
        # 1. Strong positive signal for the recommendation
        # 2. Update user job preferences
        # 3. Learn from successful applications
        # 4. Improve future job recommendations
        
        pass


class HireHook(RecommendationLearningHook):
    """
    Hire feedback hook.
    
    Tracks when recruiters hire candidates recommended to them.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.HIRE
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process hire feedback.
        
        Args:
            event: Hire feedback event
        """
        # In a real implementation, this would:
        # 1. Strong positive signal for candidate recommendations
        # 2. Update recruiter preferences
        # 3. Learn from successful hires
        # 4. Improve future candidate recommendations
        
        pass


class BookmarkHook(RecommendationLearningHook):
    """
    Bookmark feedback hook.
    
    Tracks when users bookmark/save recommendations.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.BOOKMARK
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process bookmark feedback.
        
        Args:
            event: Bookmark feedback event
        """
        # In a real implementation, this would:
        # 1. Positive signal for the recommendation
        # 2. Update user preferences
        # 3. Track saved items for future reference
        
        pass


class IgnoredRecommendationHook(RecommendationLearningHook):
    """
    Ignored recommendation feedback hook.
    
    Tracks when users ignore recommendations.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.IGNORE
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process ignored recommendation feedback.
        
        Args:
            event: Ignore feedback event
        """
        # In a real implementation, this would:
        # 1. Negative signal for the recommendation
        # 2. Update user preferences to avoid similar items
        # 3. Adjust recommendation weights
        
        pass


class RecruiterActionHook(RecommendationLearningHook):
    """
    Recruiter action feedback hook.
    
    Tracks recruiter actions on candidate recommendations.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.RECRUITER_ACTION
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process recruiter action feedback.
        
        Args:
            event: Recruiter action feedback event
        """
        # In a real implementation, this would:
        # 1. Track recruiter interactions with candidates
        # 2. Update recruiter preferences
        # 3. Improve candidate recommendations for recruiters
        
        pass


class CollaborativeFilteringHook(RecommendationLearningHook):
    """
    Collaborative filtering hook.
    
    Implements collaborative filtering based on user similarity.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.VIEW
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the collaborative filtering hook.
        
        Args:
            config: Hook configuration
        """
        super().__init__(config)
        self._user_item_matrix: Dict[str, Dict[str, float]] = {}
        self._item_user_matrix: Dict[str, Dict[str, float]] = {}
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process feedback for collaborative filtering.
        
        Args:
            event: Feedback event
        """
        user_id = event.user_id
        item_id = event.item_id
        
        # Update user-item matrix
        if user_id not in self._user_item_matrix:
            self._user_item_matrix[user_id] = {}
        
        # Increment interaction count
        self._user_item_matrix[user_id][item_id] = \
            self._user_item_matrix[user_id].get(item_id, 0) + 1
        
        # Update item-user matrix
        if item_id not in self._item_user_matrix:
            self._item_user_matrix[item_id] = {}
        
        self._item_user_matrix[item_id][user_id] = \
            self._item_user_matrix[item_id].get(user_id, 0) + 1
    
    def get_similar_users(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[tuple]:
        """
        Get similar users based on interaction patterns.
        
        Args:
            user_id: User ID
            limit: Maximum number of similar users
            
        Returns:
            List of (user_id, similarity_score) tuples
        """
        if user_id not in self._user_item_matrix:
            return []
        
        user_items = set(self._user_item_matrix[user_id].keys())
        similarities = []
        
        for other_user_id, other_items in self._user_item_matrix.items():
            if other_user_id == user_id:
                continue
            
            other_item_set = set(other_items.keys())
            
            # Calculate Jaccard similarity
            intersection = len(user_items & other_item_set)
            union = len(user_items | other_item_set)
            
            if union > 0:
                similarity = intersection / union
                similarities.append((other_user_id, similarity))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def get_similar_items(
        self,
        item_id: str,
        limit: int = 10,
    ) -> List[tuple]:
        """
        Get similar items based on user interaction patterns.
        
        Args:
            item_id: Item ID
            limit: Maximum number of similar items
            
        Returns:
            List of (item_id, similarity_score) tuples
        """
        if item_id not in self._item_user_matrix:
            return []
        
        item_users = set(self._item_user_matrix[item_id].keys())
        similarities = []
        
        for other_item_id, other_users in self._item_user_matrix.items():
            if other_item_id == item_id:
                continue
            
            other_user_set = set(other_users.keys())
            
            # Calculate Jaccard similarity
            intersection = len(item_users & other_user_set)
            union = len(item_users | other_user_set)
            
            if union > 0:
                similarity = intersection / union
                similarities.append((other_item_id, similarity))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


class MLRecommendationHook(RecommendationLearningHook):
    """
    ML-based recommendation hook.
    
    Interface for future ML-based recommendations using embeddings,
    neural networks, etc.
    """
    
    @property
    def feedback_type(self) -> FeedbackType:
        return FeedbackType.VIEW
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ML recommendation hook.
        
        Args:
            config: Hook configuration
        """
        super().__init__(config)
        self._model = None
        self._embeddings: Dict[str, Any] = {}
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process feedback for ML learning.
        
        Args:
            event: Feedback event
        """
        # In a real implementation, this would:
        # 1. Update ML model with new feedback
        # 2. Retrain model periodically
        # 3. Update embeddings
        # 4. Store for online learning
        
        # For now, this is an interface for future ML implementation
        pass
    
    def load_model(self, model_path: str) -> None:
        """
        Load a pre-trained ML model.
        
        Args:
            model_path: Path to the model file
        """
        # Interface for future ML model loading
        pass
    
    def train_model(
        self,
        training_data: List[Dict[str, Any]],
    ) -> None:
        """
        Train an ML model on the provided data.
        
        Args:
            training_data: Training data
        """
        # Interface for future ML model training
        pass
    
    def get_embedding(
        self,
        item_id: str,
    ) -> Optional[Any]:
        """
        Get embedding for an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            Item embedding or None
        """
        return self._embeddings.get(item_id)
    
    def compute_similarity(
        self,
        item_id1: str,
        item_id2: str,
    ) -> float:
        """
        Compute similarity between two items using embeddings.
        
        Args:
            item_id1: First item ID
            item_id2: Second item ID
            
        Returns:
            Similarity score
        """
        # Interface for future similarity computation using embeddings
        return 0.0


class LearningHookRegistry:
    """
    Registry for learning hooks.
    
    Manages registration and execution of learning hooks.
    """
    
    def __init__(self):
        """Initialize the learning hook registry."""
        self._hooks: Dict[FeedbackType, List[RecommendationLearningHook]] = {}
        
        # Register default hooks
        self.register_hook(ClickHook())
        self.register_hook(ApplicationHook())
        self.register_hook(HireHook())
        self.register_hook(BookmarkHook())
        self.register_hook(IgnoredRecommendationHook())
        self.register_hook(RecruiterActionHook())
        self.register_hook(CollaborativeFilteringHook())
        self.register_hook(MLRecommendationHook())
    
    def register_hook(self, hook: RecommendationLearningHook) -> None:
        """
        Register a learning hook.
        
        Args:
            hook: Hook to register
        """
        feedback_type = hook.feedback_type
        if feedback_type not in self._hooks:
            self._hooks[feedback_type] = []
        self._hooks[feedback_type].append(hook)
    
    def unregister_hook(
        self,
        feedback_type: FeedbackType,
        hook: RecommendationLearningHook,
    ) -> None:
        """
        Unregister a learning hook.
        
        Args:
            feedback_type: Feedback type
            hook: Hook to unregister
        """
        if feedback_type in self._hooks:
            self._hooks[feedback_type] = [
                h for h in self._hooks[feedback_type] if h != hook
            ]
    
    def process_feedback(
        self,
        event: FeedbackEvent,
    ) -> None:
        """
        Process feedback through all relevant hooks.
        
        Args:
            event: Feedback event
        """
        feedback_type = event.event_type
        
        if feedback_type in self._hooks:
            for hook in self._hooks[feedback_type]:
                if hook.is_enabled():
                    try:
                        hook.process_feedback(event)
                    except Exception as e:
                        # Log error but continue with other hooks
                        print(f"Hook {hook.__class__.__name__} failed: {e}")
    
    def get_hooks(
        self,
        feedback_type: Optional[FeedbackType] = None,
    ) -> List[RecommendationLearningHook]:
        """
        Get registered hooks.
        
        Args:
            feedback_type: Feedback type filter (None for all)
            
        Returns:
            List of hooks
        """
        if feedback_type:
            return self._hooks.get(feedback_type, [])
        
        all_hooks = []
        for hooks in self._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks
    
    def enable_hook(
        self,
        feedback_type: FeedbackType,
        hook_index: int = 0,
    ) -> None:
        """
        Enable a specific hook.
        
        Args:
            feedback_type: Feedback type
            hook_index: Index of hook to enable
        """
        if feedback_type in self._hooks and hook_index < len(self._hooks[feedback_type]):
            self._hooks[feedback_type][hook_index].enable()
    
    def disable_hook(
        self,
        feedback_type: FeedbackType,
        hook_index: int = 0,
    ) -> None:
        """
        Disable a specific hook.
        
        Args:
            feedback_type: Feedback type
            hook_index: Index of hook to disable
        """
        if feedback_type in self._hooks and hook_index < len(self._hooks[feedback_type]):
            self._hooks[feedback_type][hook_index].disable()
