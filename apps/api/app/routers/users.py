"""
User management endpoints.

This module provides API endpoints for managing users,
including profile management and wallet operations.
"""
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_pagination,
    get_unit_of_work,
    get_user_repository,
    get_wallet_repository,
    PaginationParams,
    require_organization_context,
)
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.db.session import get_db
from app.models import User, UserRole, WalletType
from app.repositories.user import UserRepository
from app.repositories.wallet import WalletRepository
from app.schemas.organization import OrganizationMembership
from app.schemas.user import (
    User as UserSchema,
    UserUpdate,
    UserWithOrganizations,
)
from app.schemas.wallet import Wallet, WalletCreate

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
    },
)


async def check_admin_permission(
    current_user: User,
    organization_context: Optional[dict] = None,
) -> None:
    """
    Check if user has admin permissions.
    
    Args:
        current_user: Current authenticated user
        organization_context: Optional organization context
        
    Raises:
        ForbiddenException: If user doesn't have admin permissions
    """
    # If there's an organization context, check role in that org
    if organization_context and organization_context.get("organization_id"):
        user_role = organization_context.get("user_role")
        if user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("Admin access required")
    else:
        # System-wide admin check would go here
        # For now, we don't have system admins
        raise ForbiddenException("Admin access required")


@router.get("/me", response_model=UserWithOrganizations)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserWithOrganizations:
    """
    Get current user's profile with organizations.
    
    Returns the authenticated user's complete profile including
    their organization memberships.
    """
    # Get user's organizations
    organizations = await user_repository.get_organizations(
        db, user_id=current_user.id
    )
    
    # Get membership details for each organization
    memberships = []
    for org in organizations:
        # Get user's membership in this org
        from app.repositories.organization import OrganizationRepository
        org_repo = OrganizationRepository()
        
        members = await org_repo.get_members(
            db,
            organization_id=org.id,
            skip=0,
            limit=1000
        )
        
        # Find this user's membership
        for member in members:
            if member.user_id == current_user.id:
                # Convert to OrganizationMembership schema
                membership_data = {
                    "id": member.id,
                    "organization_id": member.organization_id,
                    "user_id": member.user_id,
                    "role": member.role,
                    "permissions": member.permissions,
                    "is_active": member.is_active,
                    "invited_by": member.invited_by,
                    "invited_at": member.invited_at,
                    "accepted_at": member.accepted_at,
                    "organization": org,
                }
                memberships.append(OrganizationMembership(**membership_data))
                break
    
    # Create response
    user_data = UserSchema.model_validate(current_user).model_dump()
    user_data["organizations"] = memberships
    
    return UserWithOrganizations(**user_data)


@router.put("/me", response_model=UserSchema)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserSchema:
    """
    Update current user's profile.
    
    Users can update their own name, avatar, and primary wallet.
    Email cannot be changed through this endpoint.
    """
    logger.info(f"Updating profile for user: {current_user.id}")
    
    # Update user
    updated_user = await user_repository.update(
        db, id=current_user.id, data=user_update
    )
    
    return UserSchema.model_validate(updated_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> None:
    """
    Delete current user's account.
    
    This will remove the user and all associated data.
    This action cannot be undone.
    """
    logger.warning(f"User {current_user.id} is deleting their account")
    
    async with uow:
        # Check if user owns any organizations
        organizations = await uow.users.get_organizations(
            db, user_id=current_user.id
        )
        
        owned_orgs = []
        for org in organizations:
            # Check if user is owner
            role = await uow.organizations.get_user_role(
                db, organization_id=org.id, user_id=current_user.id
            )
            if role == UserRole.OWNER:
                owned_orgs.append(org.name)
        
        if owned_orgs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete account while owning organizations: {', '.join(owned_orgs)}. "
                       "Please transfer ownership or delete these organizations first.",
            )
        
        # Remove user from all organizations
        for org in organizations:
            await uow.organizations.remove_member(
                db, organization_id=org.id, user_id=current_user.id
            )
        
        # Delete user's wallets
        wallets = await uow.wallets.list(
            db, filters={"user_id": current_user.id}
        )
        for wallet in wallets:
            await uow.wallets.delete(db, id=wallet.id)
        
        # Delete user
        await uow.users.delete(db, id=current_user.id)
        
        await uow.commit()
        
        logger.info(f"User {current_user.id} account deleted successfully")


@router.get("", response_model=List[UserSchema])
async def list_users(
    current_user: User = Depends(get_current_user),
    organization_context: Optional[dict] = Depends(require_organization_context),
    pagination: PaginationParams = Depends(get_pagination),
    email_filter: Optional[str] = Query(None, description="Filter by email"),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> List[UserSchema]:
    """
    List users (admin only).
    
    If organization context is provided, lists users in that organization.
    Otherwise, requires system admin permissions.
    """
    # Check admin permissions
    await check_admin_permission(current_user, organization_context)
    
    if organization_context and organization_context.get("organization_id"):
        # List users in specific organization
        from app.repositories.organization import OrganizationRepository
        org_repo = OrganizationRepository()
        
        members = await org_repo.get_members(
            db,
            organization_id=organization_context["organization_id"],
            skip=pagination.skip,
            limit=pagination.limit,
        )
        
        # Get user details for each member
        users = []
        for member in members:
            user = await user_repository.get(db, id=member.user_id)
            if user and (not email_filter or email_filter.lower() in user.email.lower()):
                users.append(user)
        
        return [UserSchema.model_validate(user) for user in users]
    else:
        # System-wide user list (not implemented for security)
        raise ForbiddenException("System-wide user listing not available")


@router.get("/{user_id}", response_model=UserWithOrganizations)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    organization_context: Optional[dict] = Depends(require_organization_context),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserWithOrganizations:
    """
    Get user details (admin only or self).
    
    Users can view their own profile. Admins can view any user
    in their organization.
    """
    # Allow users to view their own profile
    if user_id == str(current_user.id):
        return await get_current_user_profile(current_user, db, user_repository)
    
    # Otherwise, check admin permissions
    await check_admin_permission(current_user, organization_context)
    
    # Get user
    user = await user_repository.get_or_404(db, id=user_id)
    
    # If organization context, verify user is in that org
    if organization_context and organization_context.get("organization_id"):
        user_orgs = await user_repository.get_organizations(
            db, user_id=user_id
        )
        org_ids = [org.id for org in user_orgs]
        if organization_context["organization_id"] not in org_ids:
            raise NotFoundException("User not found in this organization")
    
    # Get user's organizations with membership details
    organizations = await user_repository.get_organizations(
        db, user_id=user_id
    )
    
    # Convert to response format
    user_data = UserSchema.model_validate(user).model_dump()
    user_data["organizations"] = []  # Simplified for admin view
    
    return UserWithOrganizations(**user_data)


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    organization_context: Optional[dict] = Depends(require_organization_context),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserSchema:
    """
    Update user (admin only).
    
    Admins can update users in their organization.
    """
    # Check admin permissions
    await check_admin_permission(current_user, organization_context)
    
    # Get user
    user = await user_repository.get_or_404(db, id=user_id)
    
    # If organization context, verify user is in that org
    if organization_context and organization_context.get("organization_id"):
        user_orgs = await user_repository.get_organizations(
            db, user_id=user_id
        )
        org_ids = [org.id for org in user_orgs]
        if organization_context["organization_id"] not in org_ids:
            raise NotFoundException("User not found in this organization")
    
    # Update user
    updated_user = await user_repository.update(
        db, id=user_id, data=user_update
    )
    
    logger.info(f"User {user_id} updated by admin {current_user.id}")
    return UserSchema.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    organization_context: Optional[dict] = Depends(require_organization_context),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> None:
    """
    Delete user (admin only).
    
    This will remove the user from the organization or delete
    their account entirely based on context.
    """
    # Check admin permissions
    await check_admin_permission(current_user, organization_context)
    
    async with uow:
        # If organization context, just remove from org
        if organization_context and organization_context.get("organization_id"):
            removed = await uow.organizations.remove_member(
                db,
                organization_id=organization_context["organization_id"],
                user_id=user_id,
            )
            if not removed:
                raise NotFoundException("User not found in this organization")
            
            logger.info(
                f"User {user_id} removed from organization "
                f"{organization_context['organization_id']} by admin {current_user.id}"
            )
        else:
            # Full account deletion (not implemented for safety)
            raise ForbiddenException("Full account deletion requires user consent")
        
        await uow.commit()


@router.get("/{user_id}/organizations", response_model=List[OrganizationMembership])
async def get_user_organizations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> List[OrganizationMembership]:
    """
    Get user's organizations.
    
    Users can view their own organizations. Admins can view
    any user's organizations.
    """
    # Allow users to view their own organizations
    if user_id != str(current_user.id):
        # For other users, would need admin check
        # For now, just return forbidden
        raise ForbiddenException("Cannot view other users' organizations")
    
    # Get organizations
    organizations = await user_repository.get_organizations(
        db, user_id=user_id
    )
    
    # Convert to membership format (simplified)
    memberships = []
    for org in organizations:
        membership = OrganizationMembership(
            id=f"{org.id}-{user_id}",  # Synthetic ID
            organization_id=org.id,
            user_id=user_id,
            role=UserRole.VIEWER,  # Default, would need actual lookup
            permissions=[],
            is_active=True,
            invited_by=None,
            invited_at=org.created_at,
            accepted_at=org.created_at,
            organization=org,
        )
        memberships.append(membership)
    
    return memberships


@router.post("/{user_id}/wallets", response_model=Wallet, status_code=status.HTTP_201_CREATED)
async def add_user_wallet(
    user_id: str,
    wallet_data: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    wallet_repository: WalletRepository = Depends(get_wallet_repository),
) -> Wallet:
    """
    Add a wallet to user.
    
    Users can add wallets to their own account.
    The wallet address must be unique.
    """
    # Users can only add wallets to their own account
    if user_id != str(current_user.id):
        raise ForbiddenException("Cannot add wallets to other users")
    
    logger.info(f"Adding wallet {wallet_data.address} to user {user_id}")
    
    # Create wallet
    create_data = wallet_data.model_dump()
    create_data["user_id"] = user_id
    create_data["id"] = str(uuid4())
    
    try:
        wallet = await wallet_repository.create(db, data=create_data)
        return Wallet.model_validate(wallet)
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Wallet address already exists",
            )
        raise


@router.delete("/{user_id}/wallets/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_wallet(
    user_id: str,
    wallet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    uow = Depends(get_unit_of_work),
) -> None:
    """
    Remove a wallet from user.
    
    Users can remove wallets from their own account.
    Cannot remove the primary wallet if it's the only one.
    """
    # Users can only remove wallets from their own account
    if user_id != str(current_user.id):
        raise ForbiddenException("Cannot remove wallets from other users")
    
    async with uow:
        # Get the wallet
        wallet = await uow.wallets.get_or_404(db, id=wallet_id)
        
        # Verify ownership
        if wallet.user_id != user_id:
            raise NotFoundException("Wallet not found")
        
        # Check if it's the primary wallet
        user = await uow.users.get(db, id=user_id)
        if user.primary_wallet_id == wallet_id:
            # Check if user has other wallets
            user_wallets = await uow.wallets.list(
                db, filters={"user_id": user_id}
            )
            if len(user_wallets) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the only wallet",
                )
            
            # Clear primary wallet
            await uow.users.update(
                db, id=user_id, data={"primary_wallet_id": None}
            )
        
        # Delete wallet
        await uow.wallets.delete(db, id=wallet_id)
        
        await uow.commit()
        
        logger.info(f"Wallet {wallet_id} removed from user {user_id}") 