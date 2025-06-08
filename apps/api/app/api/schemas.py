"""
API-specific schemas for request/response handling.

This module contains schemas that are specific to API endpoints,
complementing the database schemas in app.schemas.
"""
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Generic type for response data
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response for list endpoints."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")
    has_more: bool = Field(..., description="Whether more items exist")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        skip: int,
        limit: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""
    
    success: bool = Field(True, description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Human-readable message")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    @classmethod
    def success_response(
        cls,
        data: T = None,
        message: str = None,
        request_id: str = None
    ) -> "ApiResponse[T]":
        """Create a success response."""
        return cls(
            success=True,
            data=data,
            message=message,
            request_id=request_id
        )
    
    @classmethod
    def error_response(
        cls,
        message: str,
        request_id: str = None
    ) -> "ApiResponse[T]":
        """Create an error response."""
        return cls(
            success=False,
            message=message,
            request_id=request_id
        )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    
    detail: str = Field("Validation error", description="General error message")
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class HTTPError(BaseModel):
    """Standard HTTP error response."""
    
    detail: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


# Authentication response schemas
class TokenResponse(BaseModel):
    """JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LoginResponse(TokenResponse):
    """Login response with user info."""
    
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    organizations: List[Dict[str, Any]] = Field(..., description="User's organizations")


# Common request schemas
class BulkOperationRequest(BaseModel):
    """Request for bulk operations."""
    
    ids: List[str] = Field(..., description="List of IDs to operate on", min_items=1, max_items=100)
    operation: str = Field(..., description="Operation to perform")
    params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    
    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details for failed items")


# Status response schemas
class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(default_factory=dict, description="Status of dependent services")


class StatusResponse(BaseModel):
    """Detailed status response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    database_connected: bool = Field(..., description="Database connection status")
    event_bus_connected: bool = Field(..., description="Event bus connection status")
    features: Dict[str, bool] = Field(..., description="Feature flags") 