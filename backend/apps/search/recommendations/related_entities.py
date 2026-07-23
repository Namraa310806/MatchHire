"""
Related Entity Recommendations.

This module provides recommendations for related entities like companies,
recruiters, skills, resumes, applications, and interviews.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class RelatedEntityType(Enum):
    """Types of related entity recommendations."""
    SIMILAR_COMPANIES = "similar_companies"
    RELATED_RECRUITERS = "related_recruiters"
    RELATED_SKILLS = "related_skills"
    RELATED_RESUMES = "related_resumes"
    RELATED_APPLICATIONS = "related_applications"
    RELATED_INTERVIEWS = "related_interviews"
    CROSS_ENTITY_RECOMMENDATIONS = "cross_entity_recommendations"


class RelatedEntityGenerator(ABC):
    """
    Abstract base class for related entity generators.
    
    Each generator implements a specific type of related entity recommendation.
    """
    
    def __init__(self, query_engine, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.
        
        Args:
            query_engine: Query engine for entity generation
            config: Generator configuration
        """
        self._query_engine = query_engine
        self._config = config or {}
    
    @abstractmethod
    def generate(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related entity recommendations.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of entities
            
        Returns:
            List of entity items
        """
        pass


class SimilarCompanies(RelatedEntityGenerator):
    """
    Similar companies to a given company.
    
    Generates companies similar based on industry, size, location,
    and other attributes.
    """
    
    def generate(
        self,
        company_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate similar companies.
        
        Args:
            company_id: ID of the reference company
            context: Recommendation context
            limit: Maximum number of companies
            
        Returns:
            List of company items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference company details
        reference_company = context.get("reference_company", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="company",
            query=context.get("query", ""),
            filters={
                "industry": reference_company.get("industry", ""),
                "location": reference_company.get("location", ""),
                "company_size": reference_company.get("company_size", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.SIMILAR_COMPANIES.value,
                "reference_company_id": company_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference company
        companies = [c for c in result.results if c.get("id") != company_id]
        
        return companies[:limit]


class RelatedRecruiters(RelatedEntityGenerator):
    """
    Related recruiters to a given recruiter or company.
    
    Generates recruiters who are related based on company, industry,
    specialization, and other attributes.
    """
    
    def generate(
        self,
        recruiter_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related recruiters.
        
        Args:
            recruiter_id: ID of the reference recruiter
            context: Recommendation context
            limit: Maximum number of recruiters
            
        Returns:
            List of recruiter items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference recruiter details
        reference_recruiter = context.get("reference_recruiter", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="recruiter",
            query=context.get("query", ""),
            filters={
                "company_id": reference_recruiter.get("company_id"),
                "specialization": reference_recruiter.get("specialization", ""),
                "industry": reference_recruiter.get("industry", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.RELATED_RECRUITERS.value,
                "reference_recruiter_id": recruiter_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference recruiter
        recruiters = [r for r in result.results if r.get("id") != recruiter_id]
        
        return recruiters[:limit]


class RelatedSkills(RelatedEntityGenerator):
    """
    Related skills to a given skill or set of skills.
    
    Generates skills that are related based on co-occurrence,
    industry trends, and skill hierarchies.
    """
    
    def generate(
        self,
        skill_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related skills.
        
        Args:
            skill_id: ID of the reference skill
            context: Recommendation context
            limit: Maximum number of skills
            
        Returns:
            List of skill items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference skill details
        reference_skill = context.get("reference_skill", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="skill",
            query=context.get("query", ""),
            filters={
                "category": reference_skill.get("category", ""),
                "industry": reference_skill.get("industry", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.RELATED_SKILLS.value,
                "reference_skill_id": skill_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference skill
        skills = [s for s in result.results if s.get("id") != skill_id]
        
        return skills[:limit]


class RelatedResumes(RelatedEntityGenerator):
    """
    Related resumes to a given resume or candidate.
    
    Generates resumes that are similar based on skills, experience,
    education, and other attributes.
    """
    
    def generate(
        self,
        resume_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related resumes.
        
        Args:
            resume_id: ID of the reference resume
            context: Recommendation context
            limit: Maximum number of resumes
            
        Returns:
            List of resume items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference resume details
        reference_resume = context.get("reference_resume", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="resume",
            query=context.get("query", ""),
            filters={
                "skills": reference_resume.get("skills", []),
                "experience_years": reference_resume.get("experience_years", 0),
                "education_level": reference_resume.get("education_level", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.RELATED_RESUMES.value,
                "reference_resume_id": resume_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference resume
        resumes = [r for r in result.results if r.get("id") != resume_id]
        
        return resumes[:limit]


class RelatedApplications(RelatedEntityGenerator):
    """
    Related applications to a given application or job.
    
    Generates applications that are related based on job similarity,
    candidate similarity, and application status.
    """
    
    def generate(
        self,
        application_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related applications.
        
        Args:
            application_id: ID of the reference application
            context: Recommendation context
            limit: Maximum number of applications
            
        Returns:
            List of application items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference application details
        reference_application = context.get("reference_application", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="application",
            query=context.get("query", ""),
            filters={
                "job_id": reference_application.get("job_id"),
                "status": reference_application.get("status", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.RELATED_APPLICATIONS.value,
                "reference_application_id": application_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference application
        applications = [a for a in result.results if a.get("id") != application_id]
        
        return applications[:limit]


class RelatedInterviews(RelatedEntityGenerator):
    """
    Related interviews to a given interview or application.
    
    Generates interviews that are related based on job similarity,
    candidate similarity, and interview status.
    """
    
    def generate(
        self,
        interview_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate related interviews.
        
        Args:
            interview_id: ID of the reference interview
            context: Recommendation context
            limit: Maximum number of interviews
            
        Returns:
            List of interview items
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Get reference interview details
        reference_interview = context.get("reference_interview", {})
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type="interview",
            query=context.get("query", ""),
            filters={
                "job_id": reference_interview.get("job_id"),
                "status": reference_interview.get("status", ""),
            },
            pagination={"limit": limit, "offset": 0},
            metadata={
                "recommendation_type": RelatedEntityType.RELATED_INTERVIEWS.value,
                "reference_interview_id": interview_id,
            },
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        # Exclude the reference interview
        interviews = [i for i in result.results if i.get("id") != interview_id]
        
        return interviews[:limit]


class CrossEntityRecommendations(RelatedEntityGenerator):
    """
    Cross-entity recommendations.
    
    Generates recommendations that span multiple entity types,
    such as companies hiring for similar roles, recruiters
    in the same industry, etc.
    """
    
    def generate(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate cross-entity recommendations.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of entities
            
        Returns:
            List of entity items from various types
        """
        from apps.search.query_engine import SearchExecutionContext
        
        # Determine entity types to search
        entity_types = context.get("entity_types", ["company", "recruiter", "job"])
        
        all_entities = []
        
        for entity_type in entity_types:
            # Build search context
            search_context = SearchExecutionContext(
                entity_type=entity_type,
                query=context.get("query", ""),
                filters=context.get("filters", {}),
                pagination={"limit": limit // len(entity_types), "offset": 0},
                metadata={
                    "recommendation_type": RelatedEntityType.CROSS_ENTITY_RECOMMENDATIONS.value,
                    "reference_entity_id": entity_id,
                    "entity_type": entity_type,
                },
            )
            
            # Execute search
            result = self._query_engine.search(search_context)
            
            # Add entity type to results
            for entity in result.results:
                entity["_entity_type"] = entity_type
            
            all_entities.extend(result.results)
        
        return all_entities[:limit]
