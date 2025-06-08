"""
Product repository for managing products.
"""
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Price, Product
from app.repositories.base import BaseRepository, DuplicateError
from app.schemas.product import ProductCreate, ProductFilter, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    """Repository for product-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Product)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Products are scoped to organizations."""
        return "organization_id"
    
    async def get_by_sku(
        self,
        db: AsyncSession,
        *,
        sku: str,
        organization_id: str
    ) -> Optional[Product]:
        """
        Get product by SKU within an organization.
        
        Args:
            db: Database session
            sku: Product SKU
            organization_id: Organization ID
            
        Returns:
            Product or None if not found
        """
        query = select(Product).where(
            and_(
                Product.sku == sku.upper(),
                Product.organization_id == organization_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ProductCreate,
        organization_id: str
    ) -> Product:
        """
        Create a new product with unique SKU validation.
        
        Args:
            db: Database session
            obj_in: Product creation data
            organization_id: Organization ID
            
        Returns:
            Created product
            
        Raises:
            DuplicateError: If SKU already exists
        """
        # Check SKU uniqueness if provided
        if obj_in.sku:
            existing = await self.get_by_sku(
                db,
                sku=obj_in.sku,
                organization_id=organization_id
            )
            if existing:
                raise DuplicateError(f"Product with SKU {obj_in.sku} already exists")
        
        return await super().create(
            db,
            obj_in=obj_in,
            organization_id=organization_id
        )
    
    async def get_with_prices(
        self,
        db: AsyncSession,
        *,
        product_id: str
    ) -> Optional[Product]:
        """
        Get product with prices eagerly loaded.
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            Product with prices or None
        """
        query = select(Product).where(
            Product.id == product_id
        ).options(
            selectinload(Product.prices)
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_products(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get active products for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active products
        """
        return await self.get_multi(
            db,
            organization_id=organization_id,
            filters={"is_active": True},
            skip=skip,
            limit=limit
        )
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: ProductFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Search products with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching products
        """
        query = select(Product).where(
            Product.organization_id == organization_id
        )
        
        # Apply filters
        if filters.name:
            query = query.where(Product.name.ilike(f"%{filters.name}%"))
        
        if filters.sku:
            query = query.where(Product.sku.ilike(f"%{filters.sku}%"))
        
        if filters.category:
            query = query.where(Product.category == filters.category)
        
        if filters.tags:
            # Product must have all specified tags
            for tag in filters.tags:
                query = query.where(
                    func.array_position(Product.tags, tag).isnot(None)
                )
        
        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)
        
        if filters.has_active_prices is not None:
            price_subquery = select(Price.product_id).where(
                Price.is_active == True
            ).distinct()
            
            if filters.has_active_prices:
                query = query.where(Product.id.in_(price_subquery))
            else:
                query = query.where(~Product.id.in_(price_subquery))
        
        if filters.created_after:
            query = query.where(Product.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(Product.created_at <= filters.created_before)
        
        # Apply ordering and pagination
        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_category(
        self,
        db: AsyncSession,
        *,
        category: str,
        organization_id: str,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products by category.
        
        Args:
            db: Database session
            category: Product category
            organization_id: Organization ID
            active_only: Only return active products
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of products in category
        """
        query = select(Product).where(
            and_(
                Product.organization_id == organization_id,
                Product.category == category
            )
        )
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.name).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tags(
        self,
        db: AsyncSession,
        *,
        tags: List[str],
        organization_id: str,
        match_all: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products by tags.
        
        Args:
            db: Database session
            tags: List of tags to match
            organization_id: Organization ID
            match_all: If True, product must have all tags. If False, any tag.
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of products with matching tags
        """
        query = select(Product).where(
            and_(
                Product.organization_id == organization_id,
                Product.is_active == True
            )
        )
        
        if match_all:
            # Product must have all tags
            for tag in tags:
                query = query.where(
                    func.array_position(Product.tags, tag).isnot(None)
                )
        else:
            # Product must have at least one tag
            tag_filters = [
                func.array_position(Product.tags, tag).isnot(None)
                for tag in tags
            ]
            query = query.where(or_(*tag_filters))
        
        query = query.order_by(Product.name).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_categories(
        self,
        db: AsyncSession,
        *,
        organization_id: str
    ) -> List[str]:
        """
        Get all unique product categories for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of unique categories
        """
        query = select(Product.category).where(
            and_(
                Product.organization_id == organization_id,
                Product.category.isnot(None)
            )
        ).distinct().order_by(Product.category)
        
        result = await db.execute(query)
        return [row[0] for row in result.all()]
    
    async def get_all_tags(
        self,
        db: AsyncSession,
        *,
        organization_id: str
    ) -> List[str]:
        """
        Get all unique tags used by products in an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of unique tags
        """
        # This would require a more complex query to unnest arrays
        # For now, we'll get all products and extract unique tags
        query = select(Product.tags).where(
            Product.organization_id == organization_id
        )
        
        result = await db.execute(query)
        all_tags = set()
        for row in result.all():
            if row[0]:
                all_tags.update(row[0])
        
        return sorted(list(all_tags))
    
    async def archive_product(
        self,
        db: AsyncSession,
        *,
        product_id: str
    ) -> Product:
        """
        Archive a product (soft delete).
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            Updated product
        """
        product = await self.get_or_404(db, id=product_id)
        product.is_active = False
        
        # Also deactivate all prices
        price_query = select(Price).where(
            and_(
                Price.product_id == product_id,
                Price.is_active == True
            )
        )
        
        price_result = await db.execute(price_query)
        for price in price_result.scalars().all():
            price.is_active = False
            db.add(price)
        
        db.add(product)
        await db.flush()
        await db.refresh(product)
        
        return product 