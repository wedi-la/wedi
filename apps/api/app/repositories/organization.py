"""
Organization repository with membership management.
"""
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Organization,
    OrganizationUser,
    PaymentLink,
    PaymentOrder,
    User,
    UserRole,
)
from app.repositories.base import BaseRepository, NotFoundError
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
    OrganizationUpdate,
)


class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    """Repository for organization-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Organization)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Organizations filter by their own ID."""
        return "id"
    
    async def get_by_slug(
        self,
        db: AsyncSession,
        *,
        slug: str
    ) -> Optional[Organization]:
        """
        Get organization by slug.
        
        Args:
            db: Database session
            slug: Organization slug
            
        Returns:
            Organization or None if not found
        """
        query = select(Organization).where(Organization.slug == slug.lower())
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def add_member(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        member_data: OrganizationMemberCreate,
        invited_by: str
    ) -> OrganizationUser:
        """
        Add a member to organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            member_data: Member creation data
            invited_by: ID of user who invited the member
            
        Returns:
            Created membership
            
        Raises:
            NotFoundError: If organization or user not found
            DuplicateError: If user is already a member
        """
        # Verify organization exists
        org = await self.get_or_404(db, id=organization_id)
        
        # Verify user exists
        user_query = select(User).where(User.id == member_data.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User {member_data.user_id} not found")
        
        # Check if already a member
        existing_query = select(OrganizationUser).where(
            and_(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.user_id == member_data.user_id
            )
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            from app.repositories.base import DuplicateError
            raise DuplicateError("User is already a member of this organization")
        
        # Create membership
        membership = OrganizationUser(
            organization_id=organization_id,
            user_id=member_data.user_id,
            role=member_data.role,
            permissions=member_data.permissions,
            invited_by=invited_by,
            is_active=True
        )
        
        db.add(membership)
        await db.flush()
        await db.refresh(membership)
        
        return membership
    
    async def update_member(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        user_id: str,
        member_data: OrganizationMemberUpdate
    ) -> OrganizationUser:
        """
        Update organization membership.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID
            member_data: Update data
            
        Returns:
            Updated membership
            
        Raises:
            NotFoundError: If membership not found
        """
        query = select(OrganizationUser).where(
            and_(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.user_id == user_id
            )
        )
        
        result = await db.execute(query)
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise NotFoundError("Organization membership not found")
        
        # Update fields
        update_data = member_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(membership, field, value)
        
        db.add(membership)
        await db.flush()
        await db.refresh(membership)
        
        return membership
    
    async def remove_member(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        user_id: str
    ) -> bool:
        """
        Remove member from organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            True if removed, False if not found
            
        Raises:
            ValueError: If trying to remove organization owner
        """
        # Check if user is the owner
        org = await self.get_or_404(db, id=organization_id)
        if org.owner_id == user_id:
            raise ValueError("Cannot remove organization owner")
        
        # Remove membership
        query = select(OrganizationUser).where(
            and_(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.user_id == user_id
            )
        )
        
        result = await db.execute(query)
        membership = result.scalar_one_or_none()
        
        if membership:
            await db.delete(membership)
            await db.flush()
            return True
        
        return False
    
    async def get_members(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[OrganizationUser]:
        """
        Get organization members.
        
        Args:
            db: Database session
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only return active members
            
        Returns:
            List of organization memberships
        """
        query = (
            select(OrganizationUser)
            .where(OrganizationUser.organization_id == organization_id)
            .options(selectinload(OrganizationUser.user))
        )
        
        if active_only:
            query = query.where(OrganizationUser.is_active == True)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_member_count(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        active_only: bool = True
    ) -> int:
        """
        Get count of organization members.
        
        Args:
            db: Database session
            organization_id: Organization ID
            active_only: Only count active members
            
        Returns:
            Member count
        """
        query = select(func.count()).select_from(OrganizationUser).where(
            OrganizationUser.organization_id == organization_id
        )
        
        if active_only:
            query = query.where(OrganizationUser.is_active == True)
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def get_user_role(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        user_id: str
    ) -> Optional[UserRole]:
        """
        Get user's role in organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            User role or None if not a member
        """
        # Check if user is the owner
        org = await self.get(db, id=organization_id)
        if org and org.owner_id == user_id:
            return UserRole.OWNER
        
        # Get membership role
        query = select(OrganizationUser.role).where(
            and_(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.user_id == user_id,
                OrganizationUser.is_active == True
            )
        )
        
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        
        return role
    
    async def get_stats(
        self,
        db: AsyncSession,
        *,
        organization_id: str
    ) -> dict:
        """
        Get organization statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Dictionary with stats
        """
        # Member count
        member_count = await self.get_member_count(
            db, organization_id=organization_id
        )
        
        # Payment link count
        link_query = select(func.count()).select_from(PaymentLink).where(
            PaymentLink.organization_id == organization_id
        )
        link_result = await db.execute(link_query)
        payment_link_count = link_result.scalar_one()
        
        # Total volume
        volume_query = (
            select(func.sum(PaymentOrder.settled_amount))
            .select_from(PaymentOrder)
            .where(
                and_(
                    PaymentOrder.organization_id == organization_id,
                    PaymentOrder.status == "COMPLETED"
                )
            )
        )
        volume_result = await db.execute(volume_query)
        total_volume = volume_result.scalar_one() or 0.0
        
        return {
            "member_count": member_count,
            "payment_link_count": payment_link_count,
            "total_volume": float(total_volume)
        }
    
    async def search(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """
        Search organizations by name or slug.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching organizations
        """
        search_filter = Organization.name.ilike(f"%{query}%") | Organization.slug.ilike(f"%{query}%")
        
        stmt = (
            select(Organization)
            .where(search_filter)
            .order_by(Organization.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all()) 