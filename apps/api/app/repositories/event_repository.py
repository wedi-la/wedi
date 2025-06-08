"""
Event-aware repository that emits domain events.

This module extends the base repository to automatically emit
domain events after successful operations.
"""
from typing import Any, List, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.publisher import DomainEvent, publish_event
from app.repositories.base import (
    BaseRepository,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)


class EventRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Repository that emits domain events after operations.
    
    Extends BaseRepository to add event publishing capabilities.
    Subclasses should override the event creation methods to emit
    appropriate domain events.
    """
    
    async def _emit_created_event(
        self,
        entity: ModelType,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Create event for entity creation.
        
        Override this in subclasses to emit specific events.
        
        Args:
            entity: Created entity
            organization_id: Organization ID if applicable
            
        Returns:
            Domain event or None if no event should be emitted
        """
        return None
    
    async def _emit_updated_event(
        self,
        entity: ModelType,
        changes: dict,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Create event for entity update.
        
        Override this in subclasses to emit specific events.
        
        Args:
            entity: Updated entity
            changes: Dictionary of changed fields
            organization_id: Organization ID if applicable
            
        Returns:
            Domain event or None if no event should be emitted
        """
        return None
    
    async def _emit_deleted_event(
        self,
        entity_id: Any,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Create event for entity deletion.
        
        Override this in subclasses to emit specific events.
        
        Args:
            entity_id: ID of deleted entity
            organization_id: Organization ID if applicable
            
        Returns:
            Domain event or None if no event should be emitted
        """
        return None
    
    async def _emit_custom_event(
        self,
        entity: ModelType,
        event_type: str,
        data: dict,
        organization_id: Optional[str] = None
    ) -> Optional[DomainEvent]:
        """Create custom domain event.
        
        Override this in subclasses to emit specific events.
        
        Args:
            entity: Related entity
            event_type: Type of event
            data: Event data
            organization_id: Organization ID if applicable
            
        Returns:
            Domain event or None if no event should be emitted
        """
        return None
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        organization_id: Optional[str] = None,
        **kwargs: Any
    ) -> ModelType:
        """Create entity and emit created event.
        
        Args:
            db: Database session
            obj_in: Creation data
            organization_id: Organization ID for multi-tenancy
            **kwargs: Additional fields
            
        Returns:
            Created entity
        """
        # Create entity using parent method
        entity = await super().create(
            db,
            obj_in=obj_in,
            organization_id=organization_id,
            **kwargs
        )
        
        # Emit created event
        event = await self._emit_created_event(entity, organization_id)
        if event:
            await publish_event(event)
        
        return entity
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        partial: bool = True
    ) -> ModelType:
        """Update entity and emit updated event.
        
        Args:
            db: Database session
            db_obj: Entity to update
            obj_in: Update data
            partial: If True, only update provided fields
            
        Returns:
            Updated entity
        """
        # Track changes before update
        if partial:
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in.model_dump()
        
        changes = {}
        for field, new_value in update_data.items():
            if hasattr(db_obj, field):
                old_value = getattr(db_obj, field)
                if old_value != new_value:
                    changes[field] = {
                        "old": old_value,
                        "new": new_value
                    }
        
        # Update entity using parent method
        entity = await super().update(
            db,
            db_obj=db_obj,
            obj_in=obj_in,
            partial=partial
        )
        
        # Emit updated event if there were changes
        if changes:
            organization_id = None
            if self._organization_id_field and hasattr(entity, self._organization_id_field):
                organization_id = getattr(entity, self._organization_id_field)
            
            event = await self._emit_updated_event(entity, changes, organization_id)
            if event:
                await publish_event(event)
        
        return entity
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: Any,
        organization_id: Optional[str] = None
    ) -> bool:
        """Delete entity and emit deleted event.
        
        Args:
            db: Database session
            id: Entity ID
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            True if deleted
        """
        # Delete entity using parent method
        deleted = await super().delete(
            db,
            id=id,
            organization_id=organization_id
        )
        
        # Emit deleted event
        if deleted:
            event = await self._emit_deleted_event(id, organization_id)
            if event:
                await publish_event(event)
        
        return deleted
    
    async def emit_event(
        self,
        entity: ModelType,
        event_type: str,
        data: dict,
        organization_id: Optional[str] = None
    ) -> None:
        """Emit a custom event for an entity.
        
        Args:
            entity: Related entity
            event_type: Type of event
            data: Event data
            organization_id: Organization ID if applicable
        """
        event = await self._emit_custom_event(
            entity,
            event_type,
            data,
            organization_id
        )
        if event:
            await publish_event(event) 