"""
SQLAlchemy models for Wedi API

This module exports all database models generated from the Prisma schema.
The models are automatically generated to maintain consistency with the Prisma schema.
"""

# Import all generated models
from .generated import (
    Base,
    # Enums
    AgentType,
    AuthProvider,
    BillingInterval,
    BlockchainTxStatus,
    ComplianceStatus,
    Environment,
    InteractionType,
    KycStatus,
    ManualStepStatus,
    ManualStepType,
    PaymentLinkStatus,
    PaymentMethodType,
    PaymentOrderStatus,
    PriceType,
    Priority,
    ProductType,
    ProviderHealth,
    ProviderTxType,
    ProviderType,
    SubscriptionStatus,
    UserRole,
    WalletType,
    # Models
    Agent,
    AgentCheckpoint,
    AgentDecision,
    AgentInteraction,
    ApiKey,
    AuditLog,
    BlockchainTransaction,
    Customer,
    CustomerPaymentMethod,
    GasSponsorship,
    IntegrationKey,
    ManualProcessStep,
    Organization,
    OrganizationUser,
    PaymentCorridor,
    PaymentEvent,
    PaymentLink,
    PaymentOrder,
    Price,
    Product,
    Provider,
    ProviderConfig,
    ProviderRoute,
    ProviderTransaction,
    Subscription,
    SubscriptionItem,
    User,
    Wallet,
    Webhook,
    WebhookDelivery,
)

__all__ = [
    "Base",
    # Enums
    "AgentType",
    "AuthProvider",
    "BillingInterval",
    "BlockchainTxStatus",
    "ComplianceStatus",
    "Environment",
    "InteractionType",
    "KycStatus",
    "ManualStepStatus",
    "ManualStepType",
    "PaymentLinkStatus",
    "PaymentMethodType",
    "PaymentOrderStatus",
    "PriceType",
    "Priority",
    "ProductType",
    "ProviderHealth",
    "ProviderTxType",
    "ProviderType",
    "SubscriptionStatus",
    "UserRole",
    "WalletType",
    # Models
    "Agent",
    "AgentCheckpoint",
    "AgentDecision",
    "AgentInteraction",
    "ApiKey",
    "AuditLog",
    "BlockchainTransaction",
    "Customer",
    "CustomerPaymentMethod",
    "GasSponsorship",
    "IntegrationKey",
    "ManualProcessStep",
    "Organization",
    "OrganizationUser",
    "PaymentCorridor",
    "PaymentEvent",
    "PaymentLink",
    "PaymentOrder",
    "Price",
    "Product",
    "Provider",
    "ProviderConfig",
    "ProviderRoute",
    "ProviderTransaction",
    "Subscription",
    "SubscriptionItem",
    "User",
    "Wallet",
    "Webhook",
    "WebhookDelivery",
]

# Add custom model extensions here if needed
# For example, you could add methods or properties to models

# Extend Organization model to include owner_id
# This is a workaround until the Prisma to SQLAlchemy converter includes it
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

# Monkey patch the Organization model to add owner_id
if hasattr(Organization, '__table__'):
    if 'owner_id' not in Organization.__table__.columns:
        Organization.owner_id = Column(String, nullable=False)
        # Note: We can't add the foreign key constraint dynamically
        # This would need to be done in a migration 

# Import the model extensions (clerk_id field, etc.)
from .extensions import *