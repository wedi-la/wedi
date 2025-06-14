"""
User factory for generating test data.
"""
import uuid
from datetime import datetime, timezone

from app.models import User, Wallet, AuthProvider


class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_user_data(**overrides):
        """Generate user data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "name": "Test User",
            "auth_provider": AuthProvider.CLERK,  # Using wallet auth
            "auth_provider_id": f"0x{uuid.uuid4().hex[:40]}",  # Mock wallet address
            "email_verified": True,  # Auto-verified for wallet users
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
            "chain_id": 1,  # Ethereum mainnet
            "type": "EOA",
            "is_active": True,
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
        # Use the same address for auth_provider_id if not specified
        if "auth_provider_id" not in user_overrides:
            user_overrides["auth_provider_id"] = f"0x{uuid.uuid4().hex[:40]}"
            
        user = await UserFactory.create_user(db_session, **user_overrides)
        
        # Create wallet with the same address as auth_provider_id
        wallet_data = UserFactory.create_wallet_data(
            user_id=user.id,
            address=user.auth_provider_id
        )
        wallet = Wallet(**wallet_data)
        db_session.add(wallet)
        
        # Update user with primary wallet
        user.primary_wallet_id = wallet.id
        db_session.add(user)
        
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(wallet)
        
        return user, wallet 