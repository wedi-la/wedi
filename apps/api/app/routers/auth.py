"""
Authentication router for Clerk integration.

This router handles Clerk authentication, user info retrieval, and webhook processing.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_db, 
    get_user_repository
)
from app.core.config import settings
from app.core.logging import get_logger
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserOut, UserCreate
from app.services.clerk_service import clerk_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={
        401: {"description": "Unauthorized"},
    },
)

@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user info.
    
    This endpoint works with Clerk authentication through the
    middleware that verifies Clerk sessions.
    """
    return current_user


@router.get("/session-check")
async def session_check(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Check if the current session is valid.
    
    Returns user ID if authenticated, or null if not authenticated.
    This is a lightweight endpoint for frontend session validation.
    """
    if current_user:
        return {"authenticated": True, "user_id": str(current_user.id)}
    return {"authenticated": False, "user_id": None}


class ClerkWebhookEvent(BaseModel):
    """
    Clerk webhook event payload schema.
    
    Contains data specific to the event type and metadata.
    """
    data: Dict[str, Any]
    object: str
    type: str


@router.post("/webhooks/clerk")
async def clerk_webhook_handler(
    request: Request,
    event: ClerkWebhookEvent,
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """
    Handle Clerk webhook events.
    
    This endpoint processes user lifecycle events from Clerk such as:
    - user.created
    - user.updated
    - user.deleted
    - session.created
    - session.revoked
    """
    # Verify webhook signature
    signature = request.headers.get("svix-signature")
    if not signature:
        logger.warning("Missing webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature",
        )
    
    # Get webhook payload as bytes for signature verification
    body = await request.body()
    
    # Verify signature
    is_valid = await clerk_service.verify_webhook_signature(signature, body)
    if not is_valid:
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    event_type = event.type
    logger.info("Processing Clerk webhook", event_type=event_type)
    
    try:
        # Handle user events
        if event_type == "user.created":
            clerk_user_data = event.data
            await clerk_service.create_or_update_local_user(db, clerk_user_data, user_repository)
            return {"status": "success", "message": "User created"}
        
        elif event_type == "user.updated":
            clerk_user_data = event.data
            clerk_id = clerk_user_data.get("id")
            if not clerk_id:
                logger.error("Missing clerk_id in user.updated webhook")
                return {"status": "error", "message": "Missing clerk_id in event data"}
                
            user = await user_repository.get_by_clerk_id(db, clerk_id=clerk_id)
            if user:
                await clerk_service.sync_user_data(user, clerk_user_data, user_repository, db)
            else:
                # If user doesn't exist yet, create them
                await clerk_service.create_or_update_local_user(db, clerk_user_data, user_repository)
            return {"status": "success", "message": "User updated"}
        
        elif event_type == "user.deleted":
            clerk_id = event.data.get("id")
            if not clerk_id:
                logger.error("Missing clerk_id in user.deleted webhook")
                return {"status": "error", "message": "Missing clerk_id in event data"}
                
            user = await user_repository.get_by_clerk_id(db, clerk_id=clerk_id)
            if user:
                # Just mark as inactive (better for auditing)
                await user_repository.update(db, db_obj=user, obj_in={"is_active": False})
            return {"status": "success", "message": "User marked as deleted"}
        
        # Other event types (handle as needed)
        else:
            return {"status": "success", "message": f"Event {event_type} acknowledged"}
    
    except Exception as e:
        logger.exception("Error processing Clerk webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )


class UserInfoRequest(BaseModel):
    """Request to manually synchronize user data from Clerk."""
    clerk_id: str


@router.post("/sync-user-info")
async def sync_user_info(
    request: UserInfoRequest,
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
):
    """
    Manually synchronize user data from Clerk.
    
    This endpoint can be used to force a sync of user data
    from Clerk to the local database.
    """
    try:
        # Only allow sync of same user or by admins
        if not current_user.is_admin and current_user.clerk_id != request.clerk_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to sync other user data",
            )
            
        # Get user data from Clerk using clerk_service
        try:
            # Create a fake token to use the get_user_by_token method
            # In a real implementation, we would use a proper Clerk admin token
            # or a direct API call to get user data by ID
            clerk_user_data = await clerk_service.clerk_api.users.get(id=request.clerk_id)
        except Exception as e:
            logger.warning("User not found in Clerk", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Clerk",
            )
            
        # Find user in local database
        user = await user_repository.get_by_clerk_id(db, clerk_id=request.clerk_id)
        if not user:
            # Create user if it doesn't exist
            user = await clerk_service.create_or_update_local_user(
                db, clerk_user_data.to_dict(), user_repository
            )
            return {"status": "success", "message": "User created", "user_id": str(user.id)}
        else:
            # Update existing user
            user = await clerk_service.sync_user_data(
                user, clerk_user_data.to_dict(), user_repository, db
            )
            return {"status": "success", "message": "User updated", "user_id": str(user.id)}
    
    except Exception as e:
        logger.exception("Error syncing user data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing user data: {str(e)}",
        )


# Keep this empty to remove all legacy endpoints from line 220 onwards 