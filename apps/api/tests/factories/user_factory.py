"""
User factory for generating test data.
"""
import uuid
from datetime import datetime, timezone

from app.core.security import get_password_hash
from app.models import User, Wallet


class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_user_data(**overrides):
        """Generate user data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password_hash": get_password_hash("Test123!"),
            "display_name": "Test User",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def create_wallet_data(user_id: str, **overrides):
        """Generate wallet data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "address": f"0x{uuid.uuid4().hex[:40]}",
            "chain": "ethereum",
            "is_primary": True,
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        return data
    
    @staticmethod
    async def create_user(db_session, **overrides):
        """Create and persist a test user."""
        user_data = UserFactory.create_user_data(**overrides)
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @staticmethod
    async def create_user_with_wallet(db_session, **user_overrides):
        """Create a user with an associated wallet."""
        user = await UserFactory.create_user(db_session, **user_overrides)
        
        wallet_data = UserFactory.create_wallet_data(user.id)
        wallet = Wallet(**wallet_data)
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)
        
        return user, wallet 