"""Service layer for IntegrationKey operations."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import hashlib

from app.db.unit_of_work import UnitOfWork
from app.models.generated import IntegrationKey
from app.schemas.integration_key import (
    IntegrationKeyCreate,
    IntegrationKeyUpdate,
    IntegrationKeyValidateRequest,
    IntegrationKeyValidateResponse
)
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException


class IntegrationKeyService:
    """Service for managing integration keys."""
    
    async def create_integration_key(
        self,
        uow: UnitOfWork,
        user_organization_id: str,
        key_data: IntegrationKeyCreate
    ) -> tuple[IntegrationKey, str]:
        """
        Create a new integration key.
        
        Returns:
            Tuple of (IntegrationKey instance, plain text key)
        """
        async with uow:
            # Verify the agent belongs to the organization
            agent = await uow.agents.get(uow.session, id=str(key_data.agent_id))
            if not agent:
                raise NotFoundException(f"Agent {key_data.agent_id} not found")
            
            if agent.organization_id != user_organization_id:
                raise ForbiddenException("Agent does not belong to your organization")
            
            # Create the integration key
            integration_key, plain_key = await uow.integration_keys.create_with_key(
                uow.session,
                name=key_data.name,
                organization_id=user_organization_id,
                agent_id=str(key_data.agent_id),
                description=key_data.description,
                allowed_corridors=key_data.allowed_corridors,
                allowed_providers=key_data.allowed_providers,
                rate_limit=key_data.rate_limit,
                expires_at=key_data.expires_at,
                is_active=key_data.is_active
            )
            
            await uow.commit()
            return integration_key, plain_key
    
    async def list_integration_keys(
        self,
        uow: UnitOfWork,
        organization_id: str,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        agent_id: Optional[str] = None
    ) -> tuple[List[IntegrationKey], int]:
        """List integration keys for an organization."""
        async with uow:
            keys = await uow.integration_keys.get_by_organization(
                uow.session,
                organization_id,
                skip=skip,
                limit=limit,
                is_active=is_active,
                agent_id=agent_id
            )
            
            total = await uow.integration_keys.count_by_organization(
                uow.session,
                organization_id,
                is_active=is_active,
                agent_id=agent_id
            )
            
            return keys, total
    
    async def get_integration_key(
        self,
        uow: UnitOfWork,
        organization_id: str,
        key_id: str
    ) -> IntegrationKey:
        """Get a specific integration key."""
        async with uow:
            key = await uow.integration_keys.get(uow.session, id=key_id)
            if not key:
                raise NotFoundException(f"Integration key {key_id} not found")
            
            if key.organization_id != organization_id:
                raise ForbiddenException("Integration key does not belong to your organization")
            
            return key
    
    async def update_integration_key(
        self,
        uow: UnitOfWork,
        organization_id: str,
        key_id: str,
        update_data: IntegrationKeyUpdate
    ) -> IntegrationKey:
        """Update an integration key."""
        async with uow:
            key = await self.get_integration_key(uow, organization_id, key_id)
            
            updated_key = await uow.integration_keys.update(
                uow.session,
                db_obj=key,
                obj_in=update_data.model_dump(exclude_unset=True)
            )
            
            await uow.commit()
            return updated_key
    
    async def revoke_integration_key(
        self,
        uow: UnitOfWork,
        organization_id: str,
        key_id: str
    ) -> IntegrationKey:
        """Revoke (deactivate) an integration key."""
        async with uow:
            key = await self.get_integration_key(uow, organization_id, key_id)
            
            revoked_key = await uow.integration_keys.revoke(uow.session, key)
            
            await uow.commit()
            return revoked_key
    
    async def validate_integration_key(
        self,
        uow: UnitOfWork,
        request: IntegrationKeyValidateRequest
    ) -> IntegrationKeyValidateResponse:
        """Validate an integration key."""
        async with uow:
            is_valid, key, error = await uow.integration_keys.validate_key(
                uow.session,
                request.key
            )
            
            if is_valid and key:
                # Check rate limit
                is_allowed, current, limit = await uow.integration_keys.check_rate_limit(
                    uow.session,
                    key
                )
                
                if not is_allowed:
                    return IntegrationKeyValidateResponse(
                        valid=False,
                        error=f"Rate limit exceeded: {current}/{limit} requests per minute"
                    )
                
                await uow.commit()
                
                return IntegrationKeyValidateResponse(
                    valid=True,
                    key_id=UUID(key.id),
                    organization_id=UUID(key.organization_id),
                    agent_id=UUID(key.agent_id)
                )
            
            return IntegrationKeyValidateResponse(
                valid=False,
                error=error or "Invalid integration key"
            )
    
    async def validate_key_for_payment_link(
        self,
        uow: UnitOfWork,
        key: str,
        corridor: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Optional[IntegrationKey]:
        """
        Validate an integration key for payment link creation.
        
        Returns the integration key if valid, None otherwise.
        """
        # Hash the key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        async with uow:
            integration_key = await uow.integration_keys.get_by_key_hash(
                uow.session,
                key_hash
            )
            
            if not integration_key:
                return None
            
            # Check if active
            if not integration_key.is_active:
                return None
            
            # Check expiration
            if integration_key.expires_at and integration_key.expires_at < datetime.utcnow():
                return None
            
            # Check corridor restriction
            if integration_key.allowed_corridors and corridor:
                if corridor not in integration_key.allowed_corridors:
                    return None
            
            # Check provider restriction
            if integration_key.allowed_providers and provider:
                if provider not in integration_key.allowed_providers:
                    return None
            
            # Update usage
            integration_key.usage_count += 1
            integration_key.last_used_at = datetime.utcnow()
            await uow.commit()
            
            return integration_key


# Singleton instance
integration_key_service = IntegrationKeyService() 