from functools import lru_cache
from decimal import Decimal

from django.utils import timezone
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from apps.jobs.models import Job
from apps.matching.models import JobMatch
from apps.resumes.models import Resume, StructuredResume, ResumeSkill


SKILL_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_skill_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence-transformers model once per process."""
    return SentenceTransformer(SKILL_EMBEDDING_MODEL_NAME, device="cpu")


class MatchingService:
    """
    Service layer for candidate-job matching.

    Calculates match scores based on:
    - Skills (60% weight, semantic similarity with embeddings)
    - Experience (30% weight)
    - Education (10% weight)

    Skill matching uses structured JobSkill rows when available and falls back to the
    legacy comma-separated Job.requirements text for backwards compatibility.
    """

    SKILL_MATCH_THRESHOLD = 0.75

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
        (
            skills_score,
            matched_skills,
            missing_skills,
            matched_count,
            total_count,
            skill_details,
        ) = cls.calculate_skill_score(candidate, job)
        experience_score, experience_years = cls.calculate_experience_score(
            candidate, job
        )
        education_score = cls.calculate_education_score(candidate)

        # Calculate final weighted score
        final_score = (
            (skills_score * Decimal("0.60"))
            + (experience_score * Decimal("0.30"))
            + (education_score * Decimal("0.10"))
        )

        # Round to 2 decimal places
        final_score = final_score.quantize(Decimal("0.01"))

        # Build explanation
        explanation = cls.build_explanation(
            job,
            matched_skills,
            missing_skills,
            skill_details,
            experience_years,
            education_score > 0,
        )

        # Create or update JobMatch
        job_match, created = JobMatch.objects.update_or_create(
            candidate=candidate,
            job=job,
            defaults={
                "match_score": final_score,
                "skills_score": skills_score,
                "experience_score": experience_score,
                "education_score": education_score,
                "matched_skills_count": matched_count,
                "total_required_skills": total_count,
                "explanation": explanation,
            },
        )

        return job_match

    @classmethod
    def recalculate_for_candidate(cls, candidate_id: str) -> int:
        """Recalculate active job matches for one candidate.

        Idempotency: calculate_match uses update_or_create on the unique
        candidate/job pair, so replaying this task updates existing rows.
        """
        from apps.users.models import User

        try:
            candidate = User.objects.only("id", "email").get(id=candidate_id)
        except User.DoesNotExist:
            return 0

        jobs = (
            Job.objects.filter(status=Job.JobStatus.ACTIVE)
            .select_related("recruiter")
            .iterator()
        )
        count = 0
        for job in jobs:
            cls.calculate_match(candidate, job)
            count += 1
        return count

    @classmethod
    def recalculate_for_job(cls, job_id: str) -> int:
        """Recalculate matches for every candidate with structured current resume."""
        try:
            job = Job.objects.select_related("recruiter").get(id=job_id)
        except Job.DoesNotExist:
            return 0

        candidates = (
            StructuredResume.objects.filter(resume_version__is_current=True)
            .select_related("resume_version__resume__user")
            .only(
                "resume_version__resume__user__id",
                "resume_version__resume__user__email",
            )
            .iterator()
        )
        count = 0
        for structured_resume in candidates:
            cls.calculate_match(structured_resume.resume_version.resume.user, job)
            count += 1
        return count

    @classmethod
    def refresh_candidate_recommendations(cls, candidate_id: str) -> int:
        """Refresh cached recommendation rows for a candidate.

        Recommendations are backed by JobMatch rows ordered by match score, so
        no separate persistent recommendation state is stored.
        """
        return JobMatch.objects.filter(
            candidate_id=candidate_id,
            job__status=Job.JobStatus.ACTIVE,
        ).count()

    @classmethod
    def calculate_skill_score(cls, candidate, job):
        """
        Calculate skill match score.

        Extracts required skills from structured JobSkill rows when present and falls
        back to job requirements text when a job has no structured skills yet.

        Exact normalized string matches short-circuit the semantic path. Remaining
        unmatched skills are compared via sentence-transformers embeddings and
        cosine similarity.

        Returns:
            Tuple of (score, matched_skills_list, missing_skills_list, matched_count,
            total_count, skill_details)
        """
        required_skills = cls._get_job_required_skills(job)
        total_count = len(required_skills)

        if total_count == 0:
            return Decimal("0"), [], [], 0, 0, {"matched": [], "missing": []}

        candidate_skills = [
            skill.name.strip()
            for skill in cls._get_candidate_skills(candidate)
            if skill.name and skill.name.strip()
        ]
        candidate_skill_lookup = {
            cls._normalize_skill_name(skill): skill for skill in candidate_skills
        }

        required_skill_embeddings = cls._get_skill_embeddings(required_skills, job=job)
        semantic_required_indices = [
            index
            for index, skill in enumerate(required_skills)
            if cls._normalize_skill_name(skill) not in candidate_skill_lookup
        ]

        if semantic_required_indices and candidate_skills:
            semantic_required_embeddings = [
                required_skill_embeddings[index] for index in semantic_required_indices
            ]
            candidate_skill_embeddings = cls._get_skill_embeddings(candidate_skills)
            semantic_similarity_matrix = cosine_similarity(
                semantic_required_embeddings,
                candidate_skill_embeddings,
            )
        else:
            semantic_similarity_matrix = None

        matched_skills = []
        missing_skills = []
        matched_details = []
        missing_details = []
        semantic_row_index = 0

        for skill in required_skills:
            normalized_required_skill = cls._normalize_skill_name(skill)
            exact_match = candidate_skill_lookup.get(normalized_required_skill)

            if exact_match:
                matched_skills.append(skill)
                matched_details.append(
                    {
                        "required_skill": skill,
                        "matched_skill": exact_match,
                        "similarity": 1.0,
                        "match_type": "exact",
                    }
                )
                continue

            similarity_score = 0.0
            matched_candidate_skill = None

            if semantic_similarity_matrix is not None:
                row = semantic_similarity_matrix[semantic_row_index]
                semantic_row_index += 1
                best_candidate_index = max(
                    range(len(row)), key=lambda candidate_index: row[candidate_index]
                )
                similarity_score = float(row[best_candidate_index])
                matched_candidate_skill = candidate_skills[best_candidate_index]

            if similarity_score >= cls.SKILL_MATCH_THRESHOLD:
                matched_skills.append(skill)
                matched_details.append(
                    {
                        "required_skill": skill,
                        "matched_skill": matched_candidate_skill,
                        "similarity": round(similarity_score, 4),
                        "match_type": "semantic",
                    }
                )
            else:
                missing_skills.append(skill)
                missing_details.append(
                    {
                        "required_skill": skill,
                        "best_candidate_skill": matched_candidate_skill,
                        "similarity": round(similarity_score, 4),
                        "match_type": "semantic" if matched_candidate_skill else "none",
                    }
                )

        matched_count = len(matched_skills)

        # Calculate percentage
        score = Decimal(str((matched_count / total_count) * 100)).quantize(
            Decimal("0.01")
        )

        return (
            score,
            matched_skills,
            missing_skills,
            matched_count,
            total_count,
            {"matched": matched_details, "missing": missing_details},
        )

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
            score = Decimal("100")
        elif experience_years >= required_years:
            score = Decimal("100")
        else:
            # Partial score based on how close they are
            if required_years > 0:
                score = Decimal(
                    str((experience_years / required_years) * 100)
                ).quantize(Decimal("0.01"))
            else:
                score = Decimal("0")

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
        return Decimal("100") if has_education else Decimal("0")

    @classmethod
    def build_explanation(
        cls,
        job,
        matched_skills,
        missing_skills,
        skill_details,
        experience_years,
        education_found,
    ):
        """
        Build explanation JSON for the match.

        Returns:
            Dictionary with match details
        """
        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_skill_details": skill_details["matched"],
            "missing_skill_details": skill_details["missing"],
            "experience_level_required": job.experience_level,
            "candidate_experience_years": experience_years,
            "education_found": education_found,
        }

    @classmethod
    def _get_job_required_skills(cls, job):
        """Get required skills from structured rows first, then legacy text."""
        cached_skills = getattr(job, "_matching_required_skills", None)
        if cached_skills is not None:
            return cached_skills

        structured_skills = list(job.required_skills.values_list("name", flat=True))
        if structured_skills:
            job._matching_required_skills = structured_skills
            return structured_skills

        legacy_skills = cls._extract_skills_from_text(job.requirements)
        job._matching_required_skills = legacy_skills
        return legacy_skills

    @classmethod
    def _get_skill_embeddings(cls, skills, job=None):
        """Embed a batch of skills once and cache job-level required skill vectors."""
        if not skills:
            return []

        if job is not None:
            cached_skills = getattr(job, "_matching_required_skills", None)
            cached_embeddings = getattr(job, "_matching_required_skill_embeddings", None)
            if cached_skills == skills and cached_embeddings is not None:
                return cached_embeddings

        model = _load_skill_embedding_model()
        embeddings = model.encode(
            skills,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        if job is not None:
            job._matching_required_skills = list(skills)
            job._matching_required_skill_embeddings = embeddings

        return embeddings

    @staticmethod
    def _normalize_skill_name(skill_name):
        return skill_name.strip().casefold()

    @classmethod
    def _extract_skills_from_text(cls, text):
        """
        Extract skills from legacy job requirements text.

        This is retained only as a backwards-compatible fallback for jobs that do not
        yet have structured JobSkill rows.
        """
        if not text:
            return []

        # Legacy fallback for comma-separated recruiter input.
        skills = []
        for skill in text.split(","):
            skill = skill.strip()
            if skill:
                skills.append(skill)

        return skills

    @classmethod
    def _get_candidate_skills(cls, candidate):
        """
        Get candidate's skills from their structured resume.

        PERFORMANCE OPTIMIZATION: Use select_related and prefetch_related to reduce queries
        from 4 to 1-2 queries.

        Returns:
            QuerySet of ResumeSkill objects
        """
        try:
            # PERFORMANCE: Use select_related for ForeignKey relationships
            resume = Resume.objects.select_related("user").get(user=candidate)

            # PERFORMANCE: Use select_related for OneToOne relationships
            current_version = (
                resume.versions.select_related("structured_resume")
                .filter(is_current=True)
                .first()
            )

            if not current_version:
                return ResumeSkill.objects.none()

            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return ResumeSkill.objects.none()

            if not structured_resume:
                return ResumeSkill.objects.none()

            # PERFORMANCE: Use prefetch_related for ManyToMany relationships
            return structured_resume.skills.all()
        except Resume.DoesNotExist:
            return ResumeSkill.objects.none()

    @classmethod
    def _get_candidate_experience_years(cls, candidate):
        """
        Get candidate's total years of experience from start_date/end_date.

        PERFORMANCE OPTIMIZATION: Use select_related and prefetch_related to reduce queries
        from 4 to 1-2 queries.

        Calculates actual time worked across all experience entries.

        Returns:
            Float: Total years of experience
        """
        try:
            # PERFORMANCE: Use select_related for ForeignKey relationships
            resume = Resume.objects.select_related("user").get(user=candidate)

            # PERFORMANCE: Use select_related for OneToOne relationships
            current_version = (
                resume.versions.select_related("structured_resume")
                .filter(is_current=True)
                .first()
            )

            if not current_version:
                return 0.0

            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return 0.0

            if not structured_resume:
                return 0.0

            # PERFORMANCE: Use prefetch_related for reverse ForeignKey relationships
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

        PERFORMANCE OPTIMIZATION: Use select_related and prefetch_related to reduce queries
        from 4 to 1-2 queries.

        Returns:
            Boolean
        """
        try:
            # PERFORMANCE: Use select_related for ForeignKey relationships
            resume = Resume.objects.select_related("user").get(user=candidate)

            # PERFORMANCE: Use select_related for OneToOne relationships
            current_version = (
                resume.versions.select_related("structured_resume")
                .filter(is_current=True)
                .first()
            )

            if not current_version:
                return False

            try:
                structured_resume = current_version.structured_resume
            except StructuredResume.DoesNotExist:
                return False

            if not structured_resume:
                return False

            # PERFORMANCE: Use exists() instead of loading all education records
            return structured_resume.education.exists()
        except Resume.DoesNotExist:
            return False
