"""
User schemas for API validation and serialization.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.models import AuthProvider

if TYPE_CHECKING:
    from app.schemas.organization import OrganizationMembership


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    auth_provider: AuthProvider = AuthProvider.EMAIL
    auth_provider_id: Optional[str] = None
    primary_wallet_id: Optional[str] = None
    
    @validator("auth_provider_id")
    def validate_auth_provider_id(cls, v, values):
        """Validate auth provider ID is present for non-email providers."""
        if values.get("auth_provider") != AuthProvider.EMAIL and not v:
            raise ValueError("auth_provider_id is required for non-email auth providers")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    primary_wallet_id: Optional[str] = None
    email_verified: Optional[bool] = None


class UserInDBBase(UserBase):
    """Base schema for user stored in database."""
    
    id: str
    auth_provider: AuthProvider
    auth_provider_id: Optional[str]
    email_verified: bool
    primary_wallet_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class User(UserInDBBase):
    """Schema for user returned in API responses."""
    pass


class UserOut(User):
    """Schema for user returned in API responses with only necessary fields."""
    pass


class UserWithOrganizations(User):
    """Schema for user with their organizations."""
    
    organizations: list[OrganizationMembership] = []


class UserAuthInfo(BaseModel):
    """Schema for user authentication information."""
    
    id: str
    email: EmailStr
    name: Optional[str]
    auth_provider: AuthProvider
    email_verified: bool
    primary_wallet_id: Optional[str]
    current_organization_id: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True 