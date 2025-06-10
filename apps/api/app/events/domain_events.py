"""
Domain event definitions for all aggregates.

This module contains concrete event classes for different domain entities.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import Field

from app.events.publisher import DomainEvent
from app.models.generated import (
    AgentType,
    AuthProvider,
    BlockchainTxStatus,
    KycStatus,
    PaymentLinkStatus,
    PaymentOrderStatus,
    UserRole,
    WalletType,
)


# User Events
class UserCreatedEvent(DomainEvent):
    """Event emitted when a new user is created."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        auth_provider: AuthProvider,
        **kwargs
    ):
        """Initialize user created event."""
        super().__init__(
            event_type="user.created",
            aggregate_id=user_id,
            aggregate_type="user",
            data={
                "email": email,
                "auth_provider": auth_provider.value,
            },
            **kwargs
        )


class UserVerifiedEvent(DomainEvent):
    """Event emitted when a user's email is verified."""
    
    def __init__(self, user_id: str, email: str, **kwargs):
        """Initialize user verified event."""
        super().__init__(
            event_type="user.verified",
            aggregate_id=user_id,
            aggregate_type="user",
            data={"email": email},
            **kwargs
        )


class UserWalletLinkedEvent(DomainEvent):
    """Event emitted when a wallet is linked to a user."""
    
    def __init__(
        self,
        user_id: str,
        wallet_id: str,
        wallet_address: str,
        **kwargs
    ):
        """Initialize wallet linked event."""
        super().__init__(
            event_type="user.wallet_linked",
            aggregate_id=user_id,
            aggregate_type="user",
            data={
                "wallet_id": wallet_id,
                "wallet_address": wallet_address,
            },
            **kwargs
        )


# Organization Events
class OrganizationCreatedEvent(DomainEvent):
    """Event emitted when a new organization is created."""
    
    def __init__(
        self,
        organization_id: str,
        name: str,
        slug: str,
        owner_id: str,
        **kwargs
    ):
        """Initialize organization created event."""
        super().__init__(
            event_type="organization.created",
            aggregate_id=organization_id,
            aggregate_type="organization",
            data={
                "name": name,
                "slug": slug,
                "owner_id": owner_id,
            },
            **kwargs
        )


class MemberAddedEvent(DomainEvent):
    """Event emitted when a member is added to an organization."""
    
    def __init__(
        self,
        organization_id: str,
        user_id: str,
        role: UserRole,
        invited_by: str,
        **kwargs
    ):
        """Initialize member added event."""
        super().__init__(
            event_type="organization.member_added",
            aggregate_id=organization_id,
            aggregate_type="organization",
            data={
                "user_id": user_id,
                "role": role.value,
                "invited_by": invited_by,
            },
            **kwargs
        )


class MemberRemovedEvent(DomainEvent):
    """Event emitted when a member is removed from an organization."""
    
    def __init__(
        self,
        organization_id: str,
        user_id: str,
        removed_by: str,
        **kwargs
    ):
        """Initialize member removed event."""
        super().__init__(
            event_type="organization.member_removed",
            aggregate_id=organization_id,
            aggregate_type="organization",
            data={
                "user_id": user_id,
                "removed_by": removed_by,
            },
            **kwargs
        )


# Payment Link Events
class PaymentLinkCreatedEvent(DomainEvent):
    """Event emitted when a payment link is created."""
    
    def __init__(
        self,
        payment_link_id: str,
        organization_id: str,
        amount: Decimal,
        currency: str,
        short_code: str,
        **kwargs
    ):
        """Initialize payment link created event."""
        super().__init__(
            event_type="payment_link.created",
            aggregate_id=payment_link_id,
            aggregate_type="payment_link",
            data={
                "organization_id": organization_id,
                "amount": str(amount),
                "currency": currency,
                "short_code": short_code,
            },
            **kwargs
        )


class PaymentLinkActivatedEvent(DomainEvent):
    """Event emitted when a payment link is activated."""
    
    def __init__(
        self,
        payment_link_id: str,
        activated_by: str,
        **kwargs
    ):
        """Initialize payment link activated event."""
        super().__init__(
            event_type="payment_link.activated",
            aggregate_id=payment_link_id,
            aggregate_type="payment_link",
            data={"activated_by": activated_by},
            **kwargs
        )


class PaymentLinkExpiredEvent(DomainEvent):
    """Event emitted when a payment link expires."""
    
    def __init__(self, payment_link_id: str, **kwargs):
        """Initialize payment link expired event."""
        super().__init__(
            event_type="payment_link.expired",
            aggregate_id=payment_link_id,
            aggregate_type="payment_link",
            data={},
            **kwargs
        )


class PaymentLinkUpdatedEvent(DomainEvent):
    """Event emitted when a payment link is updated."""
    
    def __init__(
        self,
        payment_link_id: str,
        organization_id: str,
        updated_by: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        **kwargs
    ):
        """Initialize payment link updated event."""
        data = {
            "organization_id": organization_id,
            "updated_by": updated_by,
        }
        if old_status and new_status:
            data["old_status"] = old_status
            data["new_status"] = new_status
        
        super().__init__(
            event_type="payment_link.updated",
            aggregate_id=payment_link_id,
            aggregate_type="payment_link",
            data=data,
            **kwargs
        )


class PaymentLinkArchivedEvent(DomainEvent):
    """Event emitted when a payment link is archived."""
    
    def __init__(
        self,
        payment_link_id: str,
        organization_id: str,
        archived_by: str,
        **kwargs
    ):
        """Initialize payment link archived event."""
        super().__init__(
            event_type="payment_link.archived",
            aggregate_id=payment_link_id,
            aggregate_type="payment_link",
            data={
                "organization_id": organization_id,
                "archived_by": archived_by,
            },
            **kwargs
        )


# Payment Order Events
class PaymentOrderCreatedEvent(DomainEvent):
    """Event emitted when a payment order is created."""
    
    def __init__(
        self,
        payment_order_id: str,
        order_number: str,
        payment_link_id: str,
        customer_email: str,
        requested_amount: Decimal,
        requested_currency: str,
        **kwargs
    ):
        """Initialize payment order created event."""
        super().__init__(
            event_type="payment_order.created",
            aggregate_id=payment_order_id,
            aggregate_type="payment_order",
            data={
                "order_number": order_number,
                "payment_link_id": payment_link_id,
                "customer_email": customer_email,
                "requested_amount": str(requested_amount),
                "requested_currency": requested_currency,
            },
            **kwargs
        )


class PaymentOrderProcessingEvent(DomainEvent):
    """Event emitted when payment processing starts."""
    
    def __init__(
        self,
        payment_order_id: str,
        agent_id: str,
        provider_name: str,
        **kwargs
    ):
        """Initialize payment processing event."""
        super().__init__(
            event_type="payment_order.processing",
            aggregate_id=payment_order_id,
            aggregate_type="payment_order",
            data={
                "agent_id": agent_id,
                "provider_name": provider_name,
            },
            **kwargs
        )


class PaymentOrderCompletedEvent(DomainEvent):
    """Event emitted when a payment order is completed."""
    
    def __init__(
        self,
        payment_order_id: str,
        settled_amount: Decimal,
        settled_currency: str,
        total_fee: Decimal,
        provider_transaction_id: str,
        **kwargs
    ):
        """Initialize payment completed event."""
        super().__init__(
            event_type="payment_order.completed",
            aggregate_id=payment_order_id,
            aggregate_type="payment_order",
            data={
                "settled_amount": str(settled_amount),
                "settled_currency": settled_currency,
                "total_fee": str(total_fee),
                "provider_transaction_id": provider_transaction_id,
            },
            **kwargs
        )


class PaymentOrderFailedEvent(DomainEvent):
    """Event emitted when a payment order fails."""
    
    def __init__(
        self,
        payment_order_id: str,
        failure_reason: str,
        failure_code: Optional[str] = None,
        can_retry: bool = True,
        **kwargs
    ):
        """Initialize payment failed event."""
        super().__init__(
            event_type="payment_order.failed",
            aggregate_id=payment_order_id,
            aggregate_type="payment_order",
            data={
                "failure_reason": failure_reason,
                "failure_code": failure_code,
                "can_retry": can_retry,
            },
            **kwargs
        )


class PaymentOrderRefundedEvent(DomainEvent):
    """Event emitted when a payment order is refunded."""
    
    def __init__(
        self,
        payment_order_id: str,
        refund_amount: Decimal,
        refund_currency: str,
        refund_reason: str,
        refunded_by: str,
        **kwargs
    ):
        """Initialize payment refunded event."""
        super().__init__(
            event_type="payment_order.refunded",
            aggregate_id=payment_order_id,
            aggregate_type="payment_order",
            data={
                "refund_amount": str(refund_amount),
                "refund_currency": refund_currency,
                "refund_reason": refund_reason,
                "refunded_by": refunded_by,
            },
            **kwargs
        )


# Agent Events
class AgentCreatedEvent(DomainEvent):
    """Event emitted when an agent is created."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        capabilities: list[str],
        **kwargs
    ):
        """Initialize agent created event."""
        super().__init__(
            event_type="agent.created",
            aggregate_id=agent_id,
            aggregate_type="agent",
            data={
                "name": name,
                "agent_type": agent_type.value,
                "capabilities": capabilities,
            },
            **kwargs
        )


class AgentPerformanceRecordedEvent(DomainEvent):
    """Event emitted when agent performance is recorded."""
    
    def __init__(
        self,
        agent_id: str,
        success_count: int,
        failure_count: int,
        avg_response_time_ms: float,
        period_start: datetime,
        period_end: datetime,
        **kwargs
    ):
        """Initialize agent performance event."""
        super().__init__(
            event_type="agent.performance_recorded",
            aggregate_id=agent_id,
            aggregate_type="agent",
            data={
                "success_count": success_count,
                "failure_count": failure_count,
                "avg_response_time_ms": avg_response_time_ms,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
            **kwargs
        )


# Wallet Events
class WalletCreatedEvent(DomainEvent):
    """Event emitted when a wallet is created."""
    
    def __init__(
        self,
        wallet_id: str,
        wallet_type: WalletType,
        address: str,
        chain_id: int,
        owner_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize wallet created event."""
        super().__init__(
            event_type="wallet.created",
            aggregate_id=wallet_id,
            aggregate_type="wallet",
            data={
                "wallet_type": wallet_type.value,
                "address": address,
                "chain_id": chain_id,
                "owner_id": owner_id,
            },
            **kwargs
        )


class WalletTransactionEvent(DomainEvent):
    """Event emitted when a blockchain transaction is made."""
    
    def __init__(
        self,
        wallet_id: str,
        transaction_hash: str,
        amount: Decimal,
        currency: str,
        direction: str,  # "incoming" or "outgoing"
        status: BlockchainTxStatus,
        **kwargs
    ):
        """Initialize wallet transaction event."""
        super().__init__(
            event_type="wallet.transaction",
            aggregate_id=wallet_id,
            aggregate_type="wallet",
            data={
                "transaction_hash": transaction_hash,
                "amount": str(amount),
                "currency": currency,
                "direction": direction,
                "status": status.value,
            },
            **kwargs
        )


# Customer Events
class CustomerCreatedEvent(DomainEvent):
    """Event emitted when a customer is created."""
    
    def __init__(
        self,
        customer_id: str,
        organization_id: str,
        email: str,
        country: str,
        **kwargs
    ):
        """Initialize customer created event."""
        super().__init__(
            event_type="customer.created",
            aggregate_id=customer_id,
            aggregate_type="customer",
            data={
                "organization_id": organization_id,
                "email": email,
                "country": country,
            },
            **kwargs
        )


class CustomerKycUpdatedEvent(DomainEvent):
    """Event emitted when customer KYC status is updated."""
    
    def __init__(
        self,
        customer_id: str,
        kyc_status: KycStatus,
        kyc_provider: Optional[str] = None,
        **kwargs
    ):
        """Initialize customer KYC updated event."""
        super().__init__(
            event_type="customer.kyc_updated",
            aggregate_id=customer_id,
            aggregate_type="customer",
            data={
                "kyc_status": kyc_status.value,
                "kyc_provider": kyc_provider,
            },
            **kwargs
        )


# Product Events
class ProductCreatedEvent(DomainEvent):
    """Event emitted when a product is created."""
    
    def __init__(
        self,
        product_id: str,
        organization_id: str,
        name: str,
        sku: str,
        **kwargs
    ):
        """Initialize product created event."""
        super().__init__(
            event_type="product.created",
            aggregate_id=product_id,
            aggregate_type="product",
            data={
                "organization_id": organization_id,
                "name": name,
                "sku": sku,
            },
            **kwargs
        )


class ProductPriceUpdatedEvent(DomainEvent):
    """Event emitted when product price is updated."""
    
    def __init__(
        self,
        product_id: str,
        price_id: str,
        amount: Decimal,
        currency: str,
        **kwargs
    ):
        """Initialize product price updated event."""
        super().__init__(
            event_type="product.price_updated",
            aggregate_id=product_id,
            aggregate_type="product",
            data={
                "price_id": price_id,
                "amount": str(amount),
                "currency": currency,
            },
            **kwargs
        ) 