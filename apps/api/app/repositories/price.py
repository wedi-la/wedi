"""
Price repository for managing product pricing.
"""
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BillingInterval, Price, PriceType, Product
from app.repositories.base import BaseRepository, NotFoundError
from app.schemas.product import PriceCreate, PriceFilter, PriceUpdate


class PriceRepository(BaseRepository[Price, PriceCreate, PriceUpdate]):
    """Repository for price-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Price)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Prices are scoped to organizations."""
        return "organization_id"
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: PriceCreate,
        organization_id: str
    ) -> Price:
        """
        Create a new price with product validation.
        
        Args:
            db: Database session
            obj_in: Price creation data
            organization_id: Organization ID
            
        Returns:
            Created price
            
        Raises:
            NotFoundError: If product doesn't exist
        """
        # Validate product exists and belongs to organization
        product_query = select(Product).where(
            and_(
                Product.id == obj_in.product_id,
                Product.organization_id == organization_id
            )
        )
        
        result = await db.execute(product_query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise NotFoundError(f"Product {obj_in.product_id} not found")
        
        return await super().create(
            db,
            obj_in=obj_in,
            organization_id=organization_id
        )
    
    async def get_active_price_for_product(
        self,
        db: AsyncSession,
        *,
        product_id: str,
        currency: str,
        quantity: int = 1
    ) -> Optional[Price]:
        """
        Get the best active price for a product based on currency and quantity.
        
        Args:
            db: Database session
            product_id: Product ID
            currency: Currency code
            quantity: Quantity to check against min/max constraints
            
        Returns:
            Best matching price or None
        """
        query = select(Price).where(
            and_(
                Price.product_id == product_id,
                Price.currency == currency.upper(),
                Price.is_active == True,
                # Quantity constraints
                or_(
                    Price.min_quantity.is_(None),
                    Price.min_quantity <= quantity
                ),
                or_(
                    Price.max_quantity.is_(None),
                    Price.max_quantity >= quantity
                )
            )
        )
        
        # Order by: recurring prices first, then by amount (lowest)
        query = query.order_by(
            Price.type.desc(),  # RECURRING before ONE_TIME
            Price.amount.asc()
        )
        
        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none()
    
    async def get_prices_for_product(
        self,
        db: AsyncSession,
        *,
        product_id: str,
        active_only: bool = True
    ) -> List[Price]:
        """
        Get all prices for a product.
        
        Args:
            db: Database session
            product_id: Product ID
            active_only: Only return active prices
            
        Returns:
            List of prices
        """
        query = select(Price).where(Price.product_id == product_id)
        
        if active_only:
            query = query.where(Price.is_active == True)
        
        query = query.order_by(
            Price.currency,
            Price.type,
            Price.amount
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_recurring_prices(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        billing_interval: Optional[BillingInterval] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Price]:
        """
        Get recurring prices for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            billing_interval: Optional filter by billing interval
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recurring prices
        """
        query = select(Price).where(
            and_(
                Price.organization_id == organization_id,
                Price.type == PriceType.RECURRING,
                Price.is_active == True
            )
        )
        
        if billing_interval:
            query = query.where(Price.billing_interval == billing_interval)
        
        query = query.order_by(Price.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: PriceFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Price]:
        """
        Search prices with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching prices
        """
        query = select(Price).where(
            Price.organization_id == organization_id
        )
        
        # Apply filters
        if filters.product_id:
            query = query.where(Price.product_id == filters.product_id)
        
        if filters.currency:
            query = query.where(Price.currency == filters.currency.upper())
        
        if filters.type:
            query = query.where(Price.type == filters.type)
        
        if filters.billing_interval:
            query = query.where(Price.billing_interval == filters.billing_interval)
        
        if filters.is_active is not None:
            query = query.where(Price.is_active == filters.is_active)
        
        if filters.min_amount is not None:
            query = query.where(Price.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.where(Price.amount <= filters.max_amount)
        
        if filters.has_trial is not None:
            if filters.has_trial:
                query = query.where(
                    and_(
                        Price.trial_period_days.isnot(None),
                        Price.trial_period_days > 0
                    )
                )
            else:
                query = query.where(
                    or_(
                        Price.trial_period_days.is_(None),
                        Price.trial_period_days == 0
                    )
                )
        
        # Apply ordering and pagination
        query = query.order_by(
            Price.product_id,
            Price.currency,
            Price.amount
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_with_product(
        self,
        db: AsyncSession,
        *,
        price_id: str
    ) -> Optional[Price]:
        """
        Get price with product eagerly loaded.
        
        Args:
            db: Database session
            price_id: Price ID
            
        Returns:
            Price with product or None
        """
        query = select(Price).where(
            Price.id == price_id
        ).options(
            selectinload(Price.product)
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_price_summary_by_currency(
        self,
        db: AsyncSession,
        *,
        organization_id: str
    ) -> Dict[str, Dict]:
        """
        Get price summary grouped by currency.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Dictionary with currency summaries
        """
        query = select(
            Price.currency,
            func.count(Price.id).label("count"),
            func.min(Price.amount).label("min_amount"),
            func.max(Price.amount).label("max_amount"),
            func.avg(Price.amount).label("avg_amount")
        ).where(
            and_(
                Price.organization_id == organization_id,
                Price.is_active == True
            )
        ).group_by(Price.currency)
        
        result = await db.execute(query)
        
        summaries = {}
        for row in result.all():
            summaries[row.currency] = {
                "count": row.count,
                "min_amount": float(row.min_amount),
                "max_amount": float(row.max_amount),
                "avg_amount": float(row.avg_amount)
            }
        
        return summaries
    
    async def archive_price(
        self,
        db: AsyncSession,
        *,
        price_id: str
    ) -> Price:
        """
        Archive a price (soft delete).
        
        Args:
            db: Database session
            price_id: Price ID
            
        Returns:
            Updated price
        """
        price = await self.get_or_404(db, id=price_id)
        price.is_active = False
        
        db.add(price)
        await db.flush()
        await db.refresh(price)
        
        return price
    
    async def duplicate_price(
        self,
        db: AsyncSession,
        *,
        price_id: str,
        updates: Optional[Dict] = None
    ) -> Price:
        """
        Duplicate an existing price with optional updates.
        
        Args:
            db: Database session
            price_id: Price ID to duplicate
            updates: Optional updates to apply to the duplicate
            
        Returns:
            New duplicated price
        """
        # Get original price
        original = await self.get_or_404(db, id=price_id)
        
        # Create copy data
        create_data = PriceCreate(
            product_id=original.product_id,
            amount=original.amount,
            currency=original.currency,
            type=original.type,
            billing_interval=original.billing_interval,
            billing_interval_count=original.billing_interval_count,
            trial_period_days=original.trial_period_days,
            tiers=original.tiers,
            nickname=f"Copy of {original.nickname or 'Price'}",
            min_quantity=original.min_quantity,
            max_quantity=original.max_quantity,
            metadata=original.metadata
        )
        
        # Apply any updates
        if updates:
            for key, value in updates.items():
                if hasattr(create_data, key):
                    setattr(create_data, key, value)
        
        # Create the duplicate
        return await self.create(
            db,
            obj_in=create_data,
            organization_id=original.organization_id
        )
    
    async def validate_tiered_pricing(
        self,
        tiers: List[Dict]
    ) -> bool:
        """
        Validate tiered pricing structure.
        
        Args:
            tiers: List of tier definitions
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If tiers are invalid
        """
        if not tiers:
            return True
        
        # Sort tiers by up_to
        sorted_tiers = sorted(
            tiers,
            key=lambda t: t.get("up_to", float("inf"))
        )
        
        last_up_to = 0
        for i, tier in enumerate(sorted_tiers):
            # Validate required fields
            if "unit_amount" not in tier:
                raise ValueError(f"Tier {i} missing unit_amount")
            
            # Validate up_to progression
            up_to = tier.get("up_to")
            if i < len(sorted_tiers) - 1 and up_to is None:
                raise ValueError("Only the last tier can have unlimited up_to")
            
            if up_to is not None:
                if up_to <= last_up_to:
                    raise ValueError(f"Tier {i} up_to must be greater than previous tier")
                last_up_to = up_to
        
        return True 