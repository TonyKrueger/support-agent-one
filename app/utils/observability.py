"""
Observability Utils

This module provides utilities for capturing metrics, detailed logging,
and performance tracking for document chunking and embedding operations.
"""

import time
import functools
from typing import Dict, Any, List, Callable, Optional, TypeVar, Union, Tuple
import json
import logging
from datetime import datetime

from app.utils.logger import get_logger, LogContext, log_with_context

# Type variable for decorated function return type
T = TypeVar('T')

# Configure logger
logger = get_logger(__name__)

# Metrics storage - in a production app, this would use a proper metrics system
# like Prometheus, StatsD, or CloudWatch
_metrics_store = {
    "counters": {},
    "gauges": {},
    "histograms": {},
}

class ChunkingMetrics:
    """Class for tracking chunking operation metrics"""
    
    @staticmethod
    def track_chunking_operation(
        operation: str,
        document_id: str,
        start_time: float,
        end_time: float,
        chunks_count: int,
        tokens_count: Optional[int] = None,
        strategy: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track metrics for a document chunking operation
        
        Args:
            operation: The operation type (create, update, delete)
            document_id: The document ID
            start_time: Start timestamp
            end_time: End timestamp
            chunks_count: Number of chunks generated
            tokens_count: Number of tokens processed (if available)
            strategy: Chunking strategy used
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        duration = end_time - start_time
        
        # Add to counters
        increment_counter(f"chunking.{operation}.count", 1)
        if not success:
            increment_counter(f"chunking.{operation}.error_count", 1)
        
        # Add to histograms
        add_to_histogram(f"chunking.{operation}.duration", duration)
        add_to_histogram(f"chunking.{operation}.chunks_count", chunks_count)
        if tokens_count:
            add_to_histogram(f"chunking.{operation}.tokens_count", tokens_count)
        
        # Log detailed metrics
        context = LogContext(
            component="chunking",
            operation=operation,
            extra={
                "document_id": document_id,
                "duration_ms": round(duration * 1000, 2),
                "chunks_count": chunks_count,
                "tokens_count": tokens_count,
                "strategy": strategy,
                "success": success
            }
        )
        
        if success:
            log_with_context("info", f"Chunking operation completed: {operation}", context, logger)
        else:
            context.extra["error"] = error
            log_with_context("error", f"Chunking operation failed: {operation}", context, logger)

class EmbeddingMetrics:
    """Class for tracking embedding operation metrics"""
    
    @staticmethod
    def track_embedding_generation(
        document_id: str,
        start_time: float,
        end_time: float,
        chunks_count: int,
        tokens_count: Optional[int] = None,
        model: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track metrics for an embedding generation operation
        
        Args:
            document_id: The document ID
            start_time: Start timestamp
            end_time: End timestamp
            chunks_count: Number of chunks embedded
            tokens_count: Number of tokens processed (if available)
            model: Embedding model used
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        duration = end_time - start_time
        
        # Add to counters
        increment_counter("embedding.generation.count", 1)
        if not success:
            increment_counter("embedding.generation.error_count", 1)
        
        # Add to histograms
        add_to_histogram("embedding.generation.duration", duration)
        add_to_histogram("embedding.generation.chunks_count", chunks_count)
        if tokens_count:
            add_to_histogram("embedding.generation.tokens_count", tokens_count)
            # Calculate tokens per second for performance tracking
            if duration > 0:
                tokens_per_second = tokens_count / duration
                add_to_histogram("embedding.generation.tokens_per_second", tokens_per_second)
        
        # Log detailed metrics
        context = LogContext(
            component="embedding",
            operation="generation",
            extra={
                "document_id": document_id,
                "duration_ms": round(duration * 1000, 2),
                "chunks_count": chunks_count,
                "tokens_count": tokens_count,
                "model": model,
                "success": success
            }
        )
        
        if success:
            log_with_context("info", "Embedding generation completed", context, logger)
        else:
            context.extra["error"] = error
            log_with_context("error", "Embedding generation failed", context, logger)

class SearchMetrics:
    """Class for tracking search operation metrics"""
    
    @staticmethod
    def track_search_operation(
        query_text: str,
        start_time: float,
        end_time: float,
        results_count: int,
        strategy: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track metrics for a search operation
        
        Args:
            query_text: The search query
            start_time: Start timestamp
            end_time: End timestamp
            results_count: Number of results returned
            strategy: Search strategy used
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        duration = end_time - start_time
        
        # Add to counters
        increment_counter(f"search.{strategy}.count", 1)
        if not success:
            increment_counter(f"search.{strategy}.error_count", 1)
        
        # Add to histograms
        add_to_histogram(f"search.{strategy}.duration", duration)
        add_to_histogram(f"search.{strategy}.results_count", results_count)
        
        # Log detailed metrics
        context = LogContext(
            component="search",
            operation=strategy,
            extra={
                "duration_ms": round(duration * 1000, 2),
                "results_count": results_count,
                "query_length": len(query_text),
                "success": success
            }
        )
        
        if success:
            log_with_context("info", f"Search operation completed: {strategy}", context, logger)
        else:
            context.extra["error"] = error
            log_with_context("error", f"Search operation failed: {strategy}", context, logger)

# ----- Decorator for performance tracking -----

def track_performance(component: str, operation: str) -> Callable:
    """
    Decorator for tracking function performance
    
    Args:
        component: Component name (e.g., 'chunking', 'embedding')
        operation: Operation name (e.g., 'create', 'search')
        
    Returns:
        Decorated function with performance tracking
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            
            # Extract document_id from args or kwargs if present
            document_id = None
            if len(args) > 1 and isinstance(args[1], str):
                document_id = args[1]
            elif "document_id" in kwargs:
                document_id = kwargs["document_id"]
            elif "doc_id" in kwargs:
                document_id = kwargs["doc_id"]
            
            try:
                # Call the original function
                result = func(*args, **kwargs)
                
                # Record successful execution
                end_time = time.time()
                
                # Create context for logging
                context_data = {
                    "duration_ms": round((end_time - start_time) * 1000, 2),
                    "success": True
                }
                
                if document_id:
                    context_data["document_id"] = document_id
                
                # Add result stats if available
                if hasattr(result, "__len__"):
                    try:
                        context_data["result_size"] = len(result)
                    except (TypeError, ValueError):
                        pass
                
                context = LogContext(
                    component=component,
                    operation=operation,
                    extra=context_data
                )
                
                # Log performance data
                log_with_context("info", f"Operation completed: {component}.{operation}", context, logger)
                
                # Update metrics
                increment_counter(f"{component}.{operation}.count", 1)
                add_to_histogram(f"{component}.{operation}.duration", end_time - start_time)
                
                return result
                
            except Exception as e:
                # Record failed execution
                end_time = time.time()
                
                # Log error with context
                context = LogContext(
                    component=component,
                    operation=operation,
                    extra={
                        "duration_ms": round((end_time - start_time) * 1000, 2),
                        "success": False,
                        "error": str(e),
                        "document_id": document_id
                    }
                )
                
                log_with_context("error", f"Operation failed: {component}.{operation}", context, logger)
                
                # Update error metrics
                increment_counter(f"{component}.{operation}.error_count", 1)
                add_to_histogram(f"{component}.{operation}.error_duration", end_time - start_time)
                
                # Re-raise the exception
                raise
                
        return wrapper
    return decorator

# ----- Pipeline Stage Tracking -----

class PipelineTracker:
    """Class for tracking document processing pipeline stages"""
    
    @staticmethod
    def start_pipeline(document_id: str, pipeline_name: str = "document_processing") -> Dict[str, Any]:
        """
        Start tracking a pipeline execution
        
        Args:
            document_id: The document ID
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline context dictionary
        """
        pipeline_id = f"{int(time.time())}-{document_id}"
        
        pipeline_context = {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "document_id": document_id,
            "start_time": time.time(),
            "stages": {},
            "current_stage": None
        }
        
        # Log pipeline start
        context = LogContext(
            component="pipeline",
            operation="start",
            extra={
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "document_id": document_id
            }
        )
        
        log_with_context("info", f"Pipeline started: {pipeline_name}", context, logger)
        
        return pipeline_context
    
    @staticmethod
    def start_stage(pipeline_context: Dict[str, Any], stage_name: str) -> None:
        """
        Start tracking a pipeline stage
        
        Args:
            pipeline_context: The pipeline context dictionary
            stage_name: Name of the stage
        """
        # Record stage start
        pipeline_context["stages"][stage_name] = {
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": "in_progress"
        }
        
        pipeline_context["current_stage"] = stage_name
        
        # Log stage start
        context = LogContext(
            component="pipeline_stage",
            operation="start",
            extra={
                "pipeline_id": pipeline_context["pipeline_id"],
                "pipeline_name": pipeline_context["pipeline_name"],
                "document_id": pipeline_context["document_id"],
                "stage_name": stage_name
            }
        )
        
        log_with_context("info", f"Pipeline stage started: {stage_name}", context, logger)
    
    @staticmethod
    def end_stage(
        pipeline_context: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End tracking a pipeline stage
        
        Args:
            pipeline_context: The pipeline context dictionary
            success: Whether the stage succeeded
            error: Error message if stage failed
            metrics: Additional metrics to log
        """
        if not pipeline_context["current_stage"]:
            logger.warning("Attempting to end a stage when no stage is in progress")
            return
        
        stage_name = pipeline_context["current_stage"]
        stage_data = pipeline_context["stages"][stage_name]
        
        # Record stage end
        end_time = time.time()
        stage_data["end_time"] = end_time
        stage_data["duration"] = end_time - stage_data["start_time"]
        stage_data["status"] = "completed" if success else "failed"
        
        if error:
            stage_data["error"] = error
        
        if metrics:
            stage_data["metrics"] = metrics
        
        # Update metrics
        add_to_histogram(f"pipeline.stage.{stage_name}.duration", stage_data["duration"])
        increment_counter(f"pipeline.stage.{stage_name}.count", 1)
        
        if not success:
            increment_counter(f"pipeline.stage.{stage_name}.error_count", 1)
        
        # Log stage end
        extra_data = {
            "pipeline_id": pipeline_context["pipeline_id"],
            "pipeline_name": pipeline_context["pipeline_name"],
            "document_id": pipeline_context["document_id"],
            "stage_name": stage_name,
            "duration_ms": round(stage_data["duration"] * 1000, 2),
            "status": stage_data["status"]
        }
        
        if error:
            extra_data["error"] = error
        
        if metrics:
            extra_data.update(metrics)
        
        context = LogContext(
            component="pipeline_stage",
            operation="end",
            extra=extra_data
        )
        
        log_level = "info" if success else "error"
        log_message = f"Pipeline stage {'completed' if success else 'failed'}: {stage_name}"
        log_with_context(log_level, log_message, context, logger)
        
        # Clear current stage
        pipeline_context["current_stage"] = None
    
    @staticmethod
    def end_pipeline(
        pipeline_context: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        End tracking a pipeline execution
        
        Args:
            pipeline_context: The pipeline context dictionary
            success: Whether the pipeline succeeded
            error: Error message if pipeline failed
        """
        # Ensure any in-progress stage is ended
        if pipeline_context["current_stage"]:
            PipelineTracker.end_stage(
                pipeline_context, 
                success=False, 
                error="Stage not properly ended before pipeline end"
            )
        
        # Record pipeline end
        end_time = time.time()
        duration = end_time - pipeline_context["start_time"]
        
        # Calculate total pipeline duration and success
        pipeline_context["end_time"] = end_time
        pipeline_context["duration"] = duration
        pipeline_context["status"] = "completed" if success else "failed"
        
        if error:
            pipeline_context["error"] = error
        
        # Update metrics
        pipeline_name = pipeline_context["pipeline_name"]
        add_to_histogram(f"pipeline.{pipeline_name}.duration", duration)
        increment_counter(f"pipeline.{pipeline_name}.count", 1)
        
        if not success:
            increment_counter(f"pipeline.{pipeline_name}.error_count", 1)
        
        # Log pipeline end
        extra_data = {
            "pipeline_id": pipeline_context["pipeline_id"],
            "pipeline_name": pipeline_context["pipeline_name"],
            "document_id": pipeline_context["document_id"],
            "duration_ms": round(duration * 1000, 2),
            "status": pipeline_context["status"],
            "stages_count": len(pipeline_context["stages"])
        }
        
        if error:
            extra_data["error"] = error
        
        context = LogContext(
            component="pipeline",
            operation="end",
            extra=extra_data
        )
        
        log_level = "info" if success else "error"
        log_message = f"Pipeline {'completed' if success else 'failed'}: {pipeline_name}"
        log_with_context(log_level, log_message, context, logger)

# ----- Metrics Storage Functions -----

def increment_counter(name: str, value: int = 1) -> None:
    """
    Increment a counter metric
    
    Args:
        name: Metric name
        value: Value to increment by
    """
    if name not in _metrics_store["counters"]:
        _metrics_store["counters"][name] = 0
    
    _metrics_store["counters"][name] += value

def set_gauge(name: str, value: float) -> None:
    """
    Set a gauge metric
    
    Args:
        name: Metric name
        value: Value to set
    """
    _metrics_store["gauges"][name] = value

def add_to_histogram(name: str, value: float) -> None:
    """
    Add a value to a histogram metric
    
    Args:
        name: Metric name
        value: Value to add
    """
    if name not in _metrics_store["histograms"]:
        _metrics_store["histograms"][name] = []
    
    _metrics_store["histograms"][name].append(value)

def get_metrics() -> Dict[str, Any]:
    """
    Get all current metrics
    
    Returns:
        Dictionary of all metrics
    """
    # Process histograms to calculate statistics
    processed_histograms = {}
    
    for name, values in _metrics_store["histograms"].items():
        if not values:
            continue
            
        # Calculate basic statistics
        processed_histograms[name] = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }
    
    return {
        "counters": _metrics_store["counters"].copy(),
        "gauges": _metrics_store["gauges"].copy(),
        "histograms": processed_histograms,
        "timestamp": datetime.now().isoformat()
    }

def reset_metrics() -> None:
    """Reset all metrics"""
    _metrics_store["counters"] = {}
    _metrics_store["gauges"] = {}
    _metrics_store["histograms"] = {} 