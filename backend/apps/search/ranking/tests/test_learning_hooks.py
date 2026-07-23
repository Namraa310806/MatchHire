"""
Tests for learning hooks interfaces.
"""

import unittest
from datetime import datetime
from apps.search.ranking.learning_hooks import (
    FeedbackType,
    FeedbackEvent,
    LearningHook,
    ClickFeedbackHook,
    ApplicationFeedbackHook,
    RecruiterInteractionHook,
    SavedJobHook,
    IgnoredJobHook,
    InterviewOutcomeHook,
    MLRerankingHook,
    LearningHookRegistry,
)


class TestFeedbackEvent(unittest.TestCase):
    """Test cases for FeedbackEvent."""
    
    def test_event_creation(self):
        """Test creating a feedback event."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.assertEqual(event.feedback_type, FeedbackType.CLICK)
        self.assertEqual(event.user_id, "user1")
        self.assertEqual(event.document_id, "doc1")
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        event_dict = event.to_dict()
        self.assertEqual(event_dict["feedback_type"], "click")
        self.assertEqual(event_dict["user_id"], "user1")


class TestClickFeedbackHook(unittest.TestCase):
    """Test cases for ClickFeedbackHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = ClickFeedbackHook()
    
    def test_hook_creation(self):
        """Test creating a click feedback hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(self.hook._click_count, 0)
    
    def test_process_feedback(self):
        """Test processing click feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._click_count, 1)
        self.assertIn("doc1", self.hook._unique_documents_clicked)
    
    def test_process_feedback_disabled(self):
        """Test processing feedback when disabled."""
        self.hook.disable()
        
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._click_count, 0)
    
    def test_process_feedback_wrong_type(self):
        """Test processing wrong feedback type."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.APPLICATION,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._click_count, 0)
    
    def test_get_feedback_summary(self):
        """Test getting feedback summary."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
            context={"search_id": "search1"},
        )
        
        self.hook.process_feedback(event)
        self.hook.process_feedback(event)
        
        summary = self.hook.get_feedback_summary()
        
        self.assertEqual(summary["total_clicks"], 2)
        self.assertEqual(summary["unique_documents_clicked"], 1)


class TestApplicationFeedbackHook(unittest.TestCase):
    """Test cases for ApplicationFeedbackHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = ApplicationFeedbackHook()
    
    def test_hook_creation(self):
        """Test creating an application feedback hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(self.hook._application_count, 0)
    
    def test_process_feedback(self):
        """Test processing application feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.APPLICATION,
            user_id="user1",
            document_id="job1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._application_count, 1)
    
    def test_get_feedback_summary(self):
        """Test getting feedback summary."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.APPLICATION,
            user_id="user1",
            document_id="job1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        summary = self.hook.get_feedback_summary()
        
        self.assertEqual(summary["total_applications"], 1)


class TestRecruiterInteractionHook(unittest.TestCase):
    """Test cases for RecruiterInteractionHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = RecruiterInteractionHook()
    
    def test_hook_creation(self):
        """Test creating a recruiter interaction hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(self.hook._interaction_count, 0)
    
    def test_process_feedback(self):
        """Test processing recruiter interaction feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.RECRUITER_INTERACTION,
            user_id="recruiter1",
            document_id="candidate1",
            timestamp=datetime.now(),
            metadata={"interaction_type": "view"},
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._interaction_count, 1)
    
    def test.get_feedback_summary(self):
        """Test getting feedback summary."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.RECRUITER_INTERACTION,
            user_id="recruiter1",
            document_id="candidate1",
            timestamp=datetime.now(),
            metadata={"interaction_type": "view"},
        )
        
        self.hook.process_feedback(event)
        
        summary = self.hook.get_feedback_summary()
        
        self.assertEqual(summary["total_interactions"], 1)
        self.assertIn("view", summary["interaction_types"])


class TestSavedJobHook(unittest.TestCase):
    """Test cases for SavedJobHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = SavedJobHook()
    
    def test_hook_creation(self):
        """Test creating a saved job hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(self.hook._save_count, 0)
    
    def test_process_feedback(self):
        """Test processing saved job feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.SAVE,
            user_id="user1",
            document_id="job1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._save_count, 1)


class TestIgnoredJobHook(unittest.TestCase):
    """Test cases for IgnoredJobHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = IgnoredJobHook()
    
    def test_hook_creation(self):
        """Test creating an ignored job hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(self.hook._ignore_count, 0)
    
    def test_process_feedback(self):
        """Test processing ignored job feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.IGNORE,
            user_id="user1",
            document_id="job1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._ignore_count, 1)


class TestInterviewOutcomeHook(unittest.TestCase):
    """Test cases for InterviewOutcomeHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = InterviewOutcomeHook()
    
    def test_hook_creation(self):
        """Test creating an interview outcome hook."""
        self.assertTrue(self.hook.is_enabled())
        self.assertEqual(len(self.hook._outcome_counts), 0)
    
    def test_process_feedback(self):
        """Test processing interview outcome feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.INTERVIEW_OUTCOME,
            user_id="recruiter1",
            document_id="candidate1",
            timestamp=datetime.now(),
            metadata={"outcome": "offer"},
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(self.hook._outcome_counts.get("offer"), 1)
    
    def test_get_feedback_summary(self):
        """Test getting feedback summary."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.INTERVIEW_OUTCOME,
            user_id="recruiter1",
            document_id="candidate1",
            timestamp=datetime.now(),
            metadata={"outcome": "offer"},
        )
        
        self.hook.process_feedback(event)
        
        summary = self.hook.get_feedback_summary()
        
        self.assertEqual(summary["total_interviews"], 1)
        self.assertEqual(summary["outcome_breakdown"]["offer"], 1)


class TestMLRerankingHook(unittest.TestCase):
    """Test cases for MLRerankingHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hook = MLRerankingHook(enabled=False)
    
    def test_hook_creation(self):
        """Test creating an ML reranking hook."""
        self.assertFalse(self.hook.is_enabled())
        self.assertIsNone(self.hook._model_version)
    
    def test_process_feedback(self):
        """Test processing feedback for ML training."""
        self.hook.enable()
        
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.hook.process_feedback(event)
        
        self.assertEqual(len(self.hook._feedback_events), 1)
    
    def test_set_model_info(self):
        """Test setting model information."""
        self.hook.set_model_info("v1.0", "neural_network")
        
        self.assertEqual(self.hook._model_version, "v1.0")
        self.assertEqual(self.hook._model_type, "neural_network")
    
    def test_predict_score(self):
        """Test predicting score (interface)."""
        document = {"id": "doc1"}
        context = {"query": "test"}
        
        score = self.hook.predict_score(document, context)
        
        # Should return None as not implemented
        self.assertIsNone(score)
    
    def test_rerank(self):
        """Test reranking (interface)."""
        results = [{"id": "doc1"}, {"id": "doc2"}]
        context = {"query": "test"}
        
        reranked = self.hook.rerank(results, context)
        
        # Should return unchanged results
        self.assertEqual(len(reranked), 2)


class TestLearningHookRegistry(unittest.TestCase):
    """Test cases for LearningHookRegistry."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = LearningHookRegistry()
    
    def test_registry_creation(self):
        """Test creating a learning hook registry."""
        self.assertIsNotNone(self.registry)
        self.assertGreater(len(self.registry._hooks), 0)
    
    def test_register_hook(self):
        """Test registering a hook."""
        hook = ClickFeedbackHook()
        self.registry.register_hook("custom_click", hook)
        
        self.assertIn("custom_click", self.registry._hooks)
    
    def test_unregister_hook(self):
        """Test unregistering a hook."""
        self.assertTrue(self.registry.unregister_hook("click"))
        self.assertNotIn("click", self.registry._hooks)
    
    def test_get_hook(self):
        """Test getting a hook."""
        hook = self.registry.get_hook("click")
        
        self.assertIsNotNone(hook)
        self.assertIsInstance(hook, ClickFeedbackHook)
    
    def test_process_feedback(self):
        """Test processing feedback through all hooks."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.registry.process_feedback(event)
        
        # Click hook should have processed the event
        click_hook = self.registry.get_hook("click")
        self.assertEqual(click_hook._click_count, 1)
    
    def test_get_all_summaries(self):
        """Test getting all hook summaries."""
        summaries = self.registry.get_all_summaries()
        
        self.assertIsInstance(summaries, dict)
        self.assertIn("click", summaries)
        self.assertIn("application", summaries)
    
    def test_enable_hook(self):
        """Test enabling a hook."""
        self.registry.disable_hook("click")
        self.assertFalse(self.registry.get_hook("click").is_enabled())
        
        self.assertTrue(self.registry.enable_hook("click"))
        self.assertTrue(self.registry.get_hook("click").is_enabled())
    
    def test_disable_hook(self):
        """Test disabling a hook."""
        self.assertTrue(self.registry.disable_hook("click"))
        self.assertFalse(self.registry.get_hook("click").is_enabled())
    
    def test_clear_all_feedback(self):
        """Test clearing all feedback."""
        event = FeedbackEvent(
            feedback_type=FeedbackType.CLICK,
            user_id="user1",
            document_id="doc1",
            timestamp=datetime.now(),
        )
        
        self.registry.process_feedback(event)
        self.registry.clear_all_feedback()
        
        click_hook = self.registry.get_hook("click")
        self.assertEqual(click_hook._click_count, 0)
    
    def test_to_dict(self):
        """Test converting registry to dictionary."""
        registry_dict = self.registry.to_dict()
        
        self.assertIn("hooks", registry_dict)
        self.assertIn("hook_count", registry_dict)
        self.assertGreater(registry_dict["hook_count"], 0)


if __name__ == "__main__":
    unittest.main()
