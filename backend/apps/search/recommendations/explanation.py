"""
Recommendation Explanation.

This module provides explanation capabilities for recommendations,
explaining why items were recommended to users.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class ExplanationType(Enum):
    """Types of explanations."""
    WHY_RECOMMENDED = "why_recommended"
    SHARED_SKILLS = "shared_skills"
    MATCHING_EXPERIENCE = "matching_experience"
    BUSINESS_RULES = "business_rules"
    RANKING_SIGNALS = "ranking_signals"
    CONFIDENCE_SCORE = "confidence_score"
    RECOMMENDATION_SOURCE = "recommendation_source"


@dataclass
class RecommendationExplanation:
    """
    Explanation for a recommendation.
    
    Contains detailed information about why an item was recommended.
    """
    
    item_id: str
    explanation_type: ExplanationType
    primary_reason: str
    secondary_reasons: List[str] = field(default_factory=list)
    confidence: float = 0.0
    signals: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "item_id": self.item_id,
            "explanation_type": self.explanation_type.value,
            "primary_reason": self.primary_reason,
            "secondary_reasons": self.secondary_reasons,
            "confidence": self.confidence,
            "signals": self.signals,
            "metadata": self.metadata,
        }


class ExplanationBuilder:
    """
    Builder for recommendation explanations.
    
    Generates explanations for recommendations based on various factors.
    """
    
    def __init__(self):
        """Initialize the explanation builder."""
        self._explanation_generators = {
            ExplanationType.WHY_RECOMMENDED: WhyRecommendedExplanation(),
            ExplanationType.SHARED_SKILLS: SharedSkillsExplanation(),
            ExplanationType.MATCHING_EXPERIENCE: MatchingExperienceExplanation(),
            ExplanationType.BUSINESS_RULES: BusinessRulesExplanation(),
            ExplanationType.RANKING_SIGNALS: RankingSignalsExplanation(),
            ExplanationType.CONFIDENCE_SCORE: ConfidenceScoreExplanation(),
            ExplanationType.RECOMMENDATION_SOURCE: RecommendationSourceExplanation(),
        }
    
    def build_explanation(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build explanation for a recommendation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Explanation dictionary
        """
        explanations = {}
        
        # Generate all explanation types
        for exp_type, generator in self._explanation_generators.items():
            explanation = generator.generate(candidate, context)
            explanations[exp_type.value] = explanation.to_dict()
        
        return explanations
    
    def add_explanation_generator(
        self,
        exp_type: ExplanationType,
        generator,
    ) -> None:
        """
        Add a custom explanation generator.
        
        Args:
            exp_type: Explanation type
            generator: Generator instance
        """
        self._explanation_generators[exp_type] = generator


class ExplanationGenerator(ABC):
    """
    Abstract base class for explanation generators.
    
    Each generator implements a specific type of explanation.
    """
    
    @abstractmethod
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate explanation for a recommendation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        pass


class WhyRecommendedExplanation(ExplanationGenerator):
    """
    Why recommended explanation.
    
    Explains the primary reason why an item was recommended.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate why recommended explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        
        # Determine primary reason based on signals
        signals = candidate.get("_ranking_signals", {})
        primary_signal = max(signals.items(), key=lambda x: x[1]) if signals else ("unknown", 0)
        
        # Map signal to human-readable reason
        reason_map = {
            "skill_overlap": "Strong skill match with your requirements",
            "experience_overlap": "Experience level matches your needs",
            "location_proximity": "Located in your preferred area",
            "salary_compatibility": "Salary range matches your expectations",
            "profile_completeness": "Complete and verified profile",
            "candidate_activity": "Recently active on the platform",
            "job_freshness": "Recently posted job",
            "popularity": "Popular among other candidates",
        }
        
        primary_reason = reason_map.get(primary_signal[0], "Good match for your requirements")
        
        # Generate secondary reasons
        secondary_reasons = []
        for signal, score in signals.items():
            if signal != primary_signal[0] and score > 0.5:
                secondary_reasons.append(reason_map.get(signal, f"High {signal} score"))
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.WHY_RECOMMENDED,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons[:3],
            confidence=primary_signal[1],
            signals=signals,
        )


class SharedSkillsExplanation(ExplanationGenerator):
    """
    Shared skills explanation.
    
    Explains the shared skills between the candidate and requirements.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate shared skills explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        candidate_skills = set(candidate.get("skills", []))
        required_skills = set(context.get("required_skills", []))
        
        # Find shared skills
        shared_skills = candidate_skills & required_skills
        missing_skills = required_skills - candidate_skills
        
        # Build primary reason
        if shared_skills:
            primary_reason = f"Matches {len(shared_skills)} of {len(required_skills)} required skills"
        else:
            primary_reason = "No direct skill match"
        
        # Build secondary reasons
        secondary_reasons = []
        if shared_skills:
            secondary_reasons.append(f"Shared skills: {', '.join(list(shared_skills)[:5])}")
        if missing_skills:
            secondary_reasons.append(f"Missing skills: {', '.join(list(missing_skills)[:5])}")
        
        # Calculate confidence
        confidence = len(shared_skills) / len(required_skills) if required_skills else 0
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.SHARED_SKILLS,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=confidence,
            metadata={
                "shared_skills": list(shared_skills),
                "missing_skills": list(missing_skills),
                "match_percentage": confidence,
            },
        )


class MatchingExperienceExplanation(ExplanationGenerator):
    """
    Matching experience explanation.
    
    Explains how the candidate's experience matches requirements.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate matching experience explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        candidate_experience = candidate.get("experience_years", 0) or 0
        required_experience = context.get("required_experience", 0)
        
        # Build primary reason
        if required_experience == 0:
            primary_reason = "Experience level suitable for the role"
        elif candidate_experience >= required_experience:
            primary_reason = f"Exceeds experience requirement by {candidate_experience - required_experience} years"
        else:
            primary_reason = f"Experience level is {required_experience - candidate_experience} years below requirement"
        
        # Build secondary reasons
        secondary_reasons = []
        if candidate_experience >= 10:
            secondary_reasons.append("Senior-level experience")
        elif candidate_experience >= 5:
            secondary_reasons.append("Mid-level experience")
        elif candidate_experience >= 2:
            secondary_reasons.append("Junior-level experience")
        else:
            secondary_reasons.append("Entry-level experience")
        
        # Calculate confidence
        if required_experience > 0:
            confidence = min(candidate_experience / required_experience, 1.0)
        else:
            confidence = 1.0
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.MATCHING_EXPERIENCE,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=confidence,
            metadata={
                "candidate_experience": candidate_experience,
                "required_experience": required_experience,
            },
        )


class BusinessRulesExplanation(ExplanationGenerator):
    """
    Business rules explanation.
    
    Explains how business rules affected the recommendation.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate business rules explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        business_rules = context.get("business_rules", {})
        
        # Check for business rule effects
        pinned_ids = business_rules.get("pinned_ids", [])
        promoted_ids = business_rules.get("promoted_ids", [])
        priority_companies = business_rules.get("priority_companies", [])
        
        primary_reason = "Standard recommendation"
        secondary_reasons = []
        
        if item_id in pinned_ids:
            primary_reason = "Pinned by your organization"
        
        if item_id in promoted_ids:
            secondary_reasons.append("Promoted position")
        
        company = candidate.get("company_name") or candidate.get("company", "")
        if company in priority_companies:
            secondary_reasons.append(f"Priority company: {company}")
        
        boosts = candidate.get("_boosts", [])
        if boosts:
            secondary_reasons.extend([f"Applied boost: {boost}" for boost in boosts])
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.BUSINESS_RULES,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=0.8 if primary_reason != "Standard recommendation" else 0.5,
            metadata={
                "is_pinned": item_id in pinned_ids,
                "is_promoted": item_id in promoted_ids,
                "is_priority_company": company in priority_companies,
            },
        )


class RankingSignalsExplanation(ExplanationGenerator):
    """
    Ranking signals explanation.
    
    Explains the contribution of each ranking signal.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate ranking signals explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        signals = candidate.get("_ranking_signals", {})
        
        # Sort signals by contribution
        sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        
        # Build primary reason
        if sorted_signals:
            top_signal, top_score = sorted_signals[0]
            primary_reason = f"Top ranking factor: {top_signal} (score: {top_score:.2f})"
        else:
            primary_reason = "No ranking signals available"
        
        # Build secondary reasons
        secondary_reasons = [
            f"{signal}: {score:.2f}" for signal, score in sorted_signals[1:4]
        ]
        
        # Calculate confidence based on top signal
        confidence = sorted_signals[0][1] if sorted_signals else 0
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.RANKING_SIGNALS,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=confidence,
            signals=signals,
            metadata={
                "signal_count": len(signals),
                "top_signal": sorted_signals[0][0] if sorted_signals else None,
            },
        )


class ConfidenceScoreExplanation(ExplanationGenerator):
    """
    Confidence score explanation.
    
    Explains the confidence score for the recommendation.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate confidence score explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        score = candidate.get("_ranking_score", 0.0)
        
        # Determine confidence level
        if score >= 0.8:
            confidence_level = "Very High"
            primary_reason = "Excellent match for your requirements"
        elif score >= 0.6:
            confidence_level = "High"
            primary_reason = "Strong match for your requirements"
        elif score >= 0.4:
            confidence_level = "Medium"
            primary_reason = "Moderate match for your requirements"
        else:
            confidence_level = "Low"
            primary_reason = "Partial match for your requirements"
        
        # Build secondary reasons
        secondary_reasons = [
            f"Confidence level: {confidence_level}",
            f"Match score: {score:.2f}",
        ]
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.CONFIDENCE_SCORE,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=score,
            metadata={
                "confidence_level": confidence_level,
                "score": score,
            },
        )


class RecommendationSourceExplanation(ExplanationGenerator):
    """
    Recommendation source explanation.
    
    Explains the source of the recommendation.
    """
    
    def generate(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RecommendationExplanation:
        """
        Generate recommendation source explanation.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            Recommendation explanation
        """
        item_id = candidate.get("id", "")
        source = candidate.get("_source", "query_engine")
        
        # Map source to human-readable description
        source_map = {
            "query_engine": "Found through search",
            "similarity": "Similar to your preferences",
            "collaborative_filtering": "Popular with similar users",
            "content_based": "Matches your profile",
            "rule_based": "Recommended based on rules",
            "popularity": "Trending recommendation",
            "freshness": "Recently added",
            "hybrid": "Combined recommendation",
        }
        
        primary_reason = source_map.get(source, "Standard recommendation")
        
        # Get sources if hybrid
        sources = candidate.get("_sources", [])
        if sources:
            secondary_reasons = [f"Source: {s}" for s in sources]
        else:
            secondary_reasons = [f"Source: {source}"]
        
        return RecommendationExplanation(
            item_id=item_id,
            explanation_type=ExplanationType.RECOMMENDATION_SOURCE,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            confidence=0.7,
            metadata={
                "source": source,
                "sources": sources,
            },
        )
