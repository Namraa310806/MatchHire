"""
Job Recommendations.

This module provides different types of job recommendations for
candidates. Each recommendation type uses the Query Engine
for job generation and delegates ranking to the Ranking Pipeline.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class JobRecommendationType(Enum):
    """Types of job recommendations."""
    BEST_JOBS_FOR_CANDIDATE = "best_jobs_for_candidate"
    RELATED_JOBS = "related_jobs"
    RECENTLY_POSTED_JOBS = "recently_posted_jobs"
    TRENDING_JOBS = "trending_jobs"
    NEARBY_JOBS = "nearby_jobs"
    SALARY_COMPATIBLE_JOBS = "salary_compatible_jobs"
    CAREER_PROGRESSION_JOBS = "career_progression_jobs"
    ALTERNATIVE_JOBS = "alternative_jobs"


class JobRecommendationGenerator(ABC):
    """
    Abstract base class for job recommendation generators.
    
    Each generator implements a specific type of job recommendation.
    """
    
    def __init__(self, query_engine, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.
        
        Args:
            query_engine: Query engine for job generation
            config: Generator configuration
        """
        self._query_engine = query_engine
        self._config = config or {}
    
    @abstractmethod
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate job recommendations.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        pass


class BestJobsForCandidate(JobRecommendationGenerator):
    """
    Best jobs for a candidate.
    
    Generates the best matching jobs for a specific candidate based on
    skills, experience, education, location, and preferences.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate best jobs for a candidate.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "skills": context.get("candidate_skills", []),
                "location": context.get("candidate_location", ""),
                "employment_type": context.get("preferred_employment_types", []),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.BEST_JOBS_FOR_CANDIDATE.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class RelatedJobs(JobRecommendationGenerator):
    """
    Related jobs to a given job.
    
    Generates jobs similar to a specific job based on skills,
    industry, company, and other attributes.
    """
    
    def generate(
        self,
        job_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related jobs.
        
        Args:
            job_id: ID of the reference job
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference job details
        reference_job = context.get("reference_job", {})
        
        # Build search context based on reference job
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "skills": reference_job.get("skills", []),
                "industry": reference_job.get("industry", ""),
                "company_id": reference_job.get("company_id"),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.RELATED_JOBS.value,
                "reference_job_id": job_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference job
        jobs = [j for j in result.results if j.get("id") != job_id]
        
        return jobs[:limit]


class RecentlyPostedJobs(JobRecommendationGenerator):
    """
    Recently posted jobs.
    
    Generates jobs that have been posted recently.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate recently posted jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        from datetime import datetime, timedelta
        
        # Calculate date threshold (7 days ago)
        threshold_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "posted_at": {"gte": threshold_date},
            },
            sort=[{"field": "posted_at", "direction": "desc"}],
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.RECENTLY_POSTED_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class TrendingJobs(JobRecommendationGenerator):
    """
    Trending jobs.
    
    Generates jobs that are trending based on views, applications,
    and other engagement metrics.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate trending jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "is_trending": True,
            },
            sort=[{"field": "trending_score", "direction": "desc"}],
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.TRENDING_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class NearbyJobs(JobRecommendationGenerator):
    """
    Nearby jobs.
    
    Generates jobs that are geographically close to the candidate's location.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate nearby jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        candidate_location = context.get("candidate_location", "")
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "location": candidate_location,
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.NEARBY_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class SalaryCompatibleJobs(JobRecommendationGenerator):
    """
    Salary-compatible jobs.
    
    Generates jobs that match the candidate's salary expectations.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate salary-compatible jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        salary_range = context.get("salary_range", {})
        min_salary = salary_range.get("min", 0)
        max_salary = salary_range.get("max", float('inf'))
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "salary_min": {"lte": max_salary},
                "salary_max": {"gte": min_salary},
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.SALARY_COMPATIBLE_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class CareerProgressionJobs(JobRecommendationGenerator):
    """
    Career progression jobs.
    
    Generates jobs that represent a step up in the candidate's career,
    such as senior roles, management positions, etc.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate career progression jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        current_level = context.get("current_seniority_level", "mid")
        
        # Map current level to next level
        level_progression = {
            "entry": "mid",
            "mid": "senior",
            "senior": "lead",
            "lead": "manager",
            "manager": "director",
        }
        
        target_level = level_progression.get(current_level, "senior")
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                "seniority_level": target_level,
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.CAREER_PROGRESSION_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results


class AlternativeJobs(JobRecommendationGenerator):
    """
    Alternative jobs.
    
    Generates jobs that may not be the perfect match but offer
    alternative career paths or diverse opportunities.
    """
    
    def generate(
        self,
        candidate_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative jobs.
        
        Args:
            candidate_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            
        Returns:
            List of job items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        candidate_skills = context.get("candidate_skills", [])
        
        # Build search context with broader skill matching
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters={
                # Require at least 30% skill overlap
                "skills": {"overlap": candidate_skills, "min_overlap": 0.3},
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": JobRecommendationType.ALTERNATIVE_JOBS.value,
                "candidate_id": candidate_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results
