"""
Event publisher for domain events.

This module provides interfaces and implementations for publishing
domain events to various event buses/queues.
"""
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)

# Type variable for event data
EventDataType = TypeVar("EventDataType", bound=BaseModel)


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any]
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class EventPublisher(ABC):
    """Abstract base class for event publishers."""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event.
        
        Args:
            event: Domain event to publish
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events in batch.
        
        Args:
            events: List of domain events to publish
        """
        pass


class LoggingEventPublisher(EventPublisher):
    """Event publisher that logs events (for development/testing)."""
    
    async def publish(self, event: DomainEvent) -> None:
        """Log event for debugging.
        
        Args:
            event: Domain event to log
        """
        logger.info(
            "Publishing event",
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            event_id=event.event_id,
            data=event.data
        )
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Log batch of events.
        
        Args:
            events: List of domain events to log
        """
        for event in events:
            await self.publish(event)


class RedpandaEventPublisher(EventPublisher):
    """Event publisher for Redpanda (Kafka-compatible) message broker."""
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic_prefix: str = "wedi.events",
        producer_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Redpanda publisher.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic_prefix: Prefix for topic names
            producer_config: Additional producer configuration
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.producer_config = producer_config or {}
        self._producer = None
    
    async def _get_producer(self):
        """Get or create Kafka producer.
        
        Returns:
            Kafka producer instance
        """
        if self._producer is None:
            try:
                from aiokafka import AIOKafkaProducer
                
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode(),
                    **self.producer_config
                )
                await self._producer.start()
            except ImportError:
                logger.error("aiokafka not installed. Install with: pip install aiokafka")
                raise
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise
        
        return self._producer
    
    def _get_topic_name(self, event: DomainEvent) -> str:
        """Get topic name for event.
        
        Args:
            event: Domain event
            
        Returns:
            Topic name
        """
        # Use aggregate type as part of topic name
        # e.g., wedi.events.payment_order, wedi.events.user
        aggregate_type = event.aggregate_type.lower().replace("_", ".")
        return f"{self.topic_prefix}.{aggregate_type}"
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to Redpanda.
        
        Args:
            event: Domain event to publish
        """
        try:
            producer = await self._get_producer()
            topic = self._get_topic_name(event)
            
            # Use aggregate_id as key for ordering guarantees
            key = event.aggregate_id.encode()
            value = event.model_dump_json()
            
            await producer.send(
                topic,
                key=key,
                value=value.encode()
            )
            
            logger.debug(
                f"Published event to Redpanda",
                topic=topic,
                event_type=event.event_type,
                event_id=event.event_id
            )
            
        except Exception as e:
            logger.error(
                f"Failed to publish event to Redpanda",
                error=str(e),
                event_type=event.event_type,
                event_id=event.event_id
            )
            raise
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish batch of events to Redpanda.
        
        Args:
            events: List of domain events to publish
        """
        # Group events by topic for efficiency
        from collections import defaultdict
        events_by_topic = defaultdict(list)
        
        for event in events:
            topic = self._get_topic_name(event)
            events_by_topic[topic].append(event)
        
        # Publish to each topic
        for topic, topic_events in events_by_topic.items():
            try:
                producer = await self._get_producer()
                
                # Send all events for this topic
                for event in topic_events:
                    key = event.aggregate_id.encode()
                    value = event.model_dump_json().encode()
                    
                    # Don't await each send for better performance
                    producer.send(topic, key=key, value=value)
                
                # Flush to ensure all messages are sent
                await producer.flush()
                
                logger.debug(
                    f"Published batch to Redpanda",
                    topic=topic,
                    event_count=len(topic_events)
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to publish batch to Redpanda",
                    error=str(e),
                    topic=topic,
                    event_count=len(topic_events)
                )
                raise
    
    async def close(self):
        """Close the producer connection."""
        if self._producer:
            await self._producer.stop()
            self._producer = None


class InMemoryEventPublisher(EventPublisher):
    """In-memory event publisher for testing."""
    
    def __init__(self):
        """Initialize in-memory publisher."""
        self.events: List[DomainEvent] = []
    
    async def publish(self, event: DomainEvent) -> None:
        """Store event in memory.
        
        Args:
            event: Domain event to store
        """
        self.events.append(event)
        logger.debug(
            f"Stored event in memory",
            event_type=event.event_type,
            event_id=event.event_id
        )
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Store batch of events in memory.
        
        Args:
            events: List of domain events to store
        """
        self.events.extend(events)
        logger.debug(f"Stored {len(events)} events in memory")
    
    def get_events(self, event_type: Optional[str] = None) -> List[DomainEvent]:
        """Get stored events.
        
        Args:
            event_type: Optional filter by event type
            
        Returns:
            List of events
        """
        if event_type:
            return [e for e in self.events if e.event_type == event_type]
        return self.events.copy()
    
    def clear(self):
        """Clear all stored events."""
        self.events.clear()


# Event publisher instance - configured at startup
_event_publisher: Optional[EventPublisher] = None


def set_event_publisher(publisher: EventPublisher) -> None:
    """Set the global event publisher.
    
    Args:
        publisher: Event publisher instance
    """
    global _event_publisher
    _event_publisher = publisher
    logger.info(f"Event publisher configured: {type(publisher).__name__}")


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher.
    
    Returns:
        Event publisher instance
        
    Raises:
        RuntimeError: If event publisher not configured
    """
    if _event_publisher is None:
        # Default to logging publisher if not configured
        logger.warning("Event publisher not configured, using LoggingEventPublisher")
        set_event_publisher(LoggingEventPublisher())
    
    return _event_publisher


async def publish_event(event: DomainEvent) -> None:
    """Publish a domain event using the global publisher.
    
    Args:
        event: Domain event to publish
    """
    publisher = get_event_publisher()
    await publisher.publish(event)


async def publish_events(events: List[DomainEvent]) -> None:
    """Publish multiple domain events using the global publisher.
    
    Args:
        events: List of domain events to publish
    """
    if not events:
        return
    
    publisher = get_event_publisher()
    await publisher.publish_batch(events) 