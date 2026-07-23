"""
Search document representations.

This module defines provider-independent search document models that represent
entities to be indexed. These documents are the canonical representation that
all search providers will consume.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class EntityType(str, Enum):
    """Enumeration of all entity types that can be indexed."""
    CANDIDATE = "candidate"
    RESUME = "resume"
    JOB = "job"
    COMPANY = "company"
    RECRUITER = "recruiter"
    SKILL = "skill"
    APPLICATION = "application"
    INTERVIEW = "interview"


@dataclass(kw_only=True)
class BaseDocument:
    """
    Base search document class.
    
    All search documents inherit from this class and provide a consistent
    structure for indexing across all providers.
    """
    id: str
    entity_type: EntityType
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Placeholder for future vector embedding
    vector_embedding: Optional[List[float]] = None

    def _serialize_value(self, value: Any) -> Any:
        """Convert dataclass field values into provider-friendly primitives."""
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._serialize_value(item) for key, item in value.items()}
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            key: self._serialize_value(value)
            for key, value in asdict(self).items()
        }


@dataclass(kw_only=True)
class CandidateDocument(BaseDocument):
    """Search document for candidate profiles."""
    entity_type: EntityType = field(default=EntityType.CANDIDATE, init=False)
    
    # Core fields
    user_id: str
    email: str
    full_name: str
    
    # Profile fields
    headline: str = ""
    bio: str = ""
    current_location: str = ""
    years_of_experience: int = 0
    skills_text: str = ""
    
    # Social links
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.full_name,
            self.headline,
            self.bio,
            self.current_location,
            self.skills_text,
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class ResumeDocument(BaseDocument):
    """Search document for resumes."""
    entity_type: EntityType = field(default=EntityType.RESUME, init=False)
    
    # Core fields
    resume_id: str
    user_id: str
    version_number: int
    is_current: bool = True
    
    # Parsed content
    raw_text: str = ""
    summary: str = ""
    
    # Contact info
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    
    # Skills
    skills: List[str] = field(default_factory=list)
    
    # Education
    education: List[Dict[str, Any]] = field(default_factory=list)
    
    # Experience
    experience: List[Dict[str, Any]] = field(default_factory=list)
    
    # Projects
    projects: List[Dict[str, Any]] = field(default_factory=list)
    
    # Certifications
    certifications: List[Dict[str, Any]] = field(default_factory=list)
    
    # Social links
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.full_name,
            self.summary,
            self.raw_text,
            self.location,
            " ".join(self.skills),
            " ".join([e.get("company", "") + " " + e.get("job_title", "") for e in self.experience]),
            " ".join([e.get("institution", "") + " " + e.get("degree", "") for e in self.education]),
            " ".join([p.get("title", "") for p in self.projects]),
            " ".join([c.get("name", "") for c in self.certifications]),
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class JobDocument(BaseDocument):
    """Search document for job postings."""
    entity_type: EntityType = field(default=EntityType.JOB, init=False)
    
    # Core fields
    job_id: str
    recruiter_id: str
    title: str
    company_name: str
    
    # Job details
    location: str = ""
    employment_type: str = ""
    experience_level: str = ""
    
    # Content
    description: str = ""
    requirements: str = ""
    responsibilities: str = ""
    
    # Compensation
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    
    # Status
    is_remote: bool = False
    status: str = ""
    closed_at: Optional[datetime] = None
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.title,
            self.company_name,
            self.location,
            self.description,
            self.requirements,
            self.responsibilities,
            self.employment_type,
            self.experience_level,
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class CompanyDocument(BaseDocument):
    """Search document for companies."""
    entity_type: EntityType = field(default=EntityType.COMPANY, init=False)
    
    # Core fields
    company_id: str
    name: str
    
    # Company details
    website: str = ""
    industry: str = ""
    size: str = ""
    description: str = ""
    
    # Location
    headquarters: str = ""
    locations: List[str] = field(default_factory=list)
    
    # Status
    is_verified: bool = False
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.name,
            self.industry,
            self.description,
            self.headquarters,
            " ".join(self.locations),
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class RecruiterDocument(BaseDocument):
    """Search document for recruiters."""
    entity_type: EntityType = field(default=EntityType.RECRUITER, init=False)
    
    # Core fields
    user_id: str
    email: str
    full_name: str
    
    # Company info
    company_name: str = ""
    company_website: str = ""
    job_title: str = ""
    
    # Status
    is_verified: bool = False
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.full_name,
            self.company_name,
            self.job_title,
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class SkillDocument(BaseDocument):
    """Search document for skills."""
    entity_type: EntityType = field(default=EntityType.SKILL, init=False)
    
    # Core fields
    skill_id: str
    name: str
    
    # Categorization
    category: str = ""
    synonyms: List[str] = field(default_factory=list)
    
    # Usage stats
    usage_count: int = 0
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        text_parts = [
            self.name,
            self.category,
            " ".join(self.synonyms),
        ]
        self.searchable_text = " ".join(filter(None, text_parts))


@dataclass(kw_only=True)
class ApplicationDocument(BaseDocument):
    """Search document for job applications."""
    entity_type: EntityType = field(default=EntityType.APPLICATION, init=False)
    
    # Core fields
    application_id: str
    job_id: str
    candidate_id: str
    resume_version_id: str
    
    # Status
    status: str = ""
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        self.searchable_text = f"{self.job_id} {self.candidate_id} {self.status}"


@dataclass(kw_only=True)
class InterviewDocument(BaseDocument):
    """Search document for interviews."""
    entity_type: EntityType = field(default=EntityType.INTERVIEW, init=False)
    
    # Core fields
    interview_id: str
    application_id: str
    job_id: str
    candidate_id: str
    
    # Interview details
    scheduled_at: Optional[datetime] = None
    interview_type: str = ""
    status: str = ""
    
    # Searchable text aggregation
    searchable_text: str = ""
    
    def __post_init__(self):
        """Build searchable text from all text fields."""
        self.searchable_text = f"{self.job_id} {self.candidate_id} {self.interview_type} {self.status}"
