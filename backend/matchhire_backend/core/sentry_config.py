"""
Sentry integration for error monitoring and performance tracking.

Provides centralized error tracking with:
- Exception capture
- Performance monitoring
- Release tracking
- User context
- Request context
"""
import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from matchhire_backend.core.env import get_env

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry SDK for error monitoring.
    
    Sentry is initialized only if SENTRY_DSN is configured.
    Gracefully degrades if Sentry is not available or misconfigured.
    """
    sentry_dsn = get_env("SENTRY_DSN", default=None)
    
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return
    
    environment = get_env("ENVIRONMENT", default="development")
    release = get_env("SENTRY_RELEASE", default="1.0.0")
    
    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )
    
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=release,
            integrations=[
                DjangoIntegration(
                    # Enable performance monitoring
                    transaction_style="url",
                    # Capture HTTP headers
                    send_default_pii=False,  # Don't send PII by default
                ),
                CeleryIntegration(
                    # Monitor Celery tasks
                    monitor_beat_tasks=True,
                ),
                RedisIntegration(),
                logging_integration,
            ],
            # Performance monitoring
            traces_sample_rate=float(get_env("SENTRY_TRACES_SAMPLE_RATE", default="0.1")),
            # Error sampling
            sample_rate=float(get_env("SENTRY_ERROR_SAMPLE_RATE", default="1.0")),
            # Before send callback for filtering
            before_send=before_send_filter,
            # Before breadcrumb callback for filtering
            before_breadcrumb=before_breadcrumb_filter,
            # Ignore specific exceptions
            ignore_errors=[
                # Add exception types to ignore here if needed
            ],
            # Server name (optional)
            server_name=get_env("SENTRY_SERVER_NAME", default=None),
            # Maximum number of breadcrumbs
            max_breadcrumbs=50,
            # Attach stack traces to messages
            attach_stacktrace=True,
        )
        
        logger.info(f"Sentry initialized for environment: {environment}, release: {release}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        # Don't fail the application if Sentry initialization fails


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.
    
    Args:
        event: Event dictionary
        hint: Hint dictionary with additional information
    
    Returns:
        Filtered event or None to drop the event
    """
    # Filter out specific error types if needed
    if event.get("level") == "info":
        # Don't send info level events
        return None
    
    # Add custom tags
    event["tags"] = event.get("tags", {})
    event["tags"]["service"] = "matchhire-backend"
    
    # Remove sensitive data from request headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[FILTERED]"
    
    return event


def before_breadcrumb_filter(breadcrumb, hint):
    """
    Filter breadcrumbs before adding to event.
    
    Args:
        breadcrumb: Breadcrumb dictionary
        hint: Hint dictionary with additional information
    
    Returns:
        Filtered breadcrumb or None to drop the breadcrumb
    """
    # Filter out health check breadcrumbs to reduce noise
    if breadcrumb.get("category") == "http":
        url = breadcrumb.get("data", {}).get("url", "")
        if "/health/" in url or "/metrics/" in url:
            return None
    
    return breadcrumb


def set_user_context(user_id: Optional[str] = None, email: Optional[str] = None, **kwargs):
    """
    Set user context for Sentry events.
    
    Args:
        user_id: User ID
        email: User email (optional)
        **kwargs: Additional user attributes
    """
    if not sentry_sdk.Hub.current.client:
        return
    
    user_context = {"id": user_id}
    if email:
        user_context["email"] = email
    user_context.update(kwargs)
    
    sentry_sdk.set_user(user_context)


def set_request_context(request_id: Optional[str] = None, **kwargs):
    """
    Set request context for Sentry events.
    
    Args:
        request_id: Request ID for correlation
        **kwargs: Additional request attributes
    """
    if not sentry_sdk.Hub.current.client:
        return
    
    context = {"request_id": request_id}
    context.update(kwargs)
    
    sentry_sdk.set_context("request", context)


def capture_exception(exception: Exception, **kwargs):
    """
    Capture an exception and send to Sentry.
    
    Args:
        exception: Exception to capture
        **kwargs: Additional context
    """
    if not sentry_sdk.Hub.current.client:
        logger.error(f"Exception occurred (Sentry not available): {exception}")
        return
    
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a message and send to Sentry.
    
    Args:
        message: Message to capture
        level: Log level (info, warning, error)
        **kwargs: Additional context
    """
    if not sentry_sdk.Hub.current.client:
        logger.log(getattr(logging, level.upper()), message)
        return
    
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def start_transaction(name: str, op: str = "task"):
    """
    Start a performance monitoring transaction.
    
    Args:
        name: Transaction name
        op: Operation type
    
    Returns:
        Transaction object
    """
    if not sentry_sdk.Hub.current.client:
        return None
    
    return sentry_sdk.start_transaction(name=name, op=op)


def flush_sentry(timeout: float = 2.0):
    """
    Flush pending events to Sentry.
    
    Args:
        timeout: Timeout in seconds
    """
    if sentry_sdk.Hub.current.client:
        sentry_sdk.flush(timeout)
