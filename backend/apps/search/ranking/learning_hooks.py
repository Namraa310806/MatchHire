"""
Learning Hooks Interfaces.

This module provides interfaces for future ML-based reranking and learning.
These hooks allow the system to collect feedback and prepare for
machine learning integration without implementing actual models.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    CLICK = "click"
    APPLICATION = "application"
    RECRUITER_INTERACTION = "recruiter_interaction"
    SAVE = "save"
    IGNORE = "ignore"
    INTERVIEW_OUTCOME = "interview_outcome"
    HIRE = "hire"
    REJECT = "reject"


@dataclass
class FeedbackEvent:
    """
    A single feedback event.
    """
    
    feedback_type: FeedbackType
    user_id: str
    document_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "feedback_type": self.feedback_type.value,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "context": self.context,
        }


class LearningHook(ABC):
    """
    Abstract base class for learning hooks.
    
    Learning hooks allow the system to collect feedback and
    prepare for future ML-based reranking.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the learning hook.
        
        Args:
            enabled: Whether the hook is enabled
        """
        self.enabled = enabled
        self._feedback_events: List[FeedbackEvent] = []
    
    @abstractmethod
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process a feedback event.
        
        Args:
            event: Feedback event to process
        """
        pass
    
    @abstractmethod
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected feedback.
        
        Returns:
            Feedback summary statistics
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if hook is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the hook."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the hook."""
        self.enabled = False
    
    def clear_feedback(self) -> None:
        """Clear all collected feedback."""
        self._feedback_events.clear()


class ClickFeedbackHook(LearningHook):
    """
    Hook for collecting click feedback.
    
    Tracks when users click on search results to understand
    which results are most relevant.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the click feedback hook."""
        super().__init__(enabled)
        self._click_count = 0
        self._unique_documents_clicked = set()
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process click feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.CLICK:
            return
        
        self._feedback_events.append(event)
        self._click_count += 1
        self._unique_documents_clicked.add(event.document_id)
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get click feedback summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_clicks": self._click_count,
            "unique_documents_clicked": len(self._unique_documents_clicked),
            "click_rate": self._calculate_click_rate(),
            "most_clicked_documents": self._get_most_clicked_documents(5),
        }
    
    def _calculate_click_rate(self) -> float:
        """Calculate click rate."""
        if not self._feedback_events:
            return 0.0
        
        # Count total impressions (simplified)
        total_impressions = len(set(e.context.get("search_id", "") for e in self._feedback_events))
        
        if total_impressions == 0:
            return 0.0
        
        return self._click_count / total_impressions
    
    def _get_most_clicked_documents(self, n: int) -> List[Dict[str, Any]]:
        """Get most clicked documents."""
        from collections import Counter
        
        doc_counts = Counter(e.document_id for e in self._feedback_events)
        return [
            {"document_id": doc_id, "clicks": count}
            for doc_id, count in doc_counts.most_common(n)
        ]


class ApplicationFeedbackHook(LearningHook):
    """
    Hook for collecting application feedback.
    
    Tracks when users apply to jobs to understand
    which jobs are most attractive and relevant.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the application feedback hook."""
        super().__init__(enabled)
        self._application_count = 0
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process application feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.APPLICATION:
            return
        
        self._feedback_events.append(event)
        self._application_count += 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get application feedback summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_applications": self._application_count,
            "application_rate": self._calculate_application_rate(),
            "most_applied_documents": self._get_most_applied_documents(5),
        }
    
    def _calculate_application_rate(self) -> float:
        """Calculate application rate."""
        if not self._feedback_events:
            return 0.0
        
        # Count total views before application
        total_views = len(self._feedback_events)
        
        if total_views == 0:
            return 0.0
        
        return self._application_count / total_views
    
    def _get_most_applied_documents(self, n: int) -> List[Dict[str, Any]]:
        """Get most applied documents."""
        from collections import Counter
        
        doc_counts = Counter(e.document_id for e in self._feedback_events)
        return [
            {"document_id": doc_id, "applications": count}
            for doc_id, count in doc_counts.most_common(n)
        ]


class RecruiterInteractionHook(LearningHook):
    """
    Hook for collecting recruiter interaction feedback.
    
    Tracks recruiter interactions with candidates to understand
    which candidates are most interesting to recruiters.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the recruiter interaction hook."""
        super().__init__(enabled)
        self._interaction_count = 0
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process recruiter interaction feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.RECRUITER_INTERACTION:
            return
        
        self._feedback_events.append(event)
        self._interaction_count += 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get recruiter interaction summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_interactions": self._interaction_count,
            "interaction_types": self._get_interaction_types(),
            "most_interacted_candidates": self._get_most_interacted_candidates(5),
        }
    
    def _get_interaction_types(self) -> Dict[str, int]:
        """Get breakdown of interaction types."""
        from collections import Counter
        
        interaction_types = Counter(
            e.metadata.get("interaction_type", "unknown")
            for e in self._feedback_events
        )
        return dict(interaction_types)
    
    def _get_most_interacted_candidates(self, n: int) -> List[Dict[str, Any]]:
        """Get most interacted candidates."""
        from collections import Counter
        
        doc_counts = Counter(e.document_id for e in self._feedback_events)
        return [
            {"document_id": doc_id, "interactions": count}
            for doc_id, count in doc_counts.most_common(n)
        ]


class SavedJobHook(LearningHook):
    """
    Hook for collecting saved job feedback.
    
    Tracks when users save jobs to understand
    which jobs are most interesting.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the saved job hook."""
        super().__init__(enabled)
        self._save_count = 0
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process saved job feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.SAVE:
            return
        
        self._feedback_events.append(event)
        self._save_count += 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get saved job summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_saves": self._save_count,
            "most_saved_jobs": self._get_most_saved_jobs(5),
        }
    
    def _get_most_saved_jobs(self, n: int) -> List[Dict[str, Any]]:
        """Get most saved jobs."""
        from collections import Counter
        
        doc_counts = Counter(e.document_id for e in self._feedback_events)
        return [
            {"document_id": doc_id, "saves": count}
            for doc_id, count in doc_counts.most_common(n)
        ]


class IgnoredJobHook(LearningHook):
    """
    Hook for collecting ignored job feedback.
    
    Tracks when users ignore jobs to understand
    which jobs are not relevant.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the ignored job hook."""
        super().__init__(enabled)
        self._ignore_count = 0
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process ignored job feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.IGNORE:
            return
        
        self._feedback_events.append(event)
        self._ignore_count += 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get ignored job summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_ignores": self._ignore_count,
            "most_ignored_jobs": self._get_most_ignored_jobs(5),
        }
    
    def _get_most_ignored_jobs(self, n: int) -> List[Dict[str, Any]]:
        """Get most ignored jobs."""
        from collections import Counter
        
        doc_counts = Counter(e.document_id for e in self._feedback_events)
        return [
            {"document_id": doc_id, "ignores": count}
            for doc_id, count in doc_counts.most_common(n)
        ]


class InterviewOutcomeHook(LearningHook):
    """
    Hook for collecting interview outcome feedback.
    
    Tracks interview outcomes to understand
    which candidates perform best in interviews.
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize the interview outcome hook."""
        super().__init__(enabled)
        self._outcome_counts: Dict[str, int] = {}
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process interview outcome feedback.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        if event.feedback_type != FeedbackType.INTERVIEW_OUTCOME:
            return
        
        self._feedback_events.append(event)
        
        outcome = event.metadata.get("outcome", "unknown")
        self._outcome_counts[outcome] = self._outcome_counts.get(outcome, 0) + 1
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get interview outcome summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_interviews": len(self._feedback_events),
            "outcome_breakdown": self._outcome_counts,
            "success_rate": self._calculate_success_rate(),
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate interview success rate."""
        total = len(self._feedback_events)
        if total == 0:
            return 0.0
        
        successful = self._outcome_counts.get("offer", 0) + self._outcome_counts.get("hired", 0)
        return successful / total


class MLRerankingHook(LearningHook):
    """
    Hook for future ML-based reranking.
    
    This is an interface for future ML model integration.
    The hook does not train models but provides the structure
    for ML-based reranking in the future.
    """
    
    def __init__(self, enabled: bool = False):
        """Initialize the ML reranking hook."""
        super().__init__(enabled)
        self._model_version = None
        self._model_type = None
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process feedback for ML training.
        
        Args:
            event: Feedback event
        """
        if not self.enabled:
            return
        
        # Store feedback for future model training
        self._feedback_events.append(event)
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get ML feedback summary.
        
        Returns:
            Feedback summary
        """
        return {
            "total_feedback": len(self._feedback_events),
            "model_version": self._model_version,
            "model_type": self._model_type,
            "note": "ML reranking not yet implemented",
        }
    
    def set_model_info(self, model_version: str, model_type: str) -> None:
        """
        Set model information for future use.
        
        Args:
            model_version: Model version
            model_type: Model type
        """
        self._model_version = model_version
        self._model_type = model_type
    
    def predict_score(
        self,
        document: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Optional[float]:
        """
        Predict score using ML model (interface for future implementation).
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Predicted score or None if not implemented
        """
        # Placeholder for future ML model
        # This would load and use a trained model to predict scores
        return None
    
    def rerank(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using ML model (interface for future implementation).
        
        Args:
            results: Search results to rerank
            context: Search context
            
        Returns:
            Reranked results
        """
        # Placeholder for future ML reranking
        # This would use the ML model to rerank results
        return results


class LearningHookRegistry:
    """
    Registry for managing learning hooks.
    
    Provides methods to register, retrieve, and manage
    learning hooks for different feedback types.
    """
    
    def __init__(self):
        """Initialize the learning hook registry."""
        self._hooks: Dict[str, LearningHook] = {}
        
        # Register default hooks
        self._register_default_hooks()
    
    def _register_default_hooks(self) -> None:
        """Register default learning hooks."""
        self.register_hook("click", ClickFeedbackHook())
        self.register_hook("application", ApplicationFeedbackHook())
        self.register_hook("recruiter_interaction", RecruiterInteractionHook())
        self.register_hook("save", SavedJobHook())
        self.register_hook("ignore", IgnoredJobHook())
        self.register_hook("interview_outcome", InterviewOutcomeHook())
        self.register_hook("ml_reranking", MLRerankingHook(enabled=False))
    
    def register_hook(self, name: str, hook: LearningHook) -> None:
        """
        Register a learning hook.
        
        Args:
            name: Hook name
            hook: Learning hook to register
        """
        self._hooks[name] = hook
    
    def unregister_hook(self, name: str) -> bool:
        """
        Unregister a learning hook.
        
        Args:
            name: Hook name
            
        Returns:
            True if hook was unregistered, False if not found
        """
        if name in self._hooks:
            del self._hooks[name]
            return True
        return False
    
    def get_hook(self, name: str) -> Optional[LearningHook]:
        """
        Get a learning hook by name.
        
        Args:
            name: Hook name
            
        Returns:
            Learning hook or None if not found
        """
        return self._hooks.get(name)
    
    def process_feedback(self, event: FeedbackEvent) -> None:
        """
        Process feedback through all enabled hooks.
        
        Args:
            event: Feedback event
        """
        for hook in self._hooks.values():
            if hook.is_enabled():
                try:
                    hook.process_feedback(event)
                except Exception as e:
                    print(f"Hook {hook.__class__.__name__} failed: {e}")
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """
        Get feedback summaries from all hooks.
        
        Returns:
            Dictionary of hook names to summaries
        """
        summaries = {}
        for name, hook in self._hooks.items():
            try:
                summaries[name] = hook.get_feedback_summary()
            except Exception as e:
                summaries[name] = {"error": str(e)}
        return summaries
    
    def enable_hook(self, name: str) -> bool:
        """
        Enable a hook by name.
        
        Args:
            name: Hook name
            
        Returns:
            True if hook was enabled, False if not found
        """
        hook = self.get_hook(name)
        if hook:
            hook.enable()
            return True
        return False
    
    def disable_hook(self, name: str) -> bool:
        """
        Disable a hook by name.
        
        Args:
            name: Hook name
            
        Returns:
            True if hook was disabled, False if not found
        """
        hook = self.get_hook(name)
        if hook:
            hook.disable()
            return True
        return False
    
    def clear_all_feedback(self) -> None:
        """Clear all feedback from all hooks."""
        for hook in self._hooks.values():
            hook.clear_feedback()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry state to dictionary representation."""
        return {
            "hooks": {
                name: {
                    "type": hook.__class__.__name__,
                    "enabled": hook.is_enabled(),
                    "summary": hook.get_feedback_summary(),
                }
                for name, hook in self._hooks.items()
            },
            "hook_count": len(self._hooks),
        }
