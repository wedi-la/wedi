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
from app.core.security import decode_token, verify_token_type
from app.db.session import get_db
from app.repositories.user import UserRepository

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
        "/api/v1/auth/payload",  # For thirdweb SIWE payload generation
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
        # Check if path is public
        if self._is_public_path(request.url.path):
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
            
            # Decode and validate token
            payload = decode_token(token)
            
            # Verify it's an access token
            if not verify_token_type(payload, "access"):
                logger.warning("Invalid token type")
                request.state.user = None
                request.state.user_id = None
                return await call_next(request)
            
            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No subject in token")
                request.state.user = None
                request.state.user_id = None
                return await call_next(request)
            
            # Attach user ID to request
            request.state.user_id = user_id
            
            # Optional: Load full user object (expensive, do only if needed)
            # This could be moved to a dependency instead
            if request.url.path.startswith("/api/v1/") and not request.url.path.startswith("/api/v1/auth/"):
                async with get_db() as db:
                    user_repo = UserRepository()
                    user = await user_repo.get(db, id=user_id)
                    if not user:
                        logger.warning(f"User {user_id} not found")
                        request.state.user = None
                        request.state.user_id = None
                    else:
                        request.state.user = user
            else:
                request.state.user = None
            
        except (ValueError, JWTError) as e:
            logger.warning(f"JWT validation error: {e}")
            request.state.user = None
            request.state.user_id = None
        
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
        payload = decode_token(credentials.credentials)
        
        if not verify_token_type(payload, "access"):
            return None
        
        user_id = payload.get("sub")
        return user_id
    
    except (JWTError, Exception) as e:
        logger.warning(f"Token validation error: {e}")
        return None


def require_auth(credentials: HTTPAuthorizationCredentials = security) -> str:
    """
    Dependency that requires valid authentication.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = decode_token(credentials.credentials)
        
        if not verify_token_type(payload, "access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
    
    except JWTError as e:
        logger.warning(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) 