"""
Payment link schemas for API validation and serialization.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator

from app.models import PaymentLinkStatus


class PaymentLinkBase(BaseModel):
    """Base payment link schema with common attributes."""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reference_id: Optional[str] = Field(None, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=8)
    currency: str = Field(..., min_length=3, max_length=3)  # ISO currency code
    target_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=8)
    target_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    
    # Behavior
    allow_multiple_payments: bool = False
    requires_kyc: bool = False
    expires_at: Optional[datetime] = None
    
    # Customization
    redirect_urls: Optional[Dict[str, HttpUrl]] = None
    metadata: Optional[Dict] = None
    theme: Optional[Dict] = None
    
    @validator("currency", "target_currency")
    def validate_currency(cls, v):
        """Ensure currency codes are uppercase."""
        return v.upper() if v else v
    
    @validator("redirect_urls")
    def validate_redirect_urls(cls, v):
        """Ensure redirect URLs have valid keys."""
        if v:
            valid_keys = {"success", "failure", "cancel"}
            if not set(v.keys()).issubset(valid_keys):
                raise ValueError(f"Redirect URLs must only contain keys: {valid_keys}")
        return v


class PaymentLinkCreate(PaymentLinkBase):
    """Schema for creating a new payment link."""
    
    # Smart contract integration (optional for MVP)
    smart_contract_address: Optional[str] = None
    smart_contract_chain_id: Optional[int] = None
    token_address: Optional[str] = None
    
    # Agent assignment (optional)
    executing_agent_id: Optional[str] = None


class PaymentLinkUpdate(BaseModel):
    """Schema for updating a payment link."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[PaymentLinkStatus] = None
    expires_at: Optional[datetime] = None
    redirect_urls: Optional[Dict[str, HttpUrl]] = None
    metadata: Optional[Dict] = None
    theme: Optional[Dict] = None


class PaymentLinkInDBBase(PaymentLinkBase):
    """Base schema for payment link stored in database."""
    
    id: str
    organization_id: str
    created_by_id: str
    short_code: str
    qr_code: Optional[str]
    status: PaymentLinkStatus
    
    # Smart contract fields
    smart_contract_address: Optional[str]
    smart_contract_chain_id: Optional[int]
    token_address: Optional[str]
    
    # Agent assignment
    executing_agent_id: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentLink(PaymentLinkInDBBase):
    """Schema for payment link returned in API responses."""
    
    payment_url: Optional[str] = None
    
    @validator("payment_url", always=True)
    def generate_payment_url(cls, v, values):
        """Generate the payment URL from short code."""
        if "short_code" in values:
            # This would be configured based on environment
            return f"https://pay.wedi.co/{values['short_code']}"
        return v


class PaymentLinkWithStats(PaymentLink):
    """Schema for payment link with statistics."""
    
    total_payments: int = 0
    total_amount_collected: Decimal = Decimal("0")
    success_rate: float = 0.0
    average_payment_time: Optional[int] = None  # minutes


class PaymentLinkSummary(BaseModel):
    """Schema for payment link summary (listing)."""
    
    id: str
    title: str
    amount: Decimal
    currency: str
    status: PaymentLinkStatus
    short_code: str
    payment_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    total_payments: int = 0
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentLinkFilter(BaseModel):
    """Schema for payment link search filters."""
    
    status: Optional[PaymentLinkStatus] = None
    created_by_id: Optional[str] = None
    currency: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    expires_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    has_smart_contract: Optional[bool] = None
    executing_agent_id: Optional[str] = None


# Additional schemas needed for the payment links router

class PaymentLinkListResponse(BaseModel):
    """Response schema for listing payment links."""
    
    items: List[PaymentLinkSummary]
    total: int
    page: int
    limit: int
    has_next: bool
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentLinkPublicResponse(BaseModel):
    """Public payment link response (no sensitive data)."""
    
    id: str
    title: str
    description: Optional[str]
    amount: Decimal
    currency: str
    target_amount: Optional[Decimal]
    target_currency: Optional[str]
    status: PaymentLinkStatus
    requires_kyc: bool
    expires_at: Optional[datetime]
    theme: Optional[Dict]
    redirect_urls: Optional[Dict[str, str]]
    organization_name: Optional[str]  # From organization lookup
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PaymentLinkSearchParams(BaseModel):
    """Advanced search parameters for payment links."""
    
    query: Optional[str] = Field(None, description="Search in title, description, reference_id")
    status: Optional[PaymentLinkStatus] = None
    currency: Optional[str] = None
    created_by_id: Optional[str] = None
    smart_contract_address: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class PaymentLinkSearchResponse(BaseModel):
    """Response for payment link search."""
    
    items: List[PaymentLink]
    total: int
    page: int
    limit: int
    query: Optional[str]
    filters_applied: Dict[str, Any]
    
    class Config:
        """Pydantic config."""
        from_attributes = True 