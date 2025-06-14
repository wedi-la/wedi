# 🏛️ Wedi AI-Native Payment Orchestration Architecture Blueprint

⸻

1️⃣ Core Concept Recap

👉 Wedi’s Idea:
Clients (merchants, platforms) integrate with Wedi’s platform to offer smart checkout experiences, with an optimized orchestrated payment agent deciding the best way to route a payment across available payment rails (banking, on/off-ramps, cards, blockchain).
	•	API-first
	•	Agent-native
	•	Event-driven
	•	Multitenant SaaS

👉 Agents are first-class orchestrators that:
	•	Reason about current state of transaction
	•	Consider fees, rails, market conditions, risks
	•	Use a LangGraph-based execution engine
	•	Support human-in-the-loop steps where needed
	•	Are event-driven and observable by humans in real time

👉 Unified State Model connects:
	•	Agent execution
	•	Database (Postgres via Prisma)
	•	Event bus (Kafka)
	•	CoAgent UI (via CopilotKit in Next.js app)
	•	External systems

⸻

2️⃣ Architectural Summary

+-------------------------+
| Client Systems          |
|  (embedded checkout)    |
+-------------------------+
           |
           v
+-------------------------+
| Wedi API (FastAPI)      |
| /integrations /payments |
+-------------------------+
           |
           v
+---------------------------+
| Event Bus (Kafka)         |
| transaction.created, etc. |
+---------------------------+
           |
           v
+-------------------------+
| Agentic Workers         |
| LangGraph agents        |
| Agent registry, State   |
| Transaction orchestration|
+-------------------------+
           |
           v
+-------------------------+
| Database (Postgres)     |
| Prisma schema = source  |
| of truth for state      |
+-------------------------+
           |
           +---------> CopilotKit CoAgents (Next.js UI)
           |            Real-time UI, HITL, Chat/Popup/Headless
           |
           +---------> Kafka consumers / external processors
           |
           +---------> External API calls (providers, rails)


⸻

3️⃣ Key Decisions & Justifications

Event Backbone
	•	Kafka is the backbone → high scalability, loose coupling between API ↔ agents ↔ external systems
	•	Celery/Rabbit is too limited for future scale. Kafka gives us multi-consumer patterns, replay, DLQ handling.

Agent Execution Platform
	•	LangGraph agents (Python) running as part of FastAPI or standalone worker
	•	We use langgraph.serve or FastMCP to serve them efficiently
	•	Designed to allow multi-agent graphs → e.g. separate agents for:
	•	Provider selection
	•	Rail selection
	•	Fraud/risk checks
	•	Transaction execution
	•	Compliance checks

Database Model
	•	Prisma schema is already perfect:
	•	Transaction model aligns exactly to TransactionState used in agents
	•	TransactionEvent model supports detailed state changes
	•	Webhook, Agent, Integration, Provider models already in place for orchestration!

Agent State Synchronization
	•	Agent state is always initialized from DB → agent runs with a TransactionState pulled from DB
	•	All state updates emitted via:
	•	CopilotKit emit_state → real-time frontend visibility
	•	Database write → source of truth
	•	Kafka TransactionEvent → external consumers
	•	Agents can wait on Kafka topics for asynchronous steps (e.g. external payment confirmation)

CopilotKit Integration
	•	Embedded in Next.js app (client & internal dashboards)
	•	CopilotKit Provider at root
	•	CopilotChat + Popup + Sidebar + Headless options
	•	Multi-agent capability:
	•	Single orchestrator agent (“pay_orchestrator”) exposed to UI
	•	LangGraph runs sub-agents internally → simpler for UI to handle
	•	Human-in-the-loop via useCopilotAction:
	•	Provider selection
	•	Rail selection
	•	Manual approvals
	•	Fraud override steps
	•	Anything else the business requires

API / Backend Access
	•	Agents use internal API clients to call FastAPI endpoints or directly invoke service logic
	•	No code duplication: agents call the same business logic as public API routes
	•	Fully authenticated / authorized

⸻

4️⃣ CopilotKit UI Strategy

UI Component	Usage
CopilotChat	Transparent full chat with orchestrator agent
CopilotPopup	Quick user prompts (approve provider, select rail)
CopilotSidebar	Persistent sidebar for operations dashboards
Headless CoAgent	Background state sync for real-time dashboard updates without chat

Hooks we will use:
	•	useCoAgent → real-time transaction state
	•	useCopilotAction → interactive steps from agent
	•	useCoAgentStateRender → show logs / status in UI

⸻

5️⃣ Design Principles

✅ Agent-native: LangGraph agents orchestrate the flow, not rigid workflows
✅ Event-driven: All key lifecycle events flow through Kafka
✅ Human-in-the-loop: CoAgent UI gives humans visibility & control
✅ Unified state: Prisma schema ↔ agent state ↔ Kafka events ↔ UI state
✅ Extensibility: New agents, new rails, new providers can be added by graph extension
✅ Observability: Real-time CopilotKit UI, TransactionEvent model in DB, Kafka stream → no black boxes
✅ Scalable: Kafka allows scale across agents, event consumers, provider integrations

⸻

6️⃣ Next Steps / To Implement

Immediate

✅ Finalize LangGraph orchestration graphs:
	•	PaymentOrchestrator graph with sub-agents:
	•	Provider selection
	•	Rail selection
	•	Payment execution
	•	Confirm / update state
	•	Implement in /apps/agentic-workers or /apps/api/agents

✅ Finalize CopilotKit integration:
	•	Add CopilotKit provider in Next.js app
	•	Build transaction dashboard with:
	•	Live state display (logs, status)
	•	Approvals flow via useCopilotAction
	•	Manual override capabilities
	•	Embed chat popup in the core app (optional)

✅ Align Kafka schemas with TransactionState:
	•	TransactionCreated
	•	TransactionUpdated
	•	TransactionCompleted
	•	TransactionFailed
	•	TransactionEvent (for event stream)

✅ Build agent <-> Kafka bridge:
	•	Agents should:
	•	Publish Kafka events at key steps
	•	Subscribe to Kafka topics (for confirmations)

✅ Define agent tool abstraction layer:
	•	LangGraph nodes calling:
	•	Provider API integrations
	•	Internal FastAPI endpoints
	•	External data services (FX rates, risk scoring)

Medium term
	•	Implement multi-agent experiments:
	•	Separate risk agent
	•	Separate optimization agent for fees / rates
	•	Add observability tooling:
	•	Grafana dashboards consuming TransactionEvent stream
	•	Prometheus metrics from agent runs

⸻

7️⃣ Final Synthesis

We are building:
👉 A Composable Agentic Payments Orchestration Platform
👉 Fully multitenant, agent-first, API-first, event-driven
👉 With transparent, human-visible AI reasoning via CoAgent UI
👉 With LangGraph agents acting as programmable payment routers that learn and optimize over time
👉 Exposing:
	•	API
	•	Kafka stream
	•	CoAgent interactive UI
	•	Embedded checkout SDKs (eventually)

And critically:
	•	Agent state ↔ DB state ↔ Kafka state ↔ UI state is one consistent source of truth → no divergent sources.

⸻


1. Alcance y definición del MVP
	•	Producto mínimo viable: Un link/botón de pago internacional sencillo, optimizado con Open Banking y blockchain, que permita cobros uno a uno.
	•	Funcionalidades excluidas (por ahora):
	•	Marketplaces y e-commerce
	•	Suscripciones y pagos recurrentes
	•	Integración profunda en el checkout de clientes

⸻

2. Enfoque técnico y flujos de pago
	•	Ruta piloto: Colombia ↔ México
	•	Recolección en Colombia: integrarse con Join
	•	Pago en México: integrarse con Trubit
	•	Configuración inicial:
	•	Manual (administrador crea statically el link con valor y país)
	•	APIs de Join/Trubit donde estén disponibles
	•	Proceso de usuario final:
	1.	Cliente B2B genera link en la plataforma Wy
	2.	Envía link por WhatsApp, correo o web
	3.	Usuario final hace clic y paga vía botón/link

⸻

3. Diferenciación y propuesta de valor
	•	Valor clave:
	•	Costo más bajo y velocidad superior frente a Stripe, Swift y billeteras tradicionales
	•	Cobros directos cuenta a cuenta con respaldo de blockchain y Open Banking
	•	UI embedible:
	•	Link simple que puede presentarse como botón en distintos canales sin reemplazar el checkout existente


## Wedi MVP: International B2B Payment Link Platform - Technical Blueprint

**1. Overview & MVP Definition**

*   **Core Product:** A platform for B2B clients (Organizations) to generate and send international payment links to their customers.
*   **Initial Focus:** Facilitating payments between Colombia and Mexico (e.g., a Colombian business collecting from a Mexican client, or vice-versa).
*   **Target Users (Wedi's Clients):** Businesses (e.g., SaaS companies, freelancers, service providers) needing to collect one-to-one international payments.
*   **End-Users:** The clients of Wedi's B2B customers who receive and pay via the links.
*   **Key Providers (MVP):**
    *   **Yoint:** For payment collection/initiation in Colombia.
    *   **Trubit / Prometeo:** For payment collection/initiation in Mexico.
*   **Process:**
    1.  Wedi's B2B client (within their Organization) logs into the Wedi Next.js dashboard.
    2.  They create and configure a payment link (amount, currency, description).
    3.  The client shares this link (e.g., via email, WhatsApp) with their international customer.
    4.  The end-customer clicks the link, views a payment page, and initiates payment.
    5.  Wedi's FastAPI backend (specifically the "Payment Execution Agent" module) orchestrates the transaction using Yoint and Trubit/Prometeo APIs.
    6.  The status is updated, and events are published to a managed Kafka stream (e.g., Redpanda Cloud).
    7.  The B2B client is notified and can track status in their dashboard.
*   **Core Philosophy:** Begin with a robust, simpler backend module for payment execution, designed with agentic principles (autonomy, task-specific) in mind, paving the way for future evolution into more sophisticated LangGraph-based agents.

**2. Overall Architecture (MVP)**

```mermaid
graph TD
    subgraph "User Devices"
        ClientAdmin
        EndCustomer
    end

    subgraph "Wedi Platform (Hosted on Vercel/Railway)"
        subgraph "apps/frontend (Next.js on Vercel)"
            NextApp[Next.js Application]
            NextAPIRoutes
            CopilotKitUI[(Future) CopilotKit UI for CoAgents]
        end

        subgraph "apps/backend (FastAPI on Railway)"
            FastAPI[FastAPI Application]
            PaymentExecAgent[Payment Execution Agent Module]
            UserOrgMgmt[User & Org Mgmt Module]
            LinkMgmt[Link Mgmt Module]
            NotificationSvc[Notification Module]
        end

        subgraph "Shared Infrastructure"
            NeonDB
            ManagedKafka
        end

        subgraph "Future Agentic Services (on Railway)"
            AgentsService[(apps/agents-service - LangGraph)]
            WorkersService
        end
    end

    subgraph "External Payment Service Providers (PSPs)"
        YointPSP[Yoint API]
        TrubitPrometeoPSP
    end

    subgraph "Documentation (Hosted)"
        DocsService
    end

    ClientAdmin -- HTTPS --> NextApp
    EndCustomer -- HTTPS --> NextApp
    NextApp -- Uses --> NextAPIRoutes
    NextAPIRoutes -- HTTP/S --> FastAPI

    FastAPI -- Prisma ORM --> NeonDB
    FastAPI -- Produces/Consumes --> ManagedKafka
    PaymentExecAgent -- API Calls --> YointPSP
    PaymentExecAgent -- API Calls --> TrubitPrometeoPSP

    NotificationSvc -- Consumes --> ManagedKafka

    %% Future Connections
    CopilotKitUI -.-> AgentsService
    WorkersService -.-> AgentsService
    ManagedKafka -.-> WorkersService
```

**3. Monorepo Structure (Turborepo with Bun)**

The project will use Turborepo for managing the monorepo, with Bun as the package manager and runtime. [1]

```
/
|-- apps/
| |-- backend/          # FastAPI application (Python)
| | |-- app/
| | | |-- api/        # API routers
| | | |-- core/       # Config, security
| | | |-- crud/       # CRUD operations for DB models
| | | |-- db/         # Database session, Prisma client (if used from Python via bridge/IPC, or direct SQL)
| | | |-- models/     # Pydantic models for API
| | | |-- schemas/    # Pydantic schemas for validation
| | | |-- services/   # Business logic, incl. Payment Execution Agent module
| | | |-- events/     # Kafka producer/consumer logic
| | |-- main.py
| | |-- Dockerfile
| | |-- requirements.txt
| |-- frontend/         # Next.js application (TypeScript)
| | |-- app/          # Next.js App Router
| | |-- components/   # Shadcn UI, MagicUI components
| | |-- lib/          # Helper functions, TanStack Query setup
| | |-- public/
| | |-- next.config.mjs
| | |-- bunfig.toml
| | |-- tsconfig.json
| |-- agents-service/   # (Future) LangGraph agents (Python/TypeScript)
| | |-- Dockerfile
| |-- workers-service/  # (Future) API Gateway to trigger agents (Python/Node.js)
| | |-- Dockerfile
| |-- docs-service/     # Scalar API documentation configuration
| |-- openapi.yaml  # OpenAPI spec generated from FastAPI
| |-- Dockerfile    # To serve Scalar docs
|-- packages/
| |-- ui/               # Shared React components (Shadcn UI based)
| |-- config/           # Shared configurations (e.g., ESLint, Prettier, TSConfig)
| |-- prisma/           # Prisma schema, client, and migrations
| | |-- schema.prisma
| | |-- migrations/
| | |-- client.ts     # Prisma client instance
| |-- types/            # Shared TypeScript types/interfaces (e.g., for API contracts, events)
| |-- eslint-config-custom/
| |-- tsconfig-custom/
|-- bun.lockb
|-- package.json          # Root package.json for Turborepo scripts
|-- turbo.json
```

**4. Database Schema (Neon DB - PostgreSQL with Prisma ORM)**

Neon DB provides serverless PostgreSQL. **Clerk** will be used for authentication, integrating with Next.js and Neon. When users authenticate via Clerk (using Google Auth or other providers), Circle USDC wallet functionality will be separately initialized to establish their Web3 identity alongside traditional authentication. The schema below is designed for multi-tenancy at the `Organization` level. Data segregation will be primarily enforced at the application layer by filtering queries based on `organizationId` derived from the authenticated user's context. Row-Level Security (RLS) in PostgreSQL can be explored as a future enhancement for database-level enforcement.

```prisma
// packages/prisma/schema.prisma

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL") // Neon DB connection string
}

generator client {
  provider = "prisma-client-js"
  output   = "./generated/client"
}

// Multi-tenancy: Organization is the primary tenant
model Organization {
  id                  String               @id @default(cuid())
  name                String
  createdAt           DateTime             @default(now())
  updatedAt           DateTime             @updatedAt
  ownerId             String // User ID of the organization creator/owner
  users               OrganizationUser   // Users belonging to this organization
  paymentLinks        PaymentLink
  apiKeys             ApiKey
  providerCredentials ProviderCredential
  auditLogEntries     AuditLogEntry

  @@index([ownerId])
}
model User {
  id                  String               @id @default(cuid())
  email               String               @unique
  name                String?
  walletAddress       String?              @unique // Clerk-created wallet address
  authProvider        String?              // e.g., "CLERK", "GOOGLE", "EMAIL"
  authProviderId      String?              // User ID from the auth provider
  createdAt           DateTime             @default(now())
  updatedAt           DateTime             @updatedAt
  organizationMemberships OrganizationUser
  createdPaymentLinks PaymentLink        @relation("CreatedByUser")
  auditLogEntries     AuditLogEntry

  @@unique([authProvider, authProviderId])
  @@index([walletAddress])
}

// Junction table for many-to-many relationship between User and Organization
model OrganizationUser {
  id             String       @id @default(cuid())
  organizationId String
  userId         String
  role           UserRole     @default(MEMBER) // e.g., ADMIN, MEMBER, BILLING_MANAGER
  invitedBy      String?      // User ID of who invited this user
  joinedAt       DateTime     @default(now())
  organization   Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  user           User         @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([organizationId, userId])
  @@index([userId])
}

enum UserRole {
  ADMIN
  MEMBER
  OWNER // Could be a special role for the creator
}

model ApiKey {
  id             String       @id @default(cuid())
  hashedKey      String       @unique
  prefix         String       @unique // For easy identification (e.g., wedi_pk_...)
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  name           String?
  lastUsedAt     DateTime?
  expiresAt      DateTime?
  revokedAt      DateTime?
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt
  permissions    Json?        // Granular permissions for the API key
}

model IntegrationKey {
  id             String       @id @default(cuid())
  hashedKey      String       @unique
  prefix         String       @unique // e.g., wedi_ik_...
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  agentId        String       // Agent authorized to process payments for this key
  agent          Agent        @relation(fields: [agentId], references: [id])
  name           String?
  description    String?      // Purpose or scope of this integration key
  lastUsedAt     DateTime?
  expiresAt      DateTime?
  revokedAt      DateTime?
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt
  paymentLinks   PaymentLink[]

  @@index([agentId])
}

model PaymentLink {
  id                  String            @id @default(cuid())
  organizationId      String
  organization        Organization      @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  createdById         String
  createdBy           User              @relation("CreatedByUser", fields: [createdById], references: [id])
  integrationKeyId    String            // Integration key that authorizes agent for this link
  integrationKey      IntegrationKey    @relation(fields: [integrationKeyId], references: [id])
  description         String?
  referenceId         String?           // Client's internal reference for the link
  amount              Float             // Amount in the source currency
  currency            String            // ISO currency code of the source (e.g., "COP", "MXN")
  targetAmount        Float?            // Optional: if pre-calculated, amount in target currency
  targetCurrency      String?           // Optional: ISO currency code of the target
  status              PaymentLinkStatus @default(ACTIVE)
  expiresAt           DateTime?
  metadata            Json?             // Client-defined metadata (key-value pairs)
  shortCode           String?           @unique // For shorter, shareable URLs
  allowMultiplePayments Boolean         @default(false)
  redirectUrlSuccess  String?           // URL to redirect to on successful payment
  redirectUrlFailure  String?           // URL to redirect to on failed payment
  createdAt           DateTime          @default(now())
  updatedAt           DateTime          @updatedAt
  paymentOrders       PaymentOrder[]
  auditLogEntries     AuditLogEntry[]

  @@index([organizationId])
  @@index([integrationKeyId])
}

enum PaymentLinkStatus {
  ACTIVE
  PAID
  EXPIRED
  ARCHIVED
  CANCELLED
}

model PaymentOrder {
  id                      String                  @id @default(cuid())
  paymentLinkId           String
  paymentLink             PaymentLink             @relation(fields: [paymentLinkId], references: [id], onDelete: Cascade)
  organizationId          String                  // Denormalized for easier querying within tenant scope
  status                  PaymentOrderStatus
  amountExpected          Float                   // Amount from PaymentLink
  currencyExpected        String                  // Currency from PaymentLink
  amountPaid              Float?                  // Actual amount paid by end-customer
  currencyPaid            String?                 // Actual currency paid by end-customer
  endCustomerEmail        String?                 // Email provided by payer, if any
  endCustomerName         String?
  failureReason           String?
  failureCode             String?                 // Provider-specific failure code
  providerTransactions    ProviderTransaction
  manualProcessSteps      ManualProcessStep
  createdAt               DateTime                @default(now())
  updatedAt               DateTime                @updatedAt
  auditLogEntries         AuditLogEntry
  paymentOrderEvents      PaymentOrderEvent     // For event sourcing specific to this order

  @@index([paymentLinkId])
  @@index([organizationId, status]) // Useful for tenant-specific status dashboards
}

enum PaymentOrderStatus {
  PENDING_CUSTOMER_ACTION // Link viewed, awaiting customer payment
  PROCESSING              // Payment initiated, Wedi is processing
  REQUIRES_MANUAL_INTERVENTION
  SUCCEEDED
  FAILED
  REFUNDED
  PARTIALLY_REFUNDED
  CANCELLED
}

model ProviderCredential {
  id             String       @id @default(cuid())
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  providerName   String       // e.g., "YOINT_COLOMBIA", "TRUBIT_MEXICO", "PROMETEO_MEXICO"
  config         Json         // Encrypted API keys, webhook secrets, other config
  isActive       Boolean      @default(true)
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt

  @@unique([organizationId, providerName])
}

model ProviderTransaction {
  id                      String            @id @default(cuid())
  paymentOrderId          String
  paymentOrder            PaymentOrder      @relation(fields: [paymentOrderId], references: [id], onDelete: Cascade)
  providerName            String            // e.g., "YOINT", "TRUBIT", "PROMETEO"
  providerTransactionId   String?           @unique // ID from the provider
  type                    String            // e.g., "COLLECTION_INITIATION", "PAYOUT_CONFIRMATION", "STATUS_CHECK"
  status                  String            // Provider's status for this specific interaction
  requestPayload          Json?
  responsePayload         Json?
  errorCode               String?
  errorMessage            String?
  timestamp               DateTime          @default(now())
  auditLogEntries         AuditLogEntry
}

model ManualProcessStep {
  id             String        @id @default(cuid())
  paymentOrderId String
  paymentOrder   PaymentOrder  @relation(fields: [paymentOrderId], references: [id], onDelete: Cascade)
  stepName       String        // Description of the manual step
  status         String        // e.g., "PENDING_ACTION", "IN_PROGRESS", "COMPLETED", "BLOCKED"
  assignedTo     String?       // User ID or team within Wedi
  notes          Json?         // Notes or details about the manual step
  createdAt      DateTime      @default(now())
  updatedAt      DateTime      @updatedAt
}

model AuditLogEntry {
  id                  String                @id @default(cuid())
  timestamp           DateTime              @default(now())
  actingUserId        String?               // User who performed the action (Wedi client user)
  actingUser          User?                 @relation(fields: [actingUserId], references: [id])
  organizationId      String                // Organization context of the action
  organization        Organization          @relation(fields: [organizationId], references: [id])
  targetEntityType    String?               // e.g., "PaymentLink", "PaymentOrder", "User"
  targetEntityId      String?
  action              String                // e.g., "PAYMENT_LINK_CREATED", "USER_INVITED", "PAYMENT_ORDER_STATUS_CHANGED_TO_SUCCEEDED"
  details             Json?                 // Additional context about the action
  ipAddress           String?
  userAgent           String?

  @@index([organizationId, timestamp])
  @@index([actingUserId])
  @@index()
}

// For event sourcing specific to payment orders
model PaymentOrderEvent {
  id             String       @id @default(cuid())
  paymentOrderId String
  paymentOrder   PaymentOrder @relation(fields: [paymentOrderId], references: [id], onDelete: Cascade)
  sequenceNumber Int          // Ensures order of events for a given payment order
  eventType      String       // e.g., "CustomerPaymentInitiated", "YointApiCalled", "TrubitTransferSucceeded", "ManualStepRequired"
  payload        Json         // Event-specific data
  timestamp      DateTime     @default(now())

  @@unique([paymentOrderId, sequenceNumber])
  @@index([paymentOrderId])
}

model Agent {
  id                  String            @id @default(cuid())
  organizationId      String
  organization        Organization      @relation(fields: [organizationId], references: [id], onDelete: Cascade)
  name                String
  type                AgentType         @default(PAYMENT_PROCESSOR)
  walletAddress       String?           // Agent's blockchain wallet for operations
  capabilities        Json              // Supported providers, corridors, etc.
  status              AgentStatus       @default(ACTIVE)
  metadata            Json?
  createdAt           DateTime          @default(now())
  updatedAt           DateTime          @updatedAt
  integrationKeys     IntegrationKey[]

  @@index([organizationId])
}

enum AgentType {
  PAYMENT_PROCESSOR
  FRAUD_DETECTOR
  RECONCILIATION
  CUSTOMER_SUPPORT
}

enum AgentStatus {
  ACTIVE
  INACTIVE
  SUSPENDED
}
```

**Multi-tenancy & Data Segregation:**
*   Each `Organization` is a tenant.
*   Users are associated with `Organization`s via `OrganizationUser` with specific roles.
*   All core data (`PaymentLink`, `PaymentOrder`, `ApiKey`, `ProviderCredential`) is directly linked to an `organizationId`.
*   **Application Layer Enforcement (MVP):** All database queries made through Prisma from the FastAPI backend will be filtered by `organizationId`. This ID will be derived from the authenticated user's JWT token (managed by Clerk Auth and validated by the backend).
*   **Dual Authentication Model:**
    *   **B2B Users (Dashboard/API):** Authenticate via Clerk (Google, email, etc.), receive JWT tokens, and access organization-scoped resources.
    *   **Payment Links (Public):** Use integration keys to authorize agents for processing payments without requiring end-customer authentication.
*   **Row-Level Security (RLS) in Neon DB (Future Enhancement):** As the system matures, RLS policies can be defined directly in PostgreSQL to provide an additional layer of data isolation at the database level. Prisma can work with RLS, but it requires careful setup.

**5. Backend (FastAPI - `apps/backend`)**

*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **ORM:** Prisma (Python client or direct SQL if Prisma Python client is not mature enough for all needs; for MVP, direct SQL with Pydantic for validation is also an option if Prisma Python is a hurdle). *Correction: Prisma's primary client is JS/TS. For Python, direct SQL with an async library like `asyncpg` and Pydantic for validation is more common, or using a Python-native ORM like SQLModel or Tortoise ORM. Given the Prisma schema is already defined, using a tool to generate Pydantic models from it could be useful, or manually defining them.*
    *   **Revised DB Access for FastAPI:** Use `asyncpg` for direct async PostgreSQL interaction, with Pydantic models for data validation and serialization, mapping to the Prisma-defined schema.
*   **API Endpoints:**
    *   `/auth/*`: JWT validation endpoints for Clerk-issued tokens.
    *   `/organizations/*`: CRUD for organizations, inviting users (requires Clerk JWT).
    *   `/users/*`: User profile management (requires Clerk JWT).
    *   `/payment-links/*`: CRUD for payment links (requires Clerk JWT).
    *   `/payment-links/public/{shortCode}`: Public endpoint for viewing payment link details (no auth required).
    *   `/payment-orders/*`: Status retrieval (requires Clerk JWT or integration key).
    *   `/payment-orders/initiate`: Public endpoint for initiating payments (requires integration key).
    *   `/integration-keys/*`: Manage integration keys for agents (requires Clerk JWT).
    *   `/webhooks/providers/*`: To receive incoming webhooks from Yoint, Trubit/Prometeo.
*   **Modules (`app/services/`):**
    *   **`user_org_service.py`:** Handles logic for user authentication (via Clerk JWT validation), organization creation, user invitations, role management, and automatic wallet association.
    *   **`payment_link_service.py`:** Business logic for creating, retrieving, updating, and managing the lifecycle of payment links.
    *   **`payment_execution_agent.py` (Core MVP "Agent"):**
        *   **Trigger:** Invoked when a payment is initiated via a payment link (e.g., through a public API endpoint called by the payment link UI, authenticated with an integration key).
        *   **Responsibilities:**
            1.  Validate the integration key and ensure the associated agent is authorized.
            2.  Create a `PaymentOrder` record.
            3.  Fetch `ProviderCredential` for the organization.
            3.  **Colombia-Mexico Flow Orchestration:**
                *   Make API calls to Yoint (for Colombia leg).
                *   Make API calls to Trubit/Prometeo (for Mexico leg).
                *   Handle responses, including errors and retries (for transient errors).
                *   Update `PaymentOrder` status throughout the process.
                *   Log all provider interactions in `ProviderTransaction`.
                *   If manual steps are needed (e.g., for exceptions, reconciliation), create `ManualProcessStep` records and flag the `PaymentOrder` (e.g., status `REQUIRES_MANUAL_INTERVENTION`).
            4.  Publish significant events (e.g., `PaymentOrderSucceeded`, `PaymentOrderFailed`, `ManualStepRequired`) to the managed Kafka instance.
        *   **Idempotency:** Ensure operations are idempotent, especially when reacting to webhooks or retrying steps.
    *   **`notification_service.py`:** (Can be part of the main app or a separate consumer) Listens to Kafka events (e.g., `PaymentOrderSucceeded`) and sends notifications (e.g., email to B2B client).
    *   **`kafka_producer.py` / `kafka_consumer.py`:** Utilities for interacting with Redpanda Cloud.
*   **Development Standards:** Airbnb Style Guide (adapted for Python - e.g., PEP 8, Black, Flake8, MyPy for typing). English for code/docs. Short functions, early returns. Pydantic for data validation (RO-RO pattern).

**6. Frontend (Next.js - `apps/frontend`)**

*   **Framework:** Next.js 14+ with App Router.
*   **Package Manager/Runtime:** Bun.
*   **Styling:** Tailwind CSS.
*   **UI Components:** Shadcn UI, MagicUI. [2]
*   **State Management:** React Context for simple global state; TanStack Query (React Query) for server state management, caching, and data fetching.
*   **Forms:** React Hook Form with Zod for validation.
*   **Key Features:**
    *   **B2B Client Dashboard:**
        *   Authentication via Clerk (Google Auth, email, etc.) with automatic wallet creation.
        *   Organization management (create, view members, invite users).
        *   Payment link creation and management interface.
        *   Integration key management for connecting payment links to agents.
        *   Dashboard to view payment order statuses and history.
        *   Wallet management and blockchain transaction history.
        *   Settings (e.g., API key management, provider credential input - securely).
    *   **Payment Link UI:** Simple, responsive page for end-customers to view payment details and be redirected/guided through the payment process with the selected provider (Yoint or Trubit/Prometeo).
*   **Next.js API Routes (`app/api/`) - Backend For Frontend (BFF):**
    *   Act as a proxy to the FastAPI backend. This allows:
        *   Consolidating multiple backend calls.
        *   Handling frontend-specific authentication/session logic (with Clerk Auth).
        *   Managing JWT tokens from Clerk for backend API calls.
        *   Transforming data for frontend consumption.
        *   Keeping backend API endpoints internal if desired.
    *   Example: `/api/payment-links` in Next.js would call `https://api.wedi.com/v1/payment-links` (FastAPI).
*   **CopilotKit (Future):** [3, 4, 5, 2]
    *   The frontend will be prepared for future integration of CopilotKit.
    *   `useCopilotChat()`, `<CopilotSidebar />` can be added to the dashboard.
    *   CoAgents in CopilotKit will eventually interact with the LangGraph agents in `apps/agents-service` via the `apps/workers-service` (API gateway for agents).
*   **Development Standards:** Airbnb Style Guide, named exports, comprehensive TS, JSDoc, etc., as specified.

**7. Event Bus (Managed Kafka - e.g., Redpanda Cloud)**

*   **Rationale:** Chosen for its Kafka compatibility with lower operational overhead for a small team compared to self-managed Kafka. Provides durability, replayability, and asynchronous processing. [6, 7, 8, 9, 10, 11, 12]
*   **Key Event Topics (MVP):**
    *   `wedi.organization.events` (e.g., `OrganizationCreated`, `UserInvitedToOrganization`)
    *   `wedi.lamentlink.events` (e.g., `PaymentLinkCreated`, `PaymentLinkActivated`)
    *   `wedi.lamentorder.events` (e.g., `PaymentOrderInitiated`, `PaymentOrderProcessing`, `PaymentOrderSucceeded`, `PaymentOrderFailed`, `PaymentOrderManualInterventionRequired`)
*   **Producers:** FastAPI backend (Payment Execution Agent, User/Org Mgmt, Link Mgmt modules).
*   **Consumers (MVP):**
    *   Notification module within FastAPI (or a simple separate worker if needed) for sending emails/webhooks.
    *   (Future) `apps/workers-service` will consume events to trigger LangGraph agents.
    *   (Future) Analytics/BI systems.
*   **Schema Registry:** Utilize the schema registry provided by the managed Kafka service (e.g., Redpanda Console includes one) or a compatible one to ensure event schema consistency (e.g., using Avro or Protobuf, defined in `packages/types`).

**8. Authentication Flow & Security Model**

The platform implements a dual authentication model to support both authenticated B2B users and public payment link access:

**B2B User Authentication (Dashboard/API):**
1. Users log in via Clerk using Google Auth or other supported providers
2. Clerk automatically creates a wallet for each user upon first login
3. Clerk issues JWT tokens that contain user identity and wallet information
4. Frontend stores JWT and includes it in all API requests to the backend
5. FastAPI backend validates Clerk JWTs on protected endpoints
6. User's organizationId from JWT is used for multi-tenant data filtering

**Payment Link Public Access:**
1. When creating a payment link, an integration key is assigned to connect it with an authorized agent
2. End-customers access payment links via public URLs (no authentication required)
3. Payment initiation requests include the integration key from the payment link
4. Backend validates the integration key and ensures the associated agent is active
5. Agent processes the payment using its configured capabilities and provider credentials

**Security Considerations:**
- All Clerk JWTs are validated using Clerk's public keys
- Integration keys are hashed before storage (similar to API keys)
- Rate limiting applied to public endpoints to prevent abuse
- Webhook signatures verified for provider callbacks
- Agent wallets use multi-signature for high-value operations

**9. "Payment Execution Agent" - MVP Implementation (FastAPI Module)**

This is **not** an LLM/LangGraph agent for the MVP. It's a well-structured Python module within the FastAPI backend.

*   **Input:** `PaymentOrder` ID or details.
*   **Logic:**
    1.  Load `PaymentOrder` and associated `PaymentLink`, `Organization`, and `ProviderCredential`.
    2.  Implement a state machine for the `PaymentOrder` status.
    3.  **For Colombia -> Mexico (Yoint for collection, Trubit for payout/receipt in MXN):**
        *   Call Yoint API to initiate collection in COP. Log interaction.
        *   On Yoint success confirmation (webhook or polling):
            *   Call Trubit API to facilitate the MXN leg (this might involve Trubit receiving funds from Yoint's network or a partner, then paying out in MXN, or Trubit collecting in MXN via Prometeo Open Banking). The exact mechanism depends on Yoint & Trubit capabilities and partnership.
            *   Log Trubit interaction.
        *   Update `PaymentOrder` status to `SUCCEEDED` upon final confirmation.
    4.  **For Mexico -> Colombia (Trubit/Prometeo for collection, Yoint for payout in COP):**
        *   Call Trubit/Prometeo API to initiate collection in MXN. Log interaction.
        *   On Trubit/Prometeo success confirmation:
            *   Call Yoint API to facilitate payout in COP.
            *   Log Yoint interaction.
        *   Update `PaymentOrder` status to `SUCCEEDED`.
    5.  Emit events to Kafka at each significant state change or provider interaction.
    6.  Handle API errors from providers gracefully with retries for transient issues.
    7.  If unrecoverable errors or complex exceptions occur, set `PaymentOrder` status to `REQUIRES_MANUAL_INTERVENTION` and create `ManualProcessStep` entries.

**10. Future Agentic Computing Path**

*   **`apps/agents-service` (LangGraph):** [13, 14, 15, 16, 17]
    *   Post-MVP, the logic within the FastAPI "Payment Execution Agent" module can be gradually migrated or augmented by true LangGraph agents.
    *   These agents could handle more complex routing (if more PSPs are added), dynamic fee analysis, nuanced fraud detection (as a secondary check), or automated reconciliation tasks.
    *   Example: A `ProviderSelectionAgent` (LangGraph) could choose between Yoint, Trubit, or other future PSPs based on real-time conditions, cost, and success rates, potentially using LLM reasoning capabilities. [18, 19, 20, 21, 22]
*   **`apps/workers-service`:**
    *   This service will act as an API gateway or event consumer that triggers the LangGraph agents in `agents-service`. It will listen to events from the managed Kafka stream (e.g., `PaymentOrderInitiated`) and invoke the appropriate agent.
*   **CopilotKit CoAgents (Next.js Frontend):** [3, 4, 5, 2]
    *   The Next.js dashboard can use CopilotKit's CoAgent features to provide an AI-powered interface for B2B clients.
    *   For example, a client could ask, "What's the status of my payment link to XYZ Corp?" or "Suggest the best way to collect $500 from a client in Brazil."
    *   These CoAgents in the frontend would communicate (likely via the Next.js API routes and then to the `workers-service`) with the backend LangGraph agents to get information or trigger actions.

**11. Development Standards & Best Practices**

*   **General:** Adherence to the specified guidelines (Airbnb style, English, named exports, TS, JSDoc, short functions, immutability, RO-RO, naming conventions) will be enforced via linters (ESLint, Flake8/Black/MyPy), Prettier, and code reviews.
*   **Next.js:** Correct use of Server Components (`async/await` for data fetching) and Client Components (`"use client"` for interactivity). React Context for simple global state, TanStack Query for server state.
*   **FastAPI:** Pydantic for request/response validation and serialization. Dependency Injection for services. Async/await for all I/O.
*   **Prisma:** Used in `packages/prisma` for schema definition and migrations. The Next.js app (via its API routes or server components) will use the generated Prisma Client (JS/TS). The FastAPI backend will interact with Neon DB using `asyncpg` or a Python ORM that can work with the Prisma-defined schema.
*   **UI:** Tailwind CSS for utility-first styling. Shadcn UI for pre-built, customizable components. MagicUI for specific animated/interactive elements. Focus on responsiveness (mobile-first) and accessibility (WCAG AA).
*   **Forms:** React Hook Form for structure and state, Zod for schema-based validation on both frontend and backend (via Pydantic in FastAPI, which can be inspired by Zod schemas).
*   **Data Handling:** Composite types (Pydantic models in backend, TS interfaces/types in frontend and `packages/types`). Prisma schema defines the canonical data structures.

**12. Deployment Strategy**

*   **`apps/frontend` (Next.js):** Vercel (native integration, CI/CD, global CDN).
*   **`apps/backend` (FastAPI):** Railway (Dockerized deployment, easy scaling, managed services).
*   **`apps/agents-service` (Future LangGraph):** Railway (Dockerized).
*   **`apps/workers-service` (Future):** Railway (Dockerized).
*   **`apps/docs-service` (Scalar Docs):** Can be deployed via Vercel (if static export) or Railway (if needs a small server).
*   **Database:** Neon DB (Serverless PostgreSQL, integrates well with Vercel and serverless functions).
*   **Event Bus:** Redpanda Cloud (or similar managed Kafka).
*   **Authentication:** Clerk Auth (integrates with Next.js and automatically creates wallets for users).

This blueprint provides a solid, pragmatic starting point for Wedi's MVP, focusing on delivering core value quickly while establishing a scalable and evolvable architecture that aligns with the long-term vision of agentic computing. The emphasis on managed services and a modular monolith for the backend aims to keep the operational burden manageable for a 2-person team.