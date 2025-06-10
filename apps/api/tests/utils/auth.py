"""
Authentication utilities for testing.
"""
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.models import User


def create_test_token(user: User, expires_delta: timedelta = None) -> str:
    """Create a test JWT token for a user."""
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    token_data = {
        "sub": user.id,
        "email": user.email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = jwt.encode(
        token_data,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def get_auth_headers(user: User) -> dict:
    """Get authorization headers for a user."""
    token = create_test_token(user)
    return {"Authorization": f"Bearer {token}"}


def get_expired_auth_headers(user: User) -> dict:
    """Get expired authorization headers for testing."""
    token = create_test_token(user, expires_delta=timedelta(minutes=-1))
    return {"Authorization": f"Bearer {token}"} 