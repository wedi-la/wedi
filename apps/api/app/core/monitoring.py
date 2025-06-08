"""
Performance monitoring and metrics utilities.
"""
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from app.core.logging import logger


class PerformanceTracker:
    """Track performance metrics for operations."""
    
    def __init__(self):
        """Initialize the tracker."""
        self.metrics: Dict[str, Dict[str, Any]] = {}
    
    def record_metric(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance metric.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "success_count": 0,
                "total_duration": 0.0,
                "min_duration": float("inf"),
                "max_duration": 0.0,
                "errors": 0
            }
        
        metric = self.metrics[operation]
        metric["count"] += 1
        metric["total_duration"] += duration
        metric["min_duration"] = min(metric["min_duration"], duration)
        metric["max_duration"] = max(metric["max_duration"], duration)
        
        if success:
            metric["success_count"] += 1
        else:
            metric["errors"] += 1
        
        # Log the metric
        logger.debug(
            "performance_metric",
            operation=operation,
            duration=duration,
            success=success,
            metadata=metadata
        )
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics.
        
        Args:
            operation: Specific operation or None for all
            
        Returns:
            Performance statistics
        """
        if operation:
            metric = self.metrics.get(operation, {})
            if metric:
                avg_duration = metric["total_duration"] / metric["count"]
                success_rate = metric["success_count"] / metric["count"]
                return {
                    "operation": operation,
                    "count": metric["count"],
                    "avg_duration": avg_duration,
                    "min_duration": metric["min_duration"],
                    "max_duration": metric["max_duration"],
                    "success_rate": success_rate,
                    "errors": metric["errors"]
                }
            return {}
        
        # Return all stats
        all_stats = {}
        for op, metric in self.metrics.items():
            if metric["count"] > 0:
                avg_duration = metric["total_duration"] / metric["count"]
                success_rate = metric["success_count"] / metric["count"]
                all_stats[op] = {
                    "count": metric["count"],
                    "avg_duration": avg_duration,
                    "min_duration": metric["min_duration"],
                    "max_duration": metric["max_duration"],
                    "success_rate": success_rate,
                    "errors": metric["errors"]
                }
        return all_stats


# Global performance tracker instance
performance_tracker = PerformanceTracker()


def track_performance(
    operation: Optional[str] = None,
    include_args: bool = False
) -> Callable:
    """Decorator to track function performance.
    
    Args:
        operation: Operation name (defaults to function name)
        include_args: Whether to include args in metadata
        
    Usage:
        @track_performance("user_creation")
        async def create_user(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            metadata = {}
            
            if include_args:
                metadata["args"] = str(args)
                metadata["kwargs"] = str(kwargs)
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                metadata["error"] = type(e).__name__
                raise
            finally:
                duration = time.time() - start_time
                performance_tracker.record_metric(
                    op_name,
                    duration,
                    success,
                    metadata
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            metadata = {}
            
            if include_args:
                metadata["args"] = str(args)
                metadata["kwargs"] = str(kwargs)
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                metadata["error"] = type(e).__name__
                raise
            finally:
                duration = time.time() - start_time
                performance_tracker.record_metric(
                    op_name,
                    duration,
                    success,
                    metadata
                )
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def track_operation(operation: str, **metadata):
    """Context manager to track operation performance.
    
    Args:
        operation: Operation name
        **metadata: Additional metadata to record
        
    Usage:
        with track_operation("database_query", query_type="select"):
            # perform operation
    """
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        performance_tracker.record_metric(
            operation,
            duration,
            success,
            metadata
        )


@asynccontextmanager
async def track_async_operation(operation: str, **metadata):
    """Async context manager to track operation performance.
    
    Args:
        operation: Operation name
        **metadata: Additional metadata to record
        
    Usage:
        async with track_async_operation("async_api_call", endpoint="/users"):
            # perform async operation
    """
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        performance_tracker.record_metric(
            operation,
            duration,
            success,
            metadata
        )


def log_slow_operation(threshold: float = 1.0) -> Callable:
    """Decorator to log slow operations.
    
    Args:
        threshold: Duration threshold in seconds
        
    Usage:
        @log_slow_operation(0.5)
        async def slow_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    logger.warning(
                        "slow_operation",
                        function=func.__name__,
                        module=func.__module__,
                        duration=duration,
                        threshold=threshold
                    )
                
                return result
            except Exception:
                duration = time.time() - start_time
                if duration > threshold:
                    logger.warning(
                        "slow_operation_failed",
                        function=func.__name__,
                        module=func.__module__,
                        duration=duration,
                        threshold=threshold
                    )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    logger.warning(
                        "slow_operation",
                        function=func.__name__,
                        module=func.__module__,
                        duration=duration,
                        threshold=threshold
                    )
                
                return result
            except Exception:
                duration = time.time() - start_time
                if duration > threshold:
                    logger.warning(
                        "slow_operation_failed",
                        function=func.__name__,
                        module=func.__module__,
                        duration=duration,
                        threshold=threshold
                    )
                raise
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RepositoryMetrics:
    """Track repository-specific metrics."""
    
    @staticmethod
    def track_query(model_name: str, operation: str, organization_id: Optional[str] = None):
        """Track a repository query.
        
        Args:
            model_name: Name of the model
            operation: Type of operation (create, read, update, delete)
            organization_id: Organization ID if applicable
        """
        logger.debug(
            "repository_operation",
            model=model_name,
            operation=operation,
            organization_id=organization_id,
            timestamp=datetime.utcnow().isoformat()
        )


# Helper function to get current performance stats
def get_performance_report() -> Dict[str, Any]:
    """Get a comprehensive performance report.
    
    Returns:
        Performance statistics for all tracked operations
    """
    stats = performance_tracker.get_stats()
    
    # Calculate overall statistics
    total_operations = sum(s["count"] for s in stats.values())
    total_errors = sum(s["errors"] for s in stats.values())
    
    if total_operations > 0:
        overall_success_rate = (total_operations - total_errors) / total_operations
    else:
        overall_success_rate = 1.0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall": {
            "total_operations": total_operations,
            "total_errors": total_errors,
            "success_rate": overall_success_rate
        },
        "operations": stats
    } 