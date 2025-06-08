"""User model with authentication support."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel

if TYPE_CHECKING:
    from .audit_log import AuditLog
    from .organization_user import OrganizationUser
    from .payment_link import PaymentLink
    from .wallet import Wallet


class AuthProvider(str, PyEnum):
    """Authentication provider enum."""
    
    EMAIL = "EMAIL"
    GOOGLE = "GOOGLE"
    THIRDWEB = "THIRDWEB"
    WALLET_CONNECT = "WALLET_CONNECT"


class User(Base, BaseModel):
    """User model with multi-provider authentication."""
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_provider_id", name="_auth_provider_uc"),
    )

    id: Mapped[str] = mapped_column(String(30), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Authentication
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider),
        default=AuthProvider.EMAIL,
        nullable=False
    )
    auth_provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Web3
    primary_wallet_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("wallets.id", use_alter=True),
        nullable=True
    )
    
    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    primary_wallet: Mapped[Optional["Wallet"]] = relationship(
        "Wallet",
        foreign_keys=[primary_wallet_id],
        post_update=True
    )
    organizations: Mapped[list["OrganizationUser"]] = relationship(
        "OrganizationUser",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    owned_wallets: Mapped[list["Wallet"]] = relationship(
        "Wallet",
        back_populates="user",
        foreign_keys="Wallet.user_id",
        cascade="all, delete-orphan"
    )
    payment_links: Mapped[list["PaymentLink"]] = relationship(
        "PaymentLink",
        back_populates="created_by",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    ) 