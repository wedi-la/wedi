"""Pydantic schemas for API validation and serialization."""

# Import all schemas to ensure proper resolution of forward references
from app.schemas.organization import (
    Organization,
    OrganizationBase,
    OrganizationCreate,
    OrganizationInDBBase,
    OrganizationInvite,
    OrganizationMemberBase,
    OrganizationMemberCreate,
    OrganizationMembership,
    OrganizationMemberUpdate,
    OrganizationUpdate,
    OrganizationWithStats,
)
from app.schemas.user import (
    User,
    UserAuthInfo,
    UserBase,
    UserCreate,
    UserInDBBase,
    UserUpdate,
    UserWithOrganizations,
)

# Rebuild models that have forward references
# This ensures Pydantic can properly resolve all types for OpenAPI generation
UserWithOrganizations.model_rebuild()

# Export all schemas
__all__ = [
    # Organization schemas
    "Organization",
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationInDBBase",
    "OrganizationInvite",
    "OrganizationMemberBase",
    "OrganizationMemberCreate",
    "OrganizationMembership",
    "OrganizationMemberUpdate",
    "OrganizationUpdate",
    "OrganizationWithStats",
    # User schemas
    "User",
    "UserAuthInfo",
    "UserBase",
    "UserCreate",
    "UserInDBBase",
    "UserUpdate",
    "UserWithOrganizations",
] 