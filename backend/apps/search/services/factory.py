"""
Search service factory.

This module provides a factory for creating entity-specific
search services with the appropriate provider.
"""

from typing import Optional

from apps.search.providers.base import SearchProvider
from apps.search.services.base import BaseSearchService
from apps.search.services.entity_services import (
    JobSearchService,
    CandidateSearchService,
    ResumeSearchService,
    CompanySearchService,
    RecruiterSearchService,
    SkillSearchService,
)
from apps.search.exceptions import InvalidQuery


class SearchServiceFactory:
    """
    Factory for creating entity-specific search services.

    This factory ensures that services are created with the
    correct provider and entity type.
    """

    @staticmethod
    def create_service(
        entity_type: str,
        provider: Optional[SearchProvider] = None,
    ) -> BaseSearchService:
        """
        Create a search service for the specified entity type.

        Args:
            entity_type: Type of entity (job, candidate, resume, company, recruiter, skill)
            provider: Search provider to use (optional, can be set later)

        Returns:
            Entity-specific search service instance

        Raises:
            InvalidQuery: If entity type is not recognized
        """
        service_classes = {
            "job": JobSearchService,
            "candidate": CandidateSearchService,
            "resume": ResumeSearchService,
            "company": CompanySearchService,
            "recruiter": RecruiterSearchService,
            "skill": SkillSearchService,
        }

        service_class = service_classes.get(entity_type.lower())
        if not service_class:
            raise InvalidQuery(f"Unknown entity type: {entity_type}")

        if provider is None:
            raise InvalidQuery("Provider is required to create search service")

        return service_class(provider=provider)

    @staticmethod
    def create_job_service(provider: SearchProvider) -> JobSearchService:
        """Create a job search service."""
        return JobSearchService(provider=provider)

    @staticmethod
    def create_candidate_service(provider: SearchProvider) -> CandidateSearchService:
        """Create a candidate search service."""
        return CandidateSearchService(provider=provider)

    @staticmethod
    def create_resume_service(provider: SearchProvider) -> ResumeSearchService:
        """Create a resume search service."""
        return ResumeSearchService(provider=provider)

    @staticmethod
    def create_company_service(provider: SearchProvider) -> CompanySearchService:
        """Create a company search service."""
        return CompanySearchService(provider=provider)

    @staticmethod
    def create_recruiter_service(provider: SearchProvider) -> RecruiterSearchService:
        """Create a recruiter search service."""
        return RecruiterSearchService(provider=provider)

    @staticmethod
    def create_skill_service(provider: SearchProvider) -> SkillSearchService:
        """Create a skill search service."""
        return SkillSearchService(provider=provider)
