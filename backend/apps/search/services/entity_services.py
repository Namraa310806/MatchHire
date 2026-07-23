"""
Entity-specific search services.

This module provides search services for each entity type
(Job, Candidate, Resume, Company, Recruiter, Skill).
"""

from apps.search.services.base import BaseSearchService
from apps.search.providers.base import SearchProvider


class JobSearchService(BaseSearchService):
    """Search service for Job entities."""

    def get_entity_type(self) -> str:
        return "job"


class CandidateSearchService(BaseSearchService):
    """Search service for Candidate entities."""

    def get_entity_type(self) -> str:
        return "candidate"


class ResumeSearchService(BaseSearchService):
    """Search service for Resume entities."""

    def get_entity_type(self) -> str:
        return "resume"


class CompanySearchService(BaseSearchService):
    """Search service for Company entities."""

    def get_entity_type(self) -> str:
        return "company"


class RecruiterSearchService(BaseSearchService):
    """Search service for Recruiter entities."""

    def get_entity_type(self) -> str:
        return "recruiter"


class SkillSearchService(BaseSearchService):
    """Search service for Skill entities."""

    def get_entity_type(self) -> str:
        return "skill"
