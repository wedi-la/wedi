"""
Payment order schemas for API validation and serialization.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models import KycStatus, PaymentOrderStatus


class PaymentOrderBase(BaseModel):
    """Base payment order schema with common attributes."""
    
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    customer_wallet: Optional[str] = None
    customer_ip: Optional[str] = None
    customer_country: Optional[str] = Field(None, min_length=2, max_length=2)
    
    @validator("customer_country")
    def validate_country(cls, v):
        """Ensure country code is uppercase."""
        return v.upper() if v else v


class PaymentOrderCreate(PaymentOrderBase):
    """Schema for creating a new payment order."""
    
    payment_link_id: str
    
    # Optional override amounts (if different from payment link)
    requested_amount: Optional[Decimal] = None
    requested_currency: Optional[str] = None


class PaymentOrderUpdate(BaseModel):
    """Schema for updating a payment order."""
    
    status: Optional[PaymentOrderStatus] = None
    settled_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=8)
    settled_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange_rate: Optional[Decimal] = Field(None, gt=0, decimal_places=8)
    exchange_rate_source: Optional[str] = None
    
    # Fees
    platform_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=8)
    provider_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=8)
    network_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=8)
    
    # Risk & compliance
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    risk_factors: Optional[Dict] = None
    kyc_status: Optional[KycStatus] = None
    kyc_verified_at: Optional[datetime] = None
    
    # Error info
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None


class PaymentOrderInDBBase(PaymentOrderBase):
    """Base schema for payment order stored in database."""
    
    id: str
    organization_id: str
    payment_link_id: str
    order_number: str
    status: PaymentOrderStatus
    
    # Amounts
    requested_amount: Decimal
    requested_currency: str
    settled_amount: Optional[Decimal]
    settled_currency: Optional[str]
    
    # Exchange rates
    exchange_rate: Optional[Decimal]
    exchange_rate_locked_at: Optional[datetime]
    exchange_rate_source: Optional[str]
    
    # Fees
    platform_fee: Decimal
    provider_fee: Decimal
    network_fee: Decimal
    total_fee: Decimal
    
    # Risk & compliance
    risk_score: Optional[int]
    risk_factors: Optional[Dict]
    kyc_status: KycStatus
    kyc_verified_at: Optional[datetime]
    
    # Processing
    selected_route: Optional[Dict]
    failure_reason: Optional[str]
    failure_code: Optional[str]
    retry_count: int
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentOrder(PaymentOrderInDBBase):
    """Schema for payment order returned in API responses."""
    pass


class PaymentOrderWithRelations(PaymentOrder):
    """Schema for payment order with related data."""
    
    payment_link: Optional["PaymentLink"] = None
    provider_transactions: List["ProviderTransaction"] = []
    blockchain_transactions: List["BlockchainTransaction"] = []
    events: List["PaymentEvent"] = []


class PaymentOrderSummary(BaseModel):
    """Schema for payment order summary (listing)."""
    
    id: str
    order_number: str
    status: PaymentOrderStatus
    requested_amount: Decimal
    requested_currency: str
    settled_amount: Optional[Decimal]
    settled_currency: Optional[str]
    total_fee: Decimal
    customer_email: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentOrderFilter(BaseModel):
    """Schema for payment order search filters."""
    
    status: Optional[PaymentOrderStatus] = None
    payment_link_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    kyc_status: Optional[KycStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    has_failure: Optional[bool] = None
    min_risk_score: Optional[int] = None
    max_risk_score: Optional[int] = None


class PaymentOrderStats(BaseModel):
    """Schema for payment order statistics."""
    
    total_orders: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    pending_orders: int = 0
    total_volume: Decimal = Decimal("0")
    total_fees_collected: Decimal = Decimal("0")
    average_processing_time_minutes: Optional[float] = None
    success_rate: float = 0.0
    
    # By currency breakdown
    volume_by_currency: Dict[str, float] = {}
    orders_by_status: Dict[str, int] = {}


# Circular import handling
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.payment_link import PaymentLink
    from app.schemas.provider import ProviderTransaction
    from app.schemas.blockchain import BlockchainTransaction
    from app.schemas.event import PaymentEvent 