# Wedi Platform Transaction Model & Future Architecture

## Executive Summary

This document specifies the transactional model for the Wedi platform, detailing how payments flow through the system from initiation to settlement, and outlining the architectural evolution from MVP to a fully agentic payment orchestration platform.

## Transaction Lifecycle Overview

The payment lifecycle in Wedi follows an event-driven state machine pattern, ensuring auditability, recoverability, and flexibility in handling various payment scenarios.

### Core Transaction States

1. **CREATED** - Payment order initialized
2. **AWAITING_PAYMENT** - Waiting for customer action
3. **PROCESSING** - Active payment processing
4. **REQUIRES_ACTION** - Manual intervention needed
5. **COMPLETED** - Successfully settled
6. **FAILED** - Terminal failure state
7. **REFUNDED** - Payment reversed
8. **CANCELLED** - Cancelled by user/system

## MVP Transaction Flow

### 1. Payment Initiation

```typescript
// Customer clicks payment link
POST /api/payment-orders/initiate
{
  "paymentLinkId": "link_123",
  "customerEmail": "customer@example.com",
  "customerWallet": "0x123..." // Optional for Web3
}

// Response includes:
{
  "orderId": "order_456",
  "providerUrl": "https://yoint.com/pay/...", // Or Trubit URL
  "expiresAt": "2024-01-01T00:00:00Z"
}
```

### 2. Provider Integration Flow

For the Colombia-Mexico corridor:

#### Collection in Colombia (via Yoint)
1. Create collection request via Yoint API
2. Customer completes payment via PSE/bank transfer
3. Yoint sends webhook on completion
4. System initiates payout to Mexico

#### Payout in Mexico (via Trubit)
1. Verify funds received from Yoint
2. Create payout request via Trubit API
3. Trubit processes to Mexican bank/wallet
4. Confirmation webhook received

### 3. Event Flow

Each state transition emits events to Kafka:

```json
{
  "eventType": "payment.order.processing",
  "orderId": "order_456",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "previousStatus": "AWAITING_PAYMENT",
    "newStatus": "PROCESSING",
    "provider": "YOINT",
    "amount": 1000000,
    "currency": "COP"
  }
}
```

## Data Model Relationships

### Payment Order Composition

```
PaymentOrder
├── PaymentLink (1:1)
├── ProviderTransactions (1:N)
│   ├── Yoint Collection Transaction
│   └── Trubit Payout Transaction
├── PaymentEvents (1:N)
│   ├── Created Event
│   ├── Processing Event
│   └── Completed Event
├── BlockchainTransactions (0:N)
│   └── Smart Contract Interactions
└── AgentDecisions (0:N) [Future]
    └── Routing Decisions
```

### Transaction Data Flow

1. **PaymentLink** defines the payment parameters
2. **PaymentOrder** tracks the actual transaction instance
3. **ProviderTransaction** records each provider interaction
4. **PaymentEvent** provides an immutable audit trail
5. **BlockchainTransaction** tracks on-chain activities

## Transactional Integrity

### ACID Properties

**Atomicity**: All database operations within a transaction boundary succeed or fail together
```python
async def process_payment(order_id: str):
    async with db.transaction():
        # Update order status
        order = await update_order_status(order_id, "PROCESSING")
        
        # Create provider transaction
        provider_tx = await create_provider_transaction(order)
        
        # Emit event
        await emit_payment_event(order, "processing")
        
        # All succeed or all rollback
```

**Consistency**: Business rules enforced at multiple levels
- Database constraints (foreign keys, unique indexes)
- Application-level validation
- Event schema validation

**Isolation**: Row-level locking for concurrent updates
```sql
-- Pessimistic locking for critical updates
SELECT * FROM payment_orders 
WHERE id = ? 
FOR UPDATE;
```

**Durability**: Multi-layer persistence
- Primary database (Neon PostgreSQL)
- Event stream (Kafka/Redpanda)
- Audit logs

### Idempotency

All payment operations must be idempotent:

```python
@idempotent(key="payment_order:{order_id}")
async def initiate_provider_payment(order_id: str):
    # Check if already processed
    existing = await get_provider_transaction(order_id)
    if existing:
        return existing
    
    # Process payment
    return await create_provider_payment(order_id)
```

## Fee Structure & Settlement

### Fee Calculation Model

```typescript
interface FeeBreakdown {
  // Base fees
  platformFee: Decimal;      // Wedi's fee (0.5-1%)
  providerFee: Decimal;      // PSP fees (Yoint + Trubit)
  networkFee: Decimal;       // Blockchain gas or bank fees
  
  // Derived
  totalFee: Decimal;
  effectiveRate: Decimal;    // Total fee as percentage
  
  // For transparency
  feeBreakdown: {
    yointCollectionFee: Decimal;
    trubitPayoutFee: Decimal;
    currencyConversionSpread: Decimal;
    blockchainGasFee?: Decimal;
  };
}
```

### Settlement Process

1. **T+0 Initiation**: Payment initiated by customer
2. **T+1 Collection**: Funds collected by Yoint (Colombia)
3. **T+1 Conversion**: Currency conversion COP → MXN
4. **T+2 Payout**: Funds sent via Trubit (Mexico)
5. **T+2 Confirmation**: Settlement confirmed to merchant

## Agent-Based Transaction Orchestration (Future)

### Intelligent Routing

The future platform will use LangGraph agents for dynamic routing:

```python
class PaymentOrchestrationAgent:
    async def select_route(self, payment_request):
        # Analyze payment parameters
        analysis = await self.analyze_payment(payment_request)
        
        # Consider multiple factors
        factors = {
            "amount": payment_request.amount,
            "urgency": payment_request.priority,
            "risk_score": analysis.risk_score,
            "provider_health": await self.check_provider_health(),
            "current_fees": await self.get_current_fees(),
            "success_rates": await self.get_success_rates()
        }
        
        # Agent reasoning
        decision = await self.llm.decide(
            system_prompt=ROUTING_PROMPT,
            factors=factors
        )
        
        return RouteDecision(
            provider=decision.provider,
            reasoning=decision.reasoning,
            confidence=decision.confidence
        )
```

### Multi-Agent Architecture

```
┌─────────────────────────────────────────┐
│        CopilotKit UI (Next.js)          │
│         Human-in-the-loop               │
└────────────────┬────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│      Orchestration Agent (Main)         │
│         Coordinates workflow            │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────┴─────┐          ┌─────┴─────┐
│ Risk     │          │ Route     │
│ Agent    │          │ Optimizer │
└──────────┘          └───────────┘
     │                       │
┌────┴─────┐          ┌─────┴─────┐
│ Fraud    │          │ Provider  │
│ Detector │          │ Selector  │
└──────────┘          └───────────┘
```

### Agent Decision Tracking

Every agent decision is recorded for:
- Audit compliance
- Performance optimization
- Model training
- Human review

```json
{
  "agentId": "agent_orchestrator_v1",
  "decisionType": "route_selection",
  "input": {
    "amount": 1000,
    "currency": "USD",
    "corridor": "CO-MX"
  },
  "reasoning": {
    "steps": [
      "Analyzed 3 available routes",
      "Yoint-Trubit offers lowest fees",
      "Success rate 98% in last 7 days",
      "No current service degradation"
    ]
  },
  "decision": {
    "route": "YOINT_TRUBIT",
    "estimatedFee": 12.50,
    "estimatedTime": "2 business days"
  },
  "confidence": 0.92
}
```

## Blockchain Integration Strategy

### Smart Contract Architecture

```solidity
// Payment Registry Contract
contract WediPaymentRegistry {
    struct Payment {
        bytes32 paymentId;
        address merchant;
        address customer;
        uint256 amount;
        string currency;
        uint256 timestamp;
        PaymentStatus status;
    }
    
    mapping(bytes32 => Payment) public payments;
    
    event PaymentInitiated(bytes32 indexed paymentId);
    event PaymentCompleted(bytes32 indexed paymentId);
}
```

### Hybrid Payment Flow

1. **Off-chain initiation** via traditional payment link
2. **On-chain registry** for transparency
3. **Off-chain processing** via PSPs
4. **On-chain settlement confirmation**
5. **NFT receipt** minted as proof

### Gas Optimization

- Batch transaction recording
- Meta-transactions for gasless UX
- Layer 2 solutions for scalability

## Scalability Considerations

### Database Optimization

1. **Partitioning**: Payment orders by date/organization
2. **Indexing**: Optimized for common query patterns
3. **Read replicas**: For analytics and reporting
4. **Connection pooling**: Efficient resource usage

### Event Stream Scaling

1. **Topic partitioning**: By organization/payment type
2. **Consumer groups**: Parallel processing
3. **Retention policies**: 30-day event retention
4. **Compaction**: For state reconstruction

### Caching Strategy

```typescript
// Multi-level caching
const cacheStrategy = {
  L1: "Application memory (30s TTL)",
  L2: "Redis (5min TTL)",
  L3: "Database query cache"
};

// Example usage
async function getPaymentLink(linkId: string) {
  // Check L1 cache
  const cached = memCache.get(linkId);
  if (cached) return cached;
  
  // Check L2 cache
  const redisCached = await redis.get(`link:${linkId}`);
  if (redisCached) {
    memCache.set(linkId, redisCached);
    return redisCached;
  }
  
  // Database query
  const link = await db.paymentLink.findUnique({ where: { id: linkId } });
  
  // Update caches
  await redis.set(`link:${linkId}`, link, { ex: 300 });
  memCache.set(linkId, link);
  
  return link;
}
```

## Security & Compliance

### Transaction Security

1. **Encryption**: All sensitive data encrypted at rest
2. **TLS 1.3**: For all API communications
3. **Webhook signatures**: HMAC-SHA256 verification
4. **API rate limiting**: Per organization limits
5. **Idempotency keys**: Prevent duplicate processing

### Compliance Features

1. **AML screening**: Integrated with provider checks
2. **Transaction limits**: Configurable per organization
3. **Audit trail**: Immutable event log
4. **Data residency**: Regional deployment options
5. **GDPR compliance**: Data deletion workflows

## Monitoring & Observability

### Key Metrics

```typescript
// Transaction metrics
const metrics = {
  // Success rates
  paymentSuccessRate: "payment_orders.completed / payment_orders.total",
  
  // Performance
  avgProcessingTime: "avg(completed_at - created_at)",
  p95ResponseTime: "percentile(api_response_time, 0.95)",
  
  // Financial
  totalVolume: "sum(payment_orders.amount)",
  totalFees: "sum(payment_orders.total_fee)",
  
  // Operational
  providerErrorRate: "provider_errors / provider_requests",
  manualInterventionRate: "requires_action / total"
};
```

### Alerting Rules

1. Payment success rate < 95%
2. Provider error rate > 5%
3. Processing time > 5 minutes
4. Manual intervention rate > 2%
5. Unusual transaction patterns

## Future Enhancements

### Phase 2: Enhanced Features
- Multi-currency support (beyond COP/MXN)
- Recurring payments
- Batch processing
- Advanced fraud detection

### Phase 3: AI-Native Evolution
- Predictive routing optimization
- Dynamic fee negotiation
- Automated reconciliation
- Natural language payment creation

### Phase 4: Platform Expansion
- Additional corridors (Brazil, Argentina)
- More payment methods
- White-label solutions
- Banking-as-a-Service features

## Conclusion

The Wedi transaction model is designed to evolve from a straightforward payment processing system to an intelligent, agent-driven orchestration platform. By building on solid transactional foundations with comprehensive event sourcing and preparing for blockchain integration, the platform can adapt to changing market needs while maintaining reliability and compliance. 