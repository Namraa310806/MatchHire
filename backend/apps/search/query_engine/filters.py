"""
Advanced filters for search queries.

This module provides reusable filters for all entity types in MatchHire.
Filters support various comparison operators, date ranges, location filtering,
experience levels, salary ranges, and more.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date


class FilterOperator(Enum):
    """Filter operators."""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    RANGE = "range"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class Filter:
    """
    Base filter class.
    
    Represents a single filter condition on a field.
    """
    
    field: str
    operator: FilterOperator
    value: Any = None
    nested_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        filter_dict: Dict[str, Any] = {
            "field": self.field,
            "operator": self.operator.value,
        }
        
        if self.value is not None:
            filter_dict["value"] = self.value
        if self.nested_path is not None:
            filter_dict["nested_path"] = self.nested_path
        
        return filter_dict
    
    def validate(self) -> bool:
        """Validate the filter."""
        if not self.field:
            return False
        
        # Some operators don't require a value
        if self.operator in [FilterOperator.EXISTS, FilterOperator.NOT_EXISTS,
                           FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return True
        
        return self.value is not None


@dataclass
class RangeFilter:
    """
    Range filter for numeric and date ranges.
    """
    
    field: str
    gte: Optional[Any] = None
    gt: Optional[Any] = None
    lte: Optional[Any] = None
    lt: Optional[Any] = None
    nested_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        filter_dict: Dict[str, Any] = {
            "field": self.field,
            "operator": FilterOperator.RANGE.value,
            "value": {},
        }
        
        if self.gte is not None:
            filter_dict["value"]["gte"] = self.gte
        if self.gt is not None:
            filter_dict["value"]["gt"] = self.gt
        if self.lte is not None:
            filter_dict["value"]["lte"] = self.lte
        if self.lt is not None:
            filter_dict["value"]["lt"] = self.lt
        
        if self.nested_path is not None:
            filter_dict["nested_path"] = self.nested_path
        
        return filter_dict
    
    def validate(self) -> bool:
        """Validate the filter."""
        has_bounds = any([self.gte, self.gt, self.lte, self.lt])
        return bool(self.field and has_bounds)


@dataclass
class BooleanFilter:
    """
    Boolean filter for combining multiple filters.
    """
    
    operator: str  # AND, OR, NOT
    filters: List[Union["Filter", "RangeFilter", "BooleanFilter"]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operator": self.operator,
            "filters": [f.to_dict() for f in self.filters],
        }
    
    def validate(self) -> bool:
        """Validate the filter."""
        if not self.filters:
            return False
        
        return all(f.validate() for f in self.filters)
    
    def add_filter(self, filter_obj: Union["Filter", "RangeFilter", "BooleanFilter"]) -> "BooleanFilter":
        """Add a filter to this boolean filter."""
        self.filters.append(filter_obj)
        return self


class FilterBuilder:
    """
    Builder for constructing complex filter combinations.
    """
    
    def __init__(self):
        """Initialize the filter builder."""
        self._filters: List[Union[Filter, RangeFilter, BooleanFilter]] = []
    
    def eq(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an equality filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.EQ, value=value, nested_path=nested_path))
        return self
    
    def ne(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a not-equal filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.NE, value=value, nested_path=nested_path))
        return self
    
    def gt(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a greater-than filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.GT, value=value, nested_path=nested_path))
        return self
    
    def gte(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a greater-than-or-equal filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.GTE, value=value, nested_path=nested_path))
        return self
    
    def lt(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a less-than filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.LT, value=value, nested_path=nested_path))
        return self
    
    def lte(self, field: str, value: Any, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a less-than-or-equal filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.LTE, value=value, nested_path=nested_path))
        return self
    
    def in_(self, field: str, values: List[Any], nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an IN filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.IN, value=values, nested_path=nested_path))
        return self
    
    def not_in(self, field: str, values: List[Any], nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a NOT_IN filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.NOT_IN, value=values, nested_path=nested_path))
        return self
    
    def contains(self, field: str, value: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a contains filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.CONTAINS, value=value, nested_path=nested_path))
        return self
    
    def not_contains(self, field: str, value: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a not-contains filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.NOT_CONTAINS, value=value, nested_path=nested_path))
        return self
    
    def starts_with(self, field: str, value: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a starts-with filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.STARTS_WITH, value=value, nested_path=nested_path))
        return self
    
    def ends_with(self, field: str, value: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an ends-with filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.ENDS_WITH, value=value, nested_path=nested_path))
        return self
    
    def exists(self, field: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an exists filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.EXISTS, nested_path=nested_path))
        return self
    
    def not_exists(self, field: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add a not-exists filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.NOT_EXISTS, nested_path=nested_path))
        return self
    
    def is_null(self, field: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an is-null filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.IS_NULL, nested_path=nested_path))
        return self
    
    def is_not_null(self, field: str, nested_path: Optional[str] = None) -> "FilterBuilder":
        """Add an is-not-null filter."""
        self._filters.append(Filter(field=field, operator=FilterOperator.IS_NOT_NULL, nested_path=nested_path))
        return self
    
    def range(self, field: str, **kwargs) -> "FilterBuilder":
        """Add a range filter."""
        self._filters.append(RangeFilter(field=field, **kwargs))
        return self
    
    def date_range(self, field: str, start: Optional[Union[str, date, datetime]] = None,
                   end: Optional[Union[str, date, datetime]] = None) -> "FilterBuilder":
        """Add a date range filter."""
        range_kwargs = {}
        if start is not None:
            range_kwargs["gte"] = start
        if end is not None:
            range_kwargs["lte"] = end
        return self.range(field, **range_kwargs)
    
    def and_(self, *filters: Union[Filter, RangeFilter, "BooleanFilter"]) -> "FilterBuilder":
        """Add an AND boolean filter."""
        bool_filter = BooleanFilter(operator="AND", filters=list(filters))
        self._filters.append(bool_filter)
        return self
    
    def or_(self, *filters: Union[Filter, RangeFilter, "BooleanFilter"]) -> "FilterBuilder":
        """Add an OR boolean filter."""
        bool_filter = BooleanFilter(operator="OR", filters=list(filters))
        self._filters.append(bool_filter)
        return self
    
    def not_(self, filter_obj: Union[Filter, RangeFilter, "BooleanFilter"]) -> "FilterBuilder":
        """Add a NOT boolean filter."""
        bool_filter = BooleanFilter(operator="NOT", filters=[filter_obj])
        self._filters.append(bool_filter)
        return self
    
    def build(self) -> List[Union[Filter, RangeFilter, BooleanFilter]]:
        """
        Build and return the filters.
        
        Returns:
            List of filter objects
        """
        if not all(f.validate() for f in self._filters):
            raise ValueError("One or more filters are invalid")
        
        return self._filters
    
    def reset(self) -> "FilterBuilder":
        """Reset the builder to initial state."""
        self._filters = []
        return self
    
    @classmethod
    def create(cls) -> "FilterBuilder":
        """Create a new filter builder instance."""
        return cls()


class JobFilters:
    """
    Pre-configured filters for job searches.
    """
    
    @staticmethod
    def by_status(status: str) -> Filter:
        """Filter jobs by status."""
        return Filter(field="status", operator=FilterOperator.EQ, value=status)
    
    @staticmethod
    def by_employment_type(employment_type: str) -> Filter:
        """Filter jobs by employment type (full-time, part-time, contract, etc.)."""
        return Filter(field="employment_type", operator=FilterOperator.EQ, value=employment_type)
    
    @staticmethod
    def by_employment_types(types: List[str]) -> Filter:
        """Filter jobs by multiple employment types."""
        return Filter(field="employment_type", operator=FilterOperator.IN, value=types)
    
    @staticmethod
    def by_experience_level(level: str) -> Filter:
        """Filter jobs by experience level (entry, mid, senior, executive)."""
        return Filter(field="experience_level", operator=FilterOperator.EQ, value=level)
    
    @staticmethod
    def by_experience_levels(levels: List[str]) -> Filter:
        """Filter jobs by multiple experience levels."""
        return Filter(field="experience_level", operator=FilterOperator.IN, value=levels)
    
    @staticmethod
    def by_salary_range(min_salary: Optional[int] = None, max_salary: Optional[int] = None) -> RangeFilter:
        """Filter jobs by salary range."""
        return RangeFilter(field="salary", gte=min_salary, lte=max_salary)
    
    @staticmethod
    def by_location(location: str) -> Filter:
        """Filter jobs by location."""
        return Filter(field="location", operator=FilterOperator.CONTAINS, value=location)
    
    @staticmethod
    def by_remote(is_remote: bool) -> Filter:
        """Filter jobs by remote status."""
        return Filter(field="is_remote", operator=FilterOperator.EQ, value=is_remote)
    
    @staticmethod
    def by_company(company_id: str) -> Filter:
        """Filter jobs by company ID."""
        return Filter(field="company_id", operator=FilterOperator.EQ, value=company_id)
    
    @staticmethod
    def by_companies(company_ids: List[str]) -> Filter:
        """Filter jobs by multiple company IDs."""
        return Filter(field="company_id", operator=FilterOperator.IN, value=company_ids)
    
    @staticmethod
    def by_industry(industry: str) -> Filter:
        """Filter jobs by industry."""
        return Filter(field="industry", operator=FilterOperator.CONTAINS, value=industry)
    
    @staticmethod
    def by_skill(skill: str) -> Filter:
        """Filter jobs by required skill."""
        return Filter(field="skills", operator=FilterOperator.CONTAINS, value=skill, nested_path="skills")
    
    @staticmethod
    def by_skills(skills: List[str]) -> Filter:
        """Filter jobs by required skills (any match)."""
        return Filter(field="skills", operator=FilterOperator.IN, value=skills, nested_path="skills")
    
    @staticmethod
    def by_posted_date_range(start_date: Optional[Union[str, date]] = None,
                            end_date: Optional[Union[str, date]] = None) -> RangeFilter:
        """Filter jobs by posted date range."""
        return RangeFilter(field="posted_date", gte=start_date, lte=end_date)
    
    @staticmethod
    def by_application_deadline(deadline: Union[str, date]) -> Filter:
        """Filter jobs by application deadline (not expired)."""
        return Filter(field="application_deadline", operator=FilterOperator.GTE, value=deadline)
    
    @staticmethod
    def active() -> Filter:
        """Filter for active jobs."""
        return Filter(field="status", operator=FilterOperator.EQ, value="active")
    
    @staticmethod
    def urgent() -> Filter:
        """Filter for urgent jobs."""
        return Filter(field="is_urgent", operator=FilterOperator.EQ, value=True)


class CandidateFilters:
    """
    Pre-configured filters for candidate searches.
    """
    
    @staticmethod
    def by_status(status: str) -> Filter:
        """Filter candidates by status."""
        return Filter(field="status", operator=FilterOperator.EQ, value=status)
    
    @staticmethod
    def by_experience_level(level: str) -> Filter:
        """Filter candidates by experience level."""
        return Filter(field="experience_level", operator=FilterOperator.EQ, value=level)
    
    @staticmethod
    def by_experience_years(min_years: Optional[int] = None, max_years: Optional[int] = None) -> RangeFilter:
        """Filter candidates by years of experience."""
        return RangeFilter(field="years_of_experience", gte=min_years, lte=max_years)
    
    @staticmethod
    def by_location(location: str) -> Filter:
        """Filter candidates by location."""
        return Filter(field="location", operator=FilterOperator.CONTAINS, value=location)
    
    @staticmethod
    def by_willing_to_relocate(is_willing: bool) -> Filter:
        """Filter candidates by willingness to relocate."""
        return Filter(field="willing_to_relocate", operator=FilterOperator.EQ, value=is_willing)
    
    @staticmethod
    def by_skill(skill: str) -> Filter:
        """Filter candidates by skill."""
        return Filter(field="skills", operator=FilterOperator.CONTAINS, value=skill, nested_path="skills")
    
    @staticmethod
    def by_skills(skills: List[str]) -> Filter:
        """Filter candidates by skills (any match)."""
        return Filter(field="skills", operator=FilterOperator.IN, value=skills, nested_path="skills")
    
    @staticmethod
    def by_education_level(level: str) -> Filter:
        """Filter candidates by education level."""
        return Filter(field="education_level", operator=FilterOperator.EQ, value=level)
    
    @staticmethod
    def by_salary_expectation(min_salary: Optional[int] = None, max_salary: Optional[int] = None) -> RangeFilter:
        """Filter candidates by salary expectation."""
        return RangeFilter(field="salary_expectation", gte=min_salary, lte=max_salary)
    
    @staticmethod
    def by_employment_type(employment_type: str) -> Filter:
        """Filter candidates by preferred employment type."""
        return Filter(field="preferred_employment_type", operator=FilterOperator.EQ, value=employment_type)
    
    @staticmethod
    def by_availability(availability: str) -> bool:
        """Filter candidates by availability (immediate, notice period, etc.)."""
        return Filter(field="availability", operator=FilterOperator.EQ, value=availability)
    
    @staticmethod
    def active() -> Filter:
        """Filter for active candidates."""
        return Filter(field="is_active", operator=FilterOperator.EQ, value=True)
    
    @staticmethod
    def verified() -> Filter:
        """Filter for verified candidates."""
        return Filter(field="is_verified", operator=FilterOperator.EQ, value=True)


class ResumeFilters:
    """
    Pre-configured filters for resume searches.
    """
    
    @staticmethod
    def by_candidate_id(candidate_id: str) -> Filter:
        """Filter resumes by candidate ID."""
        return Filter(field="candidate_id", operator=FilterOperator.EQ, value=candidate_id)
    
    @staticmethod
    def by_skill(skill: str) -> Filter:
        """Filter resumes by skill."""
        return Filter(field="skills", operator=FilterOperator.CONTAINS, value=skill, nested_path="skills")
    
    @staticmethod
    def by_skills(skills: List[str]) -> Filter:
        """Filter resumes by skills (any match)."""
        return Filter(field="skills", operator=FilterOperator.IN, value=skills, nested_path="skills")
    
    @staticmethod
    def by_experience_years(min_years: Optional[int] = None, max_years: Optional[int] = None) -> RangeFilter:
        """Filter resumes by total years of experience."""
        return RangeFilter(field="total_experience_years", gte=min_years, lte=max_years)
    
    @staticmethod
    def by_education_level(level: str) -> Filter:
        """Filter resumes by education level."""
        return Filter(field="education_level", operator=FilterOperator.EQ, value=level)
    
    @staticmethod
    def by_degree(degree: str) -> Filter:
        """Filter resumes by degree."""
        return Filter(field="degree", operator=FilterOperator.CONTAINS, value=degree, nested_path="education")
    
    @staticmethod
    def by_field_of_study(field: str) -> Filter:
        """Filter resumes by field of study."""
        return Filter(field="field_of_study", operator=FilterOperator.CONTAINS, value=field, nested_path="education")
    
    @staticmethod
    def by_company(company: str) -> Filter:
        """Filter resumes by work experience company."""
        return Filter(field="company", operator=FilterOperator.CONTAINS, value=company, nested_path="work_experience")
    
    @staticmethod
    def by_job_title(title: str) -> Filter:
        """Filter resumes by job title."""
        return Filter(field="job_title", operator=FilterOperator.CONTAINS, value=title, nested_path="work_experience")
    
    @staticmethod
    def by_updated_date_range(start_date: Optional[Union[str, date]] = None,
                              end_date: Optional[Union[str, date]] = None) -> RangeFilter:
        """Filter resumes by last updated date range."""
        return RangeFilter(field="updated_at", gte=start_date, lte=end_date)
    
    @staticmethod
    def recent(days: int = 30) -> Filter:
        """Filter for recently updated resumes."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        return Filter(field="updated_at", operator=FilterOperator.GTE, value=cutoff_date)


class CompanyFilters:
    """
    Pre-configured filters for company searches.
    """
    
    @staticmethod
    def by_industry(industry: str) -> Filter:
        """Filter companies by industry."""
        return Filter(field="industry", operator=FilterOperator.CONTAINS, value=industry)
    
    @staticmethod
    def by_size(size: str) -> Filter:
        """Filter companies by company size (startup, small, medium, large, enterprise)."""
        return Filter(field="company_size", operator=FilterOperator.EQ, value=size)
    
    @staticmethod
    def by_location(location: str) -> Filter:
        """Filter companies by location."""
        return Filter(field="headquarters_location", operator=FilterOperator.CONTAINS, value=location)
    
    @staticmethod
    def by_funding_stage(stage: str) -> Filter:
        """Filter companies by funding stage."""
        return Filter(field="funding_stage", operator=FilterOperator.EQ, value=stage)
    
    @staticmethod
    def by_employee_count(min_employees: Optional[int] = None, max_employees: Optional[int] = None) -> RangeFilter:
        """Filter companies by employee count."""
        return RangeFilter(field="employee_count", gte=min_employees, lte=max_employees)
    
    @staticmethod
    def by_revenue_range(min_revenue: Optional[int] = None, max_revenue: Optional[int] = None) -> RangeFilter:
        """Filter companies by revenue range."""
        return RangeFilter(field="annual_revenue", gte=min_revenue, lte=max_revenue)
    
    @staticmethod
    def verified() -> Filter:
        """Filter for verified companies."""
        return Filter(field="is_verified", operator=FilterOperator.EQ, value=True)
    
    @staticmethod
    def active() -> Filter:
        """Filter for active companies."""
        return Filter(field="is_active", operator=FilterOperator.EQ, value=True)


class RecruiterFilters:
    """
    Pre-configured filters for recruiter searches.
    """
    
    @staticmethod
    def by_company_id(company_id: str) -> Filter:
        """Filter recruiters by company ID."""
        return Filter(field="company_id", operator=FilterOperator.EQ, value=company_id)
    
    @staticmethod
    def by_company_ids(company_ids: List[str]) -> Filter:
        """Filter recruiters by multiple company IDs."""
        return Filter(field="company_id", operator=FilterOperator.IN, value=company_ids)
    
    @staticmethod
    def by_role(role: str) -> Filter:
        """Filter recruiters by role."""
        return Filter(field="role", operator=FilterOperator.EQ, value=role)
    
    @staticmethod
    def by_department(department: str) -> Filter:
        """Filter recruiters by department."""
        return Filter(field="department", operator=FilterOperator.CONTAINS, value=department)
    
    @staticmethod
    def by_location(location: str) -> Filter:
        """Filter recruiters by location."""
        return Filter(field="location", operator=FilterOperator.CONTAINS, value=location)
    
    @staticmethod
    def verified() -> Filter:
        """Filter for verified recruiters."""
        return Filter(field="is_verified", operator=FilterOperator.EQ, value=True)
    
    @staticmethod
    def active() -> Filter:
        """Filter for active recruiters."""
        return Filter(field="is_active", operator=FilterOperator.EQ, value=True)


class ApplicationFilters:
    """
    Pre-configured filters for application searches.
    """
    
    @staticmethod
    def by_job_id(job_id: str) -> Filter:
        """Filter applications by job ID."""
        return Filter(field="job_id", operator=FilterOperator.EQ, value=job_id)
    
    @staticmethod
    def by_candidate_id(candidate_id: str) -> Filter:
        """Filter applications by candidate ID."""
        return Filter(field="candidate_id", operator=FilterOperator.EQ, value=candidate_id)
    
    @staticmethod
    def by_status(status: str) -> Filter:
        """Filter applications by status."""
        return Filter(field="status", operator=FilterOperator.EQ, value=status)
    
    @staticmethod
    def by_statuses(statuses: List[str]) -> Filter:
        """Filter applications by multiple statuses."""
        return Filter(field="status", operator=FilterOperator.IN, value=statuses)
    
    @staticmethod
    def by_stage(stage: str) -> Filter:
        """Filter applications by application stage."""
        return Filter(field="stage", operator=FilterOperator.EQ, value=stage)
    
    @staticmethod
    def by_stages(stages: List[str]) -> Filter:
        """Filter applications by multiple stages."""
        return Filter(field="stage", operator=FilterOperator.IN, value=stages)
    
    @staticmethod
    def by_applied_date_range(start_date: Optional[Union[str, date]] = None,
                               end_date: Optional[Union[str, date]] = None) -> RangeFilter:
        """Filter applications by applied date range."""
        return RangeFilter(field="applied_at", gte=start_date, lte=end_date)
    
    @staticmethod
    def by_source(source: str) -> Filter:
        """Filter applications by source (direct, referral, etc.)."""
        return Filter(field="source", operator=FilterOperator.EQ, value=source)
    
    @staticmethod
    def by_recruiter_id(recruiter_id: str) -> Filter:
        """Filter applications by assigned recruiter ID."""
        return Filter(field="assigned_recruiter_id", operator=FilterOperator.EQ, value=recruiter_id)
    
    @staticmethod
    def pending() -> Filter:
        """Filter for pending applications."""
        return Filter(field="status", operator=FilterOperator.EQ, value="pending")
    
    @staticmethod
    def in_progress() -> Filter:
        """Filter for in-progress applications."""
        return Filter(field="status", operator=FilterOperator.IN, value=["screening", "interviewing", "assessment"])


class InterviewFilters:
    """
    Pre-configured filters for interview searches.
    """
    
    @staticmethod
    def by_application_id(application_id: str) -> Filter:
        """Filter interviews by application ID."""
        return Filter(field="application_id", operator=FilterOperator.EQ, value=application_id)
    
    @staticmethod
    def by_job_id(job_id: str) -> Filter:
        """Filter interviews by job ID."""
        return Filter(field="job_id", operator=FilterOperator.EQ, value=job_id)
    
    @staticmethod
    def by_candidate_id(candidate_id: str) -> Filter:
        """Filter interviews by candidate ID."""
        return Filter(field="candidate_id", operator=FilterOperator.EQ, value=candidate_id)
    
    @staticmethod
    def by_recruiter_id(recruiter_id: str) -> Filter:
        """Filter interviews by recruiter ID."""
        return Filter(field="recruiter_id", operator=FilterOperator.EQ, value=recruiter_id)
    
    @staticmethod
    def by_status(status: str) -> Filter:
        """Filter interviews by status."""
        return Filter(field="status", operator=FilterOperator.EQ, value=status)
    
    @staticmethod
    def by_statuses(statuses: List[str]) -> Filter:
        """Filter interviews by multiple statuses."""
        return Filter(field="status", operator=FilterOperator.IN, value=statuses)
    
    @staticmethod
    def by_type(interview_type: str) -> Filter:
        """Filter interviews by type (phone, video, onsite, etc.)."""
        return Filter(field="interview_type", operator=FilterOperator.EQ, value=interview_type)
    
    @staticmethod
    def by_scheduled_date_range(start_date: Optional[Union[str, date]] = None,
                                end_date: Optional[Union[str, date]] = None) -> RangeFilter:
        """Filter interviews by scheduled date range."""
        return RangeFilter(field="scheduled_at", gte=start_date, lte=end_date)
    
    @staticmethod
    def upcoming() -> Filter:
        """Filter for upcoming interviews."""
        from datetime import datetime
        return Filter(field="scheduled_at", operator=FilterOperator.GTE, value=datetime.now())
    
    @staticmethod
    def past() -> Filter:
        """Filter for past interviews."""
        from datetime import datetime
        return Filter(field="scheduled_at", operator=FilterOperator.LT, value=datetime.now())


class SkillFilters:
    """
    Pre-configured filters for skill searches.
    """
    
    @staticmethod
    def by_category(category: str) -> Filter:
        """Filter skills by category."""
        return Filter(field="category", operator=FilterOperator.CONTAINS, value=category)
    
    @staticmethod
    def by_name(name: str) -> Filter:
        """Filter skills by name."""
        return Filter(field="name", operator=FilterOperator.CONTAINS, value=name)
    
    @staticmethod
    def by_popularity(min_popularity: Optional[int] = None) -> Filter:
        """Filter skills by minimum popularity."""
        return Filter(field="popularity_score", operator=FilterOperator.GTE, value=min_popularity)
    
    @staticmethod
    def trending() -> Filter:
        """Filter for trending skills."""
        return Filter(field="is_trending", operator=FilterOperator.EQ, value=True)
    
    @staticmethod
    def verified() -> Filter:
        """Filter for verified skills."""
        return Filter(field="is_verified", operator=FilterOperator.EQ, value=True)
