"""
Audit Manager.

This module provides audit trail functionality for tracking all
important operations in the search, ranking, and recommendation systems.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import json
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityContext


class AuditAction(Enum):
    """Types of audit actions."""
    SEARCH = "search"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    INDEXING = "indexing"
    DELETION = "deletion"
    CACHE_INVALIDATION = "cache_invalidation"
    CONFIG_CHANGE = "config_change"
    PROVIDER_SWITCH = "provider_switch"
    BUSINESS_RULE_APPLIED = "business_rule_applied"
    SIGNAL_EXECUTED = "signal_executed"


@dataclass
class AuditEvent:
    """Audit event record."""
    
    action: AuditAction
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[ObservabilityContext] = None
    actor: Optional[str] = None  # user_id or system
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    component: Optional[str] = None
    provider: Optional[str] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    changes: Dict[str, Any] = field(default_factory=dict)  # before/after changes
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action": self.action.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict() if self.context else None,
            "actor": self.actor,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "component": self.component,
            "provider": self.provider,
            "success": self.success,
            "details": self.details,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditManager:
    """
    Audit trail manager.
    
    This manager records all important operations for compliance,
    debugging, and security purposes.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the audit manager.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._audit_events: List[AuditEvent] = []
        self._lock = threading.Lock()
        self._max_events = 100000  # Large retention for audit trail
        
        # File-based audit log if needed
        self._audit_file = None
        if config.audit_enabled:
            self._initialize_audit_file()
    
    def _initialize_audit_file(self) -> None:
        """Initialize file-based audit log."""
        import os
        from django.conf import settings
        
        audit_dir = getattr(settings, "AUDIT_LOG_DIR", "/var/log/matchhire/audit")
        
        try:
            os.makedirs(audit_dir, exist_ok=True)
            audit_file_path = os.path.join(
                audit_dir,
                f"audit_{datetime.utcnow().strftime('%Y%m%d')}.log"
            )
            self._audit_file = open(audit_file_path, "a")
        except Exception:
            self._audit_file = None
    
    def record_audit(
        self,
        action: AuditAction,
        actor: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        component: Optional[str] = None,
        provider: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        context: Optional[ObservabilityContext] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """
        Record an audit event.
        
        Args:
            action: Audit action
            actor: Actor who performed the action
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            component: Component that performed the action
            provider: Provider used
            success: Whether the action succeeded
            details: Additional details
            changes: Before/after changes
            context: Observability context
            ip_address: IP address of the actor
            user_agent: User agent of the actor
            
        Returns:
            AuditEvent instance
        """
        if not self._config.audit_enabled:
            return AuditEvent(action=action)
        
        event = AuditEvent(
            action=action,
            context=context,
            actor=actor or (context.user_id if context else None),
            entity_type=entity_type,
            entity_id=entity_id,
            component=component,
            provider=provider,
            success=success,
            details=details or {},
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Store in memory
        with self._lock:
            self._audit_events.append(event)
            
            # Keep events bounded
            if len(self._audit_events) > self._max_events:
                self._audit_events = self._audit_events[-self._max_events:]
        
        # Write to file if configured
        if self._audit_file:
            try:
                self._audit_file.write(event.to_json() + "\n")
                self._audit_file.flush()
            except Exception:
                pass
        
        return event
    
    def record_audit_from_event(self, event: ObservabilityEvent) -> None:
        """
        Record audit from an observability event.
        
        Args:
            event: Observability event
        """
        if event.event_type != EventType.AUDIT:
            return
        
        action_str = event.data.get("action", "unknown")
        try:
            action = AuditAction(action_str)
        except ValueError:
            action = AuditAction.SEARCH
        
        self.record_audit(
            action=action,
            entity_type=event.data.get("entity_type"),
            entity_id=event.data.get("entity_id"),
            context=event.context,
            **{k: v for k, v in event.data.items() 
               if k not in ["action", "entity_type", "entity_id"]},
        )
    
    def get_audit_events(
        self,
        action: Optional[AuditAction] = None,
        actor: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        component: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Get audit events with optional filters.
        
        Args:
            action: Optional action filter
            actor: Optional actor filter
            entity_type: Optional entity type filter
            entity_id: Optional entity ID filter
            component: Optional component filter
            since: Optional start time filter
            until: Optional end time filter
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        with self._lock:
            events = self._audit_events
            
            if action:
                events = [e for e in events if e.action == action]
            
            if actor:
                events = [e for e in events if e.actor == actor]
            
            if entity_type:
                events = [e for e in events if e.entity_type == entity_type]
            
            if entity_id:
                events = [e for e in events if e.entity_id == entity_id]
            
            if component:
                events = [e for e in events if e.component == component]
            
            if since:
                events = [e for e in events if e.timestamp >= since]
            
            if until:
                events = [e for e in events if e.timestamp <= until]
            
            return events[-limit:]
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Get audit history for a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        return self.get_audit_events(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )
    
    def get_actor_history(
        self,
        actor: str,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Get audit history for a specific actor.
        
        Args:
            actor: Actor ID
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        return self.get_audit_events(actor=actor, limit=limit)
    
    def get_failed_events(self, limit: int = 100) -> List[AuditEvent]:
        """
        Get failed audit events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of failed audit events
        """
        with self._lock:
            failed = [e for e in self._audit_events if not e.success]
            return failed[-limit:]
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """
        Get a summary of audit data.
        
        Returns:
            Audit summary dictionary
        """
        with self._lock:
            action_counts = {}
            actor_counts = {}
            component_counts = {}
            
            for event in self._audit_events:
                action = event.action.value
                action_counts[action] = action_counts.get(action, 0) + 1
                
                if event.actor:
                    actor_counts[event.actor] = actor_counts.get(event.actor, 0) + 1
                
                if event.component:
                    component_counts[event.component] = component_counts.get(event.component, 0) + 1
            
            return {
                "total_events": len(self._audit_events),
                "action_counts": action_counts,
                "actor_counts": actor_counts,
                "component_counts": component_counts,
            }
    
    def clear_old_events(self, retention_days: int = None) -> None:
        """
        Clear old audit events.
        
        Args:
            retention_days: Retention period in days (uses config default if None)
        """
        if retention_days is None:
            retention_days = self._config.audit_retention_days
        
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        with self._lock:
            self._audit_events = [
                event for event in self._audit_events
                if event.timestamp >= cutoff
            ]
    
    def export_audit_log(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> str:
        """
        Export audit log as JSON.
        
        Args:
            since: Optional start time
            until: Optional end time
            
        Returns:
            JSON string of audit events
        """
        events = self.get_audit_events(since=since, until=until, limit=self._max_events)
        return json.dumps([e.to_dict() for e in events], indent=2)
    
    def shutdown(self) -> None:
        """Shutdown the audit manager."""
        if self._audit_file:
            try:
                self._audit_file.close()
            except Exception:
                pass
