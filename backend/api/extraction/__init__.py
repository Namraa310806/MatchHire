"""Shared extraction utilities for skills, domain keywords, and experience estimation.

This module provides reusable extraction functionality for both job descriptions
and resume text. It uses a versioned skills dictionary stored as JSON data.
"""

from .domain_keywords import DomainKeywordMatch, extract_domain_keywords
from .experience_estimator import ExperienceEstimate, estimate_experience_years
from .skill_extractor import (
    SkillMatch,
    SkillsDictionary,
    extract_skills,
    get_skills_dictionary,
)

__all__ = [
    "extract_skills",
    "get_skills_dictionary",
    "SkillsDictionary",
    "SkillMatch",
    "extract_domain_keywords",
    "DomainKeywordMatch",
    "estimate_experience_years",
    "ExperienceEstimate",
]
