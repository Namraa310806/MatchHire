"""
Score Explanation System.

This module provides explainable ranking with detailed score breakdowns.
Every search result can expose how its ranking score was calculated,
including individual signal contributions, boosts applied, and business rules.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalContribution:
    """
    Contribution of a single signal to the final score.
    """
    
    signal_name: str
    signal_type: str
    raw_score: float
    normalized_score: float
    weight: float
    contribution: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "signal_name": self.signal_name,
            "signal_type": self.signal_type,
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "weight": self.weight,
            "contribution": self.contribution,
            "metadata": self.metadata,
        }


@dataclass
class BoostExplanation:
    """
    Explanation of a boost applied to a document.
    """
    
    boost_type: str
    boost_amount: float
    reason: str
    source: str
    applied_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "boost_type": self.boost_type,
            "boost_amount": self.boost_amount,
            "reason": self.reason,
            "source": self.source,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "metadata": self.metadata,
        }


@dataclass
class BusinessRuleExplanation:
    """
    Explanation of a business rule applied to a document.
    """
    
    rule_name: str
    rule_type: str
    action: str
    priority: int
    effect: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "action": self.action,
            "priority": self.priority,
            "effect": self.effect,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class RankingBreakdown:
    """
    Complete breakdown of how a ranking score was calculated.
    """
    
    document_id: str
    final_score: float
    original_score: float
    signal_contributions: List[SignalContribution] = field(default_factory=list)
    boosts: List[BoostExplanation] = field(default_factory=list)
    business_rules: List[BusinessRuleExplanation] = field(default_factory=list)
    ranking_position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "final_score": self.final_score,
            "original_score": self.original_score,
            "signal_contributions": [s.to_dict() for s in self.signal_contributions],
            "boosts": [b.to_dict() for b in self.boosts],
            "business_rules": [r.to_dict() for r in self.business_rules],
            "ranking_position": self.ranking_position,
            "metadata": self.metadata,
        }
    
    def get_total_signal_contribution(self) -> float:
        """Get total contribution from all signals."""
        return sum(s.contribution for s in self.signal_contributions)
    
    def get_total_boost(self) -> float:
        """Get total boost amount."""
        return sum(b.boost_amount for b in self.boosts)
    
    def get_total_business_rule_effect(self) -> float:
        """Get total effect from business rules."""
        return sum(r.effect for r in self.business_rules)
    
    def get_top_signals(self, n: int = 3) -> List[SignalContribution]:
        """Get top n contributing signals."""
        sorted_signals = sorted(
            self.signal_contributions,
            key=lambda x: abs(x.contribution),
            reverse=True,
        )
        return sorted_signals[:n]


class ScoreExplanation:
    """
    Main score explanation class.
    
    Provides a complete explanation of how ranking scores were calculated
    for search results, including signal contributions, boosts, and business rules.
    """
    
    def __init__(self):
        """Initialize the score explanation system."""
        self._breakdowns: Dict[str, RankingBreakdown] = {}
        self._explanation_enabled: bool = True
    
    def enable(self) -> None:
        """Enable score explanation."""
        self._explanation_enabled = True
    
    def disable(self) -> None:
        """Disable score explanation."""
        self._explanation_enabled = False
    
    def is_enabled(self) -> bool:
        """Check if explanation is enabled."""
        return self._explanation_enabled
    
    def create_breakdown(
        self,
        document: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RankingBreakdown:
        """
        Create a ranking breakdown for a document.
        
        Args:
            document: Document to explain
            context: Search context
            
        Returns:
            Ranking breakdown
        """
        if not self._explanation_enabled:
            return RankingBreakdown(
                document_id=document.get("id", ""),
                final_score=document.get("_ranking_score", 0.0),
                original_score=document.get("_score", 0.0),
            )
        
        doc_id = document.get("id", "")
        final_score = document.get("_ranking_score", 0.0)
        original_score = document.get("_score", 0.0)
        
        breakdown = RankingBreakdown(
            document_id=doc_id,
            final_score=final_score,
            original_score=original_score,
        )
        
        # Add signal contributions
        ranking_signals = document.get("_ranking_signals", {})
        for signal_name, signal_score in ranking_signals.items():
            contribution = SignalContribution(
                signal_name=signal_name,
                signal_type="unknown",  # Would be filled from signal registry
                raw_score=signal_score,
                normalized_score=signal_score,  # Simplified
                weight=1.0,  # Would be filled from pipeline config
                contribution=signal_score,
            )
            breakdown.signal_contributions.append(contribution)
        
        # Add boosts
        ranking_boost = document.get("_ranking_boost", 0.0)
        if ranking_boost != 0:
            boost = BoostExplanation(
                boost_type="ranking_boost",
                boost_amount=ranking_boost,
                reason="Applied during ranking",
                source="ranking_pipeline",
            )
            breakdown.boosts.append(boost)
        
        # Add business rules
        applied_rules = document.get("_applied_rules", [])
        for rule_name in applied_rules:
            rule_explanation = BusinessRuleExplanation(
                rule_name=rule_name,
                rule_type="unknown",
                action="boost",
                priority=1,
                effect=document.get("_ranking_boost", 0.0),
                reason=f"Business rule {rule_name} was applied",
            )
            breakdown.business_rules.append(rule_explanation)
        
        # Add metadata
        if document.get("_pinned"):
            breakdown.metadata["pinned"] = True
            breakdown.metadata["pin_position"] = document.get("_pin_position")
        
        if document.get("_hidden"):
            breakdown.metadata["hidden"] = True
            breakdown.metadata["hidden_reason"] = document.get("_hidden_reason")
        
        if document.get("_promoted"):
            breakdown.metadata["promoted"] = True
            breakdown.metadata["promotion_reason"] = document.get("_promotion_reason")
        
        if document.get("_sponsored"):
            breakdown.metadata["sponsored"] = True
        
        if document.get("_priority_company"):
            breakdown.metadata["priority_company"] = True
        
        self._breakdowns[doc_id] = breakdown
        
        return breakdown
    
    def get_breakdown(self, document_id: str) -> Optional[RankingBreakdown]:
        """
        Get breakdown for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Ranking breakdown or None if not found
        """
        return self._breakdowns.get(document_id)
    
    def get_all_breakdowns(self) -> Dict[str, RankingBreakdown]:
        """
        Get all breakdowns.
        
        Returns:
            Dictionary of document ID to breakdown
        """
        return self._breakdowns.copy()
    
    def clear_breakdowns(self) -> None:
        """Clear all breakdowns."""
        self._breakdowns.clear()
    
    def explain_results(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, RankingBreakdown]:
        """
        Create breakdowns for all results.
        
        Args:
            results: Search results
            context: Search context
            
        Returns:
            Dictionary of document ID to breakdown
        """
        for result in results:
            self.create_breakdown(result, context)
        
        return self._breakdowns.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all breakdowns to dictionary representation."""
        return {
            "breakdowns": {
                doc_id: breakdown.to_dict()
                for doc_id, breakdown in self._breakdowns.items()
            },
            "explanation_enabled": self._explanation_enabled,
        }


class ExplanationBuilder:
    """
    Builder for creating detailed explanations.
    
    Provides methods to build explanations incrementally
    and format them for different use cases (API, UI, logs).
    """
    
    def __init__(self):
        """Initialize the explanation builder."""
        self._explanation = ScoreExplanation()
    
    def build_for_document(
        self,
        document: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RankingBreakdown:
        """
        Build explanation for a single document.
        
        Args:
            document: Document to explain
            context: Search context
            
        Returns:
            Ranking breakdown
        """
        return self._explanation.create_breakdown(document, context)
    
    def build_for_results(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, RankingBreakdown]:
        """
        Build explanations for all results.
        
        Args:
            results: Search results
            context: Search context
            
        Returns:
            Dictionary of document ID to breakdown
        """
        return self._explanation.explain_results(results, context)
    
    def format_for_api(self, breakdown: RankingBreakdown) -> Dict[str, Any]:
        """
        Format breakdown for API response.
        
        Args:
            breakdown: Ranking breakdown
            
        Returns:
            API-formatted explanation
        """
        return {
            "document_id": breakdown.document_id,
            "score": {
                "final": breakdown.final_score,
                "original": breakdown.original_score,
                "delta": breakdown.final_score - breakdown.original_score,
            },
            "signals": [
                {
                    "name": s.signal_name,
                    "type": s.signal_type,
                    "contribution": s.contribution,
                    "weight": s.weight,
                }
                for s in breakdown.signal_contributions
            ],
            "boosts": [
                {
                    "type": b.boost_type,
                    "amount": b.boost_amount,
                    "reason": b.reason,
                }
                for b in breakdown.boosts
            ],
            "business_rules": [
                {
                    "name": r.rule_name,
                    "type": r.rule_type,
                    "action": r.action,
                    "effect": r.effect,
                }
                for r in breakdown.business_rules
            ],
            "position": breakdown.ranking_position,
        }
    
    def format_for_ui(self, breakdown: RankingBreakdown) -> Dict[str, Any]:
        """
        Format breakdown for UI display.
        
        Args:
            breakdown: Ranking breakdown
            
        Returns:
            UI-formatted explanation
        """
        top_signals = breakdown.get_top_signals(3)
        
        return {
            "document_id": breakdown.document_id,
            "score": breakdown.final_score,
            "top_factors": [
                {
                    "name": s.signal_name,
                    "impact": "positive" if s.contribution > 0 else "negative",
                    "value": abs(s.contribution),
                }
                for s in top_signals
            ],
            "boosts_applied": len(breakdown.boosts),
            "rules_applied": len(breakdown.business_rules),
            "is_pinned": breakdown.metadata.get("pinned", False),
            "is_promoted": breakdown.metadata.get("promoted", False),
            "is_sponsored": breakdown.metadata.get("sponsored", False),
        }
    
    def format_for_logs(self, breakdown: RankingBreakdown) -> str:
        """
        Format breakdown for logging.
        
        Args:
            breakdown: Ranking breakdown
            
        Returns:
            Log-formatted explanation string
        """
        parts = [
            f"Document: {breakdown.document_id}",
            f"Final Score: {breakdown.final_score:.4f}",
            f"Original Score: {breakdown.original_score:.4f}",
        ]
        
        if breakdown.signal_contributions:
            parts.append("Signal Contributions:")
            for signal in breakdown.signal_contributions:
                parts.append(
                    f"  - {signal.signal_name}: {signal.contribution:.4f} "
                    f"(weight: {signal.weight})"
                )
        
        if breakdown.boosts:
            parts.append("Boosts:")
            for boost in breakdown.boosts:
                parts.append(
                    f"  - {boost.boost_type}: +{boost.boost_amount:.4f} "
                    f"({boost.reason})"
                )
        
        if breakdown.business_rules:
            parts.append("Business Rules:")
            for rule in breakdown.business_rules:
                parts.append(
                    f"  - {rule.rule_name}: {rule.action} "
                    f"(effect: {rule.effect:.4f})"
                )
        
        return "\n".join(parts)
    
    def get_summary_statistics(
        self,
        breakdowns: Dict[str, RankingBreakdown],
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a set of breakdowns.
        
        Args:
            breakdowns: Dictionary of breakdowns
            
        Returns:
            Summary statistics
        """
        if not breakdowns:
            return {}
        
        total_docs = len(breakdowns)
        total_signal_contrib = sum(
            b.get_total_signal_contribution() for b in breakdowns.values()
        )
        total_boost = sum(
            b.get_total_boost() for b in breakdowns.values()
        )
        total_rule_effect = sum(
            b.get_total_business_rule_effect() for b in breakdowns.values()
        )
        
        # Count signal usage
        signal_usage: Dict[str, int] = {}
        for breakdown in breakdowns.values():
            for signal in breakdown.signal_contributions:
                signal_usage[signal.signal_name] = (
                    signal_usage.get(signal.signal_name, 0) + 1
                )
        
        # Count rule usage
        rule_usage: Dict[str, int] = {}
        for breakdown in breakdowns.values():
            for rule in breakdown.business_rules:
                rule_usage[rule.rule_name] = (
                    rule_usage.get(rule.rule_name, 0) + 1
                )
        
        return {
            "total_documents": total_docs,
            "total_signal_contribution": total_signal_contrib,
            "total_boost": total_boost,
            "total_business_rule_effect": total_rule_effect,
            "average_signal_contribution": total_signal_contrib / total_docs,
            "average_boost": total_boost / total_docs,
            "signal_usage": signal_usage,
            "rule_usage": rule_usage,
            "most_used_signals": sorted(
                signal_usage.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            "most_used_rules": sorted(
                rule_usage.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }
    
    def get_explanation(self) -> ScoreExplanation:
        """
        Get the underlying explanation instance.
        
        Returns:
            Score explanation instance
        """
        return self._explanation
