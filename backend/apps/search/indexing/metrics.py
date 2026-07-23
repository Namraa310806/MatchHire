"""
Indexing metrics.

This module provides metrics collection for indexing operations.
It tracks performance, failures, and synchronization status.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading

from apps.search.indexing.documents import EntityType

_shared_metrics: Optional["IndexingMetrics"] = None


class IndexingMetrics:
    """
    Metrics collector for indexing operations.
    
    This class tracks various metrics related to document indexing,
    synchronization, and provider performance.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = threading.Lock()
        
        # Operation metrics
        self._operation_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._operation_durations: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self._operation_failures: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Document metrics
        self._indexed_counts: Dict[str, int] = defaultdict(int)
        self._sync_counts: Dict[str, int] = defaultdict(int)
        self._failed_syncs: Dict[str, int] = defaultdict(int)
        
        # Queue metrics
        self._queue_sizes: Dict[str, int] = defaultdict(int)
        self._queue_processed: Dict[str, int] = defaultdict(int)
        
        # Provider metrics
        self._provider_latencies: Dict[str, list] = defaultdict(list)
        
        # Timestamps
        self._start_time = datetime.utcnow()
    
    def record_index_operation(
        self,
        operation: str,
        entity_type: str,
        duration: float,
        success: bool,
    ) -> None:
        """
        Record an index operation.
        
        Args:
            operation: Operation type (create, delete, rebuild, etc.)
            entity_type: Entity type
            duration: Operation duration in seconds
            success: Whether the operation succeeded
        """
        with self._lock:
            self._operation_counts[operation][entity_type] += 1
            self._operation_durations[operation][entity_type].append(duration)
            
            if not success:
                self._operation_failures[operation][entity_type] += 1
    
    def record_document_indexed(
        self,
        entity_type: str,
        count: int = 1,
    ) -> None:
        """
        Record documents indexed.
        
        Args:
            entity_type: Entity type
            count: Number of documents indexed
        """
        with self._lock:
            self._indexed_counts[entity_type] += count
    
    def record_document_synced(
        self,
        entity_type: str,
        success: bool = True,
    ) -> None:
        """
        Record a document synchronization.
        
        Args:
            entity_type: Entity type
            success: Whether the sync succeeded
        """
        with self._lock:
            self._sync_counts[entity_type] += 1
            if not success:
                self._failed_syncs[entity_type] += 1
    
    def record_queue_size(
        self,
        queue_name: str,
        size: int,
    ) -> None:
        """
        Record queue size.
        
        Args:
            queue_name: Name of the queue
            size: Current queue size
        """
        with self._lock:
            self._queue_sizes[queue_name] = size
    
    def record_queue_processed(
        self,
        queue_name: str,
        count: int = 1,
    ) -> None:
        """
        Record queue items processed.
        
        Args:
            queue_name: Name of the queue
            count: Number of items processed
        """
        with self._lock:
            self._queue_processed[queue_name] += count
    
    def record_provider_latency(
        self,
        provider_name: str,
        latency: float,
    ) -> None:
        """
        Record provider latency.
        
        Args:
            provider_name: Name of the provider
            latency: Latency in seconds
        """
        with self._lock:
            self._provider_latencies[provider_name].append(latency)
    
    def get_operation_metrics(
        self,
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get operation metrics.
        
        Args:
            operation: Optional operation filter
            entity_type: Optional entity type filter
            
        Returns:
            Metrics dictionary
        """
        with self._lock:
            if operation and entity_type:
                return {
                    "count": self._operation_counts[operation][entity_type],
                    "failures": self._operation_failures[operation][entity_type],
                    "avg_duration": self._calculate_average(
                        self._operation_durations[operation][entity_type]
                    ),
                    "success_rate": self._calculate_success_rate(
                        self._operation_counts[operation][entity_type],
                        self._operation_failures[operation][entity_type],
                    ),
                }
            elif operation:
                return {
                    entity_type: {
                        "count": self._operation_counts[operation][entity_type],
                        "failures": self._operation_failures[operation][entity_type],
                        "avg_duration": self._calculate_average(
                            self._operation_durations[operation][entity_type]
                        ),
                        "success_rate": self._calculate_success_rate(
                            self._operation_counts[operation][entity_type],
                            self._operation_failures[operation][entity_type],
                        ),
                    }
                    for entity_type in self._operation_counts[operation]
                }
            else:
                return {
                    op: {
                        et: {
                            "count": self._operation_counts[op][et],
                            "failures": self._operation_failures[op][et],
                            "avg_duration": self._calculate_average(
                                self._operation_durations[op][et]
                            ),
                            "success_rate": self._calculate_success_rate(
                                self._operation_counts[op][et],
                                self._operation_failures[op][et],
                            ),
                        }
                        for et in self._operation_counts[op]
                    }
                    for op in self._operation_counts
                }
    
    def get_document_metrics(
        self,
        entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get document metrics.
        
        Args:
            entity_type: Optional entity type filter
            
        Returns:
            Metrics dictionary
        """
        with self._lock:
            if entity_type:
                return {
                    "indexed": self._indexed_counts[entity_type],
                    "synced": self._sync_counts[entity_type],
                    "failed_syncs": self._failed_syncs[entity_type],
                    "sync_success_rate": self._calculate_success_rate(
                        self._sync_counts[entity_type],
                        self._failed_syncs[entity_type],
                    ),
                }
            else:
                return {
                    entity_type: {
                        "indexed": self._indexed_counts[entity_type],
                        "synced": self._sync_counts[entity_type],
                        "failed_syncs": self._failed_syncs[entity_type],
                        "sync_success_rate": self._calculate_success_rate(
                            self._sync_counts[entity_type],
                            self._failed_syncs[entity_type],
                        ),
                    }
                    for entity_type in self._indexed_counts
                }
    
    def get_queue_metrics(
        self,
        queue_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get queue metrics.
        
        Args:
            queue_name: Optional queue name filter
            
        Returns:
            Metrics dictionary
        """
        with self._lock:
            if queue_name:
                return {
                    "current_size": self._queue_sizes[queue_name],
                    "total_processed": self._queue_processed[queue_name],
                }
            else:
                return {
                    queue_name: {
                        "current_size": self._queue_sizes[queue_name],
                        "total_processed": self._queue_processed[queue_name],
                    }
                    for queue_name in self._queue_sizes
                }
    
    def get_provider_metrics(
        self,
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get provider metrics.
        
        Args:
            provider_name: Optional provider name filter
            
        Returns:
            Metrics dictionary
        """
        with self._lock:
            if provider_name:
                return {
                    "avg_latency": self._calculate_average(
                        self._provider_latencies[provider_name]
                    ),
                    "min_latency": min(self._provider_latencies[provider_name]) if self._provider_latencies[provider_name] else 0,
                    "max_latency": max(self._provider_latencies[provider_name]) if self._provider_latencies[provider_name] else 0,
                    "request_count": len(self._provider_latencies[provider_name]),
                }
            else:
                return {
                    provider_name: {
                        "avg_latency": self._calculate_average(
                            self._provider_latencies[provider_name]
                        ),
                        "min_latency": min(self._provider_latencies[provider_name]) if self._provider_latencies[provider_name] else 0,
                        "max_latency": max(self._provider_latencies[provider_name]) if self._provider_latencies[provider_name] else 0,
                        "request_count": len(self._provider_latencies[provider_name]),
                    }
                    for provider_name in self._provider_latencies
                }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        
        Returns:
            Summary dictionary
        """
        with self._lock:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            
            total_indexed = sum(self._indexed_counts.values())
            total_synced = sum(self._sync_counts.values())
            total_failed = sum(self._failed_syncs.values())
            
            return {
                "uptime_seconds": uptime,
                "total_documents_indexed": total_indexed,
                "total_documents_synced": total_synced,
                "total_sync_failures": total_failed,
                "overall_sync_success_rate": self._calculate_success_rate(
                    total_synced,
                    total_failed,
                ),
                "documents_per_second": total_indexed / uptime if uptime > 0 else 0,
                "entity_types": list(self._indexed_counts.keys()),
            }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._operation_counts.clear()
            self._operation_durations.clear()
            self._operation_failures.clear()
            self._indexed_counts.clear()
            self._sync_counts.clear()
            self._failed_syncs.clear()
            self._queue_sizes.clear()
            self._queue_processed.clear()
            self._provider_latencies.clear()
            self._start_time = datetime.utcnow()


def get_metrics() -> IndexingMetrics:
    """Return the shared indexing metrics collector for this process."""
    global _shared_metrics

    if _shared_metrics is None:
        _shared_metrics = IndexingMetrics()

    return _shared_metrics


def reset_metrics() -> None:
    """Reset the shared indexing metrics collector."""
    get_metrics().reset()
    
    def _calculate_average(self, values: list) -> float:
        """Calculate average of a list of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _calculate_success_rate(
        self,
        total: int,
        failures: int,
    ) -> float:
        """Calculate success rate."""
        if total == 0:
            return 1.0
        return (total - failures) / total
