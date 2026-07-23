"""
Structured Logging Manager.

This module provides structured logging capabilities with support for
JSON formatting, log levels, and integration with the observability context.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import json
import logging
import sys
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityContext


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry."""
    
    timestamp: datetime
    level: LogLevel
    message: str
    context: Optional[ObservabilityContext] = None
    component: Optional[str] = None
    provider: Optional[str] = None
    entity_type: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "context": self.context.to_dict() if self.context else None,
            "component": self.component,
            "provider": self.provider,
            "entity_type": self.entity_type,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "tags": self.tags,
            "data": self.data,
            "exception": self.exception,
            "stack_trace": self.stack_trace,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class StructuredLogger:
    """
    Structured logger with context propagation.
    
    This logger provides structured logging with automatic context
    propagation from the observability manager.
    """
    
    def __init__(
        self,
        name: str,
        config: ObservabilityConfig,
        log_manager: "LoggingManager",
    ):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name
            config: Observability configuration
            log_manager: Parent logging manager
        """
        self._name = name
        self._config = config
        self._log_manager = log_manager
        
        # Create Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, config.log_level, logging.INFO))
        
        # Configure handlers
        if not self._logger.handlers:
            self._configure_handlers()
    
    def _configure_handlers(self) -> None:
        """Configure log handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self._config.log_format == "json":
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self._logger.addHandler(console_handler)
        
        # File handler if enabled
        if self._config.log_to_file and self._config.log_file_path:
            file_handler = logging.FileHandler(self._config.log_file_path)
            
            if self._config.log_format == "json":
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            
            self._logger.addHandler(file_handler)
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[ObservabilityContext] = None,
        **kwargs
    ) -> None:
        """
        Internal log method.
        
        Args:
            level: Log level
            message: Log message
            context: Observability context
            **kwargs: Additional log data
        """
        if not self._config.logging_enabled:
            return
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            context=context,
            component=kwargs.get("component"),
            provider=kwargs.get("provider"),
            entity_type=kwargs.get("entity_type"),
            user_id=context.user_id if context else kwargs.get("user_id"),
            request_id=context.request_id if context else kwargs.get("request_id"),
            trace_id=context.trace_id if context else kwargs.get("trace_id"),
            span_id=context.span_id if context else kwargs.get("span_id"),
            tags=kwargs.get("tags", {}),
            data={k: v for k, v in kwargs.items() 
                  if k not in ["component", "provider", "entity_type", 
                              "user_id", "request_id", "trace_id", "span_id", "tags"]},
            exception=kwargs.get("exception"),
            stack_trace=kwargs.get("stack_trace"),
        )
        
        # Log to Python logger
        log_level = getattr(logging, level.value, logging.INFO)
        self._logger.log(log_level, entry.to_json())
        
        # Store in log manager
        self._log_manager.add_entry(entry)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self,message: str, **kwargs) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """
        Log an exception.
        
        Args:
            message: Log message
            exc_info: Whether to include exception info
            **kwargs: Additional log data
        """
        import traceback
        
        exc_type, exc_value, exc_tb = sys.exc_info() if exc_info else (None, None, None)
        
        if exc_value:
            kwargs["exception"] = f"{exc_type.__name__}: {exc_value}"
            kwargs["stack_trace"] = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        self._log(LogLevel.ERROR, message, **kwargs)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        return json.dumps(log_data)


class LoggingManager:
    """
    Central logging manager.
    
    This manager creates and manages structured loggers, stores log entries,
    and provides query capabilities for log data.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the logging manager.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._loggers: Dict[str, StructuredLogger] = {}
        self._log_entries: List[LogEntry] = []
        self._lock = threading.Lock()
        self._max_entries = 10000
    
    def get_logger(self, name: str) -> StructuredLogger:
        """
        Get or create a structured logger.
        
        Args:
            name: Logger name
            
        Returns:
            StructuredLogger instance
        """
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = StructuredLogger(name, self._config, self)
            return self._loggers[name]
    
    def add_entry(self, entry: LogEntry) -> None:
        """
        Add a log entry to storage.
        
        Args:
            entry: Log entry to add
        """
        with self._lock:
            self._log_entries.append(entry)
            
            # Keep entries bounded
            if len(self._log_entries) > self._max_entries:
                self._log_entries = self._log_entries[-self._max_entries:]
    
    def get_entries(
        self,
        level: Optional[LogLevel] = None,
        component: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[LogEntry]:
        """
        Get log entries with optional filters.
        
        Args:
            level: Optional log level filter
            component: Optional component filter
            request_id: Optional request ID filter
            trace_id: Optional trace ID filter
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries
        """
        with self._lock:
            entries = self._log_entries
            
            if level:
                entries = [e for e in entries if e.level == level]
            
            if component:
                entries = [e for e in entries if e.component == component]
            
            if request_id:
                entries = [e for e in entries if e.request_id == request_id]
            
            if trace_id:
                entries = [e for e in entries if e.trace_id == trace_id]
            
            return entries[-limit:]
    
    def get_entries_by_trace(self, trace_id: str) -> List[LogEntry]:
        """
        Get all log entries for a specific trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            List of log entries
        """
        return self.get_entries(trace_id=trace_id, limit=self._max_entries)
    
    def get_error_entries(self, limit: int = 100) -> List[LogEntry]:
        """
        Get error log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of error log entries
        """
        return self.get_entries(level=LogLevel.ERROR, limit=limit)
    
    def log(self, event: ObservabilityEvent) -> None:
        """
        Log from an observability event.
        
        Args:
            event: Observability event
        """
        if event.event_type != EventType.LOG:
            return
        
        logger = self.get_logger(event.component.value if event.component else "observability")
        
        level = LogLevel(event.level.upper()) if event.level else LogLevel.INFO
        
        log_method = getattr(logger, level.value.lower())
        log_method(
            event.message or "",
            context=event.context,
            **event.data,
        )
    
    def clear_old_entries(self, retention_seconds: int = 3600) -> None:
        """
        Clear old log entries.
        
        Args:
            retention_seconds: Retention period in seconds
        """
        cutoff = datetime.utcnow().timestamp() - retention_seconds
        
        with self._lock:
            self._log_entries = [
                entry for entry in self._log_entries
                if entry.timestamp.timestamp() >= cutoff
            ]
    
    def get_log_summary(self) -> Dict[str, Any]:
        """
        Get a summary of log data.
        
        Returns:
            Log summary dictionary
        """
        with self._lock:
            level_counts = {}
            for entry in self._log_entries:
                level = entry.level.value
                level_counts[level] = level_counts.get(level, 0) + 1
            
            return {
                "total_entries": len(self._log_entries),
                "level_counts": level_counts,
                "loggers": list(self._loggers.keys()),
            }
    
    def shutdown(self) -> None:
        """Shutdown the logging manager."""
        # Close all handlers
        for logger in self._loggers.values():
            for handler in logger._logger.handlers:
                handler.close()
