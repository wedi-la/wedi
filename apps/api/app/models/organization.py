"""Organization model for multi-tenancy."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .audit_log import AuditLog
    from .organization_user import OrganizationUser
    from .payment_link import PaymentLink
    from .payment_order import PaymentOrder
    from .provider_config import ProviderConfig
    from .wallet import Wallet
    from .webhook import Webhook


class ComplianceStatus(str, PyEnum):
    """Compliance status enum."""
    
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class Organization(Base, BaseModel):
    """Organization model for multi-tenant platform."""
    
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(30), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Billing & Compliance
    billing_email: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    compliance_status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus),
        default=ComplianceStatus.PENDING,
        nullable=False
    )
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Foreign Keys
    owner_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    
    # Relationships
    users: Mapped[list["OrganizationUser"]] = relationship(
        "OrganizationUser",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    wallets: Mapped[list["Wallet"]] = relationship(
        "Wallet",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    payment_links: Mapped[list["PaymentLink"]] = relationship(
        "PaymentLink",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    payment_orders: Mapped[list["PaymentOrder"]] = relationship(
        "PaymentOrder",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    provider_configs: Mapped[list["ProviderConfig"]] = relationship(
        "ProviderConfig",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan"
    ) 