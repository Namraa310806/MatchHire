"""
Ranking Pipeline Infrastructure.

This module provides a modular pipeline for combining multiple ranking signals
into a unified score. The pipeline supports score normalization, weighted fusion,
and extensible stages for different ranking strategies.
"""

from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class NormalizationMethod(Enum):
    """Methods for normalizing scores."""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    LOGISTIC = "logistic"
    TANH = "tanh"
    SOFTMAX = "softmax"
    BINARY = "binary"
    NONE = "none"


@dataclass
class PipelineConfig:
    """Configuration for the ranking pipeline."""
    
    enable_parallel_scoring: bool = True
    max_parallel_workers: int = 4
    enable_early_termination: bool = False
    early_termination_threshold: float = 0.95
    max_scoring_depth: int = 1000
    enable_lazy_scoring: bool = False
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    enable_diagnostics: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_parallel_scoring": self.enable_parallel_scoring,
            "max_parallel_workers": self.max_parallel_workers,
            "enable_early_termination": self.enable_early_termination,
            "early_termination_threshold": self.early_termination_threshold,
            "max_scoring_depth": self.max_scoring_depth,
            "enable_lazy_scoring": self.enable_lazy_scoring,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_diagnostics": self.enable_diagnostics,
        }


@dataclass
class PipelineStage:
    """
    A single stage in the ranking pipeline.
    
    Each stage can apply multiple signals with specific weights.
    """
    
    name: str
    signals: List[str] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    normalization: NormalizationMethod = NormalizationMethod.MIN_MAX
    enabled: bool = True
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "signals": self.signals,
            "weights": self.weights,
            "normalization": self.normalization.value,
            "enabled": self.enabled,
        }
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """
        Check if this stage should execute based on conditions.
        
        Args:
            context: Search context
            
        Returns:
            True if stage should execute
        """
        if not self.enabled:
            return False
        if self.condition is not None:
            return self.condition(context)
        return True


class ScoreNormalizer:
    """
    Normalizes scores across different ranges to a common scale [0, 1].
    """
    
    @staticmethod
    def min_max(
        scores: List[float],
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> List[float]:
        """
        Normalize scores using min-max normalization.
        
        Args:
            scores: List of scores to normalize
            min_val: Minimum value (uses actual min if None)
            max_val: Maximum value (uses actual max if None)
            
        Returns:
            Normalized scores in [0, 1]
        """
        if not scores:
            return []
        
        actual_min = min_val if min_val is not None else min(scores)
        actual_max = max_val if max_val is not None else max(scores)
        
        if actual_max == actual_min:
            return [0.5] * len(scores)
        
        return [
            (score - actual_min) / (actual_max - actual_min)
            for score in scores
        ]
    
    @staticmethod
    def z_score(scores: List[float]) -> List[float]:
        """
        Normalize scores using z-score normalization.
        
        Args:
            scores: List of scores to normalize
            
        Returns:
            Z-scores (mean=0, std=1)
        """
        if not scores:
            return []
        
        import statistics
        
        mean = statistics.mean(scores)
        stdev = statistics.stdev(scores) if len(scores) > 1 else 1.0
        
        if stdev == 0:
            return [0.0] * len(scores)
        
        return [(score - mean) / stdev for score in scores]
    
    @staticmethod
    def logistic(scores: List[float], k: float = 1.0) -> List[float]:
        """
        Normalize scores using logistic function.
        
        Args:
            scores: List of scores to normalize
            k: Steepness parameter
            
        Returns:
            Normalized scores in [0, 1]
        """
        import math
        
        return [
            1.0 / (1.0 + math.exp(-k * score))
            for score in scores
        ]
    
    @staticmethod
    def tanh(scores: List[float]) -> List[float]:
        """
        Normalize scores using tanh function.
        
        Args:
            scores: List of scores to normalize
            
        Returns:
            Normalized scores in [-1, 1], shifted to [0, 1]
        """
        import math
        
        tanh_scores = [math.tanh(score) for score in scores]
        # Shift from [-1, 1] to [0, 1]
        return [(score + 1.0) / 2.0 for score in tanh_scores]
    
    @staticmethod
    def softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
        """
        Normalize scores using softmax function.
        
        Args:
            scores: List of scores to normalize
            temperature: Temperature parameter
            
        Returns:
            Probability distribution summing to 1
        """
        import math
        
        exp_scores = [math.exp(score / temperature) for score in scores]
        sum_exp = sum(exp_scores)
        
        if sum_exp == 0:
            return [1.0 / len(scores)] * len(scores)
        
        return [exp_score / sum_exp for exp_score in exp_scores]
    
    @staticmethod
    def binary(scores: List[float], threshold: float = 0.5) -> List[float]:
        """
        Normalize scores to binary values.
        
        Args:
            scores: List of scores to normalize
            threshold: Threshold for binary classification
            
        Returns:
            Binary scores (0 or 1)
        """
        return [1.0 if score >= threshold else 0.0 for score in scores]
    
    @staticmethod
    def normalize(
        scores: List[float],
        method: NormalizationMethod,
        **kwargs
    ) -> List[float]:
        """
        Normalize scores using the specified method.
        
        Args:
            scores: List of scores to normalize
            method: Normalization method to use
            **kwargs: Method-specific parameters
            
        Returns:
            Normalized scores
        """
        if method == NormalizationMethod.MIN_MAX:
            return ScoreNormalizer.min_max(scores, **kwargs)
        elif method == NormalizationMethod.Z_SCORE:
            return ScoreNormalizer.z_score(scores)
        elif method == NormalizationMethod.LOGISTIC:
            return ScoreNormalizer.logistic(scores, **kwargs)
        elif method == NormalizationMethod.TANH:
            return ScoreNormalizer.tanh(scores)
        elif method == NormalizationMethod.SOFTMAX:
            return ScoreNormalizer.softmax(scores, **kwargs)
        elif method == NormalizationMethod.BINARY:
            return ScoreNormalizer.binary(scores, **kwargs)
        else:
            return scores


@dataclass
class PipelineDiagnostics:
    """Diagnostics information for pipeline execution."""
    
    total_time_ms: float = 0.0
    stage_times_ms: Dict[str, float] = field(default_factory=dict)
    signal_times_ms: Dict[str, float] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    early_termination_triggered: bool = False
    parallel_workers_used: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_time_ms": self.total_time_ms,
            "stage_times_ms": self.stage_times_ms,
            "signal_times_ms": self.signal_times_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "early_termination_triggered": self.early_termination_triggered,
            "parallel_workers_used": self.parallel_workers_used,
            "errors": self.errors,
        }


class RankingPipeline:
    """
    Modular ranking pipeline for combining multiple scoring signals.
    
    The pipeline executes stages in sequence, applying signals with weights
    and normalization to produce a final ranking score.
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        signal_registry: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the ranking pipeline.
        
        Args:
            config: Pipeline configuration
            signal_registry: Registry of available signals
        """
        self._config = config or PipelineConfig()
        self._signal_registry = signal_registry or {}
        self._stages: List[PipelineStage] = []
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        self._diagnostics = PipelineDiagnostics()
    
    def add_stage(self, stage: PipelineStage) -> "RankingPipeline":
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Pipeline stage to add
            
        Returns:
            Self for method chaining
        """
        self._stages.append(stage)
        return self
    
    def register_signal(self, name: str, signal: Any) -> None:
        """
        Register a scoring signal.
        
        Args:
            name: Signal name
            signal: Signal instance
        """
        self._signal_registry[name] = signal
    
    def get_signal(self, name: str) -> Optional[Any]:
        """
        Get a registered signal.
        
        Args:
            name: Signal name
            
        Returns:
            Signal instance or None
        """
        return self._signal_registry.get(name)
    
    def execute(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], PipelineDiagnostics]:
        """
        Execute the ranking pipeline on search results.
        
        Args:
            results: Search results to rank
            context: Search context
            
        Returns:
            Tuple of (ranked results, diagnostics)
        """
        start_time = time.time()
        self._diagnostics = PipelineDiagnostics()
        
        if not results:
            return results, self._diagnostics
        
        # Apply max scoring depth
        if self._config.max_scoring_depth > 0:
            results = results[:self._config.max_scoring_depth]
        
        # Initialize score tracking
        for result in results:
            result.setdefault("_ranking_signals", {})
            result.setdefault("_ranking_score", 0.0)
        
        # Execute each stage
        for stage in self._stages:
            if not stage.should_execute(context):
                continue
            
            stage_start = time.time()
            
            try:
                self._execute_stage(stage, results, context)
            except Exception as e:
                self._diagnostics.errors.append(
                    f"Stage '{stage.name}' failed: {str(e)}"
                )
            
            stage_time = (time.time() - stage_start) * 1000
            self._diagnostics.stage_times_ms[stage.name] = stage_time
        
        # Sort results by final score
        results.sort(key=lambda x: x.get("_ranking_score", 0.0), reverse=True)
        
        self._diagnostics.total_time_ms = (time.time() - start_time) * 1000
        
        return results, self._diagnostics
    
    def _execute_stage(
        self,
        stage: PipelineStage,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> None:
        """
        Execute a single pipeline stage.
        
        Args:
            stage: Pipeline stage to execute
            results: Search results
            context: Search context
        """
        if self._config.enable_parallel_scoring and len(stage.signals) > 1:
            self._execute_stage_parallel(stage, results, context)
        else:
            self._execute_stage_sequential(stage, results, context)
    
    def _execute_stage_sequential(
        self,
        stage: PipelineStage,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> None:
        """
        Execute stage sequentially.
        
        Args:
            stage: Pipeline stage to execute
            results: Search results
            context: Search context
        """
        for signal_name in stage.signals:
            signal = self.get_signal(signal_name)
            if signal is None:
                continue
            
            signal_start = time.time()
            
            # Calculate signal scores
            signal_scores = self._calculate_signal_scores(
                signal, results, context
            )
            
            # Normalize scores
            normalized_scores = ScoreNormalizer.normalize(
                signal_scores,
                stage.normalization,
            )
            
            # Apply weights and accumulate
            weight = stage.weights.get(signal_name, 1.0)
            for i, result in enumerate(results):
                signal_score = normalized_scores[i] * weight
                result["_ranking_signals"][signal_name] = signal_score
                result["_ranking_score"] += signal_score
            
            signal_time = (time.time() - signal_start) * 1000
            self._diagnostics.signal_times_ms[signal_name] = signal_time
    
    def _execute_stage_parallel(
        self,
        stage: PipelineStage,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> None:
        """
        Execute stage in parallel using thread pool.
        
        Args:
            stage: Pipeline stage to execute
            results: Search results
            context: Search context
        """
        with ThreadPoolExecutor(
            max_workers=self._config.max_parallel_workers
        ) as executor:
            futures = {}
            
            for signal_name in stage.signals:
                signal = self.get_signal(signal_name)
                if signal is None:
                    continue
                
                future = executor.submit(
                    self._calculate_signal_scores,
                    signal,
                    results,
                    context,
                )
                futures[future] = signal_name
            
            # Collect results
            signal_scores_map = {}
            for future in as_completed(futures):
                signal_name = futures[future]
                try:
                    signal_scores_map[signal_name] = future.result()
                except Exception as e:
                    self._diagnostics.errors.append(
                        f"Signal '{signal_name}' failed: {str(e)}"
                    )
                    signal_scores_map[signal_name] = [0.0] * len(results)
            
            self._diagnostics.parallel_workers_used = len(futures)
        
        # Apply normalized scores with weights
        for signal_name, scores in signal_scores_map.items():
            signal_start = time.time()
            
            normalized_scores = ScoreNormalizer.normalize(
                scores,
                stage.normalization,
            )
            
            weight = stage.weights.get(signal_name, 1.0)
            for i, result in enumerate(results):
                signal_score = normalized_scores[i] * weight
                result["_ranking_signals"][signal_name] = signal_score
                result["_ranking_score"] += signal_score
            
            signal_time = (time.time() - signal_start) * 1000
            self._diagnostics.signal_times_ms[signal_name] = signal_time
    
    def _calculate_signal_scores(
        self,
        signal: Any,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[float]:
        """
        Calculate scores for a signal.
        
        Args:
            signal: Signal instance
            results: Search results
            context: Search context
            
        Returns:
            List of scores for each result
        """
        # Check cache
        cache_key = self._get_cache_key(signal, results, context)
        if self._config.cache_enabled and cache_key in self._cache:
            self._diagnostics.cache_hits += 1
            return self._cache[cache_key]
        
        self._diagnostics.cache_misses += 1
        
        # Calculate scores
        scores = []
        for result in results:
            try:
                score = signal.score(result, context)
                scores.append(float(score))
            except Exception:
                scores.append(0.0)
        
        # Cache results
        if self._config.cache_enabled:
            with self._cache_lock:
                self._cache[cache_key] = scores
        
        return scores
    
    def _get_cache_key(
        self,
        signal: Any,
        results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        Generate a cache key for signal scoring.
        
        Args:
            signal: Signal instance
            results: Search results
            context: Search context
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Use signal name and result IDs for cache key
        signal_name = signal.__class__.__name__
        result_ids = [r.get("id", "") for r in results]
        query = context.get("query", "")
        
        key_data = {
            "signal": signal_name,
            "ids": result_ids,
            "query": query,
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear the scoring cache."""
        with self._cache_lock:
            self._cache.clear()
    
    def get_diagnostics(self) -> PipelineDiagnostics:
        """
        Get pipeline diagnostics.
        
        Returns:
            Pipeline diagnostics
        """
        return self._diagnostics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary representation."""
        return {
            "config": self._config.to_dict(),
            "stages": [stage.to_dict() for stage in self._stages],
            "registered_signals": list(self._signal_registry.keys()),
        }
