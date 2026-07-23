"""
Document serializers.

This module provides serializers that convert Django models into provider-independent
search documents. These serializers ensure consistent serialization across all
search providers and support nested relationships.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from apps.users.models import User, CandidateProfile, RecruiterProfile
from apps.jobs.models import Job
from apps.resumes.models import (
    Resume,
    ResumeVersion,
    ParsedResume,
    StructuredResume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
)
from apps.applications.models import Application

from apps.search.indexing.documents import (
    CandidateDocument,
    ResumeDocument,
    JobDocument,
    CompanyDocument,
    RecruiterDocument,
    SkillDocument,
    ApplicationDocument,
    InterviewDocument,
    EntityType,
)


class BaseSerializer:
    """
    Base serializer class.
    
    Provides common functionality for all serializers including version tracking
    and metadata handling.
    """
    
    DOCUMENT_VERSION = 1
    
    @classmethod
    def get_version(cls) -> int:
        """Get the current document version for migration tracking."""
        return cls.DOCUMENT_VERSION
    
    @classmethod
    def build_metadata(cls, instance: Any) -> Dict[str, Any]:
        """
        Build metadata dictionary for a document.
        
        Args:
            instance: Django model instance
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "django_model": instance.__class__.__name__,
            "django_app": instance.__class__._meta.app_label,
            "serialized_at": datetime.utcnow().isoformat(),
        }
        
        # Add soft delete status if available
        if hasattr(instance, "is_deleted"):
            metadata["is_deleted"] = instance.is_deleted
        
        return metadata


class CandidateSerializer(BaseSerializer):
    """Serializer for candidate profiles."""
    
    @classmethod
    def serialize(cls, user: User, profile: Optional[CandidateProfile] = None) -> CandidateDocument:
        """
        Serialize a user and candidate profile into a CandidateDocument.
        
        Args:
            user: User instance
            profile: Optional CandidateProfile instance
            
        Returns:
            CandidateDocument instance
        """
        if profile is None:
            profile = getattr(user, "candidate_profile", None)
        
        return CandidateDocument(
            id=str(user.id),
            entity_type=EntityType.CANDIDATE,
            version=cls.get_version(),
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name or "",
            headline=profile.headline if profile else "",
            bio=profile.bio if profile else "",
            current_location=profile.current_location if profile else "",
            years_of_experience=profile.years_of_experience if profile else 0,
            skills_text=profile.skills_text if profile else "",
            linkedin_url=profile.linkedin_url if profile else "",
            github_url=profile.github_url if profile else "",
            portfolio_url=profile.portfolio_url if profile else "",
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.date_joined,
            updated_at=user.updated_at,
            metadata=cls.build_metadata(user),
        )
    
    @classmethod
    def serialize_from_user(cls, user: User) -> CandidateDocument:
        """
        Serialize a user instance directly.
        
        Args:
            user: User instance with candidate role
            
        Returns:
            CandidateDocument instance
        """
        if user.role != User.Roles.CANDIDATE:
            raise ValueError(f"User {user.id} is not a candidate")
        
        profile = getattr(user, "candidate_profile", None)
        return cls.serialize(user, profile)


class RecruiterSerializer(BaseSerializer):
    """Serializer for recruiter profiles."""
    
    @classmethod
    def serialize(cls, user: User, profile: Optional[RecruiterProfile] = None) -> RecruiterDocument:
        """
        Serialize a user and recruiter profile into a RecruiterDocument.
        
        Args:
            user: User instance
            profile: Optional RecruiterProfile instance
            
        Returns:
            RecruiterDocument instance
        """
        if profile is None:
            profile = getattr(user, "recruiter_profile", None)
        
        return RecruiterDocument(
            id=str(user.id),
            entity_type=EntityType.RECRUITER,
            version=cls.get_version(),
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name or "",
            company_name=profile.company_name if profile else "",
            company_website=profile.company_website if profile else "",
            job_title=profile.job_title if profile else "",
            is_verified=profile.verified_company if profile else False,
            created_at=user.date_joined,
            updated_at=user.updated_at,
            metadata=cls.build_metadata(user),
        )
    
    @classmethod
    def serialize_from_user(cls, user: User) -> RecruiterDocument:
        """
        Serialize a user instance directly.
        
        Args:
            user: User instance with recruiter role
            
        Returns:
            RecruiterDocument instance
        """
        if user.role != User.Roles.RECRUITER:
            raise ValueError(f"User {user.id} is not a recruiter")
        
        profile = getattr(user, "recruiter_profile", None)
        return cls.serialize(user, profile)


class JobSerializer(BaseSerializer):
    """Serializer for job postings."""
    
    @classmethod
    def serialize(cls, job: Job) -> JobDocument:
        """
        Serialize a job instance into a JobDocument.
        
        Args:
            job: Job instance
            
        Returns:
            JobDocument instance
        """
        return JobDocument(
            id=str(job.id),
            entity_type=EntityType.JOB,
            version=cls.get_version(),
            job_id=str(job.id),
            recruiter_id=str(job.recruiter_id),
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            salary_min=float(job.salary_min) if job.salary_min else None,
            salary_max=float(job.salary_max) if job.salary_max else None,
            currency=job.currency,
            is_remote=job.is_remote,
            status=job.status,
            closed_at=job.closed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
            metadata=cls.build_metadata(job),
        )


class ResumeSerializer(BaseSerializer):
    """Serializer for resumes."""
    
    @classmethod
    def serialize(cls, resume_version: ResumeVersion) -> ResumeDocument:
        """
        Serialize a resume version into a ResumeDocument.
        
        Args:
            resume_version: ResumeVersion instance
            
        Returns:
            ResumeDocument instance
        """
        # Get parsed resume
        parsed_resume = getattr(resume_version, "parsed_resume", None)
        raw_text = parsed_resume.raw_text if parsed_resume else ""
        
        # Get structured resume
        structured_resume = getattr(resume_version, "structured_resume", None)
        
        if structured_resume:
            # Extract skills
            skills = [skill.name for skill in structured_resume.skills.all()]
            
            # Extract education
            education = [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_year": edu.start_year,
                    "end_year": edu.end_year,
                }
                for edu in structured_resume.education.all()
            ]
            
            # Extract experience
            experience = [
                {
                    "company": exp.company,
                    "job_title": exp.job_title,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "description": exp.description,
                }
                for exp in structured_resume.experience.all()
            ]
            
            # Extract projects
            projects = [
                {
                    "title": proj.title,
                    "description": proj.description,
                    "github_url": proj.github_url,
                    "project_url": proj.project_url,
                }
                for proj in structured_resume.projects.all()
            ]
            
            # Extract certifications
            certifications = [
                {
                    "name": cert.name,
                    "issuer": cert.issuer,
                    "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                }
                for cert in structured_resume.certifications.all()
            ]
            
            full_name = structured_resume.full_name
            email = structured_resume.email
            phone = structured_resume.phone
            location = structured_resume.location
            summary = structured_resume.summary
            linkedin_url = structured_resume.linkedin_url
            github_url = structured_resume.github_url
            portfolio_url = structured_resume.portfolio_url
        else:
            skills = []
            education = []
            experience = []
            projects = []
            certifications = []
            full_name = ""
            email = ""
            phone = ""
            location = ""
            summary = ""
            linkedin_url = ""
            github_url = ""
            portfolio_url = ""
        
        return ResumeDocument(
            id=str(resume_version.id),
            entity_type=EntityType.RESUME,
            version=cls.get_version(),
            resume_id=str(resume_version.resume_id),
            user_id=str(resume_version.resume.user_id),
            version_number=resume_version.version_number,
            is_current=resume_version.is_current,
            raw_text=raw_text,
            summary=summary,
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            skills=skills,
            education=education,
            experience=experience,
            projects=projects,
            certifications=certifications,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            created_at=resume_version.created_at,
            updated_at=resume_version.resume.updated_at,
            metadata=cls.build_metadata(resume_version),
        )


class CompanySerializer(BaseSerializer):
    """Serializer for companies."""
    
    @classmethod
    def serialize(cls, company_name: str, recruiter_profiles: List[RecruiterProfile]) -> CompanyDocument:
        """
        Serialize company information from recruiter profiles.
        
        Args:
            company_name: Company name
            recruiter_profiles: List of RecruiterProfile instances
            
        Returns:
            CompanyDocument instance
        """
        # Aggregate company data from recruiter profiles
        websites = set()
        locations = set()
        
        for profile in recruiter_profiles:
            if profile.company_website:
                websites.add(profile.company_website)
            # Could extract location from user profile if available
        
        return CompanyDocument(
            id=company_name.lower().replace(" ", "-"),
            entity_type=EntityType.COMPANY,
            version=cls.get_version(),
            company_id=company_name.lower().replace(" ", "-"),
            name=company_name,
            website=websites.pop() if websites else "",
            industry="",  # Could be added to RecruiterProfile in future
            size="",  # Could be added to RecruiterProfile in future
            description="",  # Could be added to RecruiterProfile in future
            headquarters="",
            locations=list(locations),
            is_verified=any(profile.verified_company for profile in recruiter_profiles),
            metadata={
                "recruiter_count": len(recruiter_profiles),
                "django_app": "users",
            },
        )


class SkillSerializer(BaseSerializer):
    """Serializer for skills."""
    
    @classmethod
    def serialize(cls, skill_name: str, usage_count: int = 0) -> SkillDocument:
        """
        Serialize a skill into a SkillDocument.
        
        Args:
            skill_name: Skill name
            usage_count: Number of times this skill is used
            
        Returns:
            SkillDocument instance
        """
        return SkillDocument(
            id=skill_name.lower().replace(" ", "-"),
            entity_type=EntityType.SKILL,
            version=cls.get_version(),
            skill_id=skill_name.lower().replace(" ", "-"),
            name=skill_name,
            category="",  # Could be added in future
            synonyms=[],
            usage_count=usage_count,
            metadata={
                "django_app": "resumes",
            },
        )


class ApplicationSerializer(BaseSerializer):
    """Serializer for job applications."""
    
    @classmethod
    def serialize(cls, application: Application) -> ApplicationDocument:
        """
        Serialize an application into an ApplicationDocument.
        
        Args:
            application: Application instance
            
        Returns:
            ApplicationDocument instance
        """
        return ApplicationDocument(
            id=str(application.id),
            entity_type=EntityType.APPLICATION,
            version=cls.get_version(),
            application_id=str(application.id),
            job_id=str(application.job_id),
            candidate_id=str(application.candidate_id),
            resume_version_id=str(application.resume_version_id),
            status=application.status,
            created_at=application.created_at,
            updated_at=application.updated_at,
            metadata=cls.build_metadata(application),
        )


class InterviewSerializer(BaseSerializer):
    """Serializer for interviews."""
    
    @classmethod
    def serialize(cls, interview: Any) -> InterviewDocument:
        """
        Serialize an interview into an InterviewDocument.
        
        Args:
            interview: Interview instance (placeholder for future implementation)
            
        Returns:
            InterviewDocument instance
        """
        # Placeholder for when Interview model is implemented
        return InterviewDocument(
            id=str(getattr(interview, "id", "")),
            entity_type=EntityType.INTERVIEW,
            version=cls.get_version(),
            interview_id=str(getattr(interview, "id", "")),
            application_id=str(getattr(interview, "application_id", "")),
            job_id=str(getattr(interview, "job_id", "")),
            candidate_id=str(getattr(interview, "candidate_id", "")),
            scheduled_at=getattr(interview, "scheduled_at", None),
            interview_type=getattr(interview, "interview_type", ""),
            status=getattr(interview, "status", ""),
            created_at=getattr(interview, "created_at", None),
            updated_at=getattr(interview, "updated_at", None),
            metadata=cls.build_metadata(interview),
        )
