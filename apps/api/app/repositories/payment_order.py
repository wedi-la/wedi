"""
Payment order repository with complex queries for reporting and analytics.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, case, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    KycStatus,
    PaymentLink,
    PaymentOrder,
    PaymentOrderStatus,
    PaymentEvent,
    EventType,
)
from app.repositories.base import BaseRepository
from app.schemas.payment_order import (
    PaymentOrderCreate,
    PaymentOrderFilter,
    PaymentOrderStats,
    PaymentOrderUpdate,
)


class PaymentOrderRepository(BaseRepository[PaymentOrder, PaymentOrderCreate, PaymentOrderUpdate]):
    """Repository for payment order-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(PaymentOrder)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Payment orders are scoped to organizations."""
        return "organization_id"
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: PaymentOrderCreate,
        organization_id: str
    ) -> PaymentOrder:
        """
        Create a new payment order with auto-generated order number.
        
        Args:
            db: Database session
            obj_in: Payment order creation data
            organization_id: Organization ID
            
        Returns:
            Created payment order
        """
        # Get payment link to inherit amounts if not specified
        payment_link_query = select(PaymentLink).where(
            PaymentLink.id == obj_in.payment_link_id
        )
        result = await db.execute(payment_link_query)
        payment_link = result.scalar_one_or_none()
        
        if not payment_link:
            raise ValueError(f"Payment link {obj_in.payment_link_id} not found")
        
        # Generate unique order number
        order_number = await self._generate_order_number(db, organization_id)
        
        # Set requested amounts (inherit from payment link if not provided)
        requested_amount = obj_in.requested_amount or payment_link.amount
        requested_currency = obj_in.requested_currency or payment_link.currency
        
        # Create the payment order
        db_obj = PaymentOrder(
            **obj_in.model_dump(exclude={"requested_amount", "requested_currency"}),
            organization_id=organization_id,
            order_number=order_number,
            requested_amount=requested_amount,
            requested_currency=requested_currency,
            status=PaymentOrderStatus.PENDING,
            kyc_status=KycStatus.NOT_REQUIRED,
            platform_fee=Decimal("0"),
            provider_fee=Decimal("0"),
            network_fee=Decimal("0"),
            total_fee=Decimal("0"),
            retry_count=0
        )
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def _generate_order_number(
        self,
        db: AsyncSession,
        organization_id: str
    ) -> str:
        """
        Generate a unique order number for the organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Unique order number
        """
        # Get the current date prefix
        today = datetime.utcnow()
        date_prefix = today.strftime("%Y%m%d")
        
        # Find the highest order number for today
        query = select(func.max(PaymentOrder.order_number)).where(
            and_(
                PaymentOrder.organization_id == organization_id,
                PaymentOrder.order_number.like(f"{date_prefix}-%")
            )
        )
        
        result = await db.execute(query)
        last_order_number = result.scalar_one_or_none()
        
        if last_order_number:
            # Extract the sequence number and increment
            sequence = int(last_order_number.split("-")[-1]) + 1
        else:
            sequence = 1
        
        return f"{date_prefix}-{sequence:06d}"
    
    async def get_by_order_number(
        self,
        db: AsyncSession,
        *,
        order_number: str,
        organization_id: str
    ) -> Optional[PaymentOrder]:
        """
        Get payment order by order number.
        
        Args:
            db: Database session
            order_number: Order number
            organization_id: Organization ID
            
        Returns:
            Payment order or None if not found
        """
        query = select(PaymentOrder).where(
            and_(
                PaymentOrder.order_number == order_number,
                PaymentOrder.organization_id == organization_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: PaymentOrderStatus,
        organization_id: str,
        limit: int = 100
    ) -> List[PaymentOrder]:
        """
        Get payment orders by status.
        
        Args:
            db: Database session
            status: Payment order status
            organization_id: Organization ID
            limit: Maximum number of records to return
            
        Returns:
            List of payment orders
        """
        query = select(PaymentOrder).where(
            and_(
                PaymentOrder.organization_id == organization_id,
                PaymentOrder.status == status
            )
        ).order_by(PaymentOrder.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_orders_for_retry(
        self,
        db: AsyncSession,
        *,
        max_retries: int = 3,
        retry_after_minutes: int = 30
    ) -> List[PaymentOrder]:
        """
        Get failed payment orders eligible for retry.
        
        Args:
            db: Database session
            max_retries: Maximum retry attempts
            retry_after_minutes: Minutes to wait before retry
            
        Returns:
            List of payment orders eligible for retry
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=retry_after_minutes)
        
        query = select(PaymentOrder).where(
            and_(
                PaymentOrder.status == PaymentOrderStatus.FAILED,
                PaymentOrder.retry_count < max_retries,
                PaymentOrder.updated_at <= cutoff_time,
                # Don't retry permanent failures
                ~PaymentOrder.failure_code.in_(["FRAUD", "SANCTIONED", "INVALID_ACCOUNT"])
            )
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: PaymentOrderFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PaymentOrder]:
        """
        Search payment orders with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching payment orders
        """
        query = select(PaymentOrder).where(
            PaymentOrder.organization_id == organization_id
        )
        
        # Apply filters
        if filters.status is not None:
            query = query.where(PaymentOrder.status == filters.status)
        
        if filters.payment_link_id is not None:
            query = query.where(PaymentOrder.payment_link_id == filters.payment_link_id)
        
        if filters.customer_email is not None:
            query = query.where(PaymentOrder.customer_email.ilike(f"%{filters.customer_email}%"))
        
        if filters.customer_country is not None:
            query = query.where(PaymentOrder.customer_country == filters.customer_country.upper())
        
        if filters.kyc_status is not None:
            query = query.where(PaymentOrder.kyc_status == filters.kyc_status)
        
        if filters.currency is not None:
            query = query.where(PaymentOrder.requested_currency == filters.currency.upper())
        
        if filters.min_amount is not None:
            query = query.where(PaymentOrder.requested_amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.where(PaymentOrder.requested_amount <= filters.max_amount)
        
        if filters.created_after is not None:
            query = query.where(PaymentOrder.created_at >= filters.created_after)
        
        if filters.created_before is not None:
            query = query.where(PaymentOrder.created_at <= filters.created_before)
        
        if filters.completed_after is not None:
            query = query.where(
                and_(
                    PaymentOrder.completed_at.isnot(None),
                    PaymentOrder.completed_at >= filters.completed_after
                )
            )
        
        if filters.completed_before is not None:
            query = query.where(
                and_(
                    PaymentOrder.completed_at.isnot(None),
                    PaymentOrder.completed_at <= filters.completed_before
                )
            )
        
        if filters.has_failure is not None:
            if filters.has_failure:
                query = query.where(PaymentOrder.failure_reason.isnot(None))
            else:
                query = query.where(PaymentOrder.failure_reason.is_(None))
        
        if filters.min_risk_score is not None:
            query = query.where(PaymentOrder.risk_score >= filters.min_risk_score)
        
        if filters.max_risk_score is not None:
            query = query.where(PaymentOrder.risk_score <= filters.max_risk_score)
        
        # Apply ordering and pagination
        query = query.order_by(PaymentOrder.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_organization_stats(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PaymentOrderStats:
        """
        Get payment order statistics for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            start_date: Start date for stats (optional)
            end_date: End date for stats (optional)
            
        Returns:
            Payment order statistics
        """
        # Base query
        base_conditions = [PaymentOrder.organization_id == organization_id]
        
        if start_date:
            base_conditions.append(PaymentOrder.created_at >= start_date)
        if end_date:
            base_conditions.append(PaymentOrder.created_at <= end_date)
        
        # Get order counts by status
        status_query = select(
            PaymentOrder.status,
            func.count(PaymentOrder.id).label("count")
        ).where(
            and_(*base_conditions)
        ).group_by(PaymentOrder.status)
        
        status_result = await db.execute(status_query)
        orders_by_status = {row.status.value: row.count for row in status_result}
        
        # Get volume by currency
        volume_query = select(
            PaymentOrder.settled_currency,
            func.sum(PaymentOrder.settled_amount).label("volume")
        ).where(
            and_(
                *base_conditions,
                PaymentOrder.status == PaymentOrderStatus.COMPLETED,
                PaymentOrder.settled_amount.isnot(None)
            )
        ).group_by(PaymentOrder.settled_currency)
        
        volume_result = await db.execute(volume_query)
        volume_by_currency = {
            row.settled_currency: float(row.volume) 
            for row in volume_result 
            if row.settled_currency
        }
        
        # Get aggregate stats
        stats_query = select(
            func.count(PaymentOrder.id).label("total_orders"),
            func.count(PaymentOrder.id).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("successful_orders"),
            func.count(PaymentOrder.id).filter(
                PaymentOrder.status == PaymentOrderStatus.FAILED
            ).label("failed_orders"),
            func.count(PaymentOrder.id).filter(
                PaymentOrder.status.in_([
                    PaymentOrderStatus.PENDING,
                    PaymentOrderStatus.PROCESSING
                ])
            ).label("pending_orders"),
            func.sum(PaymentOrder.settled_amount).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("total_volume"),
            func.sum(PaymentOrder.total_fee).filter(
                PaymentOrder.status == PaymentOrderStatus.COMPLETED
            ).label("total_fees"),
            func.avg(
                extract("epoch", PaymentOrder.completed_at - PaymentOrder.created_at)
            ).filter(
                and_(
                    PaymentOrder.status == PaymentOrderStatus.COMPLETED,
                    PaymentOrder.completed_at.isnot(None)
                )
            ).label("avg_processing_seconds")
        ).where(and_(*base_conditions))
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.one()
        
        # Calculate derived metrics
        success_rate = 0.0
        if stats.total_orders > 0:
            success_rate = (stats.successful_orders / stats.total_orders) * 100
        
        avg_processing_minutes = None
        if stats.avg_processing_seconds:
            avg_processing_minutes = float(stats.avg_processing_seconds) / 60
        
        return PaymentOrderStats(
            total_orders=stats.total_orders or 0,
            successful_orders=stats.successful_orders or 0,
            failed_orders=stats.failed_orders or 0,
            pending_orders=stats.pending_orders or 0,
            total_volume=Decimal(str(stats.total_volume or 0)),
            total_fees_collected=Decimal(str(stats.total_fees or 0)),
            average_processing_time_minutes=avg_processing_minutes,
            success_rate=round(success_rate, 2),
            volume_by_currency=volume_by_currency,
            orders_by_status=orders_by_status
        )
    
    async def get_recent_orders_with_events(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        limit: int = 10
    ) -> List[PaymentOrder]:
        """
        Get recent payment orders with their events pre-loaded.
        
        Args:
            db: Database session
            organization_id: Organization ID
            limit: Maximum number of orders to return
            
        Returns:
            List of payment orders with events
        """
        query = select(PaymentOrder).where(
            PaymentOrder.organization_id == organization_id
        ).options(
            selectinload(PaymentOrder.events),
            selectinload(PaymentOrder.payment_link),
            selectinload(PaymentOrder.provider_transactions),
            selectinload(PaymentOrder.blockchain_transactions)
        ).order_by(
            PaymentOrder.created_at.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().unique().all())
    
    async def calculate_daily_volume(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        days: int = 30,
        currency: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Calculate daily payment volume for the organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            days: Number of days to look back
            currency: Optional currency filter
            
        Returns:
            List of daily volume data
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conditions = [
            PaymentOrder.organization_id == organization_id,
            PaymentOrder.status == PaymentOrderStatus.COMPLETED,
            PaymentOrder.completed_at >= start_date,
            PaymentOrder.completed_at.isnot(None)
        ]
        
        if currency:
            conditions.append(PaymentOrder.settled_currency == currency.upper())
        
        query = select(
            func.date(PaymentOrder.completed_at).label("date"),
            func.count(PaymentOrder.id).label("order_count"),
            func.sum(PaymentOrder.settled_amount).label("volume"),
            func.sum(PaymentOrder.total_fee).label("fees")
        ).where(
            and_(*conditions)
        ).group_by(
            func.date(PaymentOrder.completed_at)
        ).order_by(
            func.date(PaymentOrder.completed_at)
        )
        
        result = await db.execute(query)
        
        return [
            {
                "date": row.date.isoformat(),
                "order_count": row.order_count,
                "volume": float(row.volume or 0),
                "fees": float(row.fees or 0)
            }
            for row in result
        ]
    
    async def update_status(
        self,
        db: AsyncSession,
        *,
        order_id: str,
        status: PaymentOrderStatus,
        **kwargs
    ) -> PaymentOrder:
        """
        Update payment order status with timestamp tracking.
        
        Args:
            db: Database session
            order_id: Payment order ID
            status: New status
            **kwargs: Additional fields to update
            
        Returns:
            Updated payment order
        """
        order = await self.get_or_404(db, id=order_id)
        
        # Update status
        order.status = status
        
        # Update timestamps based on status
        if status == PaymentOrderStatus.PROCESSING and not order.started_at:
            order.started_at = datetime.utcnow()
        elif status in [PaymentOrderStatus.COMPLETED, PaymentOrderStatus.FAILED]:
            order.completed_at = datetime.utcnow()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        db.add(order)
        await db.flush()
        await db.refresh(order)
        
        return order 