"""
Customer schemas for API validation and serialization.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.models import KycStatus, PaymentMethodType


class CustomerBase(BaseModel):
    """Base customer schema with common attributes."""
    
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code
    address: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    @validator("country")
    def validate_country(cls, v):
        """Ensure country code is uppercase."""
        return v.upper()


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    
    external_id: Optional[str] = Field(None, max_length=255)
    kyc_status: KycStatus = KycStatus.NOT_REQUIRED
    
    # Optional wallet address for crypto-native customers
    primary_wallet_address: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict] = None
    metadata: Optional[Dict] = None
    kyc_status: Optional[KycStatus] = None
    kyc_verified_at: Optional[datetime] = None
    kyc_details: Optional[Dict] = None


class CustomerInDBBase(CustomerBase):
    """Base schema for customer stored in database."""
    
    id: str
    organization_id: str
    external_id: Optional[str]
    kyc_status: KycStatus
    kyc_verified_at: Optional[datetime]
    kyc_details: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class Customer(CustomerInDBBase):
    """Schema for customer returned in API responses."""
    pass


class CustomerWithPaymentMethods(Customer):
    """Schema for customer with payment methods."""
    
    payment_methods: List["CustomerPaymentMethod"] = []
    default_payment_method_id: Optional[str] = None


class CustomerSummary(BaseModel):
    """Schema for customer summary (listing)."""
    
    id: str
    email: str
    name: Optional[str]
    country: str
    kyc_status: KycStatus
    created_at: datetime
    payment_method_count: int = 0
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Payment Method Schemas

class PaymentMethodBase(BaseModel):
    """Base payment method schema."""
    
    type: PaymentMethodType
    label: Optional[str] = Field(None, max_length=255)
    is_default: bool = False
    metadata: Optional[Dict] = None


class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating a new payment method."""
    
    # Card details (for CARD type)
    card_number: Optional[str] = None
    card_exp_month: Optional[int] = Field(None, ge=1, le=12)
    card_exp_year: Optional[int] = Field(None, ge=datetime.now().year)
    card_cvv: Optional[str] = None
    
    # Bank details (for BANK_ACCOUNT type)
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_country: Optional[str] = Field(None, min_length=2, max_length=2)
    
    # Wallet details (for WALLET type)
    wallet_address: Optional[str] = None
    wallet_chain_id: Optional[int] = None
    
    @validator("card_number")
    def validate_card_number(cls, v):
        """Basic card number validation (would use proper validation in production)."""
        if v and not v.replace(" ", "").isdigit():
            raise ValueError("Invalid card number")
        return v.replace(" ", "") if v else v
    
    @validator("bank_country")
    def validate_bank_country(cls, v):
        """Ensure country code is uppercase."""
        return v.upper() if v else v


class PaymentMethodUpdate(BaseModel):
    """Schema for updating a payment method."""
    
    label: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None
    metadata: Optional[Dict] = None
    
    # Card updates (limited for security)
    card_exp_month: Optional[int] = Field(None, ge=1, le=12)
    card_exp_year: Optional[int] = Field(None, ge=datetime.now().year)


class CustomerPaymentMethodBase(PaymentMethodBase):
    """Base schema for customer payment method stored in database."""
    
    id: str
    customer_id: str
    provider_payment_method_id: Optional[str]
    
    # Masked/safe details
    card_last4: Optional[str]
    card_brand: Optional[str]
    bank_last4: Optional[str]
    wallet_address: Optional[str]
    
    # Validation
    is_verified: bool
    verified_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class CustomerPaymentMethod(CustomerPaymentMethodBase):
    """Schema for customer payment method returned in API responses."""
    pass


class CustomerFilter(BaseModel):
    """Schema for customer search filters."""
    
    email: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    kyc_status: Optional[KycStatus] = None
    has_payment_methods: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None 