"""
JWT Authentication middleware.

This middleware handles JWT token validation and user authentication
for protected endpoints.
"""
import re
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.security import decode_token, verify_token_type # decode_token and verify_token_type might be removed later if not used
from app.db.session import get_db
from app.repositories.user import UserRepository
from app.services.clerk_service import clerk_service
from app.models import AuthProvider

logger = get_logger(__name__)

# HTTP Bearer scheme for Swagger UI
security = HTTPBearer(auto_error=False)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware.
    
    This middleware:
    1. Extracts JWT tokens from Authorization header
    2. Validates and decodes the token
    3. Attaches user information to the request state
    4. Allows public endpoints to pass through
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/status",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/payload",  # For Clerk + Circle SIWE payload generation
        "/api/v1/auth/validate-key",  # For integration key validation
    }
    
    # Path prefixes that are always public
    PUBLIC_PATH_PREFIXES = {
        "/static",
        "/public",
    }
    
    # Path patterns that are public (regex patterns)
    PUBLIC_PATH_PATTERNS = [
        re.compile(r"^/api/v1/payment-links/by-short-code/[a-z0-9]+$"),
    ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and validate JWT token if present.
        
        Args:
            request: Incoming request
            call_next: Next middleware or endpoint
            
        Returns:
            Response from the endpoint
        """
        request.state.active_org_id = None
        request.state.active_org_role = None
        request.state.active_org_permissions = None

        # Check if path is public
        if self._is_public_path(request.url.path):
            # For public paths, user and user_id should also be explicitly None
            request.state.user = None
            request.state.user_id = None
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # No auth header - let endpoint decide if auth is required
            request.state.user = None
            request.state.user_id = None
            return await call_next(request)
        
        try:
            # Parse Bearer token
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid auth scheme: {scheme}")
                request.state.user = None
                request.state.user_id = None
                return await call_next(request)
            
            # Validate token using ClerkService
            payload = await clerk_service.verify_token(token) # This will raise HTTPException on failure
            
            # Extract user ID
            clerk_user_id = payload.get("sub")
            if not clerk_user_id:
                logger.warning("No subject in token after Clerk verification") # Should ideally not happen if verify_token succeeds
                request.state.user = None
                request.state.user_id = None
                return await call_next(request)
            
            # Attach user ID to request
            request.state.user_id = clerk_user_id

            # Extract organization details from Clerk token
            request.state.active_org_id = payload.get("org_id")
            request.state.active_org_role = payload.get("org_role")
            request.state.active_org_permissions = payload.get("org_permissions") # Or "permissions" if that's the claim name

            logger.debug(
                "Clerk org claims extracted",
                org_id=request.state.active_org_id,
                org_role=request.state.active_org_role,
            )
            
            # Optional: Load full user object (expensive, do only if needed)
            # This could be moved to a dependency instead
            if request.url.path.startswith("/api/v1/") and not request.url.path.startswith("/api/v1/auth/"):
                async with get_db() as db:
                    user_repo = UserRepository()
                    user = await user_repo.get_by_auth_provider(db, provider=AuthProvider.CLERK, provider_id=clerk_user_id)
                    if not user:
                        logger.warning(f"User with Clerk ID {clerk_user_id} not found in local DB")
                        # Decide handling: either user is None, or raise error, or try to create/sync.
                        # For now, let's set user to None and keep request.state.user_id as clerk_user_id.
                        request.state.user = None
                    else:
                        request.state.user = user
                        # Optional: If request.state.user_id is intended to be the internal DB user ID
                        # request.state.user_id = user.id
                        # However, the plan is to keep it as Clerk's user ID from the token. So, the line above is commented out.
            else:
                request.state.user = None
            
        except (ValueError, JWTError, HTTPException) as e: # Added HTTPException here
            logger.warning(f"JWT validation error: {e}")
            request.state.user = None
            request.state.user_id = None
            request.state.active_org_id = None
            request.state.active_org_role = None
            request.state.active_org_permissions = None
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if the path is public and doesn't require authentication.
        
        Args:
            path: Request path
            
        Returns:
            True if path is public
        """
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True
        
        # Prefix match
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        
        # Pattern match
        for pattern in self.PUBLIC_PATH_PATTERNS:
            if pattern.match(path):
                return True
        
        return False


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[str]:
    """
    Extract and validate user ID from JWT token.
    
    This is a dependency function that can be used in endpoints.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID if valid token, None otherwise
    """
    if not credentials:
        return None
    
    try:
        payload = await clerk_service.verify_token(credentials.credentials)
        user_id = payload.get("sub") # This is the Clerk User ID
        return user_id
    
    except HTTPException: # Catch HTTPException from verify_token
        logger.warning("Token validation failed in get_current_user_from_token")
        return None
    except (JWTError, Exception) as e: # Keep other generic error handling if necessary
        logger.warning(f"Token validation error: {e}")
        return None


async def require_auth(credentials: HTTPAuthorizationCredentials = security) -> str:
    """
    Dependency that requires valid authentication.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If not authenticated or token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # No try-except here, as verify_token will raise HTTPException
    # which FastAPI will handle, effectively replacing the old error raising.
    payload = await clerk_service.verify_token(credentials.credentials)
    
    user_id = payload.get("sub") # This is the Clerk User ID
    if not user_id:
        # This case should ideally be covered by verify_token raising an exception
        # if the token is malformed or doesn't contain a sub.
        # However, keeping it as a safeguard.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: No user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id