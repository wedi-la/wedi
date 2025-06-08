"""
Dependency injection utilities for FastAPI endpoints.

This module provides common dependencies used across API endpoints,
including database sessions, authentication, and repository access.
"""
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import BackgroundTasks, Depends, HTTPException, Header, Request, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_session
from app.db.unit_of_work import UnitOfWork
from app.middleware.multi_tenancy import get_current_organization_id, current_organization_id
from app.models import User
from app.repositories.user import UserRepository

logger = get_logger(__name__)


# Repository dependencies
async def get_unit_of_work(
    db: AsyncSession = Depends(get_session)
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Get Unit of Work instance for managing transactions.
    
    Yields:
        UnitOfWork instance
    """
    async with UnitOfWork(db) as uow:
        yield uow


# Individual repository dependencies
async def get_user_repository(
    db: AsyncSession = Depends(get_session)
) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository()


async def get_organization_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get OrganizationRepository instance."""
    from app.repositories.organization import OrganizationRepository
    return OrganizationRepository()


async def get_agent_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get AgentRepository instance."""
    from app.repositories.agent import AgentRepository
    return AgentRepository()


async def get_payment_link_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get PaymentLinkRepository instance."""
    from app.repositories.payment_link import PaymentLinkRepository
    return PaymentLinkRepository()


async def get_payment_order_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get PaymentOrderRepository instance."""
    from app.repositories.payment_order import PaymentOrderRepository
    return PaymentOrderRepository()


async def get_customer_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get CustomerRepository instance."""
    from app.repositories.customer import CustomerRepository
    return CustomerRepository()


async def get_product_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get ProductRepository instance."""
    from app.repositories.product import ProductRepository
    return ProductRepository()


async def get_wallet_repository(
    db: AsyncSession = Depends(get_session)
):
    """Get WalletRepository instance."""
    from app.repositories.wallet import WalletRepository
    return WalletRepository()


# Authentication dependencies
async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    
    Args:
        authorization: Authorization header value
        db: Database session
        
    Returns:
        User if authenticated, None otherwise
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer {token}"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user_repo = UserRepository()
        user = await user_repo.get(db, id=user_id)
        
        if user is None:
            return None
        
        return user
        
    except (JWTError, ValueError):
        return None


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """
    Get current user from JWT token (required).
    
    Args:
        user: Optional user from token
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    # Add additional checks for user status if needed
    # For now, we consider all authenticated users as active
    
    return current_user


# Organization context dependencies
async def get_organization_id(
    organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Optional[str]:
    """
    Get organization ID from header or user context.
    
    Args:
        organization_id: Organization ID from header
        current_user: Current authenticated user
        
    Returns:
        Organization ID if available
    """
    # Try header first
    if organization_id:
        # TODO: Validate user has access to this organization
        current_organization_id.set(organization_id)
        return organization_id
    
    # Try context (may be set by middleware)
    context_org_id = get_current_organization_id()
    if context_org_id:
        return context_org_id
    
    # Try user's default organization
    if current_user:
        # TODO: Get user's default organization from memberships
        pass
    
    return None


async def require_organization_context(
    organization_id: Optional[str] = Depends(get_organization_id),
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Require organization context for multi-tenant operations.
    
    Args:
        organization_id: Organization ID from various sources
        current_user: Authenticated user
        
    Returns:
        Valid organization ID
        
    Raises:
        HTTPException: If no organization context
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
            headers={"X-Organization-ID": "Required"},
        )
    
    # TODO: Verify user has access to this organization
    # For now, we'll assume the organization ID is valid
    
    return organization_id


# Pagination dependencies
class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        max_limit: int = 100
    ):
        """
        Initialize pagination parameters.
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
            max_limit: Maximum allowed limit
        """
        self.skip = skip
        self.limit = min(limit, max_limit)


def get_pagination(
    skip: int = 0,
    limit: int = 20
) -> PaginationParams:
    """
    Get pagination parameters from query.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        
    Returns:
        Pagination parameters
    """
    return PaginationParams(skip=skip, limit=limit)


# Rate limiting dependencies
class RateLimitDep:
    """Rate limiting dependency."""
    
    def __init__(self, calls: int = 10, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of allowed calls
            period: Period in seconds
        """
        self.calls = calls
        self.period = period
    
    async def __call__(
        self,
        request: Request,
        user: Optional[User] = Depends(get_current_user_optional)
    ):
        """Check rate limit."""
        # TODO: Implement actual rate limiting with Redis
        # For now, just pass through
        return True


# Permission dependencies
async def check_organization_access(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> bool:
    """
    Check if user has access to organization.
    
    Args:
        organization_id: Organization to check
        current_user: Authenticated user
        db: Database session
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If no access
    """
    # TODO: Implement actual permission check
    # For now, just check if user is authenticated
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return True


# Query filter dependencies
class QueryFilters:
    """Common query filters from request."""
    
    def __init__(
        self,
        q: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
    ):
        """Initialize query filters."""
        self.q = q
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.created_after = created_after
        self.created_before = created_before
        self.updated_after = updated_after
        self.updated_before = updated_before


# Service dependencies
async def get_email_service():
    """Get email service instance."""
    # TODO: Implement actual email service
    pass


async def get_payment_service():
    """Get payment service instance."""
    # TODO: Implement actual payment service
    pass


# Background task dependencies
def get_background_tasks(background_tasks: BackgroundTasks) -> BackgroundTasks:
    """Get background tasks instance."""
    return background_tasks 