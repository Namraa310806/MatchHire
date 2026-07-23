"""
Instrumentation Layer.

This module provides decorators, middleware, and hooks for instrumenting
search, ranking, and recommendation components without modifying business logic.
The instrumentation is completely orthogonal to the core implementations.
"""

from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import time
from contextlib import contextmanager
from .core import (
    ObservabilityManager,
    ObservabilityContext,
    ObservabilityComponent,
    get_manager,
)


def instrument_search(func: Callable) -> Callable:
    """
    Decorator to instrument search operations.
    
    This decorator automatically:
    - Creates spans for tracing
    - Records metrics (latency, request count)
    - Logs search operations
    - Records audit events
    - Checks for slow queries
    
    Args:
        func: Function to instrument
        
    Returns:
        Instrumented function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_manager()
        
        # Create context if not present
        context = manager.get_context()
        context.component = ObservabilityComponent.SEARCH
        
        # Start span
        span = manager.start_span(
            name=func.__name__,
            component=ObservabilityComponent.SEARCH,
            context=context,
        )
        
        start_time = time.time()
        
        try:
            # Record request start
            manager.metrics.increment_counter("search_requests_total")
            manager.logging.info(
                f"Search request started: {func.__name__}",
                component="search",
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            manager.metrics.observe_histogram("search_latency_seconds", latency_ms / 1000)
            
            # Log success
            manager.logging.info(
                f"Search request completed: {func.__name__}",
                component="search",
                duration_ms=latency_ms,
            )
            
            # Check for slow query
            manager.diagnostics.check_slow_query(
                latency_ms=latency_ms,
                query=str(kwargs),
                component=ObservabilityComponent.SEARCH,
                request_id=context.request_id,
                trace_id=context.trace_id,
            )
            
            # End span
            span.set_status("ok")
            span.set_attribute("duration_ms", latency_ms)
            manager.tracing.end_span(span)
            
            return result
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error
            manager.metrics.increment_counter("search_errors_total")
            manager.logging.error(
                f"Search request failed: {func.__name__}",
                component="search",
                duration_ms=latency_ms,
                exception=str(e),
            )
            
            # End span with error
            span.record_exception(e)
            manager.tracing.end_span(span)
            
            raise
    
    return wrapper


def instrument_ranking(func: Callable) -> Callable:
    """
    Decorator to instrument ranking operations.
    
    Args:
        func: Function to instrument
        
    Returns:
        Instrumented function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_manager()
        
        # Create context if not present
        context = manager.get_context()
        context.component = ObservabilityComponent.RANKING
        
        # Start span
        span = manager.start_span(
            name=func.__name__,
            component=ObservabilityComponent.RANKING,
            context=context,
        )
        
        start_time = time.time()
        
        try:
            # Record request start
            manager.metrics.increment_counter("ranking_requests_total")
            manager.logging.info(
                f"Ranking request started: {func.__name__}",
                component="ranking",
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            manager.metrics.observe_histogram("ranking_latency_seconds", latency_ms / 1000)
            
            # Log success
            manager.logging.info(
                f"Ranking request completed: {func.__name__}",
                component="ranking",
                duration_ms=latency_ms,
            )
            
            # Check for slow ranking
            manager.diagnostics.check_slow_ranking(
                latency_ms=latency_ms,
                component=ObservabilityComponent.RANKING,
                request_id=context.request_id,
                trace_id=context.trace_id,
            )
            
            # End span
            span.set_status("ok")
            span.set_attribute("duration_ms", latency_ms)
            manager.tracing.end_span(span)
            
            return result
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error
            manager.logging.error(
                f"Ranking request failed: {func.__name__}",
                component="ranking",
                duration_ms=latency_ms,
                exception=str(e),
            )
            
            # End span with error
            span.record_exception(e)
            manager.tracing.end_span(span)
            
            raise
    
    return wrapper


def instrument_recommendation(func: Callable) -> Callable:
    """
    Decorator to instrument recommendation operations.
    
    Args:
        func: Function to instrument
        
    Returns:
        Instrumented function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_manager()
        
        # Create context if not present
        context = manager.get_context()
        context.component = ObservabilityComponent.RECOMMENDATION
        
        # Start span
        span = manager.start_span(
            name=func.__name__,
            component=ObservabilityComponent.RECOMMENDATION,
            context=context,
        )
        
        start_time = time.time()
        
        try:
            # Record request start
            manager.metrics.increment_counter("recommendation_requests_total")
            manager.logging.info(
                f"Recommendation request started: {func.__name__}",
                component="recommendation",
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            manager.metrics.observe_histogram("recommendation_latency_seconds", latency_ms / 1000)
            
            # Count recommendations generated
            if hasattr(result, 'recommendations'):
                manager.metrics.increment_counter(
                    "recommendations_generated_total",
                    amount=len(result.recommendations)
                )
            
            # Log success
            manager.logging.info(
                f"Recommendation request completed: {func.__name__}",
                component="recommendation",
                duration_ms=latency_ms,
            )
            
            # Check for slow recommendation
            manager.diagnostics.check_slow_recommendation(
                latency_ms=latency_ms,
                component=ObservabilityComponent.RECOMMENDATION,
                request_id=context.request_id,
                trace_id=context.trace_id,
            )
            
            # End span
            span.set_status("ok")
            span.set_attribute("duration_ms", latency_ms)
            manager.tracing.end_span(span)
            
            return result
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error
            manager.logging.error(
                f"Recommendation request failed: {func.__name__}",
                component="recommendation",
                duration_ms=latency_ms,
                exception=str(e),
            )
            
            # End span with error
            span.record_exception(e)
            manager.tracing.end_span(span)
            
            raise
    
    return wrapper


def instrument_provider(func: Callable) -> Callable:
    """
    Decorator to instrument provider operations.
    
    Args:
        func: Function to instrument
        
    Returns:
        Instrumented function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_manager()
        
        # Create context if not present
        context = manager.get_context()
        context.component = ObservabilityComponent.PROVIDER
        
        # Get provider name from self if available
        provider_name = None
        if args and hasattr(args[0], '__class__'):
            provider_name = args[0].__class__.__name__
        
        if provider_name:
            context.provider = provider_name
        
        # Start span
        span = manager.start_span(
            name=func.__name__,
            component=ObservabilityComponent.PROVIDER,
            context=context,
        )
        
        start_time = time.time()
        
        try:
            # Record request start
            manager.metrics.increment_counter("provider_requests_total")
            manager.logging.info(
                f"Provider request started: {provider_name or 'unknown'} - {func.__name__}",
                component="provider",
                provider=provider_name,
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            manager.metrics.observe_histogram("provider_latency_seconds", latency_ms / 1000)
            
            # Update provider health
            manager.metrics.set_gauge("provider_health", 1.0)
            
            # Log success
            manager.logging.info(
                f"Provider request completed: {provider_name or 'unknown'} - {func.__name__}",
                component="provider",
                provider=provider_name,
                duration_ms=latency_ms,
            )
            
            # End span
            span.set_status("ok")
            span.set_attribute("duration_ms", latency_ms)
            span.set_attribute("provider", provider_name)
            manager.tracing.end_span(span)
            
            return result
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error
            manager.metrics.increment_counter("provider_errors_total")
            manager.metrics.set_gauge("provider_health", 0.0)
            
            manager.logging.error(
                f"Provider request failed: {provider_name or 'unknown'} - {func.__name__}",
                component="provider",
                provider=provider_name,
                duration_ms=latency_ms,
                exception=str(e),
            )
            
            # Record provider failure diagnostic
            manager.diagnostics.check_provider_failure(
                provider=provider_name or "unknown",
                error=str(e),
                component=ObservabilityComponent.PROVIDER,
                request_id=context.request_id,
            )
            
            # End span with error
            span.record_exception(e)
            span.set_attribute("provider", provider_name)
            manager.tracing.end_span(span)
            
            raise
    
    return wrapper


@contextmanager
def observe_operation(
    operation_name: str,
    component: ObservabilityComponent,
    **attributes
):
    """
    Context manager for observing an operation.
    
    Args:
        operation_name: Name of the operation
        component: Component type
        **attributes: Additional attributes
        
    Yields:
        Span object
    """
    manager = get_manager()
    
    # Create context if not present
    context = manager.get_context()
    context.component = component
    
    # Start span
    span = manager.start_span(
        name=operation_name,
        component=component,
        context=context,
        **attributes
    )
    
    start_time = time.time()
    
    try:
        yield span
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # End span
        span.set_status("ok")
        span.set_attribute("duration_ms", latency_ms)
        manager.tracing.end_span(span)
        
    except Exception as e:
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # End span with error
        span.record_exception(e)
        manager.tracing.end_span(span)
        
        raise


class ObservabilityMiddleware:
    """
    Middleware for automatic observability instrumentation.
    
    This middleware can be used with Django or other web frameworks
    to automatically instrument all requests.
    """
    
    def __init__(self, get_response: Callable):
        """
        Initialize the middleware.
        
        Args:
            get_response: Django get_response callable
        """
        self.get_response = get_response
        self.manager = get_manager()
    
    def __call__(self, request: Any) -> Any:
        """
        Process the request with observability.
        
        Args:
            request: Django request object
            
        Returns:
            Django response object
        """
        # Create context for the request
        context = ObservabilityContext()
        
        # Add request information
        context.with_tag("path", request.path)
        context.with_tag("method", request.method)
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            context.user_id = str(request.user.id)
        
        # Set context
        self.manager.set_context(context)
        
        # Start span
        span = self.manager.start_span(
            name=f"{request.method} {request.path}",
            component=ObservabilityComponent.SEARCH,
            context=context,
        )
        
        start_time = time.time()
        
        try:
            # Process request
            response = self.get_response(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            self.manager.metrics.observe_histogram("request_latency_seconds", latency_ms / 1000)
            self.manager.metrics.increment_counter("requests_total")
            
            # Log request
            self.manager.logging.info(
                f"Request completed: {request.method} {request.path}",
                component="middleware",
                duration_ms=latency_ms,
                status_code=response.status_code,
            )
            
            # End span
            span.set_status("ok")
            span.set_attribute("duration_ms", latency_ms)
            span.set_attribute("status_code", response.status_code)
            self.manager.tracing.end_span(span)
            
            return response
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error
            self.manager.metrics.increment_counter("request_errors_total")
            
            self.manager.logging.error(
                f"Request failed: {request.method} {request.path}",
                component="middleware",
                duration_ms=latency_ms,
                exception=str(e),
            )
            
            # End span with error
            span.record_exception(e)
            self.manager.tracing.end_span(span)
            
            raise
        
        finally:
            # Clear context
            self.manager.clear_context()


class CacheInstrumentation:
    """
    Instrumentation for cache operations.
    """
    
    @staticmethod
    def instrument_cache_get(cache_instance: Any) -> Any:
        """
        Instrument a cache get operation.
        
        Args:
            cache_instance: Cache instance to instrument
            
        Returns:
            Instrumented cache instance
        """
        manager = get_manager()
        original_get = cache_instance.get
        
        def instrumented_get(key, *args, **kwargs):
            result = original_get(key, *args, **kwargs)
            
            if result is None:
                manager.metrics.increment_counter("cache_misses_total")
            else:
                manager.metrics.increment_counter("cache_hits_total")
            
            return result
        
        cache_instance.get = instrumented_get
        return cache_instance
    
    @staticmethod
    def instrument_cache_set(cache_instance: Any) -> Any:
        """
        Instrument a cache set operation.
        
        Args:
            cache_instance: Cache instance to instrument
            
        Returns:
            Instrumented cache instance
        """
        manager = get_manager()
        original_set = cache_instance.set
        
        def instrumented_set(key, value, *args, **kwargs):
            result = original_set(key, value, *args, **kwargs)
            
            # Update cache size metric
            manager.metrics.set_gauge("cache_size", len(cache_instance._cache) if hasattr(cache_instance, '_cache') else 0)
            
            return result
        
        cache_instance.set = instrumented_set
        return cache_instance


class PipelineInstrumentation:
    """
    Instrumentation for pipeline operations.
    """
    
    @staticmethod
    def instrument_pipeline_stage(stage_name: str, func: Callable) -> Callable:
        """
        Instrument a pipeline stage.
        
        Args:
            stage_name: Name of the stage
            func: Stage function to instrument
            
        Returns:
            Instrumented function
        """
        manager = get_manager()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with observe_operation(
                operation_name=f"pipeline_stage_{stage_name}",
                component=ObservabilityComponent.PIPELINE,
                stage_name=stage_name,
            ):
                return func(*args, **kwargs)
        
        return wrapper
