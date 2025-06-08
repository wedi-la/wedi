"""
User repository with authentication-specific queries.
"""
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuthProvider, Organization, OrganizationUser, User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for user-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(User)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Users don't have direct organization_id field."""
        return None
    
    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
        load_organizations: bool = False
    ) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: Email address to search for
            load_organizations: Whether to eagerly load organizations
            
        Returns:
            User or None if not found
        """
        query = select(User).where(User.email == email)
        
        if load_organizations:
            query = query.options(
                selectinload(User.organizations).selectinload(
                    OrganizationUser.organization
                )
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_auth_provider(
        self,
        db: AsyncSession,
        *,
        provider: AuthProvider,
        provider_id: str
    ) -> Optional[User]:
        """
        Get user by authentication provider and ID.
        
        Args:
            db: Database session
            provider: Authentication provider
            provider_id: Provider-specific user ID
            
        Returns:
            User or None if not found
        """
        query = select(User).where(
            and_(
                User.auth_provider == provider,
                User.auth_provider_id == provider_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_wallet_address(
        self,
        db: AsyncSession,
        *,
        wallet_address: str
    ) -> Optional[User]:
        """
        Get user by primary wallet address.
        
        Args:
            db: Database session
            wallet_address: Wallet address to search for
            
        Returns:
            User or None if not found
        """
        from app.models import Wallet
        
        query = (
            select(User)
            .join(Wallet, User.primary_wallet_id == Wallet.id)
            .where(Wallet.address == wallet_address.lower())
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_organizations(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        active_only: bool = True
    ) -> List[Organization]:
        """
        Get organizations that a user belongs to.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Only return active memberships
            
        Returns:
            List of organizations
        """
        query = (
            select(Organization)
            .join(OrganizationUser, Organization.id == OrganizationUser.organization_id)
            .where(OrganizationUser.user_id == user_id)
        )
        
        if active_only:
            query = query.where(OrganizationUser.is_active == True)
        
        query = query.order_by(Organization.name)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Search users by email or name.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching users
        """
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.name.ilike(f"%{query}%")
        )
        
        stmt = (
            select(User)
            .where(search_filter)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_last_login(
        self,
        db: AsyncSession,
        *,
        user_id: str
    ) -> User:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Updated user
        """
        from datetime import datetime
        
        user = await self.get_or_404(db, id=user_id)
        user.last_login_at = datetime.utcnow()
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def verify_email(
        self,
        db: AsyncSession,
        *,
        user_id: str
    ) -> User:
        """
        Mark user's email as verified.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Updated user
        """
        user = await self.get_or_404(db, id=user_id)
        user.email_verified = True
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def set_primary_wallet(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        wallet_id: str
    ) -> User:
        """
        Set user's primary wallet.
        
        Args:
            db: Database session
            user_id: User ID
            wallet_id: Wallet ID to set as primary
            
        Returns:
            Updated user
        """
        # Verify wallet exists and belongs to user
        from app.models import Wallet
        
        wallet_query = select(Wallet).where(
            and_(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
        )
        wallet_result = await db.execute(wallet_query)
        wallet = wallet_result.scalar_one_or_none()
        
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found or doesn't belong to user")
        
        # Update user's primary wallet
        user = await self.get_or_404(db, id=user_id)
        user.primary_wallet_id = wallet_id
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def get_by_organization(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[User]:
        """
        Get users in an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only return active members
            
        Returns:
            List of users in the organization
        """
        query = (
            select(User)
            .join(OrganizationUser, User.id == OrganizationUser.user_id)
            .where(OrganizationUser.organization_id == organization_id)
        )
        
        if active_only:
            query = query.where(OrganizationUser.is_active == True)
        
        query = query.order_by(User.name, User.email).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all()) 