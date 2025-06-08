"""
Multi-tenancy middleware for automatic organization filtering.
"""
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


# Context variable to store the current organization ID
current_organization_id: ContextVar[Optional[str]] = ContextVar(
    "current_organization_id", default=None
)


class MultiTenancyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and store organization context from requests.
    
    This middleware extracts the organization ID from the authenticated user's
    context and stores it in a context variable that can be accessed throughout
    the request lifecycle.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and extract organization context.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in the chain
            
        Returns:
            Response from the next middleware
        """
        # Initialize organization ID as None
        organization_id = None
        
        # Extract organization ID from the request
        # This can come from JWT claims, headers, or path parameters
        if hasattr(request.state, "user") and request.state.user:
            # Get organization ID from authenticated user
            # Assuming the user object has current_organization_id
            organization_id = getattr(request.state.user, "current_organization_id", None)
        elif "x-organization-id" in request.headers:
            # Alternative: Get from custom header (useful for API keys)
            organization_id = request.headers["x-organization-id"]
        
        # Set the organization ID in context
        token = current_organization_id.set(organization_id)
        
        try:
            # Process the request
            response = await call_next(request)
            return response
        finally:
            # Reset the context
            current_organization_id.reset(token)


def get_current_organization_id() -> Optional[str]:
    """
    Get the current organization ID from context.
    
    Returns:
        Organization ID or None if not in an organization context
    """
    return current_organization_id.get()


def require_organization_context() -> str:
    """
    Get the current organization ID or raise an error.
    
    Returns:
        Organization ID
        
    Raises:
        ValueError: If no organization context is available
    """
    org_id = get_current_organization_id()
    if not org_id:
        raise ValueError("No organization context available")
    return org_id


class TenantQueryFilter:
    """
    Helper class to apply tenant filtering to SQLAlchemy queries.
    
    This can be used as a mixin or utility class for repositories.
    """
    
    @staticmethod
    def apply_tenant_filter(query, model_class, organization_id: Optional[str] = None):
        """
        Apply tenant filter to a query if the model supports it.
        
        Args:
            query: SQLAlchemy query
            model_class: Model class to check for organization_id field
            organization_id: Organization ID to filter by (uses context if not provided)
            
        Returns:
            Filtered query
        """
        # Use provided organization ID or get from context
        if organization_id is None:
            organization_id = get_current_organization_id()
        
        # Apply filter if model has organization_id field and we have an org ID
        if organization_id and hasattr(model_class, "organization_id"):
            query = query.filter(model_class.organization_id == organization_id)
        
        return query


# Dependency to get organization ID in FastAPI routes
async def get_organization_id() -> Optional[str]:
    """
    FastAPI dependency to get current organization ID.
    
    Returns:
        Organization ID or None
        
    Example:
        @router.get("/items")
        async def get_items(
            organization_id: Optional[str] = Depends(get_organization_id)
        ):
            # Use organization_id in your logic
    """
    return get_current_organization_id()


async def require_organization_id() -> str:
    """
    FastAPI dependency to require organization context.
    
    Returns:
        Organization ID
        
    Raises:
        HTTPException: If no organization context
        
    Example:
        @router.get("/items")
        async def get_items(
            organization_id: str = Depends(require_organization_id)
        ):
            # Organization ID is guaranteed to be present
    """
    from fastapi import HTTPException, status
    
    org_id = get_current_organization_id()
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context required"
        )
    return org_id 