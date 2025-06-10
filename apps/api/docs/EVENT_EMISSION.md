# Event Emission Implementation

This document describes the event emission system implemented in the Wedi Pay API.

## Overview

The API uses a domain event system to emit events after state changes, providing:
- Audit trail for all significant actions
- Integration points for external systems
- Foundation for event-sourcing and CQRS patterns
- Real-time notifications via webhooks

## Architecture

### Event Publisher

The system uses a pluggable event publisher architecture with multiple implementations:

1. **LoggingEventPublisher** (Development)
   - Logs events to the application logger
   - Used for debugging and development

2. **RedpandaEventPublisher** (Production)
   - Publishes events to Redpanda/Kafka topics
   - Enables real-time event streaming
   - Supports multiple consumers

3. **InMemoryEventPublisher** (Testing)
   - Stores events in memory
   - Used for unit and integration tests

### Event Structure

All events inherit from `DomainEvent` base class:

```python
class DomainEvent:
    event_id: str          # Unique event identifier
    event_type: str        # Event type (e.g., "user.created")
    aggregate_id: str      # ID of the affected entity
    aggregate_type: str    # Type of entity (e.g., "user")
    occurred_at: datetime  # When the event occurred
    data: dict            # Event-specific data
    metadata: dict        # Additional context
```

## Implemented Events

### Authentication Events
- **UserCreatedEvent**: Emitted when a new user registers (first login)
- **UserWalletLinkedEvent**: Emitted when a wallet is linked during login

### Organization Events
- **OrganizationCreatedEvent**: Emitted when an organization is created
- **MemberAddedEvent**: Emitted when a member is added to an organization
- **MemberRemovedEvent**: Emitted when a member is removed

### Payment Link Events
- **PaymentLinkCreatedEvent**: Emitted when a payment link is created
- **PaymentLinkUpdatedEvent**: Emitted when a payment link is updated
- **PaymentLinkArchivedEvent**: Emitted when a payment link is archived

### Wallet Events
- **WalletCreatedEvent**: Emitted when a wallet is created
- **UserWalletLinkedEvent**: Emitted when a wallet is linked to a user

## Implementation Pattern

### 1. Dependency Injection

Event publisher is injected as a dependency:

```python
async def create_payment_link(
    payment_link_data: PaymentLinkCreate,
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> PaymentLinkCreateResponse:
    # ... create payment link ...
    
    # Emit event
    event = PaymentLinkCreatedEvent(
        payment_link_id=str(payment_link.id),
        organization_id=str(payment_link.organization_id),
        amount=float(payment_link.amount),
        currency=payment_link.currency,
        short_code=payment_link.short_code
    )
    await event_publisher.publish_event(event)
```

### 2. Transaction Boundaries

Events are emitted AFTER the database transaction commits:

```python
async with uow:
    # Perform database operations
    payment_link = await repo.create(...)
    
    # Commit transaction
    await uow.commit()
    
    # Emit event after successful commit
    await event_publisher.publish_event(event)
```

### 3. Event Data

Events contain minimal data needed for consumers:
- Entity IDs for lookup
- Key changed values
- Actor information (who performed the action)
- Timestamp of occurrence

## Event Consumers

Events can be consumed by:

1. **Webhook Service**: Sends HTTP callbacks to configured endpoints
2. **Notification Service**: Sends emails, SMS, or push notifications
3. **Analytics Service**: Tracks metrics and generates reports
4. **Agent Service**: Triggers AI agents for automated actions
5. **Audit Service**: Maintains compliance audit trail

## Testing Events

Use the `InMemoryEventPublisher` for testing:

```python
def test_payment_link_creation():
    event_publisher = InMemoryEventPublisher()
    
    # Create payment link
    response = client.post("/payment-links", ...)
    
    # Verify event was emitted
    events = event_publisher.get_events()
    assert len(events) == 1
    assert events[0].event_type == "payment_link.created"
```

## Configuration

Event publisher is configured via environment variables:

```bash
# Development
EVENT_PUBLISHER_TYPE=logging

# Production
EVENT_PUBLISHER_TYPE=redpanda
REDPANDA_BROKERS=localhost:9092
REDPANDA_TOPIC_PREFIX=wedi.events
```

## Best Practices

1. **Emit After Commit**: Always emit events after database transactions commit
2. **Minimal Data**: Include only necessary data in events
3. **Idempotency**: Design consumers to handle duplicate events
4. **Error Handling**: Don't let event emission failures break the main flow
5. **Versioning**: Include version info for schema evolution

## Future Enhancements

1. **Additional Events**:
   - UserUpdatedEvent
   - UserDeletedEvent
   - OrganizationUpdatedEvent
   - PaymentOrderCreatedEvent
   - PaymentOrderCompletedEvent

2. **Event Store**: Implement event sourcing for complete audit trail

3. **Event Replay**: Ability to replay events for debugging or recovery

4. **Schema Registry**: Centralized schema management for events

5. **Dead Letter Queue**: Handle failed event processing

## Monitoring

Monitor event emission using:
- Application logs (development)
- Redpanda metrics (production)
- Custom dashboards for event flow
- Alerts for event processing failures

## Security Considerations

1. **Sensitive Data**: Never include passwords, tokens, or PII in events
2. **Access Control**: Restrict access to event streams
3. **Encryption**: Encrypt events in transit and at rest
4. **Audit Trail**: Log all event access and consumption 