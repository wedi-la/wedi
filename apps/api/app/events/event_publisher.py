"""
Event publisher module with dependency injection support.

This module provides the event publisher interface and implementation
that can be injected as a FastAPI dependency.
"""
from typing import List, Optional

from app.events.publisher import (
    DomainEvent,
    EventPublisher,
    InMemoryEventPublisher,
    LoggingEventPublisher,
    RedpandaEventPublisher,
    get_event_publisher as _get_event_publisher,
    set_event_publisher,
)

# Re-export for convenience
__all__ = [
    "DomainEvent",
    "EventPublisher", 
    "InMemoryEventPublisher",
    "LoggingEventPublisher",
    "RedpandaEventPublisher",
    "get_event_publisher",
    "set_event_publisher",
]


class EventPublisherWrapper(EventPublisher):
    """
    Wrapper class that adds publish_event method for consistency.
    
    This allows routers to use either publish() or publish_event().
    """
    
    def __init__(self, publisher: EventPublisher):
        """Initialize wrapper with actual publisher."""
        self._publisher = publisher
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event."""
        await self._publisher.publish(event)
    
    async def publish_event(self, event: DomainEvent) -> None:
        """Publish a single event (alias for publish)."""
        await self._publisher.publish(event)
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events in batch."""
        await self._publisher.publish_batch(events)
    
    def __getattr__(self, name):
        """Forward any other attributes to the wrapped publisher."""
        return getattr(self._publisher, name)


def get_event_publisher() -> EventPublisherWrapper:
    """
    FastAPI dependency to get the event publisher.
    
    Returns:
        EventPublisher instance wrapped to support both publish and publish_event
    """
    publisher = _get_event_publisher()
    return EventPublisherWrapper(publisher) 