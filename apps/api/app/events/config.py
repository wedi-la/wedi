"""
Event publisher configuration.

This module handles the configuration of the event publishing system
based on environment settings.
"""
import os
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.events.publisher import (
    EventPublisher,
    InMemoryEventPublisher,
    LoggingEventPublisher,
    RedpandaEventPublisher,
    set_event_publisher,
)

logger = get_logger(__name__)


def configure_event_publisher() -> EventPublisher:
    """Configure the event publisher based on settings.
    
    Returns:
        Configured event publisher instance
    """
    event_bus_type = getattr(settings, "EVENT_BUS_TYPE", "logging").lower()
    
    if event_bus_type == "redpanda" or event_bus_type == "kafka":
        # Configure Redpanda/Kafka publisher
        bootstrap_servers = getattr(
            settings,
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        topic_prefix = getattr(
            settings,
            "EVENT_TOPIC_PREFIX",
            "wedi.events"
        )
        
        logger.info(
            "Configuring Redpanda event publisher",
            bootstrap_servers=bootstrap_servers,
            topic_prefix=topic_prefix
        )
        
        publisher = RedpandaEventPublisher(
            bootstrap_servers=bootstrap_servers,
            topic_prefix=topic_prefix,
            producer_config={
                "client_id": "wedi-api",
                "compression_type": "gzip",
                "acks": "all",  # Wait for all replicas
                "enable_idempotence": True,  # Prevent duplicates
                "max_in_flight_requests_per_connection": 5,
                "retries": 3,
                "retry_backoff_ms": 100,
            }
        )
    
    elif event_bus_type == "memory":
        # In-memory publisher for testing
        logger.info("Configuring in-memory event publisher")
        publisher = InMemoryEventPublisher()
    
    else:
        # Default to logging publisher
        logger.info("Configuring logging event publisher")
        publisher = LoggingEventPublisher()
    
    # Set as global publisher
    set_event_publisher(publisher)
    
    return publisher


async def startup_event_publisher() -> None:
    """Initialize event publisher on application startup."""
    try:
        publisher = configure_event_publisher()
        logger.info(
            "Event publisher initialized",
            publisher_type=type(publisher).__name__
        )
    except Exception as e:
        logger.error(
            "Failed to initialize event publisher",
            error=str(e),
            error_type=type(e).__name__
        )
        # Fall back to logging publisher
        set_event_publisher(LoggingEventPublisher())
        logger.warning("Falling back to logging event publisher")


async def shutdown_event_publisher() -> None:
    """Cleanup event publisher on application shutdown."""
    from app.events.publisher import get_event_publisher
    
    try:
        publisher = get_event_publisher()
        
        # Close Redpanda producer if applicable
        if isinstance(publisher, RedpandaEventPublisher):
            await publisher.close()
            logger.info("Redpanda event publisher closed")
        
    except Exception as e:
        logger.error(
            "Error during event publisher shutdown",
            error=str(e),
            error_type=type(e).__name__
        ) 