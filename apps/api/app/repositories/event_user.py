"""
Event-aware user repository example.

This demonstrates how to integrate domain events with repositories.
"""
from typing import Optional

from app.events.domain_events import (
    UserCreatedEvent,
    UserVerifiedEvent,
    UserWalletLinkedEvent,
)
from app.events.publisher import DomainEvent
from app.models.generated import User
from app.repositories.event_repository import EventRepository
from app.schemas.user import UserCreate, UserUpdate


class EventUserRepository(EventRepository[User, UserCreate, UserUpdate]):
    """User repository with event emission."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(User)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Users are not scoped to organizations."""
        return None
    
    async def _emit_created_event(
        self,
        entity: User,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Emit user created event.
        
        Args:
            entity: Created user
            organization_id: Not used for users
            
        Returns:
            UserCreatedEvent
        """
        return UserCreatedEvent(
            user_id=str(entity.id),
            email=entity.email,
            auth_provider=entity.auth_provider
        )
    
    async def _emit_updated_event(
        self,
        entity: User,
        changes: dict,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Emit user updated events based on changes.
        
        Args:
            entity: Updated user
            changes: Dictionary of changed fields
            organization_id: Not used for users
            
        Returns:
            Domain event or None
        """
        # Check if email was verified
        if "email_verified" in changes and changes["email_verified"]["new"] is True:
            return UserVerifiedEvent(
                user_id=str(entity.id),
                email=entity.email
            )
        
        # Check if wallet was linked
        if "primary_wallet_id" in changes and changes["primary_wallet_id"]["new"] is not None:
            # Would need to get wallet details in real implementation
            return UserWalletLinkedEvent(
                user_id=str(entity.id),
                wallet_id=changes["primary_wallet_id"]["new"],
                wallet_address="0x..."  # Would fetch from wallet
            )
        
        # For other updates, we might not emit events
        return None
    
    async def verify_email(
        self,
        db,
        *,
        user: User
    ) -> User:
        """Verify user's email address.
        
        Args:
            db: Database session
            user: User to verify
            
        Returns:
            Updated user
        """
        from app.schemas.user import UserUpdate
        
        # Update user
        update_data = UserUpdate(email_verified=True)
        updated_user = await self.update(
            db,
            db_obj=user,
            obj_in=update_data
        )
        
        # The update method will automatically emit UserVerifiedEvent
        # due to our _emit_updated_event implementation
        
        return updated_user 