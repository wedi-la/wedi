"""
Payment link repository with status filters.
"""
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PaymentLink, PaymentLinkStatus, PaymentOrder, PaymentOrderStatus
from app.repositories.base import BaseRepository
from app.schemas.payment_link import PaymentLinkCreate, PaymentLinkFilter, PaymentLinkUpdate


class PaymentLinkRepository(BaseRepository[PaymentLink, PaymentLinkCreate, PaymentLinkUpdate]):
    """Repository for payment link-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(PaymentLink)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Payment links are scoped to organizations."""
        return "organization_id"
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: PaymentLinkCreate,
        organization_id: str,
        created_by_id: str
    ) -> PaymentLink:
        """
        Create a new payment link with auto-generated short code.
        
        Args:
            db: Database session
            obj_in: Payment link creation data
            organization_id: Organization ID
            created_by_id: ID of user creating the link
            
        Returns:
            Created payment link
        """
        # Generate unique short code
        short_code = await self._generate_unique_short_code(db)
        
        # Generate QR code (placeholder - would use actual QR library)
        qr_code = f"QR_CODE_FOR_{short_code}"
        
        # Create payment link
        return await super().create(
            db,
            obj_in=obj_in,
            organization_id=organization_id,
            created_by_id=created_by_id,
            short_code=short_code,
            qr_code=qr_code
        )
    
    async def _generate_unique_short_code(self, db: AsyncSession, length: int = 8) -> str:
        """
        Generate a unique short code for the payment link.
        
        Args:
            db: Database session
            length: Length of the short code
            
        Returns:
            Unique short code
        """
        max_attempts = 10
        for _ in range(max_attempts):
            # Generate random alphanumeric code
            short_code = ''.join(
                secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789')
                for _ in range(length)
            )
            
            # Check if it already exists
            query = select(PaymentLink).where(PaymentLink.short_code == short_code)
            result = await db.execute(query)
            if not result.scalar_one_or_none():
                return short_code
        
        raise ValueError("Failed to generate unique short code")
    
    async def get_by_short_code(
        self,
        db: AsyncSession,
        *,
        short_code: str
    ) -> Optional[PaymentLink]:
        """
        Get payment link by short code.
        
        Args:
            db: Database session
            short_code: Payment link short code
            
        Returns:
            Payment link or None if not found
        """
        query = select(PaymentLink).where(PaymentLink.short_code == short_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: PaymentLinkStatus,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PaymentLink]:
        """
        Get payment links by status.
        
        Args:
            db: Database session
            status: Payment link status
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of payment links
        """
        return await self.get_multi(
            db,
            organization_id=organization_id,
            filters={"status": status},
            skip=skip,
            limit=limit
        )
    
    async def get_active_links(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PaymentLink]:
        """
        Get active payment links (not expired or completed).
        
        Args:
            db: Database session
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active payment links
        """
        query = select(PaymentLink).where(
            and_(
                PaymentLink.organization_id == organization_id,
                PaymentLink.status == PaymentLinkStatus.ACTIVE,
                or_(
                    PaymentLink.expires_at.is_(None),
                    PaymentLink.expires_at > datetime.utcnow()
                )
            )
        )
        
        query = query.order_by(PaymentLink.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_expired_links(
        self,
        db: AsyncSession,
        *,
        organization_id: Optional[str] = None
    ) -> List[PaymentLink]:
        """
        Get expired payment links that need status update.
        
        Args:
            db: Database session
            organization_id: Optional organization filter
            
        Returns:
            List of expired payment links
        """
        query = select(PaymentLink).where(
            and_(
                PaymentLink.status == PaymentLinkStatus.ACTIVE,
                PaymentLink.expires_at.isnot(None),
                PaymentLink.expires_at <= datetime.utcnow()
            )
        )
        
        if organization_id:
            query = query.where(PaymentLink.organization_id == organization_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def mark_as_expired(
        self,
        db: AsyncSession,
        *,
        payment_link_id: str
    ) -> PaymentLink:
        """
        Mark a payment link as expired.
        
        Args:
            db: Database session
            payment_link_id: Payment link ID
            
        Returns:
            Updated payment link
        """
        link = await self.get_or_404(db, id=payment_link_id)
        link.status = PaymentLinkStatus.EXPIRED
        db.add(link)
        await db.flush()
        await db.refresh(link)
        return link
    
    async def get_link_statistics(
        self,
        db: AsyncSession,
        *,
        payment_link_id: str
    ) -> Dict:
        """
        Get statistics for a payment link.
        
        Args:
            db: Database session
            payment_link_id: Payment link ID
            
        Returns:
            Dictionary with statistics
        """
        # Get payment link
        link = await self.get_or_404(db, id=payment_link_id)
        
        # Query payment orders
        stats_query = select(
            func.count(PaymentOrder.id).label("total_payments"),
            func.count(PaymentOrder.id).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("successful_payments"),
            func.sum(PaymentOrder.settled_amount).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("total_amount_collected"),
            func.avg(
                func.extract("epoch", PaymentOrder.completed_at - PaymentOrder.created_at)
            ).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("avg_payment_time_seconds")
        ).where(PaymentOrder.payment_link_id == payment_link_id)
        
        result = await db.execute(stats_query)
        stats = result.one()
        
        # Calculate success rate
        success_rate = 0.0
        if stats.total_payments > 0:
            success_rate = (stats.successful_payments / stats.total_payments) * 100
        
        # Convert average time to minutes
        avg_payment_time_minutes = None
        if stats.avg_payment_time_seconds:
            avg_payment_time_minutes = int(stats.avg_payment_time_seconds / 60)
        
        return {
            "payment_link_id": payment_link_id,
            "total_payments": stats.total_payments or 0,
            "successful_payments": stats.successful_payments or 0,
            "total_amount_collected": float(stats.total_amount_collected or 0),
            "success_rate": round(success_rate, 2),
            "average_payment_time_minutes": avg_payment_time_minutes
        }
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: PaymentLinkFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PaymentLink]:
        """
        Search payment links with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching payment links
        """
        query = select(PaymentLink).where(
            PaymentLink.organization_id == organization_id
        )
        
        # Apply filters
        if filters.status is not None:
            query = query.where(PaymentLink.status == filters.status)
        
        if filters.created_by_id is not None:
            query = query.where(PaymentLink.created_by_id == filters.created_by_id)
        
        if filters.currency is not None:
            query = query.where(PaymentLink.currency == filters.currency.upper())
        
        if filters.min_amount is not None:
            query = query.where(PaymentLink.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.where(PaymentLink.amount <= filters.max_amount)
        
        if filters.expires_before is not None:
            query = query.where(
                and_(
                    PaymentLink.expires_at.isnot(None),
                    PaymentLink.expires_at <= filters.expires_before
                )
            )
        
        if filters.expires_after is not None:
            query = query.where(
                and_(
                    PaymentLink.expires_at.isnot(None),
                    PaymentLink.expires_at >= filters.expires_after
                )
            )
        
        if filters.has_smart_contract is not None:
            if filters.has_smart_contract:
                query = query.where(PaymentLink.smart_contract_address.isnot(None))
            else:
                query = query.where(PaymentLink.smart_contract_address.is_(None))
        
        if filters.executing_agent_id is not None:
            query = query.where(PaymentLink.executing_agent_id == filters.executing_agent_id)
        
        # Apply ordering and pagination
        query = query.order_by(PaymentLink.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_reference_id(
        self,
        db: AsyncSession,
        *,
        reference_id: str,
        organization_id: str
    ) -> Optional[PaymentLink]:
        """
        Get payment link by merchant's reference ID.
        
        Args:
            db: Database session
            reference_id: Merchant's reference ID
            organization_id: Organization ID
            
        Returns:
            Payment link or None if not found
        """
        query = select(PaymentLink).where(
            and_(
                PaymentLink.reference_id == reference_id,
                PaymentLink.organization_id == organization_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_status_if_paid(
        self,
        db: AsyncSession,
        *,
        payment_link_id: str
    ) -> PaymentLink:
        """
        Update payment link status to PAID if conditions are met.
        
        Args:
            db: Database session
            payment_link_id: Payment link ID
            
        Returns:
            Updated payment link
        """
        link = await self.get_or_404(db, id=payment_link_id)
        
        # Skip if already paid or not allowing multiple payments
        if link.status == PaymentLinkStatus.PAID or link.allow_multiple_payments:
            return link
        
        # Check if any payment order is completed
        order_query = select(PaymentOrder).where(
            and_(
                PaymentOrder.payment_link_id == payment_link_id,
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            )
        )
        
        result = await db.execute(order_query.limit(1))
        if result.scalar_one_or_none():
            link.status = PaymentLinkStatus.PAID
            db.add(link)
            await db.flush()
            await db.refresh(link)
        
        return link 