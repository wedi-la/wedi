"""Schemas for IntegrationKey API operations."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class IntegrationKeyBase(BaseModel):
    """Base schema for IntegrationKey."""
    
    name: str = Field(..., description="Name of the integration key")
    description: Optional[str] = Field(None, description="Description of the key's purpose")
    
    # Capabilities & Restrictions
    allowed_corridors: List[str] = Field(
        default_factory=list, 
        description="Allowed payment corridors (e.g., ['CO-MX', 'MX-CO'])"
    )
    allowed_providers: List[str] = Field(
        default_factory=list, 
        description="Allowed provider codes (e.g., ['YOINT', 'TRUBIT'])"
    )
    
    # Rate limiting
    rate_limit: Optional[int] = Field(None, description="API calls per minute limit")
    daily_limit: Optional[int] = Field(None, description="Maximum transactions per day")
    
    # Expiration
    expires_at: Optional[datetime] = Field(None, description="When the key expires")
    
    @field_validator("allowed_corridors", "allowed_providers")
    def validate_lists(cls, v):
        """Ensure lists are not None."""
        return v or []


class IntegrationKeyCreate(IntegrationKeyBase):
    """Schema for creating a new IntegrationKey."""
    
    agent_id: str = Field(..., description="ID of the agent associated with this key")


class IntegrationKeyUpdate(BaseModel):
    """Schema for updating an IntegrationKey."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_corridors: Optional[List[str]] = None
    allowed_providers: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class IntegrationKeyResponse(IntegrationKeyBase):
    """Schema for IntegrationKey responses."""
    
    id: str
    organization_id: str
    agent_id: str
    prefix: str = Field(..., description="Key prefix for identification")
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    created_at: datetime
    revoked_at: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class IntegrationKeyWithSecret(IntegrationKeyResponse):
    """Schema for IntegrationKey response including the secret key."""
    
    key: str = Field(..., description="The actual integration key (only shown once)")


class IntegrationKeyListResponse(BaseModel):
    """Schema for paginated list of integration keys."""
    
    items: List[IntegrationKeyResponse]
    total: int
    page: int
    size: int
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class IntegrationKeyValidateRequest(BaseModel):
    """Request schema for validating an integration key."""
    
    key_prefix: str = Field(..., description="The integration key prefix to validate")


class IntegrationKeyValidateResponse(BaseModel):
    """Response schema for integration key validation."""
    
    valid: bool
    organization_id: Optional[str] = None
    agent_id: Optional[str] = None
    allowed_corridors: List[str] = Field(default_factory=list)
    allowed_providers: List[str] = Field(default_factory=list)
    rate_limit: Optional[int] = None
    daily_limit: Optional[int] = None 