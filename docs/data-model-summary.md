# Wedi Data Model Summary

## Quick Reference

This document provides a high-level summary of the Wedi platform's data model architecture. For detailed specifications, see:
- [Data Models Specification](./data-models-specification.md) - Complete Prisma schema
- [Transaction Model Specification](./transaction-model-specification.md) - Transaction flow and architecture

## Core Design Principles

1. **Multi-tenancy**: Organization-based data isolation
2. **Event Sourcing**: Complete audit trail via PaymentEvent
3. **Provider Agnostic**: Flexible integration with any PSP
4. **Web3 Native**: Built-in blockchain and wallet support
5. **Agent Ready**: Prepared for AI/LangGraph integration

## Key Entity Groups

### 1. Multi-Tenant Foundation
- **Organization**: Root tenant entity with compliance tracking
- **User**: Supports multiple auth providers (Email, Google, Clerk + Circle)
- **OrganizationUser**: Junction table for role-based access

### 2. Payment Core
- **PaymentLink**: Defines payment parameters, supports smart contracts
- **PaymentOrder**: Tracks transaction lifecycle with detailed fee breakdown
- **PaymentEvent**: Immutable event log with Kafka integration

### 3. Web3 Integration
- **Wallet**: Manages EOA and smart wallets across chains
- **BlockchainTransaction**: On-chain transaction tracking
- **GasSponsorship**: Enables gasless transactions

### 4. Provider Abstraction
- **Provider**: PSP definitions (Yoint, Trubit, etc.)
- **ProviderConfig**: Per-organization credentials
- **ProviderRoute**: Routing rules with fee structures
- **ProviderTransaction**: API interaction tracking

### 5. AI/Agent Infrastructure
- **Agent**: LangGraph agent configurations
- **AgentDecision**: Decision tracking with reasoning logs
- **AgentCheckpoint**: State persistence for replay
- **AgentInteraction**: Human-in-the-loop tracking

### 6. Operational Support
- **AuditLog**: Comprehensive compliance trail
- **Webhook**: Event notification management
- **ManualProcessStep**: Exception handling workflow
- **ApiKey**: Scoped API access control

## Transaction State Machine

```
CREATED → AWAITING_PAYMENT → PROCESSING → COMPLETED
                ↓                ↓           ↓
            CANCELLED     REQUIRES_ACTION  FAILED
                              ↓
                          PROCESSING
```

## Key Relationships

1. **Organization** owns all tenant-specific data
2. **PaymentOrder** aggregates all transaction-related entities
3. **Wallet** bridges users/orgs to blockchain transactions
4. **Provider** abstracts payment service provider integrations
5. **Agent** orchestrates intelligent payment routing

## MVP Focus Areas

For the initial MVP, prioritize:
1. Core models: Organization, User, PaymentLink, PaymentOrder
2. Basic provider integration (Yoint for Colombia, Trubit for Mexico)
3. Simple wallet support for Clerk + Circle authentication
4. Essential audit logging for compliance

## Future Enhancements

Post-MVP additions:
1. Full LangGraph agent implementation
2. Advanced routing with ML optimization
3. Multi-chain blockchain support
4. Complex KYC/AML workflows
5. Natural language payment creation via CopilotKit

## Security Considerations

- All credentials stored encrypted
- Row-level security for multi-tenancy
- Comprehensive audit trail
- GDPR-compliant data handling
- API rate limiting and scoped permissions

## Performance Optimizations

- Strategic indexes on foreign keys and query patterns
- Partitioning for large tables (PaymentOrder, PaymentEvent)
- Caching strategy for frequently accessed data
- Event stream compaction for state reconstruction 