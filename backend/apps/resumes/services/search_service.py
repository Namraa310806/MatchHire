from django.db.models import Q
from typing import List, Optional

from ..models import (
    StructuredResume,
)


class ResumeSearchService:
    """
    Service for searching and filtering structured resume data.
    Uses ORM queries only. No external search services.
    Optimized with select_related and prefetch_related to avoid N+1 queries.
    """

    # Valid ordering fields
    VALID_ORDERING_FIELDS = {
        "name": "full_name",
        "-name": "-full_name",
        "created_at": "resume_version__resume__created_at",
        "-created_at": "-resume_version__resume__created_at",
    }

    @classmethod
    def search_by_skill(cls, skill: str) -> List[StructuredResume]:
        """
        Search resumes by skill name (case-insensitive partial match).

        Query optimization:
        - Uses prefetch_related for skills to avoid N+1 queries
        - Filters at database level
        - Only searches current resume versions
        """
        return (
            StructuredResume.objects.filter(
                resume_version__is_current=True, skills__name__icontains=skill
            )
            .prefetch_related("skills")
            .distinct()
        )

    @classmethod
    def search_by_location(cls, location: str) -> List[StructuredResume]:
        """
        Search resumes by location (case-insensitive partial match).

        Query optimization:
        - Uses prefetch_related for related fields
        - Only searches current resume versions
        """
        return (
            StructuredResume.objects.filter(
                resume_version__is_current=True, location__icontains=location
            )
            .prefetch_related(
                "skills", "education", "experience", "projects", "certifications"
            )
            .distinct()
        )

    @classmethod
    def search_by_company(cls, company: str) -> List[StructuredResume]:
        """
        Search resumes by company name (case-insensitive partial match).

        Query optimization:
        - Uses prefetch_related for experience to avoid N+1 queries
        - Only searches current resume versions
        """
        return (
            StructuredResume.objects.filter(
                resume_version__is_current=True, experience__company__icontains=company
            )
            .prefetch_related("experience", "skills")
            .distinct()
        )

    @classmethod
    def search_by_education(cls, education: str) -> List[StructuredResume]:
        """
        Search resumes by education degree or institution (case-insensitive partial match).

        Query optimization:
        - Uses prefetch_related for education to avoid N+1 queries
        - Only searches current resume versions
        """
        return (
            StructuredResume.objects.filter(resume_version__is_current=True)
            .filter(
                Q(education__degree__icontains=education)
                | Q(education__institution__icontains=education)
            )
            .prefetch_related("education", "skills")
            .distinct()
        )

    @classmethod
    def search_by_certification(cls, certification: str) -> List[StructuredResume]:
        """
        Search resumes by certification name or issuer (case-insensitive partial match).

        Query optimization:
        - Uses prefetch_related for certifications to avoid N+1 queries
        - Only searches current resume versions
        """
        return (
            StructuredResume.objects.filter(resume_version__is_current=True)
            .filter(
                Q(certifications__name__icontains=certification)
                | Q(certifications__issuer__icontains=certification)
            )
            .prefetch_related("certifications", "skills")
            .distinct()
        )

    @classmethod
    def search(
        cls,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        education: Optional[str] = None,
        certification: Optional[str] = None,
        ordering: Optional[str] = None,
    ) -> List[StructuredResume]:
        """
        Combined search with multiple filters.

        Args:
            skills: List of skill names (OR logic - resumes with any of the skills)
            location: Location string
            company: Company name
            education: Education degree or institution
            certification: Certification name or issuer
            ordering: Ordering field (e.g., 'name', '-name', 'created_at', '-created_at')

        Returns:
            QuerySet of StructuredResume objects with optimized prefetching

        Query optimization strategy:
        1. Build all filters in a single query using Q objects
        2. Use select_related for ForeignKey relationships (resume_version, resume_version__resume)
        3. Use prefetch_related for ManyToMany and reverse ForeignKey relationships
        4. Use Prefetch with specific querysets for related data to optimize further
        5. Apply distinct() to avoid duplicates from joins
        6. Apply ordering at database level
        """
        # Start with base queryset - only search current resume versions
        queryset = StructuredResume.objects.filter(resume_version__is_current=True)

        # Apply skill filters (OR logic - resumes with ANY of the specified skills)
        if skills:
            skill_queries = [Q(skills__name__icontains=skill) for skill in skills]
            skill_query = skill_queries.pop()
            for q in skill_queries:
                skill_query |= q
            queryset = queryset.filter(skill_query)

        # Apply location filter
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Apply company filter
        if company:
            queryset = queryset.filter(experience__company__icontains=company)

        # Apply education filter (degree OR institution)
        if education:
            queryset = queryset.filter(
                Q(education__degree__icontains=education)
                | Q(education__institution__icontains=education)
            )

        # Apply certification filter (name OR issuer)
        if certification:
            queryset = queryset.filter(
                Q(certifications__name__icontains=certification)
                | Q(certifications__issuer__icontains=certification)
            )

        # Apply distinct to avoid duplicates from joins
        queryset = queryset.distinct()

        # Apply ordering
        if ordering:
            if ordering in cls.VALID_ORDERING_FIELDS:
                queryset = queryset.order_by(cls.VALID_ORDERING_FIELDS[ordering])
            else:
                # If invalid ordering, default to created_at desc
                queryset = queryset.order_by("-resume_version__resume__created_at")
        else:
            # Default ordering
            queryset = queryset.order_by("-resume_version__resume__created_at")

        # Apply select_related for ForeignKey relationships
        # This reduces queries from N+1 to 1 for foreign keys
        queryset = queryset.select_related(
            "resume_version",
            "resume_version__resume",
        )

        # Apply prefetch_related for reverse ForeignKey and ManyToMany relationships
        # This loads related objects in a single query
        queryset = queryset.prefetch_related(
            "skills",
            "education",
            "experience",
            "projects",
            "certifications",
        )

        return queryset

    @classmethod
    def validate_ordering(cls, ordering: Optional[str]) -> bool:
        """
        Validate ordering field.

        Returns True if ordering is valid, False otherwise.
        """
        if ordering is None:
            return True
        return ordering in cls.VALID_ORDERING_FIELDS
