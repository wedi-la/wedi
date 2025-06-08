"""
Pydantic schemas for Wallet entity.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class WalletType(str, Enum):
    """Wallet type enumeration."""
    EOA = "EOA"
    SMART_WALLET = "SMART_WALLET"
    MULTI_SIG = "MULTI_SIG"


class ChainInfo(BaseModel):
    """Blockchain chain information."""
    chain_id: int
    name: str
    native_currency: str
    explorer_url: Optional[str] = None
    rpc_url: Optional[str] = None


class WalletBase(BaseModel):
    """Base schema for Wallet."""
    address: str = Field(..., description="Wallet address (Ethereum format)")
    chain_id: int = Field(..., description="Blockchain chain ID")
    type: WalletType = Field(WalletType.EOA, description="Wallet type")
    smart_wallet_factory: Optional[str] = Field(None, description="Factory address for smart wallets")
    smart_wallet_config: Optional[Dict[str, Any]] = Field(None, description="Smart wallet configuration")
    is_active: bool = Field(True, description="Whether wallet is active")
    allowlist: bool = Field(False, description="Whether wallet is on allowlist")
    blocklist: bool = Field(False, description="Whether wallet is on blocklist")
    
    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v.lower()
    
    @field_validator("chain_id")
    @classmethod
    def validate_chain_id(cls, v: int) -> int:
        """Validate chain ID."""
        if v <= 0:
            raise ValueError("Chain ID must be positive")
        return v


class WalletCreate(WalletBase):
    """Schema for creating a Wallet."""
    user_id: Optional[str] = None
    organization_id: Optional[str] = None


class WalletUpdate(BaseModel):
    """Schema for updating a Wallet."""
    smart_wallet_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    allowlist: Optional[bool] = None
    blocklist: Optional[bool] = None


class WalletInDB(WalletBase):
    """Schema for Wallet in database."""
    id: str
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class WalletBalance(BaseModel):
    """Wallet balance information."""
    wallet_id: str
    address: str
    chain_id: int
    native_balance: Decimal = Field(..., description="Native currency balance")
    native_currency: str = Field(..., description="Native currency symbol")
    token_balances: List["TokenBalance"] = Field(default_factory=list)
    total_usd_value: Optional[Decimal] = Field(None, description="Total value in USD")
    last_updated: datetime


class TokenBalance(BaseModel):
    """Token balance information."""
    token_address: str
    symbol: str
    name: Optional[str] = None
    decimals: int
    balance: Decimal
    formatted_balance: str
    usd_value: Optional[Decimal] = None
    price_usd: Optional[Decimal] = None


class WalletTransaction(BaseModel):
    """Simplified wallet transaction for listing."""
    hash: str
    chain_id: int
    from_address: str
    to_address: Optional[str] = None
    value: str
    status: str
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    gas_used: Optional[str] = None
    gas_price: Optional[str] = None
    transaction_fee: Optional[str] = None


class GasEstimate(BaseModel):
    """Gas estimation for transaction."""
    gas_limit: str
    gas_price: str = Field(..., description="Gas price in wei")
    max_fee_per_gas: Optional[str] = Field(None, description="EIP-1559 max fee")
    max_priority_fee_per_gas: Optional[str] = Field(None, description="EIP-1559 priority fee")
    estimated_fee: str = Field(..., description="Total estimated fee in wei")
    estimated_fee_usd: Optional[Decimal] = Field(None, description="Estimated fee in USD")


class TransactionRequest(BaseModel):
    """Request to send a blockchain transaction."""
    to_address: str
    value: str = Field("0", description="Value in wei")
    data: Optional[str] = Field(None, description="Transaction data (hex)")
    gas_limit: Optional[str] = None
    gas_price: Optional[str] = None
    max_fee_per_gas: Optional[str] = None
    max_priority_fee_per_gas: Optional[str] = None
    nonce: Optional[int] = None
    
    @field_validator("to_address")
    @classmethod
    def validate_to_address(cls, v: str) -> str:
        """Validate recipient address."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid recipient address format")
        return v.lower()


class WalletWithRelations(WalletInDB):
    """Wallet with related entities."""
    user: Optional[Dict[str, Any]] = None
    organization: Optional[Dict[str, Any]] = None
    recent_transactions: List[WalletTransaction] = Field(default_factory=list)
    balance: Optional[WalletBalance] = None


class WalletStats(BaseModel):
    """Wallet statistics."""
    wallet_id: str
    total_transactions: int
    total_received: Decimal
    total_sent: Decimal
    unique_interactions: int = Field(..., description="Number of unique addresses interacted with")
    first_transaction: Optional[datetime] = None
    last_transaction: Optional[datetime] = None
    active_chains: List[int] = Field(default_factory=list)


class SmartWalletDeployment(BaseModel):
    """Smart wallet deployment request."""
    factory_address: str
    owner_address: str = Field(..., description="EOA that will own the smart wallet")
    salt: Optional[str] = Field(None, description="Salt for deterministic deployment")
    initialization_data: Optional[str] = Field(None, description="Initialization calldata")
    estimated_deployment_fee: Optional[GasEstimate] = None


class MultiSigConfig(BaseModel):
    """Multi-signature wallet configuration."""
    owners: List[str] = Field(..., min_items=1, description="List of owner addresses")
    required_confirmations: int = Field(..., ge=1, description="Number of required confirmations")
    daily_limit: Optional[str] = Field(None, description="Daily spending limit in wei")
    
    @field_validator("owners")
    @classmethod
    def validate_owners(cls, v: List[str]) -> List[str]:
        """Validate owner addresses."""
        validated = []
        for addr in v:
            if not addr.startswith("0x") or len(addr) != 42:
                raise ValueError(f"Invalid owner address format: {addr}")
            validated.append(addr.lower())
        
        # Check for duplicates
        if len(validated) != len(set(validated)):
            raise ValueError("Duplicate owner addresses not allowed")
        
        return validated
    
    @field_validator("required_confirmations")
    @classmethod
    def validate_confirmations(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate required confirmations."""
        owners = values.get("owners", [])
        if owners and v > len(owners):
            raise ValueError("Required confirmations cannot exceed number of owners")
        return v 