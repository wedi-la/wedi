"""
Product and price schemas for API validation and serialization.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models import BillingInterval, PriceType


class ProductBase(BaseModel):
    """Base product schema with common attributes."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict] = None
    
    # Payment link defaults
    default_payment_link_title: Optional[str] = None
    default_payment_link_description: Optional[str] = None
    default_success_url: Optional[str] = None
    default_cancel_url: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    
    sku: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    
    @validator("sku")
    def validate_sku(cls, v):
        """Ensure SKU is uppercase if provided."""
        return v.upper() if v else v


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    
    # Payment link defaults
    default_payment_link_title: Optional[str] = None
    default_payment_link_description: Optional[str] = None
    default_success_url: Optional[str] = None
    default_cancel_url: Optional[str] = None


class ProductInDBBase(ProductBase):
    """Base schema for product stored in database."""
    
    id: str
    organization_id: str
    sku: Optional[str]
    category: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class Product(ProductInDBBase):
    """Schema for product returned in API responses."""
    pass


class ProductWithPrices(Product):
    """Schema for product with its prices."""
    
    prices: List["Price"] = []
    active_price_count: int = 0
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None


# Price Schemas

class PriceBase(BaseModel):
    """Base price schema with common attributes."""
    
    amount: Decimal = Field(..., gt=0, decimal_places=8)
    currency: str = Field(..., min_length=3, max_length=3)  # ISO currency code
    type: PriceType = PriceType.ONE_TIME
    billing_interval: Optional[BillingInterval] = None
    billing_interval_count: Optional[int] = Field(None, ge=1)
    
    # Trial period (for recurring prices)
    trial_period_days: Optional[int] = Field(None, ge=0)
    
    # Tiered pricing
    tiers: Optional[List[Dict]] = None
    
    # Custom name/description
    nickname: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    metadata: Optional[Dict] = None
    
    @validator("currency")
    def validate_currency(cls, v):
        """Ensure currency code is uppercase."""
        return v.upper()
    
    @validator("billing_interval")
    def validate_billing_interval(cls, v, values):
        """Ensure billing interval is set for recurring prices."""
        if values.get("type") == PriceType.RECURRING and not v:
            raise ValueError("Billing interval required for recurring prices")
        return v


class PriceCreate(PriceBase):
    """Schema for creating a new price."""
    
    product_id: str
    
    # Min/max quantity constraints
    min_quantity: Optional[int] = Field(None, ge=1)
    max_quantity: Optional[int] = Field(None, ge=1)
    
    @validator("max_quantity")
    def validate_max_quantity(cls, v, values):
        """Ensure max_quantity >= min_quantity."""
        if v and values.get("min_quantity") and v < values["min_quantity"]:
            raise ValueError("max_quantity must be >= min_quantity")
        return v


class PriceUpdate(BaseModel):
    """Schema for updating a price."""
    
    nickname: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None
    trial_period_days: Optional[int] = Field(None, ge=0)


class PriceInDBBase(PriceBase):
    """Base schema for price stored in database."""
    
    id: str
    product_id: str
    organization_id: str
    min_quantity: Optional[int]
    max_quantity: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class Price(PriceInDBBase):
    """Schema for price returned in API responses."""
    pass


class PriceWithProduct(Price):
    """Schema for price with its product."""
    
    product: Optional[Product] = None


class ProductFilter(BaseModel):
    """Schema for product search filters."""
    
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    has_active_prices: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class PriceFilter(BaseModel):
    """Schema for price search filters."""
    
    product_id: Optional[str] = None
    currency: Optional[str] = None
    type: Optional[PriceType] = None
    billing_interval: Optional[BillingInterval] = None
    is_active: Optional[bool] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    has_trial: Optional[bool] = None 