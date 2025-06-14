# Wedi Platform Data Models Specification

## Overview

This document specifies the data models for the Wedi platform, supporting both the MVP requirements and future vision including Web3 integration, agentic orchestration, and multi-provider payment routing.

## Core Design Principles

1. **Multi-tenancy First**: All data is scoped to Organizations
2. **Event Sourcing**: Complete audit trail and state reconstruction capability
3. **Provider Agnostic**: Flexible model supporting any payment provider
4. **Web3 Native**: Built-in support for blockchain transactions and wallets
5. **Agent Ready**: Models designed for AI/ML agent integration
6. **Compliance Focused**: Comprehensive audit and regulatory tracking

## Enhanced Prisma Schema

```prisma
// datasource and generator configuration
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
  output   = "./generated/client"
}

// ==========================================
// CORE DOMAIN MODELS
// ==========================================

model Organization {
  id                    String                 @id @default(cuid())
  name                  String
  slug                  String                 @unique
  description           String?
  
  // Billing & Compliance
  billingEmail          String
  taxId                 String?
  country               String
  complianceStatus      ComplianceStatus       @default(PENDING)
  kycVerifiedAt         DateTime?
  
  // Settings
  settings              Json                   @default("{}")
  features              Json                   @default("[]") // Feature flags
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  // Relations
  ownerId               String
  users                 OrganizationUser[]
  wallets               Wallet[]
  paymentLinks          PaymentLink[]
  paymentOrders         PaymentOrder[]
  providers             ProviderConfig[]
  apiKeys               ApiKey[]
  webhooks              Webhook[]
  auditLogs             AuditLog[]
  agents                Agent[]
  
  @@index([slug])
  @@index([ownerId])
}

model User {
  id                    String                 @id @default(cuid())
  email                 String                 @unique
  name                  String?
  avatarUrl             String?
  
  // Authentication
  authProvider          AuthProvider           @default(EMAIL)
  authProviderId        String?
  emailVerified         Boolean                @default(false)
  
  // Web3
  primaryWalletId       String?
  primaryWallet         Wallet?                @relation("PrimaryWallet", fields: [primaryWalletId], references: [id])
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  lastLoginAt           DateTime?
  
  // Relations
  organizations         OrganizationUser[]
  ownedWallets          Wallet[]               @relation("WalletOwner")
  paymentLinks          PaymentLink[]
  auditLogs             AuditLog[]
  agentInteractions     AgentInteraction[]
  
  @@unique([authProvider, authProviderId])
  @@index([email])
}

enum AuthProvider {
  EMAIL
  GOOGLE
  CLERK
  WALLET_CONNECT
}

enum ComplianceStatus {
  PENDING
  IN_REVIEW
  APPROVED
  REJECTED
  SUSPENDED
}

// ==========================================
// WEB3 INTEGRATION MODELS
// ==========================================

model Wallet {
  id                    String                 @id @default(cuid())
  address               String                 @unique
  chainId               Int
  type                  WalletType             @default(EOA)
  
  // Ownership
  userId                String?
  user                  User?                  @relation("WalletOwner", fields: [userId], references: [id])
  organizationId        String?
  organization          Organization?          @relation(fields: [organizationId], references: [id])
  
  // Smart Wallet Config
  smartWalletFactory    String?
  smartWalletConfig     Json?
  
  // Security
  isActive              Boolean                @default(true)
  allowlist             Boolean                @default(false)
  blocklist             Boolean                @default(false)
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  // Relations
  primaryForUsers       User[]                 @relation("PrimaryWallet")
  transactions          BlockchainTransaction[]
  gasSponsorship        GasSponsorship[]
  
  @@index([address, chainId])
  @@index([userId])
  @@index([organizationId])
}

enum WalletType {
  EOA                   // Externally Owned Account
  SMART_WALLET          // Smart Contract Wallet
  MULTI_SIG             // Multi-signature Wallet
}

model BlockchainTransaction {
  id                    String                 @id @default(cuid())
  hash                  String                 @unique
  chainId               Int
  
  // Transaction Details
  fromAddress           String
  toAddress             String?
  value                 String                 // BigInt as string
  data                  String?
  gasLimit              String?
  gasPrice              String?
  nonce                 Int?
  
  // Status
  status                BlockchainTxStatus     @default(PENDING)
  blockNumber           Int?
  confirmations         Int                    @default(0)
  
  // Gas Sponsorship
  isSponsored           Boolean                @default(false)
  sponsorshipId         String?
  gasSponsorship        GasSponsorship?        @relation(fields: [sponsorshipId], references: [id])
  
  // Relations
  walletId              String
  wallet                Wallet                 @relation(fields: [walletId], references: [id])
  paymentOrderId        String?
  paymentOrder          PaymentOrder?          @relation(fields: [paymentOrderId], references: [id])
  
  // Timestamps
  createdAt             DateTime               @default(now())
  minedAt               DateTime?
  
  @@index([hash])
  @@index([walletId])
  @@index([paymentOrderId])
}

enum BlockchainTxStatus {
  PENDING
  MINED
  CONFIRMED
  FAILED
  DROPPED
}

model GasSponsorship {
  id                    String                 @id @default(cuid())
  
  // Sponsorship Details
  sponsorWalletId       String
  sponsorWallet         Wallet                 @relation(fields: [sponsorWalletId], references: [id])
  maxGasAmount          String                 // BigInt as string
  usedGasAmount         String                 @default("0")
  
  // Limits
  maxTransactions       Int?
  usedTransactions      Int                    @default(0)
  expiresAt             DateTime?
  
  // Relations
  transactions          BlockchainTransaction[]
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  @@index([sponsorWalletId])
}

// ==========================================
// PAYMENT MODELS
// ==========================================

model PaymentLink {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  createdById           String
  createdBy             User                   @relation(fields: [createdById], references: [id])
  
  // Link Details
  title                 String
  description           String?
  referenceId           String?                // Merchant's reference
  shortCode             String                 @unique
  qrCode                String?                // Base64 encoded QR
  
  // Payment Configuration
  amount                Decimal                @db.Decimal(20, 8)
  currency              String                 // ISO code
  targetAmount          Decimal?               @db.Decimal(20, 8)
  targetCurrency        String?
  
  // Smart Contract Integration
  smartContractAddress  String?
  smartContractChainId  Int?
  tokenAddress          String?                // For token payments
  
  // Behavior
  status                PaymentLinkStatus      @default(ACTIVE)
  allowMultiplePayments Boolean                @default(false)
  requiresKyc           Boolean                @default(false)
  expiresAt             DateTime?
  
  // Customization
  redirectUrls          Json?                  // {success: "", failure: "", cancel: ""}
  metadata              Json?
  theme                 Json?                  // UI customization
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  // Relations
  paymentOrders         PaymentOrder[]
  
  @@index([organizationId])
  @@index([shortCode])
  @@index([status])
}

enum PaymentLinkStatus {
  DRAFT
  ACTIVE
  PAUSED
  EXPIRED
  ARCHIVED
  COMPLETED
}

model PaymentOrder {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  paymentLinkId         String
  paymentLink           PaymentLink            @relation(fields: [paymentLinkId], references: [id])
  
  // Order Details
  orderNumber           String                 @unique
  status                PaymentOrderStatus     @default(CREATED)
  
  // Amounts
  requestedAmount       Decimal                @db.Decimal(20, 8)
  requestedCurrency     String
  settledAmount         Decimal?               @db.Decimal(20, 8)
  settledCurrency       String?
  
  // Exchange Rates
  exchangeRate          Decimal?               @db.Decimal(20, 8)
  exchangeRateLockedAt  DateTime?
  exchangeRateSource    String?
  
  // Fees
  platformFee           Decimal                @default(0) @db.Decimal(20, 8)
  providerFee           Decimal                @default(0) @db.Decimal(20, 8)
  networkFee            Decimal                @default(0) @db.Decimal(20, 8)
  totalFee              Decimal                @default(0) @db.Decimal(20, 8)
  
  // Customer Info
  customerEmail         String?
  customerName          String?
  customerWallet        String?
  customerIp            String?
  customerCountry       String?
  
  // Risk & Compliance
  riskScore             Int?
  riskFactors           Json?
  kycStatus             KycStatus              @default(NOT_REQUIRED)
  kycVerifiedAt         DateTime?
  
  // Processing
  selectedRoute         Json?                  // Provider routing decision
  failureReason         String?
  failureCode           String?
  retryCount            Int                    @default(0)
  
  // Timestamps
  createdAt             DateTime               @default(now())
  startedAt             DateTime?
  completedAt           DateTime?
  updatedAt             DateTime               @updatedAt
  
  // Relations
  providerTransactions  ProviderTransaction[]
  blockchainTxs         BlockchainTransaction[]
  events                PaymentEvent[]
  agentDecisions        AgentDecision[]
  manualSteps           ManualProcessStep[]
  
  @@index([organizationId, status])
  @@index([orderNumber])
  @@index([paymentLinkId])
}

enum PaymentOrderStatus {
  CREATED
  AWAITING_PAYMENT
  PROCESSING
  REQUIRES_ACTION
  COMPLETED
  FAILED
  REFUNDED
  CANCELLED
}

enum KycStatus {
  NOT_REQUIRED
  PENDING
  IN_REVIEW
  APPROVED
  REJECTED
}

// ==========================================
// PROVIDER INTEGRATION MODELS
// ==========================================

model Provider {
  id                    String                 @id @default(cuid())
  code                  String                 @unique // YOINT, TRUBIT, etc
  name                  String
  type                  ProviderType
  
  // Capabilities
  supportedCountries    String[]
  supportedCurrencies   String[]
  paymentMethods        String[]
  features              Json                   // {instantPayouts: true, webhooks: true, etc}
  
  // Status
  isActive              Boolean                @default(true)
  healthStatus          ProviderHealth         @default(HEALTHY)
  lastHealthCheck       DateTime               @default(now())
  
  // Performance Metrics
  avgResponseTime       Int?                   // milliseconds
  successRate           Decimal?               @db.Decimal(5, 2)
  
  // Relations
  configs               ProviderConfig[]
  routes                ProviderRoute[]
  transactions          ProviderTransaction[]
  
  @@index([code])
}

enum ProviderType {
  BANKING_RAILS
  CARD_PROCESSOR
  CRYPTO_ONRAMP
  CRYPTO_OFFRAMP
  OPEN_BANKING
  WALLET
}

enum ProviderHealth {
  HEALTHY
  DEGRADED
  DOWN
  MAINTENANCE
}

model ProviderConfig {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  providerId            String
  provider              Provider               @relation(fields: [providerId], references: [id])
  
  // Configuration
  environment           Environment            @default(PRODUCTION)
  credentials           Json                   // Encrypted
  webhookSecret         String?                // Encrypted
  settings              Json                   @default("{}")
  
  // Status
  isActive              Boolean                @default(true)
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  @@unique([organizationId, providerId, environment])
  @@index([organizationId])
}

enum Environment {
  PRODUCTION
  SANDBOX
  TEST
}

model ProviderRoute {
  id                    String                 @id @default(cuid())
  providerId            String
  provider              Provider               @relation(fields: [providerId], references: [id])
  
  // Route Definition
  name                  String
  fromCountry           String
  toCountry             String
  fromCurrency          String
  toCurrency            String
  paymentMethod         String
  
  // Costs & Limits
  fixedFee              Decimal                @db.Decimal(20, 8)
  percentageFee         Decimal                @db.Decimal(5, 4)
  minAmount             Decimal                @db.Decimal(20, 8)
  maxAmount             Decimal                @db.Decimal(20, 8)
  
  // Performance
  estimatedTime         Int                    // minutes
  cutoffTime            String?                // HH:MM format
  workingDays           String[]               // ["MON", "TUE", ...]
  
  // Status
  isActive              Boolean                @default(true)
  priority              Int                    @default(100)
  
  @@index([providerId])
  @@index([fromCountry, toCountry, isActive])
}

model ProviderTransaction {
  id                    String                 @id @default(cuid())
  paymentOrderId        String
  paymentOrder          PaymentOrder           @relation(fields: [paymentOrderId], references: [id])
  providerId            String
  provider              Provider               @relation(fields: [providerId], references: [id])
  
  // Transaction Details
  type                  ProviderTxType
  externalId            String?                // Provider's transaction ID
  status                String                 // Provider-specific status
  
  // Request/Response
  request               Json
  response              Json?
  
  // Error Handling
  errorCode             String?
  errorMessage          String?
  isRetryable           Boolean                @default(false)
  
  // Timestamps
  createdAt             DateTime               @default(now())
  completedAt           DateTime?
  
  @@index([paymentOrderId])
  @@index([externalId])
}

enum ProviderTxType {
  PAYMENT_INITIATION
  STATUS_CHECK
  REFUND
  WEBHOOK_CALLBACK
  BALANCE_CHECK
  EXCHANGE_RATE
}

// ==========================================
// AGENT/AI MODELS
// ==========================================

model Agent {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  
  // Agent Configuration
  name                  String
  type                  AgentType
  version               String
  model                 String                 // LLM model used
  
  // LangGraph Configuration
  graphDefinition       Json                   // LangGraph structure
  tools                 String[]               // Available tools
  systemPrompt          String?
  
  // Status
  isActive              Boolean                @default(true)
  
  // Performance Metrics
  totalExecutions       Int                    @default(0)
  avgExecutionTime      Int?                   // milliseconds
  successRate           Decimal?               @db.Decimal(5, 2)
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  // Relations
  decisions             AgentDecision[]
  checkpoints           AgentCheckpoint[]
  
  @@index([organizationId])
  @@index([type])
}

enum AgentType {
  PAYMENT_ORCHESTRATOR
  RISK_ANALYZER
  ROUTE_OPTIMIZER
  FRAUD_DETECTOR
  CUSTOMER_SUPPORT
  RECONCILIATION
}

model AgentDecision {
  id                    String                 @id @default(cuid())
  agentId               String
  agent                 Agent                  @relation(fields: [agentId], references: [id])
  paymentOrderId        String?
  paymentOrder          PaymentOrder?          @relation(fields: [paymentOrderId], references: [id])
  
  // Decision Details
  decisionType          String                 // route_selection, risk_assessment, etc
  input                 Json                   // Input data to agent
  reasoning             Json                   // Chain of thought
  decision              Json                   // Final decision
  confidence            Decimal                @db.Decimal(3, 2) // 0.00 - 1.00
  
  // Execution
  executionTime         Int                    // milliseconds
  tokensUsed            Int?
  
  // Human Override
  wasOverridden         Boolean                @default(false)
  overriddenBy          String?
  overrideReason        String?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  
  // Relations
  interactions          AgentInteraction[]
  
  @@index([agentId])
  @@index([paymentOrderId])
}

model AgentCheckpoint {
  id                    String                 @id @default(cuid())
  agentId               String
  agent                 Agent                  @relation(fields: [agentId], references: [id])
  
  // Checkpoint Data
  threadId              String
  checkpointId          String
  state                 Json                   // LangGraph state
  metadata              Json?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  
  @@unique([agentId, threadId, checkpointId])
  @@index([agentId, threadId])
}

model AgentInteraction {
  id                    String                 @id @default(cuid())
  agentDecisionId       String
  agentDecision         AgentDecision          @relation(fields: [agentDecisionId], references: [id])
  userId                String
  user                  User                   @relation(fields: [userId], references: [id])
  
  // Interaction Details
  type                  InteractionType
  message               String?
  action                String?
  result                Json?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  
  @@index([agentDecisionId])
  @@index([userId])
}

enum InteractionType {
  APPROVAL_REQUEST
  INFORMATION_REQUEST
  OVERRIDE
  FEEDBACK
}

// ==========================================
// OPERATIONAL MODELS
// ==========================================

model Webhook {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  
  // Configuration
  url                   String
  events                String[]               // Event types to subscribe
  secret                String                 // For signature verification
  
  // Status
  isActive              Boolean                @default(true)
  failureCount          Int                    @default(0)
  lastFailureAt         DateTime?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  updatedAt             DateTime               @updatedAt
  
  // Relations
  deliveries            WebhookDelivery[]
  
  @@index([organizationId])
}

model WebhookDelivery {
  id                    String                 @id @default(cuid())
  webhookId             String
  webhook               Webhook                @relation(fields: [webhookId], references: [id])
  
  // Delivery Details
  eventType             String
  eventId               String
  payload               Json
  
  // Response
  statusCode            Int?
  response              String?
  error                 String?
  
  // Retry
  attempts              Int                    @default(1)
  nextRetryAt           DateTime?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  deliveredAt           DateTime?
  
  @@index([webhookId])
  @@index([eventId])
}

model ManualProcessStep {
  id                    String                 @id @default(cuid())
  paymentOrderId        String
  paymentOrder          PaymentOrder           @relation(fields: [paymentOrderId], references: [id])
  
  // Step Details
  type                  ManualStepType
  reason                String
  instructions          String?
  
  // Assignment
  assignedTo            String?
  assignedTeam          String?
  priority              Priority               @default(MEDIUM)
  
  // Status
  status                ManualStepStatus       @default(PENDING)
  resolution            String?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  startedAt             DateTime?
  completedAt           DateTime?
  dueAt                 DateTime?
  
  @@index([paymentOrderId])
  @@index([status, priority])
}

enum ManualStepType {
  KYC_REVIEW
  FRAUD_REVIEW
  EXCEPTION_HANDLING
  RECONCILIATION
  CUSTOMER_SUPPORT
}

enum ManualStepStatus {
  PENDING
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

enum Priority {
  LOW
  MEDIUM
  HIGH
  URGENT
}

// ==========================================
// EVENT SOURCING & AUDIT
// ==========================================

model PaymentEvent {
  id                    String                 @id @default(cuid())
  paymentOrderId        String
  paymentOrder          PaymentOrder           @relation(fields: [paymentOrderId], references: [id])
  
  // Event Details
  sequenceNumber        Int
  eventType             String
  eventVersion          String                 @default("1.0")
  
  // Payload
  data                  Json
  metadata              Json?
  
  // Kafka Integration
  kafkaTopic            String?
  kafkaPartition        Int?
  kafkaOffset           BigInt?
  
  // Timestamps
  occurredAt            DateTime               @default(now())
  
  @@unique([paymentOrderId, sequenceNumber])
  @@index([eventType])
  @@index([occurredAt])
}

model AuditLog {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  userId                String?
  user                  User?                  @relation(fields: [userId], references: [id])
  
  // Action Details
  action                String                 // user.login, payment.create, etc
  entityType            String?
  entityId              String?
  
  // Context
  changes               Json?                  // Before/after for updates
  metadata              Json?
  
  // Request Info
  ipAddress             String?
  userAgent             String?
  requestId             String?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  
  @@index([organizationId, createdAt])
  @@index([userId])
  @@index([entityType, entityId])
}

// ==========================================
// API ACCESS MODELS
// ==========================================

model ApiKey {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  
  // Key Details
  name                  String
  keyHash               String                 @unique
  prefix                String                 // First 8 chars for identification
  
  // Permissions
  scopes                String[]               // ["payments:read", "payments:write", etc]
  
  // Limits
  rateLimit             Int?                   // Requests per minute
  
  // Status
  isActive              Boolean                @default(true)
  expiresAt             DateTime?
  lastUsedAt            DateTime?
  
  // Timestamps
  createdAt             DateTime               @default(now())
  revokedAt             DateTime?
  
  @@index([organizationId])
  @@index([prefix])
}

// ==========================================
// JUNCTION TABLES
// ==========================================

model OrganizationUser {
  id                    String                 @id @default(cuid())
  organizationId        String
  organization          Organization           @relation(fields: [organizationId], references: [id])
  userId                String
  user                  User                   @relation(fields: [userId], references: [id])
  
  // Role & Permissions
  role                  UserRole
  permissions           String[]               // Granular permissions
  
  // Invitation
  invitedBy             String?
  invitedAt             DateTime               @default(now())
  acceptedAt            DateTime?
  
  // Status
  isActive              Boolean                @default(true)
  
  @@unique([organizationId, userId])
  @@index([userId])
}

enum UserRole {
  OWNER
  ADMIN
  DEVELOPER
  FINANCE
  SUPPORT
  VIEWER
}
```

## Key Enhancements Explained

### 1. **Web3 Integration**
- Added `Wallet` model for managing both EOA and smart wallets
- `BlockchainTransaction` tracks on-chain transactions with gas sponsorship
- `GasSponsorship` enables gasless transactions for better UX
- Smart contract references in `PaymentLink` for on-chain payment metadata

### 2. **Enhanced Provider Abstraction**
- `Provider` model with capabilities and health monitoring
- `ProviderRoute` for intelligent routing decisions
- Dynamic provider configuration per organization
- Performance metrics for route optimization

### 3. **Agent/AI Infrastructure**
- `Agent` model for LangGraph agent definitions
- `AgentDecision` tracks reasoning and decisions with confidence scores
- `AgentCheckpoint` for LangGraph state persistence
- `AgentInteraction` for human-in-the-loop tracking

### 4. **Improved Transaction Model**
- Separated exchange rate tracking and locking
- Detailed fee breakdown (platform, provider, network)
- Risk scoring and KYC status
- Multi-step transaction support via events

### 5. **Event Sourcing**
- `PaymentEvent` for complete transaction history
- Kafka integration fields for event streaming
- Sequence numbers for event ordering
- Event versioning for schema evolution

### 6. **Operational Excellence**
- `ManualProcessStep` for exception handling
- `WebhookDelivery` for reliable webhook processing
- Comprehensive `AuditLog` for compliance
- API key management with scoped permissions

## Implementation Considerations

### MVP Phase
Focus on:
1. Core models: Organization, User, PaymentLink, PaymentOrder
2. Basic provider integration (Yoint, Trubit)
3. Simple wallet support for Clerk + Circle
4. Essential audit logging

### Post-MVP Phase
Add:
1. Full agent infrastructure
2. Advanced routing with ML optimization
3. Multi-chain blockchain support
4. Complex compliance workflows

## Data Migration Strategy

1. **Initial Setup**: Use Alembic migrations to create base schema
2. **Incremental Updates**: Add new models/fields as features are implemented
3. **Data Seeding**: Create test data for development
4. **Performance Optimization**: Add indexes based on query patterns

## Security Considerations

1. **Encryption**: All sensitive fields (credentials, keys) must be encrypted at rest
2. **Multi-tenancy**: Enforce organization-level data isolation at application layer
3. **Audit Trail**: Every state change must be logged
4. **PII Handling**: Customer data must comply with data protection regulations 