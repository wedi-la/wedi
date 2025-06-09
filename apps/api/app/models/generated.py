"""
SQLAlchemy models generated from Prisma schema
Generated at: 2025-06-08T20:30:46.989257
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class AgentType(enum.Enum):
    """Generated from Prisma enum AgentType"""
    PAYMENT_ORCHESTRATOR = "PAYMENT_ORCHESTRATOR"
    RISK_ANALYZER = "RISK_ANALYZER"
    ROUTE_OPTIMIZER = "ROUTE_OPTIMIZER"
    FRAUD_DETECTOR = "FRAUD_DETECTOR"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    RECONCILIATION = "RECONCILIATION"

class AuthProvider(enum.Enum):
    """Generated from Prisma enum AuthProvider"""
    EMAIL = "EMAIL"
    GOOGLE = "GOOGLE"
    THIRDWEB = "THIRDWEB"
    WALLET_CONNECT = "WALLET_CONNECT"

class BillingInterval(enum.Enum):
    """Generated from Prisma enum BillingInterval"""
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"

class BlockchainTxStatus(enum.Enum):
    """Generated from Prisma enum BlockchainTxStatus"""
    PENDING = "PENDING"
    MINED = "MINED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    DROPPED = "DROPPED"

class ComplianceStatus(enum.Enum):
    """Generated from Prisma enum ComplianceStatus"""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class Environment(enum.Enum):
    """Generated from Prisma enum Environment"""
    PRODUCTION = "PRODUCTION"
    SANDBOX = "SANDBOX"
    TEST = "TEST"

class InteractionType(enum.Enum):
    """Generated from Prisma enum InteractionType"""
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    INFORMATION_REQUEST = "INFORMATION_REQUEST"
    OVERRIDE = "OVERRIDE"
    FEEDBACK = "FEEDBACK"

class KycStatus(enum.Enum):
    """Generated from Prisma enum KycStatus"""
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ManualStepStatus(enum.Enum):
    """Generated from Prisma enum ManualStepStatus"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ManualStepType(enum.Enum):
    """Generated from Prisma enum ManualStepType"""
    KYC_REVIEW = "KYC_REVIEW"
    FRAUD_REVIEW = "FRAUD_REVIEW"
    EXCEPTION_HANDLING = "EXCEPTION_HANDLING"
    RECONCILIATION = "RECONCILIATION"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"

class PaymentLinkStatus(enum.Enum):
    """Generated from Prisma enum PaymentLinkStatus"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"

class PaymentMethodType(enum.Enum):
    """Generated from Prisma enum PaymentMethodType"""
    CARD = "CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    WALLET = "WALLET"
    CASH = "CASH"

class PaymentOrderStatus(enum.Enum):
    """Generated from Prisma enum PaymentOrderStatus"""
    CREATED = "CREATED"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PROCESSING = "PROCESSING"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"

class PriceType(enum.Enum):
    """Generated from Prisma enum PriceType"""
    ONE_TIME = "ONE_TIME"
    RECURRING = "RECURRING"

class Priority(enum.Enum):
    """Generated from Prisma enum Priority"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ProductType(enum.Enum):
    """Generated from Prisma enum ProductType"""
    SERVICE = "SERVICE"
    GOOD = "GOOD"
    SUBSCRIPTION = "SUBSCRIPTION"

class ProviderHealth(enum.Enum):
    """Generated from Prisma enum ProviderHealth"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    MAINTENANCE = "MAINTENANCE"

class ProviderTxType(enum.Enum):
    """Generated from Prisma enum ProviderTxType"""
    PAYMENT_INITIATION = "PAYMENT_INITIATION"
    STATUS_CHECK = "STATUS_CHECK"
    REFUND = "REFUND"
    WEBHOOK_CALLBACK = "WEBHOOK_CALLBACK"
    BALANCE_CHECK = "BALANCE_CHECK"
    EXCHANGE_RATE = "EXCHANGE_RATE"

class ProviderType(enum.Enum):
    """Generated from Prisma enum ProviderType"""
    BANKING_RAILS = "BANKING_RAILS"
    CARD_PROCESSOR = "CARD_PROCESSOR"
    CRYPTO_ONRAMP = "CRYPTO_ONRAMP"
    CRYPTO_OFFRAMP = "CRYPTO_OFFRAMP"
    OPEN_BANKING = "OPEN_BANKING"
    WALLET = "WALLET"

class SubscriptionStatus(enum.Enum):
    """Generated from Prisma enum SubscriptionStatus"""
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    UNPAID = "UNPAID"
    TRIALING = "TRIALING"

class UserRole(enum.Enum):
    """Generated from Prisma enum UserRole"""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    FINANCE = "FINANCE"
    SUPPORT = "SUPPORT"
    VIEWER = "VIEWER"

class WalletType(enum.Enum):
    """Generated from Prisma enum WalletType"""
    EOA = "EOA"
    SMART_WALLET = "SMART_WALLET"
    MULTI_SIG = "MULTI_SIG"

class Agent(Base):
    """Generated from Prisma model Agent"""
    __tablename__ = "agent"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    agent_wallet_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    agent_wallet: Mapped[Optional[str]] = mapped_column(String, ForeignKey("wallet.id"), nullable=True)
    graph_definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    tools: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    supported_providers: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    supported_chains: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=False)
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    total_executions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_execution_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # paymentLinks: Mapped["PaymentLink"] = relationship(back_populates="executingAgent")
    # decisions: Mapped["AgentDecision"] = relationship(back_populates="agent")
    # checkpoints: Mapped["AgentCheckpoint"] = relationship(back_populates="agent")

class AgentCheckpoint(Base):
    """Generated from Prisma model AgentCheckpoint"""
    __tablename__ = "agent_checkpoint"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String, ForeignKey("agent.id"), nullable=False)
    thread_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    checkpoint_id: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("idx_agentcheckpoint_agentId_threadId", "agent_id", "thread_id"),
        UniqueConstraint("agent_id", "thread_id", "checkpoint_id")
    )

class AgentDecision(Base):
    """Generated from Prisma model AgentDecision"""
    __tablename__ = "agent_decision"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String, ForeignKey("agent.id"), nullable=False)
    payment_order_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    payment_order: Mapped[Optional[str]] = mapped_column(String, ForeignKey("payment_order.id"), nullable=True)
    decision_type: Mapped[str] = mapped_column(String, nullable=False)
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    reasoning: Mapped[dict] = mapped_column(JSON, nullable=False)
    decision: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    execution_time: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    was_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    overridden_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    # interactions: Mapped["AgentInteraction"] = relationship(back_populates="agentDecision")

class AgentInteraction(Base):
    """Generated from Prisma model AgentInteraction"""
    __tablename__ = "agent_interaction"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    agent_decision_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    agent_decision: Mapped[str] = mapped_column(String, ForeignKey("agent_decision.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user: Mapped[str] = mapped_column(String, ForeignKey("user.id"), nullable=False)
    type: Mapped[InteractionType] = mapped_column(Enum(InteractionType), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

class ApiKey(Base):
    """Generated from Prisma model ApiKey"""
    __tablename__ = "api_key"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class AuditLog(Base):
    """Generated from Prisma model AuditLog"""
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    user: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)

    __table_args__ = (
        Index("idx_auditlog_organizationId_createdAt", "organization_id", "created_at"),
        Index("idx_auditlog_entityType_entityId", "entity_type", "entity_id")
    )

class BlockchainTransaction(Base):
    """Generated from Prisma model BlockchainTransaction"""
    __tablename__ = "blockchain_transaction"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    hash: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_address: Mapped[str] = mapped_column(String, nullable=False)
    to_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gas_limit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gas_price: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nonce: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[BlockchainTxStatus] = mapped_column(Enum(BlockchainTxStatus), nullable=False, default="PENDING")
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sponsorship_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gas_sponsorship: Mapped[Optional[str]] = mapped_column(String, ForeignKey("gas_sponsorship.id"), nullable=True)
    wallet_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    wallet: Mapped[str] = mapped_column(String, ForeignKey("wallet.id"), nullable=False)
    payment_order_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    payment_order: Mapped[Optional[str]] = mapped_column(String, ForeignKey("payment_order.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    mined_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class Customer(Base):
    """Generated from Prisma model Customer"""
    __tablename__ = "customer"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    billing_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class CustomerPaymentMethod(Base):
    """Generated from Prisma model CustomerPaymentMethod"""
    __tablename__ = "customer_payment_method"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    customer: Mapped[str] = mapped_column(String, ForeignKey("customer.id"), nullable=False)
    type: Mapped[PaymentMethodType] = mapped_column(Enum(PaymentMethodType), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last4: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expiry_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expiry_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    account_last4: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wallet_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chain_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class GasSponsorship(Base):
    """Generated from Prisma model GasSponsorship"""
    __tablename__ = "gas_sponsorship"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    sponsor_wallet_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    sponsor_wallet: Mapped[str] = mapped_column(String, ForeignKey("wallet.id"), nullable=False)
    max_gas_amount: Mapped[str] = mapped_column(String, nullable=False)
    used_gas_amount: Mapped[str] = mapped_column(String, nullable=False, default="0")
    max_transactions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # transactions: Mapped["BlockchainTransaction"] = relationship(back_populates="gasSponsorship")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class ManualProcessStep(Base):
    """Generated from Prisma model ManualProcessStep"""
    __tablename__ = "manual_process_step"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    payment_order_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payment_order: Mapped[str] = mapped_column(String, ForeignKey("payment_order.id"), nullable=False)
    type: Mapped[ManualStepType] = mapped_column(Enum(ManualStepType), nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_team: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), nullable=False, default="MEDIUM", index=True)
    status: Mapped[ManualStepStatus] = mapped_column(Enum(ManualStepStatus), nullable=False, default="PENDING", index=True)
    resolution: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_manualprocessstep_status_priority", "status", "priority"),
    )

class Organization(Base):
    """Generated from Prisma model Organization"""
    __tablename__ = "organization"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    billing_email: Mapped[str] = mapped_column(String, nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False)
    compliance_status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus), nullable=False, default="PENDING")
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False)

class OrganizationUser(Base):
    """Generated from Prisma model OrganizationUser"""
    __tablename__ = "organization_user"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user: Mapped[str] = mapped_column(String, ForeignKey("user.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    permissions: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    invited_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    invited_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id"),
    )

class PaymentEvent(Base):
    """Generated from Prisma model PaymentEvent"""
    __tablename__ = "payment_event"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    payment_order_id: Mapped[str] = mapped_column(String, nullable=False)
    payment_order: Mapped[str] = mapped_column(String, ForeignKey("payment_order.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_version: Mapped[str] = mapped_column(String, nullable=False, default="1.0")
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    kafka_topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    kafka_partition: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kafka_offset: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)

    __table_args__ = (
        UniqueConstraint("payment_order_id", "sequence_number"),
    )

class PaymentLink(Base):
    """Generated from Prisma model PaymentLink"""
    __tablename__ = "payment_link"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    created_by_id: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("user.id"), nullable=False)
    executing_agent_id: Mapped[str] = mapped_column(String, nullable=False)
    executing_agent: Mapped[str] = mapped_column(String, ForeignKey("agent.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    short_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    qr_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[Optional[str]] = mapped_column(String, ForeignKey("price.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    target_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    target_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    smart_contract_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    smart_contract_chain_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[PaymentLinkStatus] = mapped_column(Enum(PaymentLinkStatus), nullable=False, default="ACTIVE")
    allow_multiple_payments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_kyc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    redirect_urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class PaymentOrder(Base):
    """Generated from Prisma model PaymentOrder"""
    __tablename__ = "payment_order"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    payment_link_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payment_link: Mapped[str] = mapped_column(String, ForeignKey("payment_link.id"), nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    customer: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customer.id"), nullable=True)
    order_number: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    status: Mapped[PaymentOrderStatus] = mapped_column(Enum(PaymentOrderStatus), nullable=False, default="CREATED", index=True)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    requested_currency: Mapped[str] = mapped_column(String, nullable=False)
    settled_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    settled_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    exchange_rate_locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    exchange_rate_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    provider_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    network_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    total_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    customer_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_wallet: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_ip: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    kyc_status: Mapped[KycStatus] = mapped_column(Enum(KycStatus), nullable=False, default="NOT_REQUIRED")
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    selected_route: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # providerTransactions: Mapped["ProviderTransaction"] = relationship(back_populates="paymentOrder")
    # blockchainTxs: Mapped["BlockchainTransaction"] = relationship(back_populates="paymentOrder")
    # events: Mapped["PaymentEvent"] = relationship(back_populates="paymentOrder")
    # agentDecisions: Mapped["AgentDecision"] = relationship(back_populates="paymentOrder")
    # manualSteps: Mapped["ManualProcessStep"] = relationship(back_populates="paymentOrder")

    __table_args__ = (
        Index("idx_paymentorder_organizationId_status", "organization_id", "status"),
    )

class Price(Base):
    """Generated from Prisma model Price"""
    __tablename__ = "price"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    product: Mapped[str] = mapped_column(String, ForeignKey("product.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False, default="ONE_TIME")
    interval: Mapped[Optional[BillingInterval]] = mapped_column(Enum(BillingInterval), nullable=True)
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trial_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # subscriptionItems: Mapped["SubscriptionItem"] = relationship(back_populates="price")
    # paymentLinks: Mapped["PaymentLink"] = relationship(back_populates="price")

class Product(Base):
    """Generated from Prisma model Product"""
    __tablename__ = "product"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[ProductType] = mapped_column(Enum(ProductType), nullable=False, default="SERVICE")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    images: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # prices: Mapped["Price"] = relationship(back_populates="product")

class Provider(Base):
    """Generated from Prisma model Provider"""
    __tablename__ = "provider"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ProviderType] = mapped_column(Enum(ProviderType), nullable=False)
    supported_countries: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    supported_currencies: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    payment_methods: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)

class ProviderConfig(Base):
    """Generated from Prisma model ProviderConfig"""
    __tablename__ = "provider_config"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, ForeignKey("provider.id"), nullable=False)
    environment: Mapped[Environment] = mapped_column(Enum(Environment), nullable=False, default="PRODUCTION")
    credentials: Mapped[dict] = mapped_column(JSON, nullable=False)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False)

class ProviderRoute(Base):
    """Generated from Prisma model ProviderRoute"""
    __tablename__ = "provider_route"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, ForeignKey("provider.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    from_country: Mapped[str] = mapped_column(String, nullable=False, index=True)
    to_country: Mapped[str] = mapped_column(String, nullable=False, index=True)
    from_currency: Mapped[str] = mapped_column(String, nullable=False)
    to_currency: Mapped[str] = mapped_column(String, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    fixed_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    percentage_fee: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    max_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    estimated_time: Mapped[int] = mapped_column(Integer, nullable=False)
    cutoff_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    working_days: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    __table_args__ = (
        Index("idx_providerroute_fromCountry_toCountry_isActive", "from_country", "to_country", "is_active"),
    )

class ProviderTransaction(Base):
    """Generated from Prisma model ProviderTransaction"""
    __tablename__ = "provider_transaction"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    payment_order_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payment_order: Mapped[str] = mapped_column(String, ForeignKey("payment_order.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, ForeignKey("provider.id"), nullable=False)
    type: Mapped[ProviderTxType] = mapped_column(Enum(ProviderTxType), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    request: Mapped[dict] = mapped_column(JSON, nullable=False)
    response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class Subscription(Base):
    """Generated from Prisma model Subscription"""
    __tablename__ = "subscription"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    customer: Mapped[str] = mapped_column(String, ForeignKey("customer.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), nullable=False, default="ACTIVE", index=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancel_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # items: Mapped["SubscriptionItem"] = relationship(back_populates="subscription")

class SubscriptionItem(Base):
    """Generated from Prisma model SubscriptionItem"""
    __tablename__ = "subscription_item"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    subscription_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subscription: Mapped[str] = mapped_column(String, ForeignKey("subscription.id"), nullable=False)
    price_id: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[str] = mapped_column(String, ForeignKey("price.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class User(Base):
    """Generated from Prisma model User"""
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(Enum(AuthProvider), nullable=False, default="EMAIL")
    auth_provider_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    primary_wallet_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    primary_wallet: Mapped[Optional[str]] = mapped_column(String, ForeignKey("wallet.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # organizations: Mapped["OrganizationUser"] = relationship(back_populates="user")
    # ownedWallets: Mapped["Wallet"] = relationship(back_populates="user")
    # paymentLinks: Mapped["PaymentLink"] = relationship(back_populates="createdBy")
    # auditLogs: Mapped["AuditLog"] = relationship(back_populates="user")
    # agentInteractions: Mapped["AgentInteraction"] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_provider_id"),
    )

class Wallet(Base):
    """Generated from Prisma model Wallet"""
    __tablename__ = "wallet"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    address: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[WalletType] = mapped_column(Enum(WalletType), nullable=False, default="EOA")
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    user: Mapped[Optional[str]] = mapped_column(String, ForeignKey("user.id"), nullable=True)
    organization_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    organization: Mapped[Optional[str]] = mapped_column(String, ForeignKey("organization.id"), nullable=True)
    smart_wallet_factory: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    smart_wallet_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowlist: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blocklist: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # primaryForUsers: Mapped["User"] = relationship(back_populates="primaryWallet")
    # agent: Mapped["Agent"] = relationship(back_populates="agentWallet")
    # transactions: Mapped["BlockchainTransaction"] = relationship(back_populates="wallet")
    # gasSponsorship: Mapped["GasSponsorship"] = relationship(back_populates="sponsorWallet")

    __table_args__ = (
        Index("idx_wallet_address_chainId", "address", "chain_id"),
    )

class Webhook(Base):
    """Generated from Prisma model Webhook"""
    __tablename__ = "webhook"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String, ForeignKey("organization.id"), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    events: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # deliveries: Mapped["WebhookDelivery"] = relationship(back_populates="webhook")

class WebhookDelivery(Base):
    """Generated from Prisma model WebhookDelivery"""
    __tablename__ = "webhook_delivery"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    webhook_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    webhook: Mapped[str] = mapped_column(String, ForeignKey("webhook.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
