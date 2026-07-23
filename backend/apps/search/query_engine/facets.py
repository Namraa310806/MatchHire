"""
Faceted search implementation.

This module provides dynamic faceted search capabilities, allowing users
to filter and explore search results by various dimensions like location,
company, skills, experience, salary, education, and more.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class FacetSort(Enum):
    """Facet sorting options."""
    COUNT = "count"  # Sort by count (descending)
    VALUE = "value"  # Sort by value (ascending)
    ALPHA = "alpha"  # Sort alphabetically


@dataclass
class FacetConfig:
    """
    Configuration for a single facet.
    
    Defines how a facet should be computed and displayed.
    """
    
    field: str
    name: str
    size: int = 10
    sort: FacetSort = FacetSort.COUNT
    show_missing: bool = False
    min_doc_count: int = 1
    nested_path: Optional[str] = None
    value_filter: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        config_dict: Dict[str, Any] = {
            "field": self.field,
            "name": self.name,
            "size": self.size,
            "sort": self.sort.value,
            "show_missing": self.show_missing,
            "min_doc_count": self.min_doc_count,
        }
        
        if self.nested_path is not None:
            config_dict["nested_path"] = self.nested_path
        if self.value_filter is not None:
            config_dict["value_filter"] = self.value_filter
        
        return config_dict


@dataclass
class FacetValue:
    """
    A single facet value with count.
    """
    
    value: Any
    count: int
    selected: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "value": self.value,
            "count": self.count,
            "selected": self.selected,
            "metadata": self.metadata,
        }


@dataclass
class FacetResponse:
    """
    Response containing facet values for a field.
    """
    
    field: str
    name: str
    values: List[FacetValue]
    total: int
    other: int = 0
    missing: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "name": self.name,
            "values": [v.to_dict() for v in self.values],
            "total": self.total,
            "other": self.other,
            "missing": self.missing,
        }
    
    def get_selected_values(self) -> List[Any]:
        """Get all selected facet values."""
        return [v.value for v in self.values if v.selected]
    
    def get_selected_count(self) -> int:
        """Get count of selected facet values."""
        return sum(1 for v in self.values if v.selected)


@dataclass
class FacetState:
    """
    State of selected facets across all facets.
    
    Tracks which facet values are currently selected.
    """
    
    selected_facets: Dict[str, List[Any]] = field(default_factory=dict)
    
    def add_selection(self, field: str, value: Any) -> None:
        """Add a facet selection."""
        if field not in self.selected_facets:
            self.selected_facets[field] = []
        if value not in self.selected_facets[field]:
            self.selected_facets[field].append(value)
    
    def remove_selection(self, field: str, value: Any) -> None:
        """Remove a facet selection."""
        if field in self.selected_facets:
            if value in self.selected_facets[field]:
                self.selected_facets[field].remove(value)
            if not self.selected_facets[field]:
                del self.selected_facets[field]
    
    def clear_field(self, field: str) -> None:
        """Clear all selections for a field."""
        if field in self.selected_facets:
            del self.selected_facets[field]
    
    def clear_all(self) -> None:
        """Clear all facet selections."""
        self.selected_facets.clear()
    
    def is_selected(self, field: str, value: Any) -> bool:
        """Check if a facet value is selected."""
        return field in self.selected_facets and value in self.selected_facets[field]
    
    def get_selections(self, field: str) -> List[Any]:
        """Get all selected values for a field."""
        return self.selected_facets.get(field, [])
    
    def has_selections(self) -> bool:
        """Check if any facets are selected."""
        return bool(self.selected_facets)
    
    def to_dict(self) -> Dict[str, List[Any]]:
        """Convert to dictionary representation."""
        return self.selected_facets.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, List[Any]]) -> "FacetState":
        """Create FacetState from dictionary."""
        return cls(selected_facets=data.copy())


class FacetBuilder:
    """
    Builder for constructing facet configurations.
    """
    
    def __init__(self):
        """Initialize the facet builder."""
        self._facets: List[FacetConfig] = []
    
    def add_facet(
        self,
        field: str,
        name: str,
        size: int = 10,
        sort: FacetSort = FacetSort.COUNT,
        show_missing: bool = False,
        min_doc_count: int = 1,
        nested_path: Optional[str] = None,
        value_filter: Optional[Dict[str, Any]] = None,
    ) -> "FacetBuilder":
        """
        Add a facet configuration.
        
        Args:
            field: Field to facet on
            name: Display name for the facet
            size: Number of facet values to return
            sort: How to sort facet values
            show_missing: Whether to include missing values
            min_doc_count: Minimum document count for inclusion
            nested_path: Path for nested fields
            value_filter: Filter for facet values
            
        Returns:
            Self for method chaining
        """
        config = FacetConfig(
            field=field,
            name=name,
            size=size,
            sort=sort,
            show_missing=show_missing,
            min_doc_count=min_doc_count,
            nested_path=nested_path,
            value_filter=value_filter,
        )
        self._facets.append(config)
        return self
    
    def location_facet(self, size: int = 20) -> "FacetBuilder":
        """Add a location facet."""
        return self.add_facet(
            field="location",
            name="Location",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def company_facet(self, size: int = 20) -> "FacetBuilder":
        """Add a company facet."""
        return self.add_facet(
            field="company_name",
            name="Company",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def skills_facet(self, size: int = 30, nested_path: str = "skills") -> "FacetBuilder":
        """Add a skills facet."""
        return self.add_facet(
            field="name",
            name="Skills",
            size=size,
            sort=FacetSort.COUNT,
            nested_path=nested_path,
        )
    
    def experience_facet(self, size: int = 10) -> "FacetBuilder":
        """Add an experience level facet."""
        return self.add_facet(
            field="experience_level",
            name="Experience Level",
            size=size,
            sort=FacetSort.VALUE,
        )
    
    def salary_facet(self, size: int = 10) -> "FacetBuilder":
        """Add a salary range facet."""
        return self.add_facet(
            field="salary_range",
            name="Salary Range",
            size=size,
            sort=FacetSort.VALUE,
        )
    
    def education_facet(self, size: int = 10) -> "FacetBuilder":
        """Add an education level facet."""
        return self.add_facet(
            field="education_level",
            name="Education Level",
            size=size,
            sort=FacetSort.VALUE,
        )
    
    def employment_type_facet(self, size: int = 10) -> "FacetBuilder":
        """Add an employment type facet."""
        return self.add_facet(
            field="employment_type",
            name="Employment Type",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def industry_facet(self, size: int = 20) -> "FacetBuilder":
        """Add an industry facet."""
        return self.add_facet(
            field="industry",
            name="Industry",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def status_facet(self, size: int = 10) -> "FacetBuilder":
        """Add a status facet."""
        return self.add_facet(
            field="status",
            name="Status",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def application_stage_facet(self, size: int = 10) -> "FacetBuilder":
        """Add an application stage facet."""
        return self.add_facet(
            field="stage",
            name="Application Stage",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def company_size_facet(self, size: int = 10) -> "FacetBuilder":
        """Add a company size facet."""
        return self.add_facet(
            field="company_size",
            name="Company Size",
            size=size,
            sort=FacetSort.VALUE,
        )
    
    def funding_stage_facet(self, size: int = 10) -> "FacetBuilder":
        """Add a funding stage facet."""
        return self.add_facet(
            field="funding_stage",
            name="Funding Stage",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def interview_type_facet(self, size: int = 10) -> "FacetBuilder":
        """Add an interview type facet."""
        return self.add_facet(
            field="interview_type",
            name="Interview Type",
            size=size,
            sort=FacetSort.COUNT,
        )
    
    def posted_date_facet(self, size: int = 10) -> "FacetBuilder":
        """Add a posted date facet."""
        return self.add_facet(
            field="posted_date",
            name="Posted Date",
            size=size,
            sort=FacetSort.VALUE,
        )
    
    def build(self) -> List[FacetConfig]:
        """
        Build and return the facet configurations.
        
        Returns:
            List of FacetConfig objects
        """
        return self._facets
    
    def reset(self) -> "FacetBuilder":
        """Reset the builder to initial state."""
        self._facets = []
        return self
    
    @classmethod
    def create(cls) -> "FacetBuilder":
        """Create a new facet builder instance."""
        return cls()


class PredefinedFacets:
    """
    Pre-configured facet sets for common use cases.
    """
    
    @staticmethod
    def job_search_facets() -> List[FacetConfig]:
        """Facets for job search."""
        builder = FacetBuilder()
        return (
            builder
            .location_facet(size=20)
            .company_facet(size=15)
            .skills_facet(size=30)
            .experience_facet(size=5)
            .employment_type_facet(size=5)
            .industry_facet(size=15)
            .salary_facet(size=10)
            .build()
        )
    
    @staticmethod
    def candidate_search_facets() -> List[FacetConfig]:
        """Facets for candidate search."""
        builder = FacetBuilder()
        return (
            builder
            .location_facet(size=20)
            .skills_facet(size=30)
            .experience_facet(size=5)
            .education_facet(size=5)
            .employment_type_facet(size=5)
            .salary_facet(size=10)
            .build()
        )
    
    @staticmethod
    def company_search_facets() -> List[FacetConfig]:
        """Facets for company search."""
        builder = FacetBuilder()
        return (
            builder
            .industry_facet(size=20)
            .company_size_facet(size=5)
            .location_facet(size=20)
            .funding_stage_facet(size=10)
            .build()
        )
    
    @staticmethod
    def application_search_facets() -> List[FacetConfig]:
        """Facets for application search."""
        builder = FacetBuilder()
        return (
            builder
            .status_facet(size=10)
            .application_stage_facet(size=10)
            .company_facet(size=15)
            .build()
        )
    
    @staticmethod
    def interview_search_facets() -> List[FacetConfig]:
        """Facets for interview search."""
        builder = FacetBuilder()
        return (
            builder
            .status_facet(size=10)
            .interview_type_facet(size=5)
            .build()
        )
