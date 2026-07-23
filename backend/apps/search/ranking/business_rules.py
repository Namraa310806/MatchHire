"""
Business Rules Engine.

This module provides a configurable business rules engine for ranking.
Rules can pin results, hide results, promote content, block entities,
and apply custom boosts based on business logic.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re


class RuleType(Enum):
    """Types of business rules."""
    PINNED_RESULT = "pinned_result"
    HIDDEN_RESULT = "hidden_result"
    PROMOTED_JOB = "promoted_job"
    BLOCKED_CANDIDATE = "blocked_candidate"
    PRIORITY_COMPANY = "priority_company"
    SPONSORED = "sponsored"
    MANUAL_BOOST = "manual_boost"
    CUSTOM = "custom"


class RulePriority(Enum):
    """Priority levels for business rules."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class RuleAction(Enum):
    """Actions that business rules can take."""
    PIN = "pin"
    HIDE = "hide"
    PROMOTE = "promote"
    BLOCK = "block"
    BOOST = "boost"
    PENALIZE = "penalize"
    CUSTOM = "custom"


@dataclass
class BusinessRule:
    """
    Base class for business rules.
    
    Each rule defines a condition and an action to take
    when the condition is met.
    """
    
    name: str
    rule_type: RuleType
    priority: RulePriority = RulePriority.MEDIUM
    enabled: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "rule_type": self.rule_type.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "description": self.description,
            "metadata": self.metadata,
        }
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Check if the rule matches the document.
        
        Args:
            document: Document to check
            context: Search context
            
        Returns:
            True if rule matches
        """
        return True
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the rule to the document.
        
        Args:
            document: Document to modify
            context: Search context
            
        Returns:
            Modified document with rule applied
        """
        return document


@dataclass
class PinnedResultRule(BusinessRule):
    """
    Rule to pin specific results to the top of search results.
    """
    
    document_ids: List[str] = field(default_factory=list)
    position: int = 0
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.PINNED_RESULT
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document should be pinned."""
        doc_id = document.get("id")
        return doc_id in self.document_ids
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pin to document."""
        document["_pinned"] = True
        document["_pin_position"] = self.position
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + 100.0
        return document


@dataclass
class HiddenResultRule(BusinessRule):
    """
    Rule to hide specific results from search results.
    """
    
    document_ids: List[str] = field(default_factory=list)
    reason: str = "Hidden by business rule"
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.HIDDEN_RESULT
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document should be hidden."""
        doc_id = document.get("id")
        return doc_id in self.document_ids
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply hide to document."""
        document["_hidden"] = True
        document["_hidden_reason"] = self.reason
        document["_ranking_boost"] = document.get("_ranking_boost", 0) - 1000.0
        return document


@dataclass
class PromotedJobRule(BusinessRule):
    """
    Rule to promote specific jobs in search results.
    """
    
    job_ids: List[str] = field(default_factory=list)
    boost_amount: float = 5.0
    promotion_reason: str = "Promoted job"
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.PROMOTED_JOB
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if job should be promoted."""
        doc_id = document.get("id")
        return doc_id in self.job_ids
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply promotion to document."""
        document["_promoted"] = True
        document["_promotion_reason"] = self.promotion_reason
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + self.boost_amount
        return document


@dataclass
class BlockedCandidateRule(BusinessRule):
    """
    Rule to block specific candidates from search results.
    """
    
    candidate_ids: List[str] = field(default_factory=list)
    block_reason: str = "Blocked candidate"
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.BLOCKED_CANDIDATE
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if candidate should be blocked."""
        doc_id = document.get("id")
        return doc_id in self.candidate_ids
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply block to document."""
        document["_blocked"] = True
        document["_block_reason"] = self.block_reason
        document["_ranking_boost"] = document.get("_ranking_boost", 0) - 1000.0
        return document


@dataclass
class PriorityCompanyRule(BusinessRule):
    """
    Rule to boost results from priority companies.
    """
    
    company_names: List[str] = field(default_factory=list)
    boost_amount: float = 3.0
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.PRIORITY_COMPANY
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document is from priority company."""
        company = document.get("company_name") or document.get("company", "")
        return company in self.company_names
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply priority boost to document."""
        document["_priority_company"] = True
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + self.boost_amount
        return document


@dataclass
class SponsoredRule(BusinessRule):
    """
    Rule to mark and boost sponsored content.
    """
    
    sponsored_ids: List[str] = field(default_factory=list)
    boost_amount: float = 2.0
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.SPONSORED
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document is sponsored."""
        doc_id = document.get("id")
        is_sponsored = document.get("is_sponsored", False)
        return doc_id in self.sponsored_ids or is_sponsored
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sponsored boost to document."""
        document["_sponsored"] = True
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + self.boost_amount
        return document


@dataclass
class ManualBoostRule(BusinessRule):
    """
    Rule for manual boosts based on custom conditions.
    """
    
    condition: str = ""
    boost_amount: float = 1.0
    field: Optional[str] = None
    value_pattern: Optional[str] = None
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.MANUAL_BOOST
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document matches manual boost condition."""
        if not self.field or not self.value_pattern:
            return False
        
        field_value = str(document.get(self.field, ""))
        
        # Support regex patterns
        try:
            if re.match(self.value_pattern, field_value, re.IGNORECASE):
                return True
        except re.error:
            # If regex fails, try exact match
            return self.value_pattern.lower() in field_value.lower()
        
        return False
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply manual boost to document."""
        document["_manual_boost"] = True
        document["_manual_boost_amount"] = self.boost_amount
        document["_ranking_boost"] = document.get("_ranking_boost", 0) + self.boost_amount
        return document


@dataclass
class CustomRule(BusinessRule):
    """
    Custom rule with user-defined matching and application logic.
    """
    
    match_function: Optional[Callable[[Dict[str, Any], Dict[str, Any]], bool]] = None
    apply_function: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Initialize rule type."""
        self.rule_type = RuleType.CUSTOM
    
    def matches(self, document: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if document matches custom condition."""
        if self.match_function:
            return self.match_function(document, context)
        return False
    
    def apply(self, document: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom rule to document."""
        if self.apply_function:
            return self.apply_function(document, context)
        return document


class BusinessRulesEngine:
    """
    Engine for managing and applying business rules to search results.
    
    The engine maintains a registry of rules, applies them in priority order,
    and handles conflict resolution when multiple rules apply.
    """
    
    def __init__(self):
        """Initialize the business rules engine."""
        self._rules: List[BusinessRule] = []
        self._rule_conflicts: List[str] = []
    
    def add_rule(self, rule: BusinessRule) -> None:
        """
        Add a business rule.
        
        Args:
            rule: Business rule to add
        """
        self._rules.append(rule)
        self._sort_rules_by_priority()
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove a business rule by name.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                del self._rules[i]
                return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[BusinessRule]:
        """
        Get a rule by name.
        
        Args:
            rule_name: Name of the rule
            
        Returns:
            Rule instance or None if not found
        """
        for rule in self._rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[BusinessRule]:
        """
        Get all rules of a specific type.
        
        Args:
            rule_type: Type of rules to get
            
        Returns:
            List of rules of the specified type
        """
        return [rule for rule in self._rules if rule.rule_type == rule_type]
    
    def enable_rule(self, rule_name: str) -> bool:
        """
        Enable a rule by name.
        
        Args:
            rule_name: Name of the rule to enable
            
        Returns:
            True if rule was enabled, False if not found
        """
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = True
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """
        Disable a rule by name.
        
        Args:
            rule_name: Name of the rule to disable
            
        Returns:
            True if rule was disabled, False if not found
        """
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = False
            return True
        return False
    
    def apply_rules(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Apply all enabled rules to search results.
        
        Args:
            results: Search results to apply rules to
            context: Search context
            
        Returns:
            Tuple of (modified results, applied rules info)
        """
        applied_rules_info = []
        
        for result in results:
            result.setdefault("_ranking_boost", 0.0)
            result.setdefault("_applied_rules", [])
            
            for rule in self._rules:
                if not rule.enabled:
                    continue
                
                try:
                    if rule.matches(result, context):
                        rule.apply(result, context)
                        result["_applied_rules"].append(rule.name)
                        
                        applied_rules_info.append({
                            "rule_name": rule.name,
                            "rule_type": rule.rule_type.value,
                            "document_id": result.get("id"),
                            "priority": rule.priority.value,
                        })
                except Exception as e:
                    # Log error but continue with other rules
                    print(f"Rule {rule.name} failed: {e}")
        
        # Re-sort results based on ranking boosts
        results.sort(
            key=lambda x: (
                -x.get("_pin_position", float('inf')),
                -(x.get("_ranking_boost", 0) + x.get("_ranking_score", 0)),
            )
        )
        
        # Filter out hidden results
        visible_results = [r for r in results if not r.get("_hidden")]
        
        return visible_results, applied_rules_info
    
    def _sort_rules_by_priority(self) -> None:
        """Sort rules by priority (lower priority value = higher priority)."""
        self._rules.sort(key=lambda r: r.priority.value)
    
    def get_all_rules(self) -> List[BusinessRule]:
        """
        Get all registered rules.
        
        Returns:
            List of all rules
        """
        return self._rules.copy()
    
    def clear_rules(self) -> None:
        """Clear all rules."""
        self._rules.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary representation."""
        return {
            "rules": [rule.to_dict() for rule in self._rules],
            "rule_count": len(self._rules),
            "conflicts": self._rule_conflicts,
        }
    
    def validate_rules(self) -> List[str]:
        """
        Validate all rules and return any issues found.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        for rule in self._rules:
            if not rule.name:
                issues.append("Rule has no name")
            
            if not rule.description:
                issues.append(f"Rule '{rule.name}' has no description")
        
        return issues


class RuleBuilder:
    """
    Builder for creating business rules.
    
    Provides a fluent interface for constructing rules.
    """
    
    @staticmethod
    def pinned(name: str, document_ids: List[str], position: int = 0) -> PinnedResultRule:
        """
        Create a pinned result rule.
        
        Args:
            name: Rule name
            document_ids: IDs of documents to pin
            position: Position to pin at
            
        Returns:
            PinnedResultRule instance
        """
        return PinnedResultRule(
            name=name,
            document_ids=document_ids,
            position=position,
            description=f"Pin results {document_ids} to position {position}",
        )
    
    @staticmethod
    def hidden(name: str, document_ids: List[str], reason: str = "Hidden") -> HiddenResultRule:
        """
        Create a hidden result rule.
        
        Args:
            name: Rule name
            document_ids: IDs of documents to hide
            reason: Reason for hiding
            
        Returns:
            HiddenResultRule instance
        """
        return HiddenResultRule(
            name=name,
            document_ids=document_ids,
            reason=reason,
            description=f"Hide results {document_ids}: {reason}",
        )
    
    @staticmethod
    def promoted(name: str, job_ids: List[str], boost: float = 5.0) -> PromotedJobRule:
        """
        Create a promoted job rule.
        
        Args:
            name: Rule name
            job_ids: IDs of jobs to promote
            boost: Boost amount
            
        Returns:
            PromotedJobRule instance
        """
        return PromotedJobRule(
            name=name,
            job_ids=job_ids,
            boost_amount=boost,
            description=f"Promote jobs {job_ids} with boost {boost}",
        )
    
    @staticmethod
    def blocked(name: str, candidate_ids: List[str], reason: str = "Blocked") -> BlockedCandidateRule:
        """
        Create a blocked candidate rule.
        
        Args:
            name: Rule name
            candidate_ids: IDs of candidates to block
            reason: Reason for blocking
            
        Returns:
            BlockedCandidateRule instance
        """
        return BlockedCandidateRule(
            name=name,
            candidate_ids=candidate_ids,
            block_reason=reason,
            description=f"Block candidates {candidate_ids}: {reason}",
        )
    
    @staticmethod
    def priority_company(name: str, company_names: List[str], boost: float = 3.0) -> PriorityCompanyRule:
        """
        Create a priority company rule.
        
        Args:
            name: Rule name
            company_names: Names of priority companies
            boost: Boost amount
            
        Returns:
            PriorityCompanyRule instance
        """
        return PriorityCompanyRule(
            name=name,
            company_names=company_names,
            boost_amount=boost,
            description=f"Boost results from companies {company_names} by {boost}",
        )
    
    @staticmethod
    def sponsored(name: str, sponsored_ids: List[str], boost: float = 2.0) -> SponsoredRule:
        """
        Create a sponsored rule.
        
        Args:
            name: Rule name
            sponsored_ids: IDs of sponsored items
            boost: Boost amount
            
        Returns:
            SponsoredRule instance
        """
        return SponsoredRule(
            name=name,
            sponsored_ids=sponsored_ids,
            boost_amount=boost,
            description=f"Mark and boost sponsored items {sponsored_ids} by {boost}",
        )
    
    @staticmethod
    def manual_boost(
        name: str,
        field: str,
        value_pattern: str,
        boost: float = 1.0,
    ) -> ManualBoostRule:
        """
        Create a manual boost rule.
        
        Args:
            name: Rule name
            field: Field to match
            value_pattern: Pattern to match (supports regex)
            boost: Boost amount
            
        Returns:
            ManualBoostRule instance
        """
        return ManualBoostRule(
            name=name,
            field=field,
            value_pattern=value_pattern,
            boost_amount=boost,
            description=f"Boost {field} matching {value_pattern} by {boost}",
        )
