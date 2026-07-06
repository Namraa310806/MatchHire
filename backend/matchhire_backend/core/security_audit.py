"""
Security Audit Service for logging security events.

Logs security-related events using Python logging.
No database model required - uses standard logging infrastructure.
"""
import logging
from typing import Optional
from django.conf import settings


class SecurityAuditService:
    """
    Centralized service for logging security events.
    
    Uses Python logging to record security-related events.
    Logs can be configured to go to file, syslog, or other handlers.
    """
    
    # Create a dedicated logger for security events
    logger = logging.getLogger('matchhire.security')
    
    @classmethod
    def log_failed_login(cls, email: str, ip_address: Optional[str] = None):
        """Log failed login attempt"""
        cls.logger.warning(
            f"FAILED_LOGIN | email={email} | ip={ip_address or 'unknown'}"
        )
    
    @classmethod
    def log_permission_denied(cls, user_id: Optional[str], endpoint: str, method: str):
        """Log permission denied event"""
        cls.logger.warning(
            f"PERMISSION_DENIED | user_id={user_id or 'anonymous'} | endpoint={endpoint} | method={method}"
        )
    
    @classmethod
    def log_invalid_upload(cls, user_id: str, filename: str, reason: str):
        """Log invalid file upload attempt"""
        cls.logger.warning(
            f"INVALID_UPLOAD | user_id={user_id} | filename={filename} | reason={reason}"
        )
    
    @classmethod
    def log_rate_limit_exceeded(cls, user_id: Optional[str], scope: str, endpoint: str):
        """Log rate limit exceeded event"""
        cls.logger.warning(
            f"RATE_LIMIT_EXCEEDED | user_id={user_id or 'anonymous'} | scope={scope} | endpoint={endpoint}"
        )
    
    @classmethod
    def log_invalid_status_transition(cls, user_id: str, resource_type: str, resource_id: str, from_status: str, to_status: str):
        """Log invalid status transition attempt"""
        cls.logger.warning(
            f"INVALID_STATUS_TRANSITION | user_id={user_id} | resource_type={resource_type} | "
            f"resource_id={resource_id} | from_status={from_status} | to_status={to_status}"
        )
    
    @classmethod
    def log_invalid_moderation_attempt(cls, admin_id: str, resource_type: str, resource_id: str, action: str):
        """Log invalid moderation attempt"""
        cls.logger.warning(
            f"INVALID_MODERATION | admin_id={admin_id} | resource_type={resource_type} | "
            f"resource_id={resource_id} | action={action}"
        )
    
    @classmethod
    def log_suspicious_activity(cls, user_id: Optional[str], activity_type: str, details: str):
        """Log suspicious activity"""
        cls.logger.warning(
            f"SUSPICIOUS_ACTIVITY | user_id={user_id or 'anonymous'} | type={activity_type} | details={details}"
        )
