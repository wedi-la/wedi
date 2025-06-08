"""
API-specific exceptions.

This module contains exceptions that are commonly raised in API endpoints.
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base API exception with additional context."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize API exception."""
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.context = context or {}


class UnauthorizedException(APIException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required"):
        """Initialize unauthorized exception."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(APIException):
    """Raised when user lacks permissions."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        """Initialize forbidden exception."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class NotFoundException(APIException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, resource_id: str):
        """Initialize not found exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID {resource_id} not found",
            error_code="NOT_FOUND",
            context={"resource": resource, "resource_id": resource_id}
        )


class ConflictException(APIException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        """Initialize conflict exception."""
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
            context=context
        )


class BadRequestException(APIException):
    """Raised for invalid requests."""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        """Initialize bad request exception."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
            context=context
        )


class RateLimitException(APIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        """Initialize rate limit exception."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers,
            error_code="RATE_LIMIT_EXCEEDED",
            context={"retry_after": retry_after}
        )


class PaymentRequiredException(APIException):
    """Raised when payment is required for an action."""
    
    def __init__(self, detail: str = "Payment required"):
        """Initialize payment required exception."""
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            error_code="PAYMENT_REQUIRED"
        )


class ServiceUnavailableException(APIException):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None
    ):
        """Initialize service unavailable exception."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
            
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers,
            error_code="SERVICE_UNAVAILABLE",
            context={"retry_after": retry_after}
        ) 