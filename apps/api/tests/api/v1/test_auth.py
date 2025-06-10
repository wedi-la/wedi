"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient

from app.core.security import verify_password
from tests.factories.user_factory import UserFactory


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_siwe_payload(self, client: AsyncClient):
        """Test SIWE payload generation."""
        response = await client.post(
            "/api/v1/auth/payload",
            json={
                "address": "0x1234567890123456789012345678901234567890",
                "chainId": 1,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "payload" in data
        assert "domain" in data["payload"]
        assert "address" in data["payload"]
        assert "statement" in data["payload"]
        assert "nonce" in data["payload"]
        assert "issuedAt" in data["payload"]
        assert "expirationTime" in data["payload"]
    
    @pytest.mark.asyncio
    async def test_login_creates_new_user(self, client: AsyncClient, db_session):
        """Test login creates a new user if not exists."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "payload": {
                    "domain": "testserver",
                    "address": wallet_address,
                    "statement": "Sign in to Wedi Pay",
                    "nonce": "test-nonce",
                    "issuedAt": "2024-01-01T00:00:00Z",
                    "expirationTime": "2024-01-02T00:00:00Z",
                },
                "signature": "test-signature",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["wallet_address"] == wallet_address
    
    @pytest.mark.asyncio
    async def test_login_existing_user(self, client: AsyncClient, db_session):
        """Test login with existing user."""
        # Create user with wallet
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "payload": {
                    "domain": "testserver",
                    "address": wallet.address,
                    "statement": "Sign in to Wedi Pay",
                    "nonce": "test-nonce",
                    "issuedAt": "2024-01-01T00:00:00Z",
                    "expirationTime": "2024-01-02T00:00:00Z",
                },
                "signature": "test-signature",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == user.id
        assert data["user"]["email"] == user.email
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, db_session):
        """Test token refresh."""
        # First login to get tokens
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "payload": {
                    "domain": "testserver",
                    "address": wallet.address,
                    "statement": "Sign in to Wedi Pay",
                    "nonce": "test-nonce",
                    "issuedAt": "2024-01-01T00:00:00Z",
                    "expirationTime": "2024-01-02T00:00:00Z",
                },
                "signature": "test-signature",
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, db_session):
        """Test getting current user info."""
        from tests.utils.auth import get_auth_headers
        
        # Create user
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert "organizations" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, db_session):
        """Test logout endpoint."""
        from tests.utils.auth import get_auth_headers
        
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient, db_session):
        """Test expired token is rejected."""
        from tests.utils.auth import get_expired_auth_headers
        
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_expired_auth_headers(user)
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401 