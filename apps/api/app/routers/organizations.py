"""
Organization management endpoints.

This module provides API endpoints for managing organizations,
including CRUD operations and member management.
"""
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_organization_repository,
    get_pagination,
    get_unit_of_work,
    PaginationParams,
    require_organization_context,
)
from app.core.logging import get_logger
from app.db.session import get_db
from app.events import (
    OrganizationCreatedEvent,
    MemberAddedEvent,
    MemberRemovedEvent,
)
from app.events.event_publisher import get_event_publisher, EventPublisher
from app.models import User, UserRole
from app.repositories.organization import OrganizationRepository
from app.repositories.base import DuplicateError, NotFoundError
from app.schemas.organization import (
    Organization,
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMembership,
    OrganizationMemberUpdate,
    OrganizationUpdate,
    OrganizationWithStats,
)
from app.schemas.integration_key import (
    IntegrationKeyCreate,
    IntegrationKeyUpdate,
    IntegrationKeyResponse,
    IntegrationKeyWithSecret,
    IntegrationKeyListResponse,
)
from app.services.integration_key_service import integration_key_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
    },
)


@router.get("", response_model=List[Organization])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> List[Organization]:
    """
    List organizations the current user belongs to.
    
    Returns all organizations where the user is a member,
    ordered by organization name.
    """
    logger.info(f"Listing organizations for user: {current_user.id}")
    
    # Get user's organizations from the user repository
    from app.repositories.user import UserRepository
    user_repo = UserRepository()
    
    organizations = await user_repo.get_organizations(
        db,
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        active_only=True,
    )
    
    return [Organization.model_validate(org) for org in organizations]


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> Organization:
    """
    Create a new organization.
    
    The current user will be set as the owner of the organization.
    """
    logger.info(f"Creating organization: {organization_data.name} for user: {current_user.id}")
    
    async with uow:
        try:
            # Set the current user as the owner
            create_data = organization_data.model_dump()
            create_data["owner_id"] = str(current_user.id)
            create_data["id"] = str(uuid4())
            # Set defaults if not provided
            if "settings" not in create_data:
                create_data["settings"] = {}
            if "features" not in create_data:
                create_data["features"] = []
            
            # Create organization
            organization = await uow.organizations.create(
                db, data=create_data
            )
            
            # Add the owner as a member with OWNER role
            membership_data = OrganizationMemberCreate(
                user_id=str(current_user.id),
                role=UserRole.OWNER,
                permissions=["*"],  # Full permissions
            )
            
            await uow.organizations.add_member(
                db,
                organization_id=organization.id,
                member_data=membership_data,
                invited_by=str(current_user.id),
            )
            
            await uow.commit()
            
            # Emit organization created event
            event = OrganizationCreatedEvent(
                organization_id=organization.id,
                name=organization.name,
                slug=organization.slug,
                owner_id=str(current_user.id),
            )
            await event_publisher.publish_event(event)
            
            logger.info(f"Organization created successfully: {organization.id}")
            return Organization.model_validate(organization)
            
        except DuplicateError as e:
            logger.warning(f"Duplicate organization slug: {organization_data.slug}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with slug '{organization_data.slug}' already exists",
            )
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization",
            )


@router.get("/{organization_id}", response_model=OrganizationWithStats)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> OrganizationWithStats:
    """
    Get organization details with statistics.
    
    Requires the user to be a member of the organization.
    """
    # Check if user has access to this organization
    user_role = await organization_repository.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if not user_role:
        logger.warning(f"User {current_user.id} attempted to access organization {organization_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )
    
    try:
        # Get organization
        organization = await organization_repository.get_or_404(
            db, id=organization_id
        )
        
        # Get statistics
        stats = await organization_repository.get_stats(
            db, organization_id=organization_id
        )
        
        # Combine organization and stats
        org_dict = Organization.model_validate(organization).model_dump()
        org_dict.update(stats)
        
        return OrganizationWithStats(**org_dict)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )


@router.put("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> Organization:
    """
    Update organization details.
    
    Requires ADMIN or OWNER role in the organization.
    """
    # Check user role
    user_role = await organization_repository.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can update organization details",
        )
    
    try:
        # Update organization
        organization = await organization_repository.update(
            db, id=organization_id, data=update_data
        )
        
        logger.info(f"Organization {organization_id} updated by user {current_user.id}")
        return Organization.model_validate(organization)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )


@router.get("/{organization_id}/members", response_model=List[OrganizationMembership])
async def list_organization_members(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    active_only: bool = Query(True, description="Only return active members"),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> List[OrganizationMembership]:
    """
    List organization members.
    
    Requires the user to be a member of the organization.
    """
    # Check if user has access
    user_role = await organization_repository.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )
    
    # Get members
    members = await organization_repository.get_members(
        db,
        organization_id=organization_id,
        skip=pagination.skip,
        limit=pagination.limit,
        active_only=active_only,
    )
    
    return [
        OrganizationMembership.model_validate(member)
        for member in members
    ]


@router.post("/{organization_id}/members", response_model=OrganizationMembership, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    organization_id: str,
    member_data: OrganizationMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> OrganizationMembership:
    """
    Add a member to the organization.
    
    Requires ADMIN or OWNER role in the organization.
    """
    async with uow:
        # Check user role
        user_role = await uow.organizations.get_user_role(
            db, organization_id=organization_id, user_id=current_user.id
        )
        
        if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can add members",
            )
        
        try:
            # Add member
            membership = await uow.organizations.add_member(
                db,
                organization_id=organization_id,
                member_data=member_data,
                invited_by=str(current_user.id),
            )
            
            await uow.commit()
            
            # Emit event
            event = MemberAddedEvent(
                organization_id=organization_id,
                user_id=member_data.user_id,
                role=member_data.role,
                invited_by=str(current_user.id),
            )
            await event_publisher.publish_event(event)
            
            logger.info(f"User {member_data.user_id} added to organization {organization_id}")
            return OrganizationMembership.model_validate(membership)
            
        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except DuplicateError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member",
            )


@router.put("/{organization_id}/members/{user_id}", response_model=OrganizationMembership)
async def update_organization_member(
    organization_id: str,
    user_id: str,
    update_data: OrganizationMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> OrganizationMembership:
    """
    Update a member's role or permissions.
    
    Requires ADMIN or OWNER role. Cannot modify the owner's membership.
    """
    # Check user role
    user_role = await organization_repository.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can update member roles",
        )
    
    # Check if trying to modify owner
    org = await organization_repository.get_or_404(db, id=organization_id)
    if org.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify organization owner's membership",
        )
    
    try:
        # Update membership
        membership = await organization_repository.update_member(
            db,
            organization_id=organization_id,
            user_id=user_id,
            member_data=update_data,
        )
        
        logger.info(f"Updated membership for user {user_id} in organization {organization_id}")
        return OrganizationMembership.model_validate(membership)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization membership not found",
        )


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    organization_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> None:
    """
    Remove a member from the organization.
    
    Requires ADMIN or OWNER role. The owner cannot be removed.
    Users can remove themselves from an organization.
    """
    async with uow:
        # Allow users to remove themselves
        if user_id != str(current_user.id):
            # Check user role for removing others
            user_role = await uow.organizations.get_user_role(
                db, organization_id=organization_id, user_id=current_user.id
            )
            
            if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins and owners can remove members",
                )
        
        try:
            # Remove member
            removed = await uow.organizations.remove_member(
                db,
                organization_id=organization_id,
                user_id=user_id,
            )
            
            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found in organization",
                )
            
            await uow.commit()
            
            # Emit event
            event = MemberRemovedEvent(
                organization_id=organization_id,
                user_id=user_id,
                removed_by=str(current_user.id),
            )
            await event_publisher.publish_event(event)
            
            logger.info(f"User {user_id} removed from organization {organization_id}")
            
        except ValueError as e:
            # Trying to remove owner
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member",
            )


@router.get("/{organization_id}/stats", response_model=dict)
async def get_organization_stats(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> dict:
    """
    Get detailed organization statistics.
    
    Requires the user to be a member of the organization.
    """
    # Check if user has access
    user_role = await organization_repository.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )
    
    try:
        # Get statistics
        stats = await organization_repository.get_stats(
            db, organization_id=organization_id
        )
        
        return stats
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )


# Integration Key Endpoints

@router.post("/{organization_id}/integration-keys", response_model=IntegrationKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_integration_key(
    organization_id: str,
    key_data: IntegrationKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> IntegrationKeyWithSecret:
    """
    Create a new integration key for the organization.
    
    Requires ADMIN or OWNER role in the organization.
    
    Returns the integration key with the secret. The secret is only shown once
    and cannot be retrieved later.
    """
    async with uow:
        # Check user role
        user_role = await uow.organizations.get_user_role(
            db, organization_id=organization_id, user_id=current_user.id
        )
        
        if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can create integration keys",
            )
        
        try:
            # Create integration key
            integration_key, plain_key = await integration_key_service.create(
                db, organization_id, key_data
            )
            
            await uow.commit()
            
            logger.info(f"Integration key {integration_key.id} created for organization {organization_id}")
            
            # Return with the plain key
            return IntegrationKeyWithSecret(
                id=integration_key.id,
                name=integration_key.name,
                description=integration_key.description,
                organization_id=integration_key.organization_id,
                payment_corridors=integration_key.payment_corridors,
                webhook_url=integration_key.webhook_url,
                expires_at=integration_key.expires_at,
                is_active=integration_key.is_active,
                last_used_at=integration_key.last_used_at,
                created_at=integration_key.created_at,
                updated_at=integration_key.updated_at,
                key=plain_key,
            )
            
        except Exception as e:
            logger.error(f"Error creating integration key: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create integration key",
            )


@router.get("/{organization_id}/integration-keys", response_model=IntegrationKeyListResponse)
async def list_integration_keys(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> IntegrationKeyListResponse:
    """
    List integration keys for the organization.
    
    Requires the user to be a member of the organization.
    """
    # Check if user has access
    from app.repositories.organization import OrganizationRepository
    org_repo = OrganizationRepository()
    user_role = await org_repo.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )
    
    try:
        # Get integration keys
        keys, total = await integration_key_service.list_by_organization(
            db,
            organization_id=organization_id,
            skip=pagination.skip,
            limit=pagination.limit,
            is_active=is_active,
        )
        
        return IntegrationKeyListResponse(
            items=[IntegrationKeyResponse.model_validate(key) for key in keys],
            total=total,
            page=pagination.skip // pagination.limit + 1,
            size=pagination.limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing integration keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list integration keys",
        )


@router.get("/{organization_id}/integration-keys/{key_id}", response_model=IntegrationKeyResponse)
async def get_integration_key(
    organization_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IntegrationKeyResponse:
    """
    Get details of a specific integration key.
    
    Requires the user to be a member of the organization.
    """
    # Check if user has access
    from app.repositories.organization import OrganizationRepository
    org_repo = OrganizationRepository()
    user_role = await org_repo.get_user_role(
        db, organization_id=organization_id, user_id=current_user.id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )
    
    try:
        # Get integration key
        integration_key = await integration_key_service.get(db, key_id)
        
        if not integration_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration key not found",
            )
        
        # Verify it belongs to the organization
        if integration_key.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration key not found",
            )
        
        return IntegrationKeyResponse.model_validate(integration_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integration key",
        )


@router.put("/{organization_id}/integration-keys/{key_id}", response_model=IntegrationKeyResponse)
async def update_integration_key(
    organization_id: str,
    key_id: str,
    update_data: IntegrationKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> IntegrationKeyResponse:
    """
    Update an integration key.
    
    Requires ADMIN or OWNER role in the organization.
    """
    async with uow:
        # Check user role
        user_role = await uow.organizations.get_user_role(
            db, organization_id=organization_id, user_id=current_user.id
        )
        
        if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can update integration keys",
            )
        
        try:
            # Get integration key to verify ownership
            integration_key = await integration_key_service.get(db, key_id)
            
            if not integration_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration key not found",
                )
            
            # Verify it belongs to the organization
            if integration_key.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration key not found",
                )
            
            # Update integration key
            updated_key = await integration_key_service.update(db, key_id, update_data)
            
            await uow.commit()
            
            logger.info(f"Integration key {key_id} updated")
            
            return IntegrationKeyResponse.model_validate(updated_key)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating integration key: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update integration key",
            )


@router.delete("/{organization_id}/integration-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_integration_key(
    organization_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> None:
    """
    Revoke (soft delete) an integration key.
    
    Requires ADMIN or OWNER role in the organization.
    """
    async with uow:
        # Check user role
        user_role = await uow.organizations.get_user_role(
            db, organization_id=organization_id, user_id=current_user.id
        )
        
        if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can revoke integration keys",
            )
        
        try:
            # Get integration key to verify ownership
            integration_key = await integration_key_service.get(db, key_id)
            
            if not integration_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration key not found",
                )
            
            # Verify it belongs to the organization
            if integration_key.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Integration key not found",
                )
            
            # Revoke integration key
            await integration_key_service.revoke(db, key_id)
            
            await uow.commit()
            
            logger.info(f"Integration key {key_id} revoked by user {current_user.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking integration key: {e}")
            await uow.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke integration key",
            ) 