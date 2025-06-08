"""
Organization schemas for API validation and serialization.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.models import ComplianceStatus, UserRole


class OrganizationBase(BaseModel):
    """Base organization schema with common attributes."""
    
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, regex="^[a-z0-9-]+$")
    description: Optional[str] = None
    billing_email: str
    tax_id: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code
    
    @validator("slug")
    def validate_slug(cls, v):
        """Ensure slug is lowercase and valid."""
        return v.lower()


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    
    owner_id: str


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    billing_email: Optional[str] = None
    tax_id: Optional[str] = None
    compliance_status: Optional[ComplianceStatus] = None
    kyc_verified_at: Optional[datetime] = None
    settings: Optional[dict] = None
    features: Optional[List[str]] = None


class OrganizationInDBBase(OrganizationBase):
    """Base schema for organization stored in database."""
    
    id: str
    owner_id: str
    compliance_status: ComplianceStatus
    kyc_verified_at: Optional[datetime]
    settings: dict
    features: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class Organization(OrganizationInDBBase):
    """Schema for organization returned in API responses."""
    pass


class OrganizationWithStats(Organization):
    """Schema for organization with statistics."""
    
    member_count: int = 0
    payment_link_count: int = 0
    total_volume: float = 0.0


class OrganizationMemberBase(BaseModel):
    """Base schema for organization membership."""
    
    user_id: str
    role: UserRole


class OrganizationMemberCreate(OrganizationMemberBase):
    """Schema for adding a member to organization."""
    
    permissions: List[str] = []


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating organization membership."""
    
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class OrganizationMembership(BaseModel):
    """Schema for organization membership details."""
    
    id: str
    organization_id: str
    user_id: str
    role: UserRole
    permissions: List[str]
    is_active: bool
    invited_by: Optional[str]
    invited_at: datetime
    accepted_at: Optional[datetime]
    organization: Optional[Organization] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class OrganizationInvite(BaseModel):
    """Schema for inviting a user to organization."""
    
    email: str
    role: UserRole = UserRole.VIEWER
    permissions: List[str] = []
    message: Optional[str] = None 