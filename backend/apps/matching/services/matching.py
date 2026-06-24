from decimal import Decimal

from django.utils import timezone

from apps.jobs.models import Job
from apps.matching.models import JobMatch
from apps.resumes.models import Resume, ResumeVersion, StructuredResume, ResumeSkill


class MatchingService:
    """
    Service layer for deterministic candidate-job matching.
    
    Calculates match scores based on:
    - Skills (60% weight)
    - Experience (30% weight)
    - Education (10% weight)
    """

    # Experience level requirements in years
    EXPERIENCE_REQUIREMENTS = {
        Job.ExperienceLevel.ENTRY: 0,
        Job.ExperienceLevel.JUNIOR: 1,
        Job.ExperienceLevel.MID: 3,
        Job.ExperienceLevel.SENIOR: 5,
        Job.ExperienceLevel.LEAD: 8,
    }

    @classmethod
    def calculate_match(cls, candidate, job) -> JobMatch:
        """
        Calculate match score between candidate and job.

        Args:
            candidate: User instance (candidate)
            job: Job instance

        Returns:
            JobMatch instance with calculated scores
        """
        skills_score, matched_skills, missing_skills, matched_count, total_count = cls.calculate_skill_score(candidate, job)
        experience_score, experience_years = cls.calculate_experience_score(candidate, job)
        education_score = cls.calculate_education_score(candidate)

        # Calculate final weighted score
        final_score = (
            (skills_score * Decimal('0.60')) +
            (experience_score * Decimal('0.30')) +
            (education_score * Decimal('0.10'))
        )

        # Round to 2 decimal places
        final_score = final_score.quantize(Decimal('0.01'))

        # Build explanation
        explanation = cls.build_explanation(
            job,
            matched_skills,
            missing_skills,
            experience_years,
            education_score > 0,
        )
        
        # Create or update JobMatch
        job_match, created = JobMatch.objects.update_or_create(
            candidate=candidate,
            job=job,
            defaults={
                'match_score': final_score,
                'skills_score': skills_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'matched_skills_count': matched_count,
                'total_required_skills': total_count,
                'explanation': explanation,
            }
        )
        
        return job_match

    @classmethod
    def calculate_skill_score(cls, candidate, job):
        """
        Calculate skill match score.
        
        Extracts required skills from job requirements text and matches against candidate's skills.
        
        Returns:
            Tuple of (score, matched_skills_list, missing_skills_list, matched_count, total_count)
        """
        # Extract required skills from job requirements
        required_skills = cls._extract_skills_from_text(job.requirements)
        total_count = len(required_skills)
        
        if total_count == 0:
            return Decimal('0'), [], [], 0, 0
        
        # Get candidate's structured resume skills
        candidate_skills = cls._get_candidate_skills(candidate)
        candidate_skill_names = {skill.name.lower() for skill in candidate_skills}
        
        # Match skills (case-insensitive)
        matched_skills = []
        missing_skills = []
        
        for skill in required_skills:
            if skill.lower() in candidate_skill_names:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        matched_count = len(matched_skills)
        
        # Calculate percentage
        score = Decimal(str((matched_count / total_count) * 100)).quantize(Decimal('0.01'))
        
        return score, matched_skills, missing_skills, matched_count, total_count

    @classmethod
    def calculate_experience_score(cls, candidate, job):
        """
        Calculate experience match score.

        Compares candidate's actual years of experience (calculated from start_date/end_date)
        against job's required experience level.

        Returns:
            Tuple of (score, experience_years)
        """
        required_years = cls.EXPERIENCE_REQUIREMENTS.get(job.experience_level, 0)

        # Get candidate's actual years of experience from structured resume
        experience_years = cls._get_candidate_experience_years(candidate)

        # Calculate score based on experience level
        if job.experience_level == Job.ExperienceLevel.ENTRY:
            score = Decimal('100')
        elif experience_years >= required_years:
            score = Decimal('100')
        else:
            # Partial score based on how close they are
            if required_years > 0:
                score = Decimal(str((experience_years / required_years) * 100)).quantize(Decimal('0.01'))
            else:
                score = Decimal('0')

        return score, experience_years

    @classmethod
    def calculate_education_score(cls, candidate):
        """
        Calculate education match score.
        
        Simple binary check: 100 if candidate has at least one education record, 0 otherwise.
        
        Returns:
            Decimal score (0 or 100)
        """
        has_education = cls._get_candidate_has_education(candidate)
        return Decimal('100') if has_education else Decimal('0')

    @classmethod
    def build_explanation(cls, job, matched_skills, missing_skills, experience_years, education_found):
        """
        Build explanation JSON for the match.

        Returns:
            Dictionary with match details
        """
        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "experience_level_required": job.experience_level,
            "candidate_experience_years": experience_years,
            "education_found": education_found,
        }

    @classmethod
    def _extract_skills_from_text(cls, text):
        """
        Extract skills from job requirements text.

        Simple extraction: split by comma and clean whitespace.

        TECHNICAL DEBT: This simple comma-separated parsing is insufficient for real-world
        recruiter requirements which are often in natural language paragraphs.
        Future improvement: Create a JobSkill model to store structured skill requirements
        instead of parsing free text. This would enable more sophisticated matching and
        better handle natural language requirements like "strong Python and Django experience".
        """
        if not text:
            return []

        skills = []
        for skill in text.split(','):
            skill = skill.strip()
            if skill:
                skills.append(skill)

        return skills

    @classmethod
    def _get_candidate_skills(cls, candidate):
        """
        Get candidate's skills from their structured resume.
        
        Returns:
            QuerySet of ResumeSkill objects
        """
        try:
            resume = Resume.objects.get(user=candidate)
            current_version = resume.versions.filter(is_current=True).first()
            
            if not current_version:
                return ResumeSkill.objects.none()
            
            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return ResumeSkill.objects.none()
            
            if not structured_resume:
                return ResumeSkill.objects.none()
            
            return structured_resume.skills.all()
        except Resume.DoesNotExist:
            return ResumeSkill.objects.none()

    @classmethod
    def _get_candidate_experience_years(cls, candidate):
        """
        Get candidate's total years of experience from start_date/end_date.
        
        Calculates actual time worked across all experience entries.
        
        Returns:
            Float: Total years of experience
        """
        try:
            resume = Resume.objects.get(user=candidate)
            current_version = resume.versions.filter(is_current=True).first()
            
            if not current_version:
                return 0.0
            
            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return 0.0
            
            if not structured_resume:
                return 0.0
            
            experiences = structured_resume.experience.all()
            total_days = 0
            
            for exp in experiences:
                if exp.start_date:
                    end = exp.end_date if exp.end_date else timezone.now().date()
                    delta = end - exp.start_date
                    total_days += delta.days
            
            # Convert days to years
            total_years = total_days / 365.25
            return round(total_years, 2)
            
        except Resume.DoesNotExist:
            return 0.0

    @classmethod
    def _get_candidate_has_education(cls, candidate):
        """
        Check if candidate has at least one education record.
        
        Returns:
            Boolean
        """
        try:
            resume = Resume.objects.get(user=candidate)
            current_version = resume.versions.filter(is_current=True).first()
            
            if not current_version:
                return False
            
            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return False
            
            if not structured_resume:
                return False
            
            return structured_resume.education.exists()
        except Resume.DoesNotExist:
            return False
