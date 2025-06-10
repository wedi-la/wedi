"""
Tests for user management endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models import Role
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.user_factory import UserFactory
from tests.utils.auth import get_auth_headers


class TestUserEndpoints:
    """Test cases for user endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, client: AsyncClient, db_session):
        """Test getting current user profile."""
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        response = await client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["display_name"] == user.display_name
        assert len(data["organizations"]) == 1
        assert data["organizations"][0]["id"] == org.id
    
    @pytest.mark.asyncio
    async def test_update_current_user_profile(self, client: AsyncClient, db_session):
        """Test updating current user profile."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        update_data = {
            "display_name": "Updated Name",
            "metadata": {"bio": "Test bio"},
        }
        
        response = await client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["metadata"]["bio"] == "Test bio"
    
    @pytest.mark.asyncio
    async def test_delete_current_user_with_organizations(self, client: AsyncClient, db_session):
        """Test cannot delete user who owns organizations."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        response = await client.delete("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 400
        assert "owns organizations" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_current_user_success(self, client: AsyncClient, db_session):
        """Test successful user deletion."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.delete("/api/v1/users/me", headers=headers)
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client: AsyncClient, db_session):
        """Test listing users as organization admin."""
        admin, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, admin)
        
        # Add some members
        for i in range(3):
            member, _ = await UserFactory.create_user_with_wallet(
                db_session, 
                email=f"member{i}@example.com"
            )
            await OrganizationFactory.add_member(db_session, org, member)
        
        headers = get_auth_headers(admin)
        headers["X-Organization-ID"] = org.id
        
        response = await client.get("/api/v1/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # admin + 3 members
    
    @pytest.mark.asyncio
    async def test_list_users_as_member_forbidden(self, client: AsyncClient, db_session):
        """Test members cannot list all users."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member, Role.MEMBER)
        
        headers = get_auth_headers(member)
        headers["X-Organization-ID"] = org.id
        
        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_specific_user_as_admin(self, client: AsyncClient, db_session):
        """Test getting specific user as admin."""
        admin, _ = await UserFactory.create_user_with_wallet(db_session)
        other_user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, admin)
        await OrganizationFactory.add_member(db_session, org, other_user)
        
        headers = get_auth_headers(admin)
        headers["X-Organization-ID"] = org.id
        
        response = await client.get(f"/api/v1/users/{other_user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == other_user.id
    
    @pytest.mark.asyncio
    async def test_get_self_without_admin(self, client: AsyncClient, db_session):
        """Test users can get their own profile without admin rights."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.get(f"/api/v1/users/{user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
    
    @pytest.mark.asyncio
    async def test_update_other_user_as_admin(self, client: AsyncClient, db_session):
        """Test admin can update other users."""
        admin, _ = await UserFactory.create_user_with_wallet(db_session)
        other_user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, admin)
        await OrganizationFactory.add_member(db_session, org, other_user)
        
        headers = get_auth_headers(admin)
        headers["X-Organization-ID"] = org.id
        
        response = await client.put(
            f"/api/v1/users/{other_user.id}",
            json={"display_name": "Admin Updated"},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["display_name"] == "Admin Updated"
    
    @pytest.mark.asyncio
    async def test_get_user_organizations(self, client: AsyncClient, db_session):
        """Test getting user's organizations."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org1, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        org2, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        # Another user trying to access
        other_user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(other_user)
        
        response = await client.get(f"/api/v1/users/{user.id}/organizations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        org_ids = [org["id"] for org in data]
        assert org1.id in org_ids
        assert org2.id in org_ids
    
    @pytest.mark.asyncio
    async def test_add_wallet_to_user(self, client: AsyncClient, db_session):
        """Test adding a wallet to user account."""
        user, existing_wallet = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        new_wallet_address = "0x" + "a" * 40
        response = await client.post(
            f"/api/v1/users/{user.id}/wallets",
            json={
                "address": new_wallet_address,
                "chain": "polygon",
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == new_wallet_address
        assert data["chain"] == "polygon"
        assert data["is_primary"] is False
    
    @pytest.mark.asyncio
    async def test_add_duplicate_wallet(self, client: AsyncClient, db_session):
        """Test cannot add duplicate wallet address."""
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.post(
            f"/api/v1/users/{user.id}/wallets",
            json={
                "address": wallet.address,
                "chain": wallet.chain,
            },
            headers=headers
        )
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_add_wallet_to_other_user_forbidden(self, client: AsyncClient, db_session):
        """Test cannot add wallet to other user's account."""
        user1, _ = await UserFactory.create_user_with_wallet(db_session)
        user2, _ = await UserFactory.create_user_with_wallet(db_session)
        
        headers = get_auth_headers(user1)
        response = await client.post(
            f"/api/v1/users/{user2.id}/wallets",
            json={
                "address": "0x" + "b" * 40,
                "chain": "ethereum",
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_remove_wallet(self, client: AsyncClient, db_session):
        """Test removing a wallet from user account."""
        user, primary_wallet = await UserFactory.create_user_with_wallet(db_session)
        
        # Add a second wallet
        secondary_wallet_data = UserFactory.create_wallet_data(
            user.id, 
            address="0x" + "c" * 40,
            is_primary=False
        )
        from app.models import Wallet
        secondary_wallet = Wallet(**secondary_wallet_data)
        db_session.add(secondary_wallet)
        await db_session.commit()
        
        headers = get_auth_headers(user)
        response = await client.delete(
            f"/api/v1/users/{user.id}/wallets/{secondary_wallet.id}",
            headers=headers
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_cannot_remove_only_wallet(self, client: AsyncClient, db_session):
        """Test cannot remove the only wallet."""
        user, wallet = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        response = await client.delete(
            f"/api/v1/users/{user.id}/wallets/{wallet.id}",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "at least one wallet" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_remove_user_from_organization(self, client: AsyncClient, db_session):
        """Test admin removing user from organization."""
        admin, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, admin)
        await OrganizationFactory.add_member(db_session, org, member)
        
        headers = get_auth_headers(admin)
        headers["X-Organization-ID"] = org.id
        
        response = await client.delete(f"/api/v1/users/{member.id}", headers=headers)
        
        assert response.status_code == 204 