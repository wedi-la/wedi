"""
Authentication endpoints compatible with thirdweb auth.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_unit_of_work,
    get_user_repository,
    get_organization_repository,
    get_current_user,
)
from app.core.logging import get_logger
from app.db.session import get_db
from app.models import User
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.schemas.auth import (
    SIWEPayloadRequest,
    SIWEPayload,
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    CurrentUserResponse,
)
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)


@router.post("/payload", response_model=SIWEPayload)
async def generate_payload(
    request: SIWEPayloadRequest,
) -> SIWEPayload:
    """
    Generate a SIWE (Sign-In with Ethereum) payload for the frontend to sign.
    
    This endpoint is called by the thirdweb ConnectButton to get a message
    that the user will sign with their wallet.
    """
    logger.info(f"Generating SIWE payload for address: {request.address}")
    
    try:
        payload = await AuthService.generate_siwe_payload(request)
        return payload
    except Exception as e:
        logger.error(f"Error generating SIWE payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication payload"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> LoginResponse:
    """
    Verify the signed SIWE message and create a session.
    
    This endpoint is called after the user signs the SIWE message with their wallet.
    It verifies the signature and returns JWT tokens for authentication.
    """
    logger.info(f"Login attempt for address: {login_request.payload.address}")
    
    try:
        response = await AuthService.verify_and_login(
            db,
            user_repository,
            organization_repository,
            login_request
        )
        
        logger.info(f"Successful login for user: {response.user.id}")
        return response
        
    except UnauthorizedException as e:
        logger.warning(f"Unauthorized login attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
) -> TokenRefreshResponse:
    """
    Refresh access token using refresh token.
    
    This endpoint is used to get a new access token when the current one expires.
    """
    try:
        response = await AuthService.refresh_tokens(
            db,
            user_repository,
            refresh_request
        )
        return response
        
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Logout the current user.
    
    This endpoint invalidates the user's session. Currently, logout is handled
    client-side by removing tokens. In production, implement token blacklisting.
    """
    await AuthService.logout(str(current_user.id))
    logger.info(f"User logged out: {current_user.id}")


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> CurrentUserResponse:
    """
    Get current user information.
    
    Returns detailed information about the authenticated user including
    their organizations.
    """
    user_data = await AuthService.get_current_user(
        db,
        user_repository,
        organization_repository,
        str(current_user.id)
    )
    
    return CurrentUserResponse(**user_data) 