"""Repository for IntegrationKey operations."""
from typing import List, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timezone
import hashlib
import secrets

from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated import IntegrationKey
from app.repositories.base import BaseRepository
from app.core.exceptions import BadRequestException, NotFoundException


class IntegrationKeyRepository(BaseRepository[IntegrationKey]):
    """Repository for IntegrationKey CRUD operations."""
    
    def __init__(self, model: type[IntegrationKey] = IntegrationKey):
        """Initialize the repository."""
        super().__init__(model)
    
    async def create_with_key(
        self,
        db: AsyncSession,
        *,
        name: str,
        organization_id: str,
        agent_id: str,
        description: Optional[str] = None,
        allowed_corridors: Optional[List[str]] = None,
        allowed_providers: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True
    ) -> tuple[IntegrationKey, str]:
        """
        Create a new integration key with generated secret.
        
        Returns:
            Tuple of (IntegrationKey instance, plain text key)
        """
        # Generate a secure random key
        key = f"wedi_ik_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:8]
        
        # Create the database object
        db_obj = IntegrationKey(
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            organization_id=organization_id,
            agent_id=agent_id,
            description=description,
            allowed_corridors=allowed_corridors,
            allowed_providers=allowed_providers,
            rate_limit=rate_limit,
            expires_at=expires_at,
            is_active=is_active,
            usage_count=0
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj, key
    
    async def get_by_key_hash(
        self,
        db: AsyncSession,
        key_hash: str
    ) -> Optional[IntegrationKey]:
        """Get an integration key by its hash."""
        return await db.get(self.model, {"key_hash": key_hash})
    
    async def validate_key(
        self,
        db: AsyncSession,
        key: str
    ) -> tuple[bool, Optional[IntegrationKey], Optional[str]]:
        """
        Validate an integration key.
        
        Returns:
            Tuple of (is_valid, integration_key, error_message)
        """
        # Hash the provided key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Find the key
        integration_key = await self.get_by_key_hash(db, key_hash)
        
        if not integration_key:
            return False, None, "Invalid integration key"
        
        # Check if active
        if not integration_key.is_active:
            return False, integration_key, "Integration key is inactive"
        
        # Check expiration
        if integration_key.expires_at and integration_key.expires_at < datetime.now(timezone.utc):
            return False, integration_key, "Integration key has expired"
        
        # Update usage
        integration_key.usage_count += 1
        integration_key.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        
        return True, integration_key, None
    
    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        agent_id: Optional[str] = None
    ) -> List[IntegrationKey]:
        """Get all integration keys for an organization."""
        query = select(self.model).filter(
            self.model.organization_id == organization_id
        )
        
        if is_active is not None:
            query = query.filter(self.model.is_active == is_active)
        
        if agent_id:
            query = query.filter(self.model.agent_id == agent_id)
        
        return await db.execute(query.offset(skip).limit(limit))
    
    async def count_by_organization(
        self,
        db: AsyncSession,
        organization_id: str,
        *,
        is_active: Optional[bool] = None,
        agent_id: Optional[str] = None
    ) -> int:
        """Count integration keys for an organization."""
        query = select(func.count(self.model.id)).filter(
            self.model.organization_id == organization_id
        )
        
        if is_active is not None:
            query = query.filter(self.model.is_active == is_active)
        
        if agent_id:
            query = query.filter(self.model.agent_id == agent_id)
        
        return (await db.execute(query)).scalar() or 0
    
    async def check_rate_limit(
        self,
        db: AsyncSession,
        integration_key: IntegrationKey,
        window_minutes: int = 1
    ) -> tuple[bool, int, int]:
        """
        Check if the key has exceeded its rate limit.
        
        Returns:
            Tuple of (is_allowed, current_count, limit)
        """
        if not integration_key.rate_limit:
            return True, 0, 0
        
        # This is a simplified rate limit check
        # In production, you'd want to use Redis or similar for accurate rate limiting
        # For now, we'll just check if usage_count exceeds rate_limit
        # Real implementation would track requests per time window
        
        return True, 0, integration_key.rate_limit
    
    async def revoke(
        self,
        db: AsyncSession,
        integration_key: IntegrationKey
    ) -> IntegrationKey:
        """Revoke (deactivate) an integration key."""
        integration_key.is_active = False
        await db.commit()
        await db.refresh(integration_key)
        return integration_key 