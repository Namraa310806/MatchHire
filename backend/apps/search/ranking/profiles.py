"""
Ranking Profiles.

This module provides pre-configured ranking profiles for different use cases.
Each profile has different weighting configurations optimized for specific
search scenarios.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .pipeline import PipelineConfig, PipelineStage, NormalizationMethod
from .signals import (
    LexicalSignal,
    MetadataSignal,
    BusinessRuleSignal,
    FreshnessSignal,
    PopularitySignal,
    QualitySignal,
    SkillOverlapSignal,
    ExperienceOverlapSignal,
    EducationOverlapSignal,
    LocationProximitySignal,
    SalaryCompatibilitySignal,
    EmploymentTypeCompatibilitySignal,
    CompanyPreferenceSignal,
    RecruiterPreferenceSignal,
    ProfileCompletenessSignal,
    CandidateActivitySignal,
    JobFreshnessSignal,
    ApplicationHistorySignal,
)


class ProfileType(Enum):
    """Types of ranking profiles."""
    RECRUITER_SEARCH = "recruiter_search"
    CANDIDATE_SEARCH = "candidate_search"
    JOB_DISCOVERY = "job_discovery"
    RESUME_SEARCH = "resume_search"
    ADMIN_SEARCH = "admin_search"


@dataclass
class RankingProfile:
    """
    A ranking profile with specific signal weights and pipeline configuration.
    
    Each profile is optimized for a specific search scenario with different
    signal weights and pipeline stages.
    """
    
    name: str
    profile_type: ProfileType
    description: str
    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)
    stages: List[PipelineStage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "profile_type": self.profile_type.value,
            "description": self.description,
            "pipeline_config": self.pipeline_config.to_dict(),
            "stages": [stage.to_dict() for stage in self.stages],
            "metadata": self.metadata,
        }
    
    def get_stage(self, stage_name: str) -> Optional[PipelineStage]:
        """
        Get a stage by name.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Pipeline stage or None if not found
        """
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None


class RecruiterSearchProfile(RankingProfile):
    """
    Profile for recruiter searching for candidates.
    
    Optimized for finding the best candidates based on skills,
    experience, education, and activity.
    """
    
    def __init__(self):
        """Initialize the recruiter search profile."""
        stages = [
            PipelineStage(
                name="lexical_relevance",
                signals=["lexical"],
                weights={"lexical": 1.0},
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="skill_matching",
                signals=["skill_overlap", "experience_overlap", "education_overlap"],
                weights={
                    "skill_overlap": 2.0,
                    "experience_overlap": 1.5,
                    "education_overlap": 1.0,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="candidate_quality",
                signals=["profile_completeness", "candidate_activity", "quality"],
                weights={
                    "profile_completeness": 1.0,
                    "candidate_activity": 1.5,
                    "quality": 1.0,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="business_rules",
                signals=["business_rule"],
                weights={"business_rule": 3.0},
                normalization=NormalizationMethod.NONE,
            ),
        ]
        
        super().__init__(
            name="recruiter_search",
            profile_type=ProfileType.RECRUITER_SEARCH,
            description="Optimized for recruiters searching for candidates with emphasis on skills, experience, and activity",
            stages=stages,
            metadata={
                "primary_focus": "skill_matching",
                "secondary_focus": "candidate_quality",
                "target_entity": "candidate",
            },
        )


class CandidateSearchProfile(RankingProfile):
    """
    Profile for candidates searching for jobs.
    
    Optimized for finding relevant jobs based on skills,
    location, salary, and job freshness.
    """
    
    def __init__(self):
        """Initialize the candidate search profile."""
        stages = [
            PipelineStage(
                name="lexical_relevance",
                signals=["lexical"],
                weights={"lexical": 1.0},
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="job_matching",
                signals=[
                    "skill_overlap",
                    "location_proximity",
                    "salary_compatibility",
                    "employment_type_compatibility",
                ],
                weights={
                    "skill_overlap": 2.0,
                    "location_proximity": 1.5,
                    "salary_compatibility": 1.0,
                    "employment_type_compatibility": 0.5,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="job_quality",
                signals=["job_freshness", "quality", "popularity"],
                weights={
                    "job_freshness": 1.5,
                    "quality": 1.0,
                    "popularity": 0.5,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="preferences",
                signals=["company_preference", "application_history"],
                weights={
                    "company_preference": 1.0,
                    "application_history": 0.5,
                },
                normalization=NormalizationMethod.NONE,
            ),
            PipelineStage(
                name="business_rules",
                signals=["business_rule"],
                weights={"business_rule": 3.0},
                normalization=NormalizationMethod.NONE,
            ),
        ]
        
        super().__init__(
            name="candidate_search",
            profile_type=ProfileType.CANDIDATE_SEARCH,
            description="Optimized for candidates searching for jobs with emphasis on skills, location, and freshness",
            stages=stages,
            metadata={
                "primary_focus": "job_matching",
                "secondary_focus": "job_quality",
                "target_entity": "job",
            },
        )


class JobDiscoveryProfile(RankingProfile):
    """
    Profile for job discovery and exploration.
    
    Optimized for surfacing diverse and interesting jobs
    with emphasis on freshness and popularity.
    """
    
    def __init__(self):
        """Initialize the job discovery profile."""
        stages = [
            PipelineStage(
                name="relevance",
                signals=["lexical", "metadata"],
                weights={
                    "lexical": 1.0,
                    "metadata": 0.5,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="engagement",
                signals=["popularity", "quality"],
                weights={
                    "popularity": 2.0,
                    "quality": 1.0,
                },
                normalization=NormalizationMethod.LOGISTIC,
            ),
            PipelineStage(
                name="freshness",
                signals=["job_freshness", "freshness"],
                weights={
                    "job_freshness": 2.0,
                    "freshness": 1.0,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="business_rules",
                signals=["business_rule"],
                weights={"business_rule": 2.0},
                normalization=NormalizationMethod.NONE,
            ),
        ]
        
        super().__init__(
            name="job_discovery",
            profile_type=ProfileType.JOB_DISCOVERY,
            description="Optimized for job discovery with emphasis on freshness, popularity, and diversity",
            stages=stages,
            metadata={
                "primary_focus": "engagement",
                "secondary_focus": "freshness",
                "target_entity": "job",
                "diversity_weight": 0.3,
            },
        )


class ResumeSearchProfile(RankingProfile):
    """
    Profile for searching resumes and CVs.
    
    Optimized for matching resumes to job requirements
    with emphasis on skills and experience.
    """
    
    def __init__(self):
        """Initialize the resume search profile."""
        stages = [
            PipelineStage(
                name="content_matching",
                signals=["lexical"],
                weights={"lexical": 1.5},
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="skill_experience",
                signals=[
                    "skill_overlap",
                    "experience_overlap",
                    "education_overlap",
                ],
                weights={
                    "skill_overlap": 2.5,
                    "experience_overlap": 2.0,
                    "education_overlap": 1.0,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="resume_quality",
                signals=["profile_completeness", "quality"],
                weights={
                    "profile_completeness": 1.0,
                    "quality": 1.5,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="activity",
                signals=["candidate_activity"],
                weights={"candidate_activity": 1.0},
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="business_rules",
                signals=["business_rule"],
                weights={"business_rule": 2.0},
                normalization=NormalizationMethod.NONE,
            ),
        ]
        
        super().__init__(
            name="resume_search",
            profile_type=ProfileType.RESUME_SEARCH,
            description="Optimized for resume search with emphasis on skills, experience, and education matching",
            stages=stages,
            metadata={
                "primary_focus": "skill_experience",
                "secondary_focus": "resume_quality",
                "target_entity": "resume",
            },
        )


class AdminSearchProfile(RankingProfile):
    """
    Profile for admin and internal search.
    
    Optimized for comprehensive search with all signals
    and detailed explanations for debugging.
    """
    
    def __init__(self):
        """Initialize the admin search profile."""
        stages = [
            PipelineStage(
                name="all_signals",
                signals=[
                    "lexical",
                    "metadata",
                    "skill_overlap",
                    "experience_overlap",
                    "education_overlap",
                    "location_proximity",
                    "salary_compatibility",
                    "freshness",
                    "popularity",
                    "quality",
                    "profile_completeness",
                    "candidate_activity",
                    "job_freshness",
                ],
                weights={
                    "lexical": 1.0,
                    "metadata": 0.5,
                    "skill_overlap": 1.0,
                    "experience_overlap": 1.0,
                    "education_overlap": 0.5,
                    "location_proximity": 0.5,
                    "salary_compatibility": 0.5,
                    "freshness": 0.5,
                    "popularity": 0.5,
                    "quality": 0.5,
                    "profile_completeness": 0.5,
                    "candidate_activity": 0.5,
                    "job_freshness": 0.5,
                },
                normalization=NormalizationMethod.MIN_MAX,
            ),
            PipelineStage(
                name="business_rules",
                signals=["business_rule"],
                weights={"business_rule": 5.0},
                normalization=NormalizationMethod.NONE,
            ),
        ]
        
        config = PipelineConfig(
            enable_diagnostics=True,
            enable_parallel_scoring=True,
            cache_enabled=False,  # Disable cache for admin to see real-time behavior
        )
        
        super().__init__(
            name="admin_search",
            profile_type=ProfileType.ADMIN_SEARCH,
            description="Comprehensive admin search profile with all signals enabled for debugging and analysis",
            pipeline_config=config,
            stages=stages,
            metadata={
                "primary_focus": "comprehensive",
                "diagnostics_enabled": True,
                "target_entity": "all",
            },
        )


class RankingProfileRegistry:
    """
    Registry for managing ranking profiles.
    
    Provides methods to register, retrieve, and manage
    ranking profiles for different use cases.
    """
    
    def __init__(self):
        """Initialize the ranking profile registry."""
        self._profiles: Dict[str, RankingProfile] = {}
        self._default_profile: Optional[str] = None
        
        # Register default profiles
        self._register_default_profiles()
    
    def _register_default_profiles(self) -> None:
        """Register default ranking profiles."""
        self.register_profile(RecruiterSearchProfile())
        self.register_profile(CandidateSearchProfile())
        self.register_profile(JobDiscoveryProfile())
        self.register_profile(ResumeSearchProfile())
        self.register_profile(AdminSearchProfile())
        
        # Set default profile
        self._default_profile = "candidate_search"
    
    def register_profile(self, profile: RankingProfile) -> None:
        """
        Register a ranking profile.
        
        Args:
            profile: Ranking profile to register
        """
        self._profiles[profile.name] = profile
    
    def unregister_profile(self, profile_name: str) -> bool:
        """
        Unregister a ranking profile.
        
        Args:
            profile_name: Name of the profile to unregister
            
        Returns:
            True if profile was unregistered, False if not found
        """
        if profile_name in self._profiles:
            del self._profiles[profile_name]
            return True
        return False
    
    def get_profile(self, profile_name: str) -> Optional[RankingProfile]:
        """
        Get a ranking profile by name.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Ranking profile or None if not found
        """
        return self._profiles.get(profile_name)
    
    def get_profile_by_type(self, profile_type: ProfileType) -> Optional[RankingProfile]:
        """
        Get a ranking profile by type.
        
        Args:
            profile_type: Type of profile
            
        Returns:
            Ranking profile or None if not found
        """
        for profile in self._profiles.values():
            if profile.profile_type == profile_type:
                return profile
        return None
    
    def set_default_profile(self, profile_name: str) -> bool:
        """
        Set the default profile.
        
        Args:
            profile_name: Name of the profile to set as default
            
        Returns:
            True if profile was set as default, False if not found
        """
        if profile_name in self._profiles:
            self._default_profile = profile_name
            return True
        return False
    
    def get_default_profile(self) -> Optional[RankingProfile]:
        """
        Get the default profile.
        
        Returns:
            Default ranking profile or None if not set
        """
        if self._default_profile:
            return self._profiles.get(self._default_profile)
        return None
    
    def list_profiles(self) -> List[str]:
        """
        List all registered profile names.
        
        Returns:
            List of profile names
        """
        return list(self._profiles.keys())
    
    def get_all_profiles(self) -> Dict[str, RankingProfile]:
        """
        Get all registered profiles.
        
        Returns:
            Dictionary of profile name to profile
        """
        return self._profiles.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry state to dictionary representation."""
        return {
            "profiles": {
                name: profile.to_dict()
                for name, profile in self._profiles.items()
            },
            "default_profile": self._default_profile,
            "profile_count": len(self._profiles),
        }


class ProfileBuilder:
    """
    Builder for creating custom ranking profiles.
    
    Provides a fluent interface for constructing profiles
    with custom signal weights and pipeline stages.
    """
    
    def __init__(self, name: str, profile_type: ProfileType):
        """
        Initialize the profile builder.
        
        Args:
            name: Profile name
            profile_type: Profile type
        """
        self._name = name
        self._profile_type = profile_type
        self._description = ""
        self._pipeline_config = PipelineConfig()
        self._stages: List[PipelineStage] = []
        self._metadata: Dict[str, Any] = {}
    
    def with_description(self, description: str) -> "ProfileBuilder":
        """
        Set the profile description.
        
        Args:
            description: Profile description
            
        Returns:
            Self for method chaining
        """
        self._description = description
        return self
    
    def with_pipeline_config(self, config: PipelineConfig) -> "ProfileBuilder":
        """
        Set the pipeline configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Self for method chaining
        """
        self._pipeline_config = config
        return self
    
    def add_stage(self, stage: PipelineStage) -> "ProfileBuilder":
        """
        Add a pipeline stage.
        
        Args:
            stage: Pipeline stage to add
            
        Returns:
            Self for method chaining
        """
        self._stages.append(stage)
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> "ProfileBuilder":
        """
        Set the profile metadata.
        
        Args:
            metadata: Profile metadata
            
        Returns:
            Self for method chaining
        """
        self._metadata = metadata
        return self
    
    def build(self) -> RankingProfile:
        """
        Build the ranking profile.
        
        Returns:
            Ranking profile instance
        """
        return RankingProfile(
            name=self._name,
            profile_type=self._profile_type,
            description=self._description,
            pipeline_config=self._pipeline_config,
            stages=self._stages,
            metadata=self._metadata,
        )
