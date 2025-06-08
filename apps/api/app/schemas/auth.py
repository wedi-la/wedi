from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from uuid import UUID


class SIWEPayloadRequest(BaseModel):
    """Request to generate a SIWE payload."""
    address: str = Field(..., description="Ethereum wallet address")
    chain_id: Optional[int] = Field(1, description="Chain ID (default: 1 for mainnet)")


class SIWEPayload(BaseModel):
    """SIWE (Sign-In with Ethereum) payload following EIP-4361."""
    domain: str = Field(..., description="Domain requesting the signature")
    address: str = Field(..., description="Ethereum wallet address")
    statement: str = Field(..., description="Human-readable statement")
    uri: str = Field(..., description="URI of the resource")
    version: str = Field(..., description="Version of the SIWE message")
    chain_id: int = Field(..., description="Chain ID")
    nonce: str = Field(..., description="Random nonce for replay protection")
    issued_at: str = Field(..., description="ISO 8601 datetime when the message was issued")
    expiration_time: str = Field(..., description="ISO 8601 datetime when the message expires")
    message: str = Field(..., description="Full SIWE message to be signed")


class LoginRequest(BaseModel):
    """Login request with signed SIWE message."""
    payload: SIWEPayload = Field(..., description="The SIWE payload that was signed")
    signature: str = Field(..., description="Signature of the SIWE message")


class UserInfo(BaseModel):
    """User information returned after login."""
    id: str
    wallet_address: str
    email: Optional[str] = None
    name: Optional[str] = None
    organizations: List[Dict[str, Any]] = Field(default_factory=list)


class LoginResponse(BaseModel):
    """Response after successful login."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: UserInfo = Field(..., description="User information")


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenRefreshResponse(BaseModel):
    """Response after refreshing tokens."""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class CurrentUserResponse(BaseModel):
    """Current user information."""
    id: str
    wallet_address: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    email_verified: bool = False
    organizations: List[Dict[str, Any]] = Field(default_factory=list) 