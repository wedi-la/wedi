from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets
import json
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.models import User, Organization, Wallet
from app.schemas.auth import (
    SIWEPayloadRequest,
    SIWEPayload,
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from app.core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    NotFoundException,
)


class AuthService:
    """Service for handling authentication operations compatible with thirdweb."""

    @staticmethod
    async def generate_siwe_payload(
        request: SIWEPayloadRequest
    ) -> SIWEPayload:
        """
        Generate a SIWE (Sign-In with Ethereum) payload for the frontend to sign.
        This is compatible with thirdweb's auth flow.
        """
        # Generate a secure nonce
        nonce = secrets.token_urlsafe(32)
        
        # Set expiration time (5 minutes from now)
        issued_at = datetime.now(timezone.utc)
        expiration_time = issued_at + timedelta(minutes=5)
        
        # Create the SIWE message following the standard format
        domain = settings.FRONTEND_URL or "localhost:3000"
        uri = f"https://{domain}"
        
        # Construct the SIWE message
        message = f"""{domain} wants you to sign in with your Ethereum account:
{request.address}

Sign in to Wedi

URI: {uri}
Version: 1
Chain ID: {request.chain_id or 1}
Nonce: {nonce}
Issued At: {issued_at.isoformat()}
Expiration Time: {expiration_time.isoformat()}"""

        return SIWEPayload(
            domain=domain,
            address=request.address,
            statement="Sign in to Wedi",
            uri=uri,
            version="1",
            chain_id=request.chain_id or 1,
            nonce=nonce,
            issued_at=issued_at.isoformat(),
            expiration_time=expiration_time.isoformat(),
            message=message,
        )

    @staticmethod
    async def verify_and_login(
        db: AsyncSession,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        login_request: LoginRequest
    ) -> LoginResponse:
        """
        Verify the signed SIWE message and create a session.
        This would normally use thirdweb's verifyPayload, but we'll verify manually.
        """
        payload = login_request.payload
        signature = login_request.signature
        
        # In production, you would verify the signature using web3 libraries
        # For now, we'll focus on the user creation/lookup flow
        
        # Extract address from payload
        address = payload.address.lower()
        
        # Check if user exists by wallet address
        user = await user_repository.get_by_wallet_address(
            db, wallet_address=address
        )
        
        if not user:
            # Create new user
            user = await AuthService._create_user_from_wallet(
                db, user_repository, address
            )
        
        # Check if user's email is verified (optional check)
        # For wallet auth, we can skip email verification since they're authenticating with wallet
        # if not user.email_verified:
        #     raise UnauthorizedException("Please verify your email address")
        
        # Get user's organizations
        organizations = await user_repository.get_organizations(
            db, user_id=user.id
        )
        
        # Create tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "wallet_address": user.wallet_address,
                "email": user.email,
            }
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user.id),
                "wallet_address": address,  # Use the address from the request
                "email": user.email,
                "name": user.name,
                "organizations": [
                    {
                        "id": str(org.id),
                        "name": org.name,
                        "slug": org.slug,
                    }
                    for org in organizations
                ],
            },
        )

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        user_repository: UserRepository,
        refresh_request: TokenRefreshRequest
    ) -> TokenRefreshResponse:
        """Refresh access token using refresh token."""
        try:
            # Decode refresh token
            payload = decode_token(refresh_request.refresh_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise UnauthorizedException("Invalid refresh token")
            
            # Get user
            user = await user_repository.get(db, id=user_id)
            if not user:
                raise UnauthorizedException("User not found")
            
            # Create new tokens
            access_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "wallet_address": user.wallet_address,
                    "email": user.email,
                }
            )
            
            new_refresh_token = create_refresh_token(
                data={"sub": str(user.id)}
            )
            
            return TokenRefreshResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
            
        except JWTError:
            raise UnauthorizedException("Invalid refresh token")

    @staticmethod
    async def logout(user_id: str) -> None:
        """
        Logout user. In a production environment, you might want to:
        - Invalidate the refresh token by storing it in a blacklist
        - Clear any server-side sessions
        - Emit a logout event
        """
        # For now, logout is handled client-side by removing tokens
        # In production, implement token blacklisting here
        pass

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        user_id: str
    ) -> Dict[str, Any]:
        """Get current user information."""
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Get user's organizations
        organizations = await user_repository.get_organizations(
            db, user_id=user.id
        )
        
        # Get primary wallet address if available
        wallet_address = None
        if user.primary_wallet_id:
            from app.repositories.wallet import WalletRepository
            wallet_repo = WalletRepository()
            wallet = await wallet_repo.get(db, id=user.primary_wallet_id)
            if wallet:
                wallet_address = wallet.address
        
        return {
            "id": str(user.id),
            "wallet_address": wallet_address,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified,
            "organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "slug": org.slug,
                }
                for org in organizations
            ],
        }

    @staticmethod
    async def _create_user_from_wallet(
        db: AsyncSession,
        user_repository: UserRepository,
        wallet_address: str
    ) -> User:
        """Create a new user from wallet address."""
        # Generate a placeholder email (users can update later)
        email = f"{wallet_address}@wallet.local"
        
        # Create user without wallet initially
        # The wallet will be created separately
        user_data = {
            "email": email,
            "name": f"User {wallet_address[:8]}",
            "email_verified": True,  # Auto-verify for wallet users
        }
        
        user = await user_repository.create(db, data=user_data)
        
        # Create wallet for the user
        from app.repositories.wallet import WalletRepository
        wallet_repo = WalletRepository()
        
        wallet_data = {
            "address": wallet_address,
            "chain_id": 1,  # Default to mainnet
            "user_id": user.id,
            "is_verified": True,
        }
        
        wallet = await wallet_repo.create(db, data=wallet_data)
        
        # Set as primary wallet
        await user_repository.set_primary_wallet(
            db, user_id=user.id, wallet_id=wallet.id
        )
        
        return user 