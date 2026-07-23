"""
Tests for ranking profiles.
"""

import unittest
from apps.search.ranking.profiles import (
    RankingProfile,
    RankingProfileRegistry,
    RecruiterSearchProfile,
    CandidateSearchProfile,
    JobDiscoveryProfile,
    ResumeSearchProfile,
    AdminSearchProfile,
    ProfileType,
    ProfileBuilder,
)
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod


class TestRankingProfile(unittest.TestCase):
    """Test cases for RankingProfile."""
    
    def test_profile_creation(self):
        """Test creating a ranking profile."""
        profile = RankingProfile(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Test profile",
        )
        
        self.assertEqual(profile.name, "test_profile")
        self.assertEqual(profile.profile_type, ProfileType.CANDIDATE_SEARCH)
        self.assertEqual(profile.description, "Test profile")
    
    def test_profile_to_dict(self):
        """Test converting profile to dictionary."""
        profile = RankingProfile(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Test profile",
        )
        
        profile_dict = profile.to_dict()
        self.assertEqual(profile_dict["name"], "test_profile")
        self.assertEqual(profile_dict["profile_type"], "candidate_search")
    
    def test_get_stage(self):
        """Test getting a stage by name."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
        )
        
        profile = RankingProfile(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Test profile",
            stages=[stage],
        )
        
        retrieved = profile.get_stage("test_stage")
        self.assertEqual(retrieved, stage)
        
        retrieved = profile.get_stage("nonexistent")
        self.assertIsNone(retrieved)


class TestRecruiterSearchProfile(unittest.TestCase):
    """Test cases for RecruiterSearchProfile."""
    
    def test_profile_creation(self):
        """Test creating recruiter search profile."""
        profile = RecruiterSearchProfile()
        
        self.assertEqual(profile.name, "recruiter_search")
        self.assertEqual(profile.profile_type, ProfileType.RECRUITER_SEARCH)
        self.assertGreater(len(profile.stages), 0)
    
    def test_profile_stages(self):
        """Test profile has correct stages."""
        profile = RecruiterSearchProfile()
        
        stage_names = [stage.name for stage in profile.stages]
        self.assertIn("lexical_relevance", stage_names)
        self.assertIn("skill_matching", stage_names)
        self.assertIn("candidate_quality", stage_names)


class TestCandidateSearchProfile(unittest.TestCase):
    """Test cases for CandidateSearchProfile."""
    
    def test_profile_creation(self):
        """Test creating candidate search profile."""
        profile = CandidateSearchProfile()
        
        self.assertEqual(profile.name, "candidate_search")
        self.assertEqual(profile.profile_type, ProfileType.CANDIDATE_SEARCH)
        self.assertGreater(len(profile.stages), 0)
    
    def test_profile_stages(self):
        """Test profile has correct stages."""
        profile = CandidateSearchProfile()
        
        stage_names = [stage.name for stage in profile.stages]
        self.assertIn("lexical_relevance", stage_names)
        self.assertIn("job_matching", stage_names)
        self.assertIn("job_quality", stage_names)


class TestJobDiscoveryProfile(unittest.TestCase):
    """Test cases for JobDiscoveryProfile."""
    
    def test_profile_creation(self):
        """Test creating job discovery profile."""
        profile = JobDiscoveryProfile()
        
        self.assertEqual(profile.name, "job_discovery")
        self.assertEqual(profile.profile_type, ProfileType.JOB_DISCOVERY)
        self.assertGreater(len(profile.stages), 0)


class TestResumeSearchProfile(unittest.TestCase):
    """Test cases for ResumeSearchProfile."""
    
    def test_profile_creation(self):
        """Test creating resume search profile."""
        profile = ResumeSearchProfile()
        
        self.assertEqual(profile.name, "resume_search")
        self.assertEqual(profile.profile_type, ProfileType.RESUME_SEARCH)
        self.assertGreater(len(profile.stages), 0)


class TestAdminSearchProfile(unittest.TestCase):
    """Test cases for AdminSearchProfile."""
    
    def test_profile_creation(self):
        """Test creating admin search profile."""
        profile = AdminSearchProfile()
        
        self.assertEqual(profile.name, "admin_search")
        self.assertEqual(profile.profile_type, ProfileType.ADMIN_SEARCH)
        self.assertGreater(len(profile.stages), 0)
    
    def test_diagnostics_enabled(self):
        """Test admin profile has diagnostics enabled."""
        profile = AdminSearchProfile()
        
        self.assertTrue(profile.pipeline_config.enable_diagnostics)
        self.assertFalse(profile.pipeline_config.cache_enabled)


class TestRankingProfileRegistry(unittest.TestCase):
    """Test cases for RankingProfileRegistry."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = RankingProfileRegistry()
    
    def test_registry_creation(self):
        """Test creating a profile registry."""
        self.assertIsNotNone(self.registry)
        self.assertGreater(len(self.registry._profiles), 0)
    
    def test_register_profile(self):
        """Test registering a profile."""
        profile = RankingProfile(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Test",
        )
        
        self.registry.register_profile(profile)
        self.assertIn("test_profile", self.registry._profiles)
    
    def test_unregister_profile(self):
        """Test unregistering a profile."""
        profile = RankingProfile(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Test",
        )
        
        self.registry.register_profile(profile)
        self.assertTrue(self.registry.unregister_profile("test_profile"))
        self.assertNotIn("test_profile", self.registry._profiles)
    
    def test_get_profile(self):
        """Test getting a profile by name."""
        profile = self.registry.get_profile("candidate_search")
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "candidate_search")
    
    def test_get_profile_by_type(self):
        """Test getting a profile by type."""
        profile = self.registry.get_profile_by_type(ProfileType.CANDIDATE_SEARCH)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.profile_type, ProfileType.CANDIDATE_SEARCH)
    
    def test_set_default_profile(self):
        """Test setting default profile."""
        self.assertTrue(self.registry.set_default_profile("recruiter_search"))
        self.assertEqual(self.registry._default_profile, "recruiter_search")
    
    def test_get_default_profile(self):
        """Test getting default profile."""
        profile = self.registry.get_default_profile()
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "candidate_search")
    
    def test_list_profiles(self):
        """Test listing all profile names."""
        profiles = self.registry.list_profiles()
        
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)
        self.assertIn("candidate_search", profiles)
    
    def test_get_all_profiles(self):
        """Test getting all profiles."""
        profiles = self.registry.get_all_profiles()
        
        self.assertIsInstance(profiles, dict)
        self.assertGreater(len(profiles), 0)


class TestProfileBuilder(unittest.TestCase):
    """Test cases for ProfileBuilder."""
    
    def test_builder_creation(self):
        """Test creating a profile builder."""
        builder = ProfileBuilder(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
        )
        
        self.assertEqual(builder._name, "test_profile")
        self.assertEqual(builder._profile_type, ProfileType.CANDIDATE_SEARCH)
    
    def test_with_description(self):
        """Test setting description."""
        builder = ProfileBuilder(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
        )
        
        result = builder.with_description("Test description")
        self.assertEqual(result, builder)
        self.assertEqual(builder._description, "Test description")
    
    def test_add_stage(self):
        """Test adding a stage."""
        builder = ProfileBuilder(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
        )
        
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
        )
        
        result = builder.add_stage(stage)
        self.assertEqual(result, builder)
        self.assertEqual(len(builder._stages), 1)
    
    def test_build(self):
        """Test building a profile."""
        builder = ProfileBuilder(
            name="test_profile",
            profile_type=ProfileType.CANDIDATE_SEARCH,
        )
        
        builder.with_description("Test profile")
        
        profile = builder.build()
        
        self.assertEqual(profile.name, "test_profile")
        self.assertEqual(profile.description, "Test profile")
        self.assertEqual(profile.profile_type, ProfileType.CANDIDATE_SEARCH)


if __name__ == "__main__":
    unittest.main()
