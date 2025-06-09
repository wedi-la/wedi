"""
Custom exceptions for Wedi API with structured error handling.
"""
from typing import Any, Dict, Optional


class WediException(Exception):
    """Base exception for all Wedi-specific errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "WEDI_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


# Repository Exceptions

class RepositoryException(WediException):
    """Base exception for repository operations."""
    
    def __init__(self, message: str, code: str = "REPOSITORY_ERROR", **kwargs):
        super().__init__(message, code, status_code=500, **kwargs)


class NotFoundError(RepositoryException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class DuplicateError(RepositoryException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            code="DUPLICATE_RESOURCE",
            status_code=409,
            details={"resource": resource, "field": field, "value": str(value)}
        )


class ValidationError(WediException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, errors: Dict[str, Any]):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"validation_errors": errors}
        )


# Business Logic Exceptions

class BusinessRuleViolation(WediException):
    """Raised when a business rule is violated."""
    
    def __init__(self, message: str, rule: str, **kwargs):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=400,
            details={"rule": rule, **kwargs}
        )


class InsufficientPermissions(WediException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, action: str, resource: str, required_permission: str):
        super().__init__(
            message=f"Insufficient permissions to {action} {resource}",
            code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
            details={
                "action": action,
                "resource": resource,
                "required_permission": required_permission
            }
        )


class RateLimitExceeded(WediException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={
                "limit": limit,
                "window": window,
                "retry_after": retry_after
            }
        )


# Payment-specific Exceptions

class PaymentException(WediException):
    """Base exception for payment-related errors."""
    
    def __init__(self, message: str, code: str = "PAYMENT_ERROR", **kwargs):
        super().__init__(message, code, status_code=400, **kwargs)


class PaymentProviderError(PaymentException):
    """Raised when payment provider returns an error."""
    
    def __init__(self, provider: str, provider_error: str, provider_code: Optional[str] = None):
        super().__init__(
            message=f"Payment provider error: {provider_error}",
            code="PAYMENT_PROVIDER_ERROR",
            details={
                "provider": provider,
                "provider_error": provider_error,
                "provider_code": provider_code
            }
        )


class InsufficientFunds(PaymentException):
    """Raised when payment fails due to insufficient funds."""
    
    def __init__(self, amount: float, currency: str):
        super().__init__(
            message="Insufficient funds for payment",
            code="INSUFFICIENT_FUNDS",
            details={
                "amount": amount,
                "currency": currency
            }
        )


class PaymentLinkExpired(PaymentException):
    """Raised when attempting to use an expired payment link."""
    
    def __init__(self, link_id: str, expired_at: str):
        super().__init__(
            message="Payment link has expired",
            code="PAYMENT_LINK_EXPIRED",
            details={
                "link_id": link_id,
                "expired_at": expired_at
            }
        )


# Agent-specific Exceptions

class AgentException(WediException):
    """Base exception for agent-related errors."""
    
    def __init__(self, message: str, code: str = "AGENT_ERROR", **kwargs):
        super().__init__(message, code, status_code=500, **kwargs)


class AgentExecutionError(AgentException):
    """Raised when agent execution fails."""
    
    def __init__(self, agent_id: str, execution_error: str, decision_id: Optional[str] = None):
        super().__init__(
            message=f"Agent execution failed: {execution_error}",
            code="AGENT_EXECUTION_ERROR",
            details={
                "agent_id": agent_id,
                "execution_error": execution_error,
                "decision_id": decision_id
            }
        )


class AgentTimeoutError(AgentException):
    """Raised when agent execution times out."""
    
    def __init__(self, agent_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Agent execution timed out after {timeout_seconds} seconds",
            code="AGENT_TIMEOUT",
            details={
                "agent_id": agent_id,
                "timeout_seconds": timeout_seconds
            }
        )


# External Service Exceptions

class ExternalServiceError(WediException):
    """Base exception for external service errors."""
    
    def __init__(self, service: str, message: str, **kwargs):
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **kwargs}
        )


class BlockchainError(ExternalServiceError):
    """Raised when blockchain operations fail."""
    
    def __init__(self, chain: str, operation: str, error: str, tx_hash: Optional[str] = None):
        super().__init__(
            service=f"blockchain_{chain}",
            message=f"{operation} failed: {error}",
            chain=chain,
            operation=operation,
            tx_hash=tx_hash
        )


class KYCProviderError(ExternalServiceError):
    """Raised when KYC provider operations fail."""
    
    def __init__(self, provider: str, operation: str, error: str):
        super().__init__(
            service=f"kyc_{provider}",
            message=f"KYC {operation} failed: {error}",
            provider=provider,
            operation=operation
        ) 


class UnauthorizedException(WediException):
    """Raised when a user is not authorized to access a resource."""
    
    def __init__(self, message: str, code: str = "UNAUTHORIZED", **kwargs):
        super().__init__(message, code, status_code=401, **kwargs)


class ForbiddenException(WediException):
    """Raised when a user is not allowed to access a resource."""
    
    def __init__(self, message: str, code: str = "FORBIDDEN", **kwargs):
        super().__init__(message, code, status_code=403, **kwargs)


class BadRequestException(WediException):
    """Raised when a request is invalid."""

    def __init__(self, message: str, code: str = "BAD_REQUEST", **kwargs):
        super().__init__(message, code, status_code=400, **kwargs)


class NotFoundException(WediException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Any, **kwargs):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )
