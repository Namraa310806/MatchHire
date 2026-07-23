"""
Recommendation Signals.

This module provides recommendation-specific signals that extend the
existing ranking signals. These signals are designed for recommendation
scenarios and can be used in the Ranking Pipeline.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import math
from datetime import datetime, timedelta

from apps.search.ranking.signals import BaseSignal, SignalConfig


class RecommendationSignalType(Enum):
    """Types of recommendation signals."""
    SKILL_SIMILARITY = "skill_similarity"
    CAREER_PROGRESSION = "career_progression"
    TECHNOLOGY_SIMILARITY = "technology_similarity"
    INDUSTRY_SIMILARITY = "industry_similarity"
    LOCATION_SIMILARITY = "location_similarity"
    BEHAVIOR_HOOKS = "behavior_hooks"
    RECOMMENDATION_DIVERSITY = "recommendation_diversity"
    NOVELTY = "novelty"
    COVERAGE = "coverage"


class SkillSimilaritySignal(BaseSignal):
    """
    Skill similarity signal for recommendations.
    
    Scores items based on skill similarity to the target entity.
    Uses Jaccard similarity and weighted skill matching.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.SKILL_SIMILARITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate skill similarity score.
        
        Args:
            document: Document to score
            context: Recommendation context with target skills
            
        Returns:
            Skill similarity score
        """
        target_skills = set(context.get("target_skills", []))
        doc_skills = set(document.get("skills", []))
        
        if not target_skills:
            return 0.5
        
        # Calculate Jaccard similarity
        intersection = target_skills & doc_skills
        union = target_skills | doc_skills
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Bonus for exact match
        if target_skills == doc_skills:
            jaccard += 0.2
        
        # Weight important skills higher
        important_skills = set(context.get("important_skills", []))
        if important_skills:
            important_intersection = important_skills & doc_skills
            if important_intersection:
                jaccard += 0.3 * (len(important_intersection) / len(important_skills))
        
        return min(jaccard, 1.0)


class CareerProgressionSignal(BaseSignal):
    """
    Career progression signal for recommendations.
    
    Scores items based on career progression potential, such as
    seniority level, career path alignment, etc.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.CAREER_PROGRESSION
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate career progression score.
        
        Args:
            document: Document to score
            context: Recommendation context with career info
            
        Returns:
            Career progression score
        """
        current_level = context.get("current_level", "mid")
        target_level = document.get("seniority_level", "mid")
        
        # Career level hierarchy
        level_hierarchy = {
            "entry": 0,
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "manager": 5,
            "director": 6,
            "executive": 7,
        }
        
        current_idx = level_hierarchy.get(current_level.lower(), 2)
        target_idx = level_hierarchy.get(target_level.lower(), 2)
        
        # Score based on progression (next level or higher)
        if target_idx > current_idx:
            # Progressive step
            diff = target_idx - current_idx
            if diff == 1:
                return 1.0  # Perfect next step
            elif diff == 2:
                return 0.8  # Two steps up
            else:
                return 0.5  # Larger jump
        elif target_idx == current_idx:
            return 0.6  # Same level
        else:
            # Lower level
            return 0.3


class TechnologySimilaritySignal(BaseSignal):
    """
    Technology similarity signal for recommendations.
    
    Scores items based on technology stack similarity.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.TECHNOLOGY_SIMILARITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate technology similarity score.
        
        Args:
            document: Document to score
            context: Recommendation context with target technologies
            
        Returns:
            Technology similarity score
        """
        target_tech = set(context.get("target_technologies", []))
        doc_tech = set(document.get("technologies", []))
        
        if not target_tech:
            return 0.5
        
        # Calculate overlap
        intersection = target_tech & doc_tech
        
        if not intersection:
            return 0.0
        
        # Score based on overlap percentage
        overlap_ratio = len(intersection) / len(target_tech)
        
        # Bonus for exact match
        if target_tech == doc_tech:
            overlap_ratio += 0.2
        
        return min(overlap_ratio, 1.0)


class IndustrySimilaritySignal(BaseSignal):
    """
    Industry similarity signal for recommendations.
    
    Scores items based on industry alignment.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.INDUSTRY_SIMILARITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate industry similarity score.
        
        Args:
            document: Document to score
            context: Recommendation context with target industry
            
        Returns:
            Industry similarity score
        """
        target_industry = context.get("target_industry", "").lower()
        doc_industry = document.get("industry", "").lower()
        
        if not target_industry:
            return 0.5
        
        # Exact match
        if target_industry == doc_industry:
            return 1.0
        
        # Partial match (same sector)
        target_sector = context.get("target_sector", "")
        doc_sector = document.get("sector", "")
        
        if target_sector and doc_sector and target_sector == doc_sector:
            return 0.7
        
        return 0.0


class LocationSimilaritySignal(BaseSignal):
    """
    Location similarity signal for recommendations.
    
    Scores items based on geographic proximity and location preferences.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.LOCATION_SIMILARITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate location similarity score.
        
        Args:
            document: Document to score
            context: Recommendation context with location info
            
        Returns:
            Location similarity score
        """
        target_location = context.get("target_location", "").lower()
        doc_location = document.get("location", "").lower()
        
        if not target_location or not doc_location:
            return 0.5
        
        # Exact match
        if target_location == doc_location:
            return 1.0
        
        # Same city
        target_city = target_location.split(",")[0].strip()
        doc_city = doc_location.split(",")[0].strip()
        
        if target_city == doc_city:
            return 0.8
        
        # Same country/region
        target_parts = target_location.split(",")
        doc_parts = doc_location.split(",")
        
        if len(target_parts) > 1 and len(doc_parts) > 1:
            if target_parts[-1].strip() == doc_parts[-1].strip():
                return 0.5
        
        return 0.0


class BehaviorHooksSignal(BaseSignal):
    """
    Behavior hooks signal for recommendations.
    
    Scores items based on user behavior patterns like click history,
    application history, saved items, etc.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.BEHAVIOR_HOOKS
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate behavior hooks score.
        
        Args:
            document: Document to score
            context: Recommendation context with behavior data
            
        Returns:
            Behavior hooks score
        """
        score = 0.0
        
        # Check if user has viewed this item
        viewed_items = set(context.get("viewed_items", []))
        if document.get("id") in viewed_items:
            score += 0.3
        
        # Check if user has similar items in history
        similar_items = set(context.get("similar_items", []))
        if document.get("id") in similar_items:
            score += 0.5
        
        # Check if user has interacted with similar companies
        similar_companies = set(context.get("similar_companies", []))
        doc_company = document.get("company_name") or document.get("company", "")
        if doc_company in similar_companies:
            score += 0.4
        
        # Check if user has interacted with similar skills
        similar_skills = set(context.get("similar_skills", []))
        doc_skills = set(document.get("skills", []))
        if doc_skills & similar_skills:
            score += 0.3
        
        return min(score, 1.0)


class RecommendationDiversitySignal(BaseSignal):
    """
    Recommendation diversity signal.
    
    Scores items based on how much they add diversity to the
    recommendation set (e.g., different companies, skills, etc.).
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.RECOMMENDATION_DIVERSITY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate recommendation diversity score.
        
        Args:
            document: Document to score
            context: Recommendation context with current recommendations
            
        Returns:
            Diversity score
        """
        current_recommendations = context.get("current_recommendations", [])
        
        if not current_recommendations:
            return 0.5
        
        score = 0.0
        
        # Check company diversity
        doc_company = document.get("company_name") or document.get("company", "")
        companies = [r.get("company_name") or r.get("company", "") for r in current_recommendations]
        if doc_company not in companies:
            score += 0.3
        
        # Check skill diversity
        doc_skills = set(document.get("skills", []))
        all_skills = set()
        for rec in current_recommendations:
            all_skills.update(rec.get("skills", []))
        
        new_skills = doc_skills - all_skills
        if new_skills:
            score += 0.3 * (len(new_skills) / max(len(doc_skills), 1))
        
        # Check location diversity
        doc_location = document.get("location", "")
        locations = [r.get("location", "") for r in current_recommendations]
        if doc_location not in locations:
            score += 0.2
        
        # Check industry diversity
        doc_industry = document.get("industry", "")
        industries = [r.get("industry", "") for r in current_recommendations]
        if doc_industry not in industries:
            score += 0.2
        
        return min(score, 1.0)


class NoveltySignal(BaseSignal):
    """
    Novelty signal for recommendations.
    
    Scores items based on how novel they are to the user,
    i.e., items the user hasn't seen before.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.NOVELTY
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate novelty score.
        
        Args:
            document: Document to score
            context: Recommendation context with user history
            
        Returns:
            Novelty score
        """
        # Check if user has seen this item
        seen_items = set(context.get("seen_items", []))
        if document.get("id") in seen_items:
            return 0.0  # Not novel if already seen
        
        # Check if user has seen similar items
        similar_items = set(context.get("similar_items", []))
        if document.get("id") in similar_items:
            return 0.3  # Low novelty if similar items seen
        
        # Check if user has seen items from same company
        seen_companies = set(context.get("seen_companies", []))
        doc_company = document.get("company_name") or document.get("company", "")
        if doc_company in seen_companies:
            return 0.5  # Medium novelty
        
        # High novelty if completely new
        return 1.0


class CoverageSignal(BaseSignal):
    """
    Coverage signal for recommendations.
    
    Scores items based on how well they cover the user's
    preferences and requirements.
    """
    
    @property
    def signal_type(self) -> RecommendationSignalType:
        return RecommendationSignalType.COVERAGE
    
    def score(self, document: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculate coverage score.
        
        Args:
            document: Document to score
            context: Recommendation context with user preferences
            
        Returns:
            Coverage score
        """
        score = 0.0
        
        # Check skill coverage
        required_skills = set(context.get("required_skills", []))
        doc_skills = set(document.get("skills", []))
        if required_skills:
            skill_coverage = len(required_skills & doc_skills) / len(required_skills)
            score += 0.4 * skill_coverage
        
        # Check location coverage
        preferred_locations = set(context.get("preferred_locations", []))
        doc_location = document.get("location", "")
        if preferred_locations and doc_location:
            if any(loc in doc_location for loc in preferred_locations):
                score += 0.3
        
        # Check employment type coverage
        preferred_types = set(context.get("preferred_employment_types", []))
        doc_type = document.get("employment_type", "")
        if preferred_types and doc_type in preferred_types:
            score += 0.2
        
        # Check salary coverage
        salary_range = context.get("salary_range", {})
        if salary_range:
            min_salary = salary_range.get("min", 0)
            max_salary = salary_range.get("max", float('inf'))
            doc_salary = document.get("salary", 0) or 0
            if min_salary <= doc_salary <= max_salary:
                score += 0.1
        
        return min(score, 1.0)
