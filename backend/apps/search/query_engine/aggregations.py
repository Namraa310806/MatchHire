"""
Aggregations framework for search results.

This module provides provider-independent aggregations for computing
statistics, metrics, and bucketed data from search results.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AggregationType(Enum):
    """Aggregation type enumeration."""
    COUNT = "count"
    TERMS = "terms"
    RANGE = "range"
    HISTOGRAM = "histogram"
    DATE_HISTOGRAM = "date_histogram"
    STATS = "stats"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    PERCENTILES = "percentiles"
    CARDINALITY = "cardinality"


class HistogramInterval(Enum):
    """Pre-defined histogram intervals."""
    SECOND = "1s"
    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"
    QUARTER = "1q"
    YEAR = "1y"


@dataclass
class Aggregation(ABC):
    """
    Base class for all aggregation types.
    """
    
    name: str
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the aggregation."""
        pass


@dataclass
class CountAggregation(Aggregation):
    """
    Count aggregation for counting documents.
    """
    
    field: Optional[str] = None  # None for document count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.COUNT.value,
        }
        
        if self.field is not None:
            agg_dict["field"] = self.field
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name)


@dataclass
class TermsAggregation(Aggregation):
    """
    Terms aggregation for bucketing by unique field values.
    """
    
    field: str
    size: int = 10
    order: Optional[str] = None  # count, _key, term
    min_doc_count: int = 1
    missing: Optional[Any] = None
    include: Optional[Union[str, List[Any]]] = None
    exclude: Optional[Union[str, List[Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.TERMS.value,
            "field": self.field,
            "size": self.size,
            "min_doc_count": self.min_doc_count,
        }
        
        if self.order is not None:
            agg_dict["order"] = self.order
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        if self.include is not None:
            agg_dict["include"] = self.include
        if self.exclude is not None:
            agg_dict["exclude"] = self.exclude
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field and self.size > 0)


@dataclass
class RangeBucket:
    """A single range bucket."""
    key: str
    from_value: Optional[Any] = None
    to_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        bucket_dict: Dict[str, Any] = {"key": self.key}
        
        if self.from_value is not None:
            bucket_dict["from"] = self.from_value
        if self.to_value is not None:
            bucket_dict["to"] = self.to_value
        
        return bucket_dict


@dataclass
class RangeAggregation(Aggregation):
    """
    Range aggregation for bucketing by numeric ranges.
    """
    
    field: str
    ranges: List[RangeBucket]
    keyed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.RANGE.value,
            "field": self.field,
            "ranges": [r.to_dict() for r in self.ranges],
            "keyed": self.keyed,
        }
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field and self.ranges)


@dataclass
class HistogramAggregation(Aggregation):
    """
    Histogram aggregation for bucketing by numeric intervals.
    """
    
    field: str
    interval: float
    min_doc_count: int = 1
    offset: Optional[float] = None
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.HISTOGRAM.value,
            "field": self.field,
            "interval": self.interval,
            "min_doc_count": self.min_doc_count,
        }
        
        if self.offset is not None:
            agg_dict["offset"] = self.offset
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field and self.interval > 0)


@dataclass
class DateHistogramAggregation(Aggregation):
    """
    Date histogram aggregation for bucketing by time intervals.
    """
    
    field: str
    interval: Union[str, HistogramInterval]
    format: Optional[str] = None
    min_doc_count: int = 1
    time_zone: Optional[str] = None
    missing: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        interval_value = self.interval.value if isinstance(self.interval, HistogramInterval) else self.interval
        
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.DATE_HISTOGRAM.value,
            "field": self.field,
            "interval": interval_value,
            "min_doc_count": self.min_doc_count,
        }
        
        if self.format is not None:
            agg_dict["format"] = self.format
        if self.time_zone is not None:
            agg_dict["time_zone"] = self.time_zone
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field and self.interval)


@dataclass
class StatsAggregation(Aggregation):
    """
    Stats aggregation for computing basic statistics (count, sum, avg, min, max).
    """
    
    field: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": AggregationType.STATS.value,
            "field": self.field,
        }
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class AverageAggregation(Aggregation):
    """
    Average aggregation for computing the mean value.
    """
    
    field: str
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.AVG.value,
            "field": self.field,
        }
        
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class MinAggregation(Aggregation):
    """
    Min aggregation for computing the minimum value.
    """
    
    field: str
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.MIN.value,
            "field": self.field,
        }
        
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class MaxAggregation(Aggregation):
    """
    Max aggregation for computing the maximum value.
    """
    
    field: str
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.MAX.value,
            "field": self.field,
        }
        
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class SumAggregation(Aggregation):
    """
    Sum aggregation for computing the sum of values.
    """
    
    field: str
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.SUM.value,
            "field": self.field,
        }
        
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class PercentilesAggregation(Aggregation):
    """
    Percentiles aggregation for computing percentile values.
    """
    
    field: str
    percents: List[float] = field(default_factory=lambda: [1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0])
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.PERCENTILES.value,
            "field": self.field,
            "percents": self.percents,
        }
        
        if self.missing is not None:
            agg_dict["missing"] = self.missing
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field and self.percents)


@dataclass
class CardinalityAggregation(Aggregation):
    """
    Cardinality aggregation for counting unique values.
    """
    
    field: str
    precision_threshold: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        agg_dict: Dict[str, Any] = {
            "name": self.name,
            "type": AggregationType.CARDINALITY.value,
            "field": self.field,
        }
        
        if self.precision_threshold is not None:
            agg_dict["precision_threshold"] = self.precision_threshold
        
        return agg_dict
    
    def validate(self) -> bool:
        """Validate the aggregation."""
        return bool(self.name and self.field)


@dataclass
class AggregationResult:
    """
    Result of an aggregation computation.
    """
    
    name: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "metadata": self.metadata,
        }


@dataclass
class Bucket:
    """
    A single bucket in a bucket aggregation.
    """
    
    key: Any
    doc_count: int
    aggregations: Dict[str, AggregationResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "key": self.key,
            "doc_count": self.doc_count,
            "aggregations": {k: v.to_dict() for k, v in self.aggregations.items()},
            "metadata": self.metadata,
        }


@dataclass
class BucketAggregationResult(AggregationResult):
    """
    Result of a bucket aggregation (terms, range, histogram, etc.).
    """
    
    buckets: List[Bucket]
    sum_other_doc_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        base_dict = super().to_dict()
        base_dict["buckets"] = [b.to_dict() for b in self.buckets]
        base_dict["sum_other_doc_count"] = self.sum_other_doc_count
        return base_dict


@dataclass
class StatsResult:
    """Result of a stats aggregation."""
    count: int
    sum: Optional[float] = None
    avg: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": self.avg,
            "min": self.min,
            "max": self.max,
        }


class AggregationBuilder:
    """
    Builder for constructing aggregations.
    """
    
    def __init__(self):
        """Initialize the aggregation builder."""
        self._aggregations: List[Aggregation] = []
    
    def count(self, name: str, field: Optional[str] = None) -> "AggregationBuilder":
        """Add a count aggregation."""
        self._aggregations.append(CountAggregation(name=name, field=field))
        return self
    
    def terms(self, name: str, field: str, size: int = 10, **kwargs) -> "AggregationBuilder":
        """Add a terms aggregation."""
        self._aggregations.append(TermsAggregation(name=name, field=field, size=size, **kwargs))
        return self
    
    def range(self, name: str, field: str, ranges: List[RangeBucket], **kwargs) -> "AggregationBuilder":
        """Add a range aggregation."""
        self._aggregations.append(RangeAggregation(name=name, field=field, ranges=ranges, **kwargs))
        return self
    
    def histogram(self, name: str, field: str, interval: float, **kwargs) -> "AggregationBuilder":
        """Add a histogram aggregation."""
        self._aggregations.append(HistogramAggregation(name=name, field=field, interval=interval, **kwargs))
        return self
    
    def date_histogram(self, name: str, field: str, interval: Union[str, HistogramInterval], **kwargs) -> "AggregationBuilder":
        """Add a date histogram aggregation."""
        self._aggregations.append(DateHistogramAggregation(name=name, field=field, interval=interval, **kwargs))
        return self
    
    def stats(self, name: str, field: str) -> "AggregationBuilder":
        """Add a stats aggregation."""
        self._aggregations.append(StatsAggregation(name=name, field=field))
        return self
    
    def avg(self, name: str, field: str, **kwargs) -> "AggregationBuilder":
        """Add an average aggregation."""
        self._aggregations.append(AverageAggregation(name=name, field=field, **kwargs))
        return self
    
    def min(self, name: str, field: str, **kwargs) -> "AggregationBuilder":
        """Add a min aggregation."""
        self._aggregations.append(MinAggregation(name=name, field=field, **kwargs))
        return self
    
    def max(self, name: str, field: str, **kwargs) -> "AggregationBuilder":
        """Add a max aggregation."""
        self._aggregations.append(MaxAggregation(name=name, field=field, **kwargs))
        return self
    
    def sum(self, name: str, field: str, **kwargs) -> "AggregationBuilder":
        """Add a sum aggregation."""
        self._aggregations.append(SumAggregation(name=name, field=field, **kwargs))
        return self
    
    def percentiles(self, name: str, field: str, percents: Optional[List[float]] = None, **kwargs) -> "AggregationBuilder":
        """Add a percentiles aggregation."""
        if percents is None:
            percents = [1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0]
        self._aggregations.append(PercentilesAggregation(name=name, field=field, percents=percents, **kwargs))
        return self
    
    def cardinality(self, name: str, field: str, **kwargs) -> "AggregationBuilder":
        """Add a cardinality aggregation."""
        self._aggregations.append(CardinalityAggregation(name=name, field=field, **kwargs))
        return self
    
    def build(self) -> List[Aggregation]:
        """
        Build and return the aggregations.
        
        Returns:
            List of Aggregation objects
            
        Raises:
            ValueError: If any aggregation is invalid
        """
        if not all(agg.validate() for agg in self._aggregations):
            raise ValueError("One or more aggregations are invalid")
        
        return self._aggregations
    
    def reset(self) -> "AggregationBuilder":
        """Reset the builder to initial state."""
        self._aggregations = []
        return self
    
    @classmethod
    def create(cls) -> "AggregationBuilder":
        """Create a new aggregation builder instance."""
        return cls()


class PredefinedAggregations:
    """
    Pre-configured aggregation sets for common use cases.
    """
    
    @staticmethod
    def job_salary_stats() -> List[Aggregation]:
        """Salary statistics for jobs."""
        builder = AggregationBuilder()
        return (
            builder
            .stats(name="salary_stats", field="salary")
            .avg(name="avg_salary", field="salary")
            .min(name="min_salary", field="salary")
            .max(name="max_salary", field="salary")
            .build()
        )
    
    @staticmethod
    def job_location_distribution() -> List[Aggregation]:
        """Location distribution for jobs."""
        builder = AggregationBuilder()
        return (
            builder
            .terms(name="by_location", field="location", size=20)
            .build()
        )
    
    @staticmethod
    def job_posting_timeline(interval: str = "1M") -> List[Aggregation]:
        """Job posting timeline."""
        builder = AggregationBuilder()
        return (
            builder
            .date_histogram(name="posted_over_time", field="posted_date", interval=interval)
            .build()
        )
    
    @staticmethod
    def candidate_experience_stats() -> List[Aggregation]:
        """Experience statistics for candidates."""
        builder = AggregationBuilder()
        return (
            builder
            .stats(name="experience_stats", field="years_of_experience")
            .avg(name="avg_experience", field="years_of_experience")
            .histogram(name="experience_distribution", field="years_of_experience", interval=1.0)
            .build()
        )
    
    @staticmethod
    def skill_popularity() -> List[Aggregation]:
        """Skill popularity ranking."""
        builder = AggregationBuilder()
        return (
            builder
            .terms(name="skill_ranking", field="name", size=50, order="count")
            .build()
        )
    
    @staticmethod
    def application_status_breakdown() -> List[Aggregation]:
        """Application status breakdown."""
        builder = AggregationBuilder()
        return (
            builder
            .terms(name="by_status", field="status", size=10)
            .terms(name="by_stage", field="stage", size=10)
            .build()
        )
    
    @staticmethod
    def company_size_distribution() -> List[Aggregation]:
        """Company size distribution."""
        builder = AggregationBuilder()
        return (
            builder
            .terms(name="by_size", field="company_size", size=10)
            .build()
        )
