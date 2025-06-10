"""
Tests for organization management endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models import UserRole
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.user_factory import UserFactory
from tests.utils.auth import get_auth_headers


class TestOrganizationEndpoints:
    """Test cases for organization endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_user_organizations(self, client: AsyncClient, db_session):
        """Test listing user's organizations."""
        # Create user with organizations
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org1, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        org2, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        response = await client.get("/api/v1/organizations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        org_ids = [org["id"] for org in data]
        assert org1.id in org_ids
        assert org2.id in org_ids
    
    @pytest.mark.asyncio
    async def test_create_organization(self, client: AsyncClient, db_session):
        """Test creating a new organization."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        headers = get_auth_headers(user)
        
        org_data = {
            "name": "test_new_org",
            "display_name": "Test New Organization",
            "description": "A new test organization",
            "settings": {
                "currency": "USD",
                "timezone": "America/New_York",
            }
        }
        
        response = await client.post(
            "/api/v1/organizations",
            json=org_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == org_data["name"]
        assert data["display_name"] == org_data["display_name"]
        assert data["owner_id"] == user.id
    
    @pytest.mark.asyncio
    async def test_create_organization_duplicate_name(self, client: AsyncClient, db_session):
        """Test creating organization with duplicate name."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        response = await client.post(
            "/api/v1/organizations",
            json={"name": org.name, "display_name": "Another Org"},
            headers=headers
        )
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_get_organization_details(self, client: AsyncClient, db_session):
        """Test getting organization details."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        response = await client.get(f"/api/v1/organizations/{org.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org.id
        assert data["name"] == org.name
        assert "stats" in data
    
    @pytest.mark.asyncio
    async def test_get_organization_unauthorized(self, client: AsyncClient, db_session):
        """Test getting organization details without being a member."""
        user1, _ = await UserFactory.create_user_with_wallet(db_session)
        user2, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user1)
        
        headers = get_auth_headers(user2)
        response = await client.get(f"/api/v1/organizations/{org.id}", headers=headers)
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_update_organization(self, client: AsyncClient, db_session):
        """Test updating organization details."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        update_data = {
            "display_name": "Updated Organization Name",
            "description": "Updated description",
        }
        
        response = await client.put(
            f"/api/v1/organizations/{org.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_update_organization_member_forbidden(self, client: AsyncClient, db_session):
        """Test members cannot update organization."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member, UserRole.VIEWER)
        
        headers = get_auth_headers(member)
        response = await client.put(
            f"/api/v1/organizations/{org.id}",
            json={"display_name": "Should Not Update"},
            headers=headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_list_organization_members(self, client: AsyncClient, db_session):
        """Test listing organization members."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member1, _ = await UserFactory.create_user_with_wallet(db_session)
        member2, _ = await UserFactory.create_user_with_wallet(db_session)
        
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member1, UserRole.ADMIN)
        await OrganizationFactory.add_member(db_session, org, member2, UserRole.VIEWER)
        
        headers = get_auth_headers(owner)
        response = await client.get(f"/api/v1/organizations/{org.id}/members", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check roles
        role_map = {m["user"]["id"]: m["role"] for m in data}
        assert role_map[owner.id] == "OWNER"
        assert role_map[member1.id] == "ADMIN"
        assert role_map[member2.id] == "VIEWER"
    
    @pytest.mark.asyncio
    async def test_add_organization_member(self, client: AsyncClient, db_session):
        """Test adding a member to organization."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        new_member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        
        headers = get_auth_headers(owner)
        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "email": new_member.email,
                "role": "VIEWER",
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["id"] == new_member.id
        assert data["role"] == "VIEWER"
    
    @pytest.mark.asyncio
    async def test_update_member_role(self, client: AsyncClient, db_session):
        """Test updating member role."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member, UserRole.VIEWER)
        
        headers = get_auth_headers(owner)
        response = await client.put(
            f"/api/v1/organizations/{org.id}/members/{member.id}",
            json={"role": "ADMIN"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "ADMIN"
    
    @pytest.mark.asyncio
    async def test_remove_organization_member(self, client: AsyncClient, db_session):
        """Test removing a member from organization."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member, UserRole.VIEWER)
        
        headers = get_auth_headers(owner)
        response = await client.delete(
            f"/api/v1/organizations/{org.id}/members/{member.id}",
            headers=headers
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_member_remove_self(self, client: AsyncClient, db_session):
        """Test member can remove themselves."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        member, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        await OrganizationFactory.add_member(db_session, org, member, UserRole.VIEWER)
        
        headers = get_auth_headers(member)
        response = await client.delete(
            f"/api/v1/organizations/{org.id}/members/{member.id}",
            headers=headers
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_cannot_remove_owner(self, client: AsyncClient, db_session):
        """Test cannot remove organization owner."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        
        headers = get_auth_headers(owner)
        response = await client.delete(
            f"/api/v1/organizations/{org.id}/members/{owner.id}",
            headers=headers
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_organization_stats(self, client: AsyncClient, db_session):
        """Test getting organization statistics."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        
        # Add some members
        for _ in range(3):
            member, _ = await UserFactory.create_user_with_wallet(db_session)
            await OrganizationFactory.add_member(db_session, org, member)
        
        headers = get_auth_headers(owner)
        response = await client.get(f"/api/v1/organizations/{org.id}/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["member_count"] == 4  # owner + 3 members
        assert "payment_link_count" in data
        assert "total_volume" in data 