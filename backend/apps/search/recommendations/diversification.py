"""
Diversification Engine.

This module provides diversification algorithms to ensure recommendation
sets are diverse across multiple dimensions (skills, companies, locations,
experience, salary, industry, etc.).
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import math


class DiversificationType(Enum):
    """Types of diversification."""
    SKILL = "skill"
    COMPANY = "company"
    LOCATION = "location"
    EXPERIENCE = "experience"
    SALARY = "salary"
    INDUSTRY = "industry"
    DEDUPLICATION = "deduplication"


@dataclass
class DiversificationConfig:
    """Configuration for diversification."""
    
    enable_skill_diversification: bool = True
    enable_company_diversification: bool = True
    enable_location_diversification: bool = True
    enable_experience_diversification: bool = True
    enable_salary_diversification: bool = True
    enable_industry_diversification: bool = True
    enable_deduplication: bool = True
    
    skill_diversity_threshold: float = 0.3
    company_diversity_threshold: int = 2
    location_diversity_threshold: int = 2
    experience_diversity_threshold: float = 0.5
    salary_diversity_threshold: float = 0.2
    industry_diversity_threshold: int = 2
    
    max_same_company: int = 3
    max_same_location: int = 3
    max_same_industry: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_skill_diversification": self.enable_skill_diversification,
            "enable_company_diversification": self.enable_company_diversification,
            "enable_location_diversification": self.enable_location_diversification,
            "enable_experience_diversification": self.enable_experience_diversification,
            "enable_salary_diversification": self.enable_salary_diversification,
            "enable_industry_diversification": self.enable_industry_diversification,
            "enable_deduplication": self.enable_deduplication,
            "skill_diversity_threshold": self.skill_diversity_threshold,
            "company_diversity_threshold": self.company_diversity_threshold,
            "location_diversity_threshold": self.location_diversity_threshold,
            "experience_diversity_threshold": self.experience_diversity_threshold,
            "salary_diversity_threshold": self.salary_diversity_threshold,
            "industry_diversity_threshold": self.industry_diversity_threshold,
            "max_same_company": self.max_same_company,
            "max_same_location": self.max_same_location,
            "max_same_industry": self.max_same_industry,
        }


class Diversifier(ABC):
    """
    Abstract base class for diversifiers.
    
    Each diversifier implements diversification for a specific dimension.
    """
    
    def __init__(self, config: Optional[DiversificationConfig] = None):
        """
        Initialize the diversifier.
        
        Args:
            config: Diversification configuration
        """
        self._config = config or DiversificationConfig()
    
    @property
    def diversification_type(self) -> DiversificationType:
        """Get the diversification type."""
        return DiversificationType.SKILL
    
    @abstractmethod
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify candidates along this dimension.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        pass


class SkillDiversifier(Diversifier):
    """
    Skill diversifier.
    
    Ensures recommendations have diverse skill sets.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.SKILL
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by skills.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_skill_diversification:
            return candidates
        
        threshold = self._config.skill_diversity_threshold
        diversified = []
        seen_skills: Set[str] = set()
        
        for candidate in candidates:
            candidate_skills = set(candidate.get("skills", []))
            
            # Calculate overlap with already seen skills
            if seen_skills:
                overlap = len(candidate_skills & seen_skills) / max(len(candidate_skills), 1)
                if overlap > threshold:
                    continue  # Skip if too similar
            
            diversified.append(candidate)
            seen_skills.update(candidate_skills)
        
        return diversified


class CompanyDiversifier(Diversifier):
    """
    Company diversifier.
    
    Ensures recommendations don't have too many from the same company.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.COMPANY
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by company.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_company_diversification:
            return candidates
        
        max_same = self._config.max_same_company
        company_counts: Dict[str, int] = {}
        diversified = []
        
        for candidate in candidates:
            company = candidate.get("company_name") or candidate.get("company", "")
            
            if company_counts.get(company, 0) >= max_same:
                continue
            
            diversified.append(candidate)
            company_counts[company] = company_counts.get(company, 0) + 1
        
        return diversified


class LocationDiversifier(Diversifier):
    """
    Location diversifier.
    
    Ensures recommendations don't have too many from the same location.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.LOCATION
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by location.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_location_diversification:
            return candidates
        
        max_same = self._config.max_same_location
        location_counts: Dict[str, int] = {}
        diversified = []
        
        for candidate in candidates:
            location = candidate.get("location", "")
            
            if location_counts.get(location, 0) >= max_same:
                continue
            
            diversified.append(candidate)
            location_counts[location] = location_counts.get(location, 0) + 1
        
        return diversified


class ExperienceDiversifier(Diversifier):
    """
    Experience diversifier.
    
    Ensures recommendations have diverse experience levels.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.EXPERIENCE
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by experience.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_experience_diversification:
            return candidates
        
        threshold = self._config.experience_diversity_threshold
        diversified = []
        seen_experience_levels: Set[str] = set()
        
        for candidate in candidates:
            experience_years = candidate.get("experience_years", 0) or 0
            
            # Categorize experience level
            if experience_years < 2:
                level = "junior"
            elif experience_years < 5:
                level = "mid"
            elif experience_years < 10:
                level = "senior"
            else:
                level = "lead"
            
            # Check if we already have this level
            if level in seen_experience_levels:
                # Allow some duplicates but limit them
                count = sum(1 for c in diversified if c.get("experience_years", 0) or 0 < 2 if level == "junior" else 5 if level == "mid" else 10)
                if count >= 2:
                    continue
            
            diversified.append(candidate)
            seen_experience_levels.add(level)
        
        return diversified


class SalaryDiversifier(Diversifier):
    """
    Salary diversifier.
    
    Ensures recommendations have diverse salary ranges.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.SALARY
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by salary.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_salary_diversification:
            return candidates
        
        threshold = self._config.salary_diversity_threshold
        diversified = []
        seen_salary_ranges: List[tuple] = []
        
        for candidate in candidates:
            salary = candidate.get("salary", 0) or 0
            
            if salary == 0:
                diversified.append(candidate)
                continue
            
            # Check if salary is too close to existing salaries
            too_close = False
            for min_sal, max_sal in seen_salary_ranges:
                if min_sal * (1 - threshold) <= salary <= max_sal * (1 + threshold):
                    too_close = True
                    break
            
            if too_close and len(seen_salary_ranges) >= 3:
                continue
            
            diversified.append(candidate)
            seen_salary_ranges.append((salary * 0.9, salary * 1.1))
        
        return diversified


class IndustryDiversifier(Diversifier):
    """
    Industry diversifier.
    
    Ensures recommendations don't have too many from the same industry.
    """
    
    @property
    def diversification_type(self) -> DiversificationType:
        return DiversificationType.INDUSTRY
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify by industry.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        if not self._config.enable_industry_diversification:
            return candidates
        
        max_same = self._config.max_same_industry
        industry_counts: Dict[str, int] = {}
        diversified = []
        
        for candidate in candidates:
            industry = candidate.get("industry", "")
            
            if industry_counts.get(industry, 0) >= max_same:
                continue
            
            diversified.append(candidate)
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        return diversified


class DeduplicationEngine:
    """
    Deduplication engine for removing duplicate recommendations.
    
    Removes duplicates based on various criteria like ID, content similarity, etc.
    """
    
    def __init__(self, config: Optional[DiversificationConfig] = None):
        """
        Initialize the deduplication engine.
        
        Args:
            config: Diversification configuration
        """
        self._config = config or DiversificationConfig()
    
    def deduplicate(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate candidates.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Deduplicated candidates
        """
        if not self._config.enable_deduplication:
            return candidates
        
        # Deduplicate by ID
        seen_ids: Set[str] = set()
        deduplicated = []
        
        for candidate in candidates:
            candidate_id = candidate.get("id", "")
            
            if candidate_id in seen_ids:
                continue
            
            deduplicated.append(candidate)
            seen_ids.add(candidate_id)
        
        return deduplicated


class DiversificationEngine:
    """
    Main diversification engine.
    
    Orchestrates multiple diversifiers to ensure diverse recommendations.
    """
    
    def __init__(self, config: Optional[DiversificationConfig] = None):
        """
        Initialize the diversification engine.
        
        Args:
            config: Diversification configuration
        """
        self._config = config or DiversificationConfig()
        
        # Initialize diversifiers
        self._diversifiers: List[Diversifier] = [
            SkillDiversifier(self._config),
            CompanyDiversifier(self._config),
            LocationDiversifier(self._config),
            ExperienceDiversifier(self._config),
            SalaryDiversifier(self._config),
            IndustryDiversifier(self._config),
        ]
        
        self._deduplication_engine = DeduplicationEngine(self._config)
    
    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Diversify candidates using all enabled diversifiers.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Diversified candidates
        """
        # First, deduplicate
        diversified = self._deduplication_engine.deduplicate(candidates, context)
        
        # Apply each diversifier
        for diversifier in self._diversifiers:
            diversified = diversifier.diversify(diversified, context)
        
        return diversified
    
    def add_diversifier(self, diversifier: Diversifier) -> None:
        """
        Add a custom diversifier.
        
        Args:
            diversifier: Diversifier to add
        """
        self._diversifiers.append(diversifier)
    
    def remove_diversifier(self, diversifier_type: DiversificationType) -> None:
        """
        Remove a diversifier by type.
        
        Args:
            diversifier_type: Type of diversifier to remove
        """
        self._diversifiers = [
            d for d in self._diversifiers
            if d.diversification_type != diversifier_type
        ]
    
    def get_config(self) -> DiversificationConfig:
        """
        Get the diversification configuration.
        
        Returns:
            Diversification configuration
        """
        return self._config
