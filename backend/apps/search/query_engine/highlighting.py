"""
Highlighting support for search results.

This module provides configurable highlighting for matched text in search results,
supporting multiple fields, custom tags, snippet length, and fragment selection.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class HighlighterType(Enum):
    """Highlighter type enumeration."""
    UNIFIED = "unified"
    FVH = "fvh"  # Fast Vector Highlighter
    PLAIN = "plain"


class FragmentOrder(Enum):
    """Fragment order for multiple fragments."""
    SCORE = "score"  # Order by score
    OFFSET = "offset"  # Order by offset


@dataclass
class HighlightConfig:
    """
    Configuration for highlighting on a single field.
    """
    
    field: str
    pre_tags: List[str] = field(default_factory=lambda: ["<em>"])
    post_tags: List[str] = field(default_factory=lambda: ["</em>"])
    fragment_size: int = 150
    number_of_fragments: int = 3
    fragment_offset: int = 0
    type: HighlighterType = HighlighterType.UNIFIED
    order: FragmentOrder = FragmentOrder.SCORE
    highlight_query: Optional[Dict[str, Any]] = None
    require_field_match: bool = False
    boundary_chars: Optional[str] = None
    boundary_max_scan: int = 20
    boundary_scanner: str = "simple"
    boundary_scanner_locale: Optional[str] = None
    encoder: str = "default"
    no_match_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        config_dict: Dict[str, Any] = {
            "field": self.field,
            "pre_tags": self.pre_tags,
            "post_tags": self.post_tags,
            "fragment_size": self.fragment_size,
            "number_of_fragments": self.number_of_fragments,
            "fragment_offset": self.fragment_offset,
            "type": self.type.value,
            "order": self.order.value,
            "require_field_match": self.require_field_match,
            "boundary_max_scan": self.boundary_max_scan,
            "boundary_scanner": self.boundary_scanner,
            "encoder": self.encoder,
        }
        
        if self.highlight_query is not None:
            config_dict["highlight_query"] = self.highlight_query
        if self.boundary_chars is not None:
            config_dict["boundary_chars"] = self.boundary_chars
        if self.boundary_scanner_locale is not None:
            config_dict["boundary_scanner_locale"] = self.boundary_scanner_locale
        if self.no_match_size is not None:
            config_dict["no_match_size"] = self.no_match_size
        
        return config_dict
    
    def validate(self) -> bool:
        """Validate the configuration."""
        return bool(self.field and self.fragment_size > 0 and self.number_of_fragments >= 0)


@dataclass
class HighlightFragment:
    """
    A single highlighted fragment.
    """
    
    text: str
    score: Optional[float] = None
    matched_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "text": self.text,
            "score": self.score,
            "matched_fields": self.matched_fields,
        }


@dataclass
class FieldHighlight:
    """
    Highlight results for a single field.
    """
    
    field: str
    fragments: List[HighlightFragment]
    matched_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "fragments": [f.to_dict() for f in self.fragments],
            "matched_fields": self.matched_fields,
        }
    
    def get_best_fragment(self) -> Optional[HighlightFragment]:
        """Get the highest-scoring fragment."""
        if not self.fragments:
            return None
        return max(self.fragments, key=lambda f: f.score or 0)
    
    def get_all_text(self) -> str:
        """Get all fragments combined as text."""
        return " ... ".join(f.text for f in self.fragments)


@dataclass
class HighlightResult:
    """
    Complete highlight results for a document.
    """
    
    highlights: Dict[str, FieldHighlight]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            field: highlight.to_dict()
            for field, highlight in self.highlights.items()
        }
    
    def get_field_highlight(self, field: str) -> Optional[FieldHighlight]:
        """Get highlight for a specific field."""
        return self.highlights.get(field)
    
    def has_highlights(self) -> bool:
        """Check if any highlights exist."""
        return bool(self.highlights)
    
    def get_all_fields(self) -> List[str]:
        """Get all fields with highlights."""
        return list(self.highlights.keys())


class HighlightBuilder:
    """
    Builder for constructing highlight configurations.
    """
    
    def __init__(self):
        """Initialize the highlight builder."""
        self._configs: List[HighlightConfig] = []
        self._global_tags: Optional[Dict[str, List[str]]]] = None
    
    def add_field(
        self,
        field: str,
        pre_tags: Optional[List[str]] = None,
        post_tags: Optional[List[str]] = None,
        fragment_size: int = 150,
        number_of_fragments: int = 3,
        **kwargs
    ) -> "HighlightBuilder":
        """
        Add a field to highlight.
        
        Args:
            field: Field name to highlight
            pre_tags: Opening tags for highlights
            post_tags: Closing tags for highlights
            fragment_size: Size of each fragment in characters
            number_of_fragments: Number of fragments to return
            **kwargs: Additional highlight configuration
            
        Returns:
            Self for method chaining
        """
        if pre_tags is None:
            pre_tags = self._global_tags["pre"] if self._global_tags else ["<em>"]
        if post_tags is None:
            post_tags = self._global_tags["post"] if self._global_tags else ["</em>"]
        
        config = HighlightConfig(
            field=field,
            pre_tags=pre_tags,
            post_tags=post_tags,
            fragment_size=fragment_size,
            number_of_fragments=number_of_fragments,
            **kwargs
        )
        self._configs.append(config)
        return self
    
    def set_global_tags(self, pre_tags: List[str], post_tags: List[str]) -> "HighlightBuilder":
        """Set global highlight tags for all fields."""
        self._global_tags = {"pre": pre_tags, "post": post_tags}
        return self
    
    def title(self, field: str = "title") -> "HighlightBuilder":
        """Add title field highlighting with short fragments."""
        return self.add_field(
            field=field,
            fragment_size=50,
            number_of_fragments=1,
        )
    
    def description(self, field: str = "description") -> "HighlightBuilder":
        """Add description field highlighting with standard fragments."""
        return self.add_field(
            field=field,
            fragment_size=150,
            number_of_fragments=3,
        )
    
    def content(self, field: str = "content") -> "HighlightBuilder":
        """Add content field highlighting with larger fragments."""
        return self.add_field(
            field=field,
            fragment_size=200,
            number_of_fragments=5,
        )
    
    def skills(self, field: str = "skills") -> "HighlightBuilder":
        """Add skills field highlighting."""
        return self.add_field(
            field=field,
            fragment_size=100,
            number_of_fragments=3,
        )
    
    def requirements(self, field: str = "requirements") -> "HighlightBuilder":
        """Add requirements field highlighting."""
        return self.add_field(
            field=field,
            fragment_size=150,
            number_of_fragments=3,
        )
    
    def summary(self, field: str = "summary") -> "HighlightBuilder":
        """Add summary field highlighting."""
        return self.add_field(
            field=field,
            fragment_size=150,
            number_of_fragments=2,
        )
    
    def build(self) -> List[HighlightConfig]:
        """
        Build and return the highlight configurations.
        
        Returns:
            List of HighlightConfig objects
            
        Raises:
            ValueError: If any configuration is invalid
        """
        if not all(config.validate() for config in self._configs):
            raise ValueError("One or more highlight configurations are invalid")
        
        return self._configs
    
    def reset(self) -> "HighlightBuilder":
        """Reset the builder to initial state."""
        self._configs = []
        self._global_tags = None
        return self
    
    @classmethod
    def create(cls) -> "HighlightBuilder":
        """Create a new highlight builder instance."""
        return cls()


class PredefinedHighlights:
    """
    Pre-configured highlight sets for common use cases.
    """
    
    @staticmethod
    def job_search() -> List[HighlightConfig]:
        """Highlights for job search."""
        builder = HighlightBuilder()
        return (
            builder
            .title(field="title")
            .description(field="description")
            .requirements(field="requirements")
            .build()
        )
    
    @staticmethod
    def candidate_search() -> List[HighlightConfig]:
        """Highlights for candidate search."""
        builder = HighlightBuilder()
        return (
            builder
            .title(field="full_name")
            .summary(field="summary")
            .skills(field="skills")
            .build()
        )
    
    @staticmethod
    def resume_search() -> List[HighlightConfig]:
        """Highlights for resume search."""
        builder = HighlightBuilder()
        return (
            builder
            .summary(field="summary")
            .content(field="raw_text")
            .skills(field="skills")
            .build()
        )
    
    @staticmethod
    def company_search() -> List[HighlightConfig]:
        """Highlights for company search."""
        builder = HighlightBuilder()
        return (
            builder
            .title(field="company_name")
            .description(field="description")
            .build()
        )
