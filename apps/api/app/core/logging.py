"""
Logging configuration and utilities for Wedi API.
"""
import json
import logging
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder

from app.core.config import settings


# Configure structlog for structured logging
def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Determine log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level
    )
    
    # Structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    # Add different renderers based on environment
    if settings.ENVIRONMENT == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        
    Returns:
        A bound logger instance
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Create logger instance
logger = structlog.get_logger()


class LogContext:
    """Context manager for adding temporary logging context."""
    
    def __init__(self, **kwargs):
        """Initialize with context variables."""
        self.context = kwargs
        self.logger = None
    
    def __enter__(self):
        """Enter context and bind variables."""
        self.logger = logger.bind(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and unbind variables."""
        if self.logger:
            for key in self.context:
                self.logger = self.logger.unbind(key)
        return False


@contextmanager
def log_context(**kwargs):
    """Context manager for temporary logging context.
    
    Usage:
        with log_context(user_id="123", organization_id="456"):
            logger.info("Processing payment")
    """
    bound_logger = logger.bind(**kwargs)
    try:
        yield bound_logger
    finally:
        for key in kwargs:
            bound_logger.unbind(key)


def log_execution(
    *,
    log_args: bool = True,
    log_result: bool = False,
    log_errors: bool = True,
    level: str = "info"
) -> Callable:
    """Decorator to log function execution.
    
    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log exceptions
        level: Log level to use
        
    Usage:
        @log_execution(log_result=True)
        async def process_payment(payment_id: str) -> PaymentResult:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = logger.bind(
                function=func.__name__,
                module=func.__module__
            )
            
            # Log function call
            log_data = {"event": f"calling_{func.__name__}"}
            if log_args:
                log_data["args"] = args
                log_data["kwargs"] = kwargs
            
            getattr(func_logger, level)(**log_data)
            
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful execution
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                success_data = {
                    "event": f"completed_{func.__name__}",
                    "execution_time": execution_time
                }
                
                if log_result:
                    success_data["result"] = result
                
                getattr(func_logger, level)(**success_data)
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                if log_errors:
                    func_logger.error(
                        f"error_in_{func.__name__}",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        execution_time=execution_time,
                        traceback=traceback.format_exc()
                    )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_logger = logger.bind(
                function=func.__name__,
                module=func.__module__
            )
            
            # Log function call
            log_data = {"event": f"calling_{func.__name__}"}
            if log_args:
                log_data["args"] = args
                log_data["kwargs"] = kwargs
            
            getattr(func_logger, level)(**log_data)
            
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful execution
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                success_data = {
                    "event": f"completed_{func.__name__}",
                    "execution_time": execution_time
                }
                
                if log_result:
                    success_data["result"] = result
                
                getattr(func_logger, level)(**success_data)
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                if log_errors:
                    func_logger.error(
                        f"error_in_{func.__name__}",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        execution_time=execution_time,
                        traceback=traceback.format_exc()
                    )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_database_query(query: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Log database query execution.
    
    Args:
        query: SQL query string
        params: Query parameters
    """
    logger.debug(
        "database_query",
        query=query,
        params=params,
        query_type=query.split()[0].upper() if query else "UNKNOWN"
    )


def log_external_api_call(
    service: str,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """Log external API calls.
    
    Args:
        service: Name of the external service
        method: HTTP method
        url: Request URL
        status_code: Response status code
        duration: Request duration in seconds
        error: Error message if failed
    """
    log_data = {
        "event": "external_api_call",
        "service": service,
        "method": method,
        "url": url
    }
    
    if status_code:
        log_data["status_code"] = status_code
    if duration:
        log_data["duration"] = duration
    if error:
        log_data["error"] = error
        logger.error(**log_data)
    else:
        logger.info(**log_data)


def log_payment_event(
    event_type: str,
    payment_order_id: str,
    organization_id: str,
    **kwargs
) -> None:
    """Log payment-related events.
    
    Args:
        event_type: Type of payment event
        payment_order_id: Payment order ID
        organization_id: Organization ID
        **kwargs: Additional event data
    """
    logger.info(
        "payment_event",
        event_type=event_type,
        payment_order_id=payment_order_id,
        organization_id=organization_id,
        **kwargs
    )


def log_agent_decision(
    agent_id: str,
    decision_type: str,
    decision: Dict[str, Any],
    confidence: float,
    execution_time: float,
    **kwargs
) -> None:
    """Log agent decisions for audit trail.
    
    Args:
        agent_id: Agent ID
        decision_type: Type of decision made
        decision: The actual decision data
        confidence: Confidence score (0-1)
        execution_time: Time taken to make decision
        **kwargs: Additional context
    """
    logger.info(
        "agent_decision",
        agent_id=agent_id,
        decision_type=decision_type,
        decision=decision,
        confidence=confidence,
        execution_time=execution_time,
        **kwargs
    )


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    **kwargs
) -> None:
    """Log security-related events.
    
    Args:
        event_type: Type of security event (login, logout, permission_denied, etc.)
        user_id: User ID if available
        ip_address: Client IP address
        success: Whether the operation was successful
        **kwargs: Additional context
    """
    log_level = "info" if success else "warning"
    getattr(logger, log_level)(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        success=success,
        **kwargs
    )


# Utility functions for common logging patterns

def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or mask sensitive data from logs.
    
    Args:
        data: Dictionary potentially containing sensitive data
        
    Returns:
        Sanitized dictionary safe for logging
    """
    sensitive_fields = {
        "password", "secret", "token", "api_key", "private_key",
        "card_number", "cvv", "account_number", "ssn", "tax_id"
    }
    
    sanitized = {}
    for key, value in data.items():
        if any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        else:
            sanitized[key] = value
    
    return sanitized


def get_request_id() -> Optional[str]:
    """Get current request ID from context if available."""
    # This would be implemented to get request ID from FastAPI context
    # For now, return None
    return None


def bind_request_context(
    request_id: str,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None
) -> structlog.BoundLogger:
    """Bind request context to logger.
    
    Args:
        request_id: Unique request ID
        user_id: User ID if authenticated
        organization_id: Organization ID if available
        
    Returns:
        Logger with bound context
    """
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    if organization_id:
        context["organization_id"] = organization_id
    
    return logger.bind(**context)


# Configure logging on module import
configure_logging() 