"""
Candidate Recommendations.

This module provides different types of candidate recommendations for
recruiters and jobs. Each recommendation type uses the Query Engine
for candidate generation and delegates ranking to the Ranking Pipeline.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class CandidateRecommendationType(Enum):
    """Types of candidate recommendations."""
    BEST_CANDIDATES_FOR_JOB = "best_candidates_for_job"
    SIMILAR_CANDIDATES = "similar_candidates"
    RECENTLY_ACTIVE_CANDIDATES = "recently_active_candidates"
    HIGH_QUALITY_CANDIDATES = "high_quality_candidates"
    PASSIVE_CANDIDATES = "passive_candidates"
    INTERNAL_TALENT_SUGGESTIONS = "internal_talent_suggestions"
    SKILL_GAP_CANDIDATES = "skill_gap_candidates"
    ALTERNATIVE_CANDIDATES = "alternative_candidates"


class CandidateRecommendationGenerator(ABC):
    """
    Abstract base class for candidate recommendation generators.
    
    Each generator implements a specific type of candidate recommendation.
    """
    
    def __init__(self, query_engine, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.
        
        Args:
            query_engine: Query engine for candidate generation
            config: Generator configuration
        """
        self._query_engine = query_engine
        self._config = config or {}
    
    @abstractmethod
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate recommendations.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        pass


class BestCandidatesForJob(CandidateRecommendationGenerator):
    """
    Best candidates for a job.
    
    Generates the best matching candidates for a specific job based on
    skills, experience, education, and other requirements.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate best candidates for a job.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "skills": context.get("required_skills", []),
                "experience_years": context.get("required_experience", 0),
                "education_level": context.get("required_education", ""),
                "location": context.get("required_location", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.BEST_CANDIDATES_FOR_JOB.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class SimilarCandidates(CandidateRecommendationGenerator):
    """
    Similar candidates to a given candidate.
    
    Generates candidates similar to a specific candidate based on
    skills, experience, education, and other attributes.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate similar candidates.
        
        Args:
            candidate_id: ID of the reference candidate
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference candidate details
        reference_candidate = context.get("reference_candidate", {})
        
        # Build search context based on reference candidate
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "skills": reference_candidate.get("skills", []),
                "experience_years": reference_candidate.get("experience_years", 0),
                "education_level": reference_candidate.get("education_level", ""),
                "location": reference_candidate.get("location", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.SIMILAR_CANDIDATES.value,
                "reference_candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference candidate
        candidates = [
            c for c in result.results
            if c.get("id") != candidate_id
        ]
        
        return candidates[:limit]


class RecentlyActiveCandidates(CandidateRecommendationGenerator):
    """
    Recently active candidates.
    
    Generates candidates who have been recently active on the platform.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate recently active candidates.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        from datetime import datetime, timedelta
        
        # Calculate date threshold (30 days ago)
        threshold_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "last_active_at": {"gte": threshold_date},
            },
            sort=[{"field": "last_active_at", "direction": "desc"}],
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.RECENTLY_ACTIVE_CANDIDATES.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class HighQualityCandidates(CandidateRecommendationGenerator):
    """
    High-quality candidates.
    
    Generates candidates with high quality indicators like verified
    profiles, complete profiles, high engagement, etc.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate high-quality candidates.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "is_verified": True,
                "completeness": {"gte": 80},  # 80%+ complete
            },
            sort=[{"field": "completeness", "direction": "desc"}],
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.HIGH_QUALITY_CANDIDATES.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class PassiveCandidates(CandidateRecommendationGenerator):
    """
    Passive candidates.
    
    Generates candidates who are not actively looking but may be
    open to opportunities (passive job seekers).
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate passive candidates.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "job_seeking_status": "passive",
                "open_to_opportunities": True,
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.PASSIVE_CANDIDATES.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class InternalTalentSuggestions(CandidateRecommendationGenerator):
    """
    Internal talent suggestions.
    
    Generates recommendations for internal employees who may be
    suitable for the position.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate internal talent suggestions.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                "is_internal": True,
                "company_id": context.get("company_id"),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.INTERNAL_TALENT_SUGGESTIONS.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class SkillGapCandidates(CandidateRecommendationGenerator):
    """
    Skill-gap candidates.
    
    Generates candidates who partially match the requirements but
    have the potential to fill skill gaps through training.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate skill-gap candidates.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        required_skills = context.get("required_skills", [])
        
        # Build search context with partial skill match
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                # Require at least 50% of skills
                "skills": {"overlap": required_skills, "min_overlap": 0.5},
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.SKILL_GAP_CANDIDATES.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class AlternativeCandidates(CandidateRecommendationGenerator):
    """
    Alternative candidates.
    
    Generates candidates who may not be the perfect match but offer
    alternative approaches or diverse perspectives.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative candidates.
        
        Args:
            job_id: ID of the job
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context with broader filters
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters={
                # Relax experience requirement
                "experience_years": context.get("required_experience", 0) * 0.7,
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": CandidateRecommendationType.ALTERNATIVE_CANDIDATES.value,
                "job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results
