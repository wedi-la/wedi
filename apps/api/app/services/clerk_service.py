"""
Clerk authentication service for user verification and session management.
"""
from typing import Any, Dict, Optional, Union
import os
import httpx

from clerk_backend_api import Clerk as ClerkAPI, authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions, RequestState
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.logging import get_logger
from app.models import User, AuthProvider
from app.repositories.user import UserRepository
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


class ClerkService:
    """Service for interacting with Clerk authentication."""

    def __init__(self):
        """Initialize the Clerk client."""
        # Check for required API keys
        if not settings.CLERK_SECRET_KEY:
            logger.warning(
                "CLERK_SECRET_KEY not set. Clerk authentication will not function properly."
            )

        # Create Clerk API client
        self.clerk_api = ClerkAPI(bearer_auth=settings.CLERK_SECRET_KEY)

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a Clerk session token.

        Args:
            token: The session token to verify

        Returns:
            Dict containing the decoded token data

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Create a mock request with the token in Authorization header
            mock_request = httpx.Request(
                "GET", "/", headers={"Authorization": f"Bearer {token}"}
            )

            # Use the authenticate_request helper to validate the token
            auth_options = AuthenticateRequestOptions(
                allowed_syncing_strategies=["immediate"]
            )
            if settings.CLERK_JWT_VERIFICATION_KEY:
                auth_options.jwt_key = settings.CLERK_JWT_VERIFICATION_KEY

            request_state = authenticate_request(
                mock_request,
                auth_options
            )

            if not request_state.is_signed_in:
                logger.warning(
                    "Token verification failed",
                    reason=request_state.reason
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )

            logger.debug(
                "Token verified successfully",
                session_id=request_state.payload.get("sid")
            )
            return request_state.payload

        except Exception as e:
            logger.warning("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    async def get_user_by_token(self, token: str) -> Dict[str, Any]:
        """
        Get user data from a Clerk session token.

        Args:
            token: The session token

        Returns:
            Dict containing user data

        Raises:
            HTTPException: If user not found or token invalid
        """
        try:
            # Verify token first
            decoded = await self.verify_token(token)

            # Get user ID from token
            user_id = decoded.get("sub")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user identifier in token",
                )

            # Get user from Clerk
            user_response = self.clerk_api.users.get(id=user_id)
            return user_response.to_dict()

        except Exception as e:
            logger.warning("Failed to get user from Clerk", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    async def create_or_update_local_user(
        self, db, clerk_user_data: Dict[str, Any], user_repository: UserRepository
    ) -> User:
        """
        Create or update a local user record based on Clerk user data.

        Args:
            db: Database session
            clerk_user_data: User data from Clerk
            user_repository: User repository instance

        Returns:
            Local user record
        """
        clerk_id = clerk_user_data.get("id")

        # Extract primary email and verification status
        email_addresses = clerk_user_data.get("email_addresses", [])
        primary_email_obj = None
        email = None
        email_verified_status = False

        if email_addresses:
            # Try to find the email address explicitly marked as primary,
            # or if not available, the one matching primary_email_address_id
            # or fallback to the first email.
            primary_email_obj = next((e for e in email_addresses if e.get("id") == clerk_user_data.get("primary_email_address_id")), None)
            if not primary_email_obj: # Fallback to first email if no primary_email_address_id or it's not in the list
                 primary_email_obj = email_addresses[0]

            if primary_email_obj:
                email = primary_email_obj.get("email_address")
                if primary_email_obj.get("verification") and primary_email_obj.get("verification").get("status") == "verified":
                    email_verified_status = True

        if not clerk_id or not email:
            logger.error(
                "Invalid Clerk user data",
                clerk_id=clerk_id,
                email_present=bool(email),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user data from authentication provider",
            )

        # Try to find existing user by clerk_id
        existing_user = await user_repository.get_by_auth_provider(db, provider=AuthProvider.CLERK, provider_id=clerk_id)

        # If not found by clerk_id, try by email
        if not existing_user and email:
            existing_user = await user_repository.get_by_email(db, email=email)

        # If user exists, update clerk_id (if needed) and other details
        if existing_user:
            user_data = {
                "auth_provider_id": clerk_id,
                "email": email,
                "name": (clerk_user_data.get("first_name", "") + " " + clerk_user_data.get("last_name", "")).strip() or existing_user.name,
                "auth_provider": AuthProvider.CLERK,
                "email_verified": email_verified_status,
                "avatar_url": clerk_user_data.get("image_url") or clerk_user_data.get("profile_image_url") or existing_user.avatar_url, # Assuming existing_user.avatar_url
            }

            updated_user = await user_repository.update(db, db_obj=existing_user, obj_in=user_data)
            logger.info("Updated user from Clerk data", user_id=str(updated_user.id))
            return updated_user

        # Create new user
        user_data = {
            "auth_provider_id": clerk_id,
            "email": email,
            "name": (clerk_user_data.get("first_name", "") + " " + clerk_user_data.get("last_name", "")).strip(),
            "auth_provider": AuthProvider.CLERK,
            "email_verified": email_verified_status,
            "avatar_url": clerk_user_data.get("image_url") or clerk_user_data.get("profile_image_url"),
        }

        new_user = await user_repository.create(db, obj_in=user_data)
        logger.info("Created new user from Clerk data", user_id=str(new_user.id))
        return new_user

    async def sync_user_data(
        self, user: User, clerk_user_data: Dict[str, Any], user_repository: UserRepository, db
    ) -> User:
        """
        Synchronize local user record with the latest data from Clerk.

        Args:
            user: Local user record
            clerk_user_data: Current user data from Clerk
            user_repository: User repository instance
            db: Database session

        Returns:
            Updated user record
        """
        update_needed = False
        user_data = {}

        # Check for fields that need updating
        full_name = (clerk_user_data.get("first_name", "") + " " + clerk_user_data.get("last_name", "")).strip()
        if full_name and full_name != user.name: # Assuming 'user' is the local SQLAlchemy User object
            user_data["name"] = full_name
            update_needed = True

        email = clerk_user_data.get("email_addresses", [{}])[0].get("email_address")
        if email and email != user.email:
            user_data["email"] = email
            update_needed = True

        # Simplified logic for subtask - robustly find primary email and its verification status
        primary_email_obj = next((e for e in clerk_user_data.get("email_addresses", []) if e.get("id") == clerk_user_data.get("primary_email_address_id")), None)
        clerk_email_verified = False
        if primary_email_obj and primary_email_obj.get("verification") and primary_email_obj.get("verification").get("status") == "verified":
            clerk_email_verified = True

        if hasattr(user, 'email_verified') and clerk_email_verified != user.email_verified:
            user_data["email_verified"] = clerk_email_verified
            update_needed = True
        # Fallback for older schema or direct attribute name if different (less likely for Pydantic alignment)
        elif hasattr(user, 'emailVerified') and clerk_email_verified != user.emailVerified:
            user_data["email_verified"] = clerk_email_verified # Still assign to snake_case for consistency towards repo
            update_needed = True

        clerk_avatar_url = clerk_user_data.get("image_url") or clerk_user_data.get("profile_image_url")
        if hasattr(user, 'avatar_url') and clerk_avatar_url and clerk_avatar_url != user.avatar_url:
            user_data["avatar_url"] = clerk_avatar_url
            update_needed = True
        # Fallback for older schema or direct attribute name
        elif hasattr(user, 'avatarUrl') and clerk_avatar_url and clerk_avatar_url != user.avatarUrl:
            user_data["avatar_url"] = clerk_avatar_url # Still assign to snake_case
            update_needed = True

        # Only update if needed
        if update_needed:
            updated_user = await user_repository.update(db, db_obj=user, obj_in=user_data)
            logger.info("Synchronized user data with Clerk", user_id=str(updated_user.id))
            return updated_user

        return user

    async def verify_webhook_signature(self, signature: str, payload: bytes) -> bool:
        """
        Verify a webhook signature from Clerk.

        Args:
            signature: The svix signature from request headers
            payload: The request body as bytes

        Returns:
            True if signature is valid, False otherwise
        """
        if not settings.CLERK_WEBHOOK_SECRET:
            logger.warning(
                "CLERK_WEBHOOK_SECRET not set, webhook verification disabled"
            )
            return True

        try:
            # Clerk Backend API already uses svix internally for webhook verification
            # Import svix for webhook signature verification
            from svix.webhooks import Webhook, WebhookVerificationError

            wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
            try:
                wh.verify(payload.decode("utf-8"), {"svix-signature": signature})
                return True
            except WebhookVerificationError as e:
                logger.error("Webhook signature verification failed", error=str(e))
                return False
        except Exception as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return False


# Create a singleton instance
clerk_service = ClerkService()
