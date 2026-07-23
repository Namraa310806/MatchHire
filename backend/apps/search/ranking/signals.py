"""
Ranking Signals.

This module provides reusable scoring signals that can be combined
in the ranking pipeline. Each signal calculates a score for a document
based on specific criteria.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
import math


class SignalType(Enum):
    """Types of ranking signals."""
    LEXICAL = "lexical"
    METADATA = "metadata"
    BUSINESS_RULE = "business_rule"
    FRESHNESS = "freshness"
    POPULARITY = "popularity"
    QUALITY = "quality"
    SKILL_OVERLAP = "skill_overlap"
    EXPERIENCE_OVERLAP = "experience_overlap"
    EDUCATION_OVERLAP = "education_overlap"
    LOCATION_PROXIMITY = "location_proximity"
    SALARY_COMPATIBILITY = "salary_compatibility"
    EMPLOYMENT_TYPE_COMPATIBILITY = "employment_type_compatibility"
    COMPANY_PREFERENCE = "company_preference"
    RECRUITER_PREFERENCE = "recruiter_preference"
    PROFILE_COMPLETENESS = "profile_completeness"
    CANDIDATE_ACTIVITY = "candidate_activity"
    JOB_FRESHNESS = "job_freshness"
    APPLICATION_HISTORY = "application_history"


@dataclass
class SignalConfig:
    """Configuration for a ranking signal."""
    
    enabled: bool = True
    weight: float = 1.0
    normalization: str = "min_max"
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "weight": self.weight,
            "normalization": self.normalization,
            "params": self.params,
        }


class BaseSignal(ABC):
    """
    Abstract base class for ranking signals.
    
    All ranking signals must implement this interface to ensure
    compatibility with the ranking pipeline.
    """
    
    def __init__(self, config: Optional[SignalConfig] = None):
        """
        Initialize the signal.
        
        Args:
            config: Signal configuration
        """
        self._config = config or SignalConfig()
    
    @property
    def signal_type(self) -> SignalType:
        """Get the signal type."""
        return SignalType.METADATA
    
    @abstractmethod
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate a score for a document.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Score value (higher is better)
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if signal is enabled."""
        return self._config.enabled
    
    def get_weight(self) -> float:
        """Get the signal weight."""
        return self._config.weight
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a configuration parameter."""
        return self._config.params.get(key, default)


class LexicalSignal(BaseSignal):
    """
    Lexical relevance signal based on text matching.
    
    Scores documents based on term frequency, field matching,
    and query relevance.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.LEXICAL
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate lexical relevance score.
        
        Args:
            document: Document to score
            context: Search context with query information
            
        Returns:
            Lexical relevance score
        """
        # Use the provider's relevance score if available
        if "_score" in document:
            return float(document["_score"])
        
        # Fallback: calculate based on field matches
        query = context.get("query", "").lower()
        if not query:
            return 0.0
        
        score = 0.0
        fields_to_check = [
            "title", "description", "skills", "requirements",
            "name", "summary", "content"
        ]
        
        for field in fields_to_check:
            field_value = str(document.get(field, "")).lower()
            if query in field_value:
                score += 1.0
                # Bonus for exact match in title
                if field == "title" and query == field_value:
                    score += 2.0
        
        return min(score, 10.0)


class MetadataSignal(BaseSignal):
    """
    Metadata signal based on document metadata fields.
    
    Scores documents based on structured metadata like
    category, tags, industry, etc.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.METADATA
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate metadata relevance score.
        
        Args:
            document: Document to score
            context: Search context with filters
            
        Returns:
            Metadata relevance score
        """
        filters = context.get("filters", {})
        score = 0.0
        
        # Check field matches
        for field, filter_value in filters.items():
            doc_value = document.get(field)
            if doc_value == filter_value:
                score += 1.0
            elif isinstance(filter_value, list) and doc_value in filter_value:
                score += 1.0
        
        # Bonus for having rich metadata
        metadata_fields = ["category", "tags", "industry", "location", "company"]
        for field in metadata_fields:
            if document.get(field):
                score += 0.1
        
        return min(score, 5.0)


class BusinessRuleSignal(BaseSignal):
    """
    Business rule signal based on configurable business rules.
    
    This signal applies boosts and penalties based on business rules
    like pinned results, promoted content, etc.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.BUSINESS_RULE
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate business rule score.
        
        Args:
            document: Document to score
            context: Search context with business rules
            
        Returns:
            Business rule score (boosts and penalties)
        """
        business_rules = context.get("business_rules", {})
        score = 0.0
        
        # Check for pinned results
        pinned_ids = business_rules.get("pinned_ids", [])
        if document.get("id") in pinned_ids:
            score += 10.0
        
        # Check for promoted content
        promoted_ids = business_rules.get("promoted_ids", [])
        if document.get("id") in promoted_ids:
            score += 5.0
        
        # Check for priority companies
        priority_companies = business_rules.get("priority_companies", [])
        company = document.get("company_name") or document.get("company")
        if company in priority_companies:
            score += 3.0
        
        # Check for blocked content (negative score)
        blocked_ids = business_rules.get("blocked_ids", [])
        if document.get("id") in blocked_ids:
            score -= 100.0
        
        return score


class FreshnessSignal(BaseSignal):
    """
    Freshness signal based on document age.
    
    Scores documents based on how recent they are,
    with exponential decay over time.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.FRESHNESS
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate freshness score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Freshness score (higher for newer documents)
        """
        # Get document date
        date_field = self.get_param("date_field", "created_at")
        doc_date = document.get(date_field)
        
        if not doc_date:
            return 0.0
        
        # Parse date if needed
        if isinstance(doc_date, str):
            try:
                doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return 0.0
        
        if not isinstance(doc_date, datetime):
            return 0.0
        
        # Calculate age
        now = datetime.now(doc_date.tzinfo)
        age_days = (now - doc_date).days
        
        # Get decay parameters
        scale_days = self.get_param("scale_days", 30)
        decay = self.get_param("decay", 0.5)
        
        # Calculate exponential decay
        score = math.exp(-decay * (age_days / scale_days))
        
        return score


class PopularitySignal(BaseSignal):
    """
    Popularity signal based on engagement metrics.
    
    Scores documents based on views, applications, saves,
    and other engagement metrics.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.POPULARITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate popularity score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Popularity score
        """
        score = 0.0
        
        # View count
        view_count = document.get("view_count", 0) or 0
        score += math.log1p(view_count) * 0.5
        
        # Application count
        application_count = document.get("application_count", 0) or 0
        score += math.log1p(application_count) * 1.0
        
        # Save count
        save_count = document.get("save_count", 0) or 0
        score += math.log1p(save_count) * 0.8
        
        # Click count
        click_count = document.get("click_count", 0) or 0
        score += math.log1p(click_count) * 0.3
        
        return min(score, 10.0)


class QualitySignal(BaseSignal):
    """
    Quality signal based on document quality indicators.
    
    Scores documents based on completeness, verification status,
    and other quality metrics.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.QUALITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate quality score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Quality score
        """
        score = 0.0
        
        # Verification status
        is_verified = document.get("is_verified", False)
        if is_verified:
            score += 2.0
        
        # Featured status
        is_featured = document.get("is_featured", False)
        if is_featured:
            score += 1.5
        
        # Premium status
        is_premium = document.get("is_premium", False)
        if is_premium:
            score += 1.0
        
        # Profile/job completeness
        completeness = document.get("completeness", 0) or 0
        score += completeness * 0.05
        
        return min(score, 5.0)


class SkillOverlapSignal(BaseSignal):
    """
    Skill overlap signal for matching candidates to jobs.
    
    Scores documents based on the overlap between required skills
    and candidate/available skills.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.SKILL_OVERLAP
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate skill overlap score.
        
        Args:
            document: Document to score
            context: Search context with skill requirements
            
        Returns:
            Skill overlap score
        """
        required_skills = set(context.get("required_skills", []))
        available_skills = set(document.get("skills", []))
        
        if not required_skills:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = required_skills & available_skills
        union = required_skills | available_skills
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Bonus for exact match
        if required_skills == available_skills:
            jaccard += 0.2
        
        return min(jaccard, 1.0)


class ExperienceOverlapSignal(BaseSignal):
    """
    Experience overlap signal for matching candidates to jobs.
    
    Scores documents based on experience level compatibility.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.EXPERIENCE_OVERLAP
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate experience overlap score.
        
        Args:
            document: Document to score
            context: Search context with experience requirements
            
        Returns:
            Experience overlap score
        """
        required_experience = context.get("required_experience", 0)
        available_experience = document.get("experience_years", 0) or 0
        
        if required_experience == 0:
            return 1.0
        
        # Calculate ratio
        ratio = min(available_experience / required_experience, 2.0)
        
        # Normalize to [0, 1]
        score = min(ratio / 2.0, 1.0)
        
        return score


class EducationOverlapSignal(BaseSignal):
    """
    Education overlap signal for matching candidates to jobs.
    
    Scores documents based on education level compatibility.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.EDUCATION_OVERLAP
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate education overlap score.
        
        Args:
            document: Document to score
            context: Search context with education requirements
            
        Returns:
            Education overlap score
        """
        required_education = context.get("required_education", "")
        available_education = document.get("education_level", "")
        
        if not required_education:
            return 1.0
        
        # Education level hierarchy
        education_levels = [
            "high_school",
            "associate",
            "bachelor",
            "master",
            "phd",
        ]
        
        try:
            required_idx = education_levels.index(required_education.lower())
            available_idx = education_levels.index(available_education.lower())
        except ValueError:
            return 0.0
        
        # Score based on meeting or exceeding requirement
        if available_idx >= required_idx:
            return 1.0
        else:
            # Partial credit for close match
            diff = required_idx - available_idx
            return max(0.0, 1.0 - (diff * 0.3))


class LocationProximitySignal(BaseSignal):
    """
    Location proximity signal for geo-based matching.
    
    Scores documents based on geographic proximity.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.LOCATION_PROXIMITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate location proximity score.
        
        Args:
            document: Document to score
            context: Search context with location requirements
            
        Returns:
            Location proximity score
        """
        required_location = context.get("required_location", "")
        document_location = document.get("location", "")
        
        if not required_location or not document_location:
            return 0.5
        
        # Exact match
        if required_location.lower() == document_location.lower():
            return 1.0
        
        # Partial match (same city, different area)
        required_parts = required_location.lower().split(",")
        document_parts = document_location.lower().split(",")
        
        if required_parts[0].strip() == document_parts[0].strip():
            return 0.8
        
        # Same country/region
        if len(required_parts) > 1 and len(document_parts) > 1:
            if required_parts[-1].strip() == document_parts[-1].strip():
                return 0.5
        
        return 0.0


class SalaryCompatibilitySignal(BaseSignal):
    """
    Salary compatibility signal for matching jobs to candidates.
    
    Scores documents based on salary range compatibility.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.SALARY_COMPATIBILITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate salary compatibility score.
        
        Args:
            document: Document to score
            context: Search context with salary requirements
            
        Returns:
            Salary compatibility score
        """
        min_salary = context.get("min_salary", 0)
        max_salary = context.get("max_salary", float('inf'))
        doc_salary = document.get("salary", 0) or 0
        
        if doc_salary == 0:
            return 0.5
        
        if min_salary <= doc_salary <= max_salary:
            return 1.0
        
        # Partial credit for close match
        if doc_salary < min_salary:
            diff = min_salary - doc_salary
            ratio = diff / min_salary
            return max(0.0, 1.0 - ratio)
        
        if doc_salary > max_salary:
            diff = doc_salary - max_salary
            ratio = diff / max_salary
            return max(0.0, 1.0 - ratio)
        
        return 0.0


class EmploymentTypeCompatibilitySignal(BaseSignal):
    """
    Employment type compatibility signal.
    
    Scores documents based on employment type preferences.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.EMPLOYMENT_TYPE_COMPATIBILITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate employment type compatibility score.
        
        Args:
            document: Document to score
            context: Search context with employment type preferences
            
        Returns:
            Employment type compatibility score
        """
        preferred_types = set(context.get("preferred_employment_types", []))
        doc_type = document.get("employment_type", "")
        
        if not preferred_types:
            return 1.0
        
        if doc_type in preferred_types:
            return 1.0
        
        return 0.0


class CompanyPreferenceSignal(BaseSignal):
    """
    Company preference signal based on user preferences.
    
    Scores documents based on company preferences.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.COMPANY_PREFERENCE
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate company preference score.
        
        Args:
            document: Document to score
            context: Search context with company preferences
            
        Returns:
            Company preference score
        """
        preferred_companies = set(context.get("preferred_companies", []))
        blocked_companies = set(context.get("blocked_companies", []))
        
        company = document.get("company_name") or document.get("company", "")
        
        # Blocked companies get negative score
        if company in blocked_companies:
            return -1.0
        
        # Preferred companies get positive score
        if company in preferred_companies:
            return 1.0
        
        return 0.0


class RecruiterPreferenceSignal(BaseSignal):
    """
    Recruiter preference signal based on recruiter preferences.
    
    Scores documents based on recruiter-specific preferences.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.RECRUITER_PREFERENCE
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate recruiter preference score.
        
        Args:
            document: Document to score
            context: Search context with recruiter preferences
            
        Returns:
            Recruiter preference score
        """
        recruiter_id = context.get("recruiter_id")
        doc_recruiter_id = document.get("recruiter_id")
        
        # Same recruiter gets boost
        if recruiter_id and doc_recruiter_id == recruiter_id:
            return 1.0
        
        # Check for recruiter team preferences
        recruiter_team = context.get("recruiter_team", [])
        doc_team = document.get("team", "")
        
        if doc_team in recruiter_team:
            return 0.5
        
        return 0.0


class ProfileCompletenessSignal(BaseSignal):
    """
    Profile completeness signal based on how complete a profile is.
    
    Scores documents based on the percentage of required fields filled.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.PROFILE_COMPLETENESS
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate profile completeness score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Profile completeness score
        """
        # Use pre-calculated completeness if available
        completeness = document.get("completeness")
        if completeness is not None:
            return float(completeness) / 100.0
        
        # Calculate completeness based on required fields
        required_fields = context.get("required_fields", [])
        if not required_fields:
            return 1.0
        
        filled_count = sum(1 for field in required_fields if document.get(field))
        completeness = filled_count / len(required_fields)
        
        return completeness


class CandidateActivitySignal(BaseSignal):
    """
    Candidate activity signal based on recent activity.
    
    Scores documents based on how active a candidate has been.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.CANDIDATE_ACTIVITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate candidate activity score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Candidate activity score
        """
        score = 0.0
        
        # Last active date
        last_active = document.get("last_active_at")
        if last_active:
            if isinstance(last_active, str):
                try:
                    last_active = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            if isinstance(last_active, datetime):
                days_since = (datetime.now(last_active.tzinfo) - last_active).days
                # Decay based on days since last activity
                score += math.exp(-days_since / 30) * 2.0
        
        # Application count in last 30 days
        recent_applications = document.get("recent_applications", 0) or 0
        score += min(recent_applications * 0.5, 2.0)
        
        # Profile views
        profile_views = document.get("profile_views", 0) or 0
        score += math.log1p(profile_views) * 0.3
        
        return min(score, 5.0)


class JobFreshnessSignal(BaseSignal):
    """
    Job freshness signal specific to job postings.
    
    Scores job postings based on how recently they were posted.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.JOB_FRESHNESS
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate job freshness score.
        
        Args:
            document: Document to score
            context: Search context
            
        Returns:
            Job freshness score
        """
        posted_date = document.get("posted_at") or document.get("created_at")
        
        if not posted_date:
            return 0.0
        
        # Parse date if needed
        if isinstance(posted_date, str):
            try:
                posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return 0.0
        
        if not isinstance(posted_date, datetime):
            return 0.0
        
        # Calculate age
        now = datetime.now(posted_date.tzinfo)
        age_days = (now - posted_date).days
        
        # Urgent jobs get boost
        is_urgent = document.get("is_urgent", False)
        if is_urgent:
            age_days = max(0, age_days - 7)
        
        # Calculate freshness score
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.8
        elif age_days <= 14:
            return 0.6
        elif age_days <= 30:
            return 0.4
        elif age_days <= 60:
            return 0.2
        else:
            return 0.1


class ApplicationHistorySignal(BaseSignal):
    """
    Application history signal based on past application behavior.
    
    Scores documents based on historical application patterns.
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.APPLICATION_HISTORY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate application history score.
        
        Args:
            document: Document to score
            context: Search context with user application history
            
        Returns:
            Application history score
        """
        user_id = context.get("user_id")
        document_id = document.get("id")
        
        if not user_id or not document_id:
            return 0.0
        
        # Check if user has already applied
        applied_jobs = set(context.get("applied_jobs", []))
        if document_id in applied_jobs:
            return -0.5  # Penalize already applied jobs
        
        # Check if user has viewed this job
        viewed_jobs = set(context.get("viewed_jobs", []))
        if document_id in viewed_jobs:
            return 0.3  # Small boost for viewed jobs
        
        # Check if user has similar jobs in history
        similar_companies = set(context.get("similar_companies", []))
        company = document.get("company_name") or document.get("company", "")
        if company in similar_companies:
            return 0.5  # Boost for companies user has interacted with
        
        return 0.0
