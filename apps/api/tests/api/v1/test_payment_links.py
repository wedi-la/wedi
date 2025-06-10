"""
Tests for payment link management endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models import PaymentLinkStatus
from tests.factories.organization_factory import OrganizationFactory
from tests.factories.payment_factory import PaymentFactory
from tests.factories.user_factory import UserFactory
from tests.utils.auth import get_auth_headers


class TestPaymentLinkEndpoints:
    """Test cases for payment link endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_payment_links(self, client: AsyncClient, db_session):
        """Test listing payment links for an organization."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        # Create payment links
        for i in range(3):
            await PaymentFactory.create_payment_link(
                db_session,
                organization_id=org.id,
                user_id=user.id,
                title=f"Payment {i}"
            )
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        response = await client.get("/api/v1/payment-links/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    @pytest.mark.asyncio
    async def test_create_payment_link(self, client: AsyncClient, db_session):
        """Test creating a new payment link."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        link_data = {
            "title": "New Payment Link",
            "description": "Test payment description",
            "amount": 250.50,
            "currency": "USD",
            "recipient_wallet": "0x" + "d" * 40,
        }
        
        response = await client.post(
            "/api/v1/payment-links/",
            json=link_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == link_data["title"]
        assert data["amount"] == link_data["amount"]
        assert data["status"] == "ACTIVE"
        assert "short_code" in data
        assert "qr_code" in data
    
    @pytest.mark.asyncio
    async def test_create_payment_link_with_reference(self, client: AsyncClient, db_session):
        """Test creating payment link with reference ID."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        link_data = {
            "title": "Payment with Reference",
            "amount": 100.00,
            "currency": "USD",
            "recipient_wallet": "0x" + "e" * 40,
            "reference_id": "INV-12345",
        }
        
        response = await client.post(
            "/api/v1/payment-links/",
            json=link_data,
            headers=headers
        )
        
        assert response.status_code == 201
        assert response.json()["reference_id"] == "INV-12345"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_reference_id(self, client: AsyncClient, db_session):
        """Test cannot create payment link with duplicate reference ID."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        # Create first link with reference
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            reference_id="DUP-123"
        )
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        response = await client.post(
            "/api/v1/payment-links/",
            json={
                "title": "Duplicate Reference",
                "amount": 100.00,
                "currency": "USD",
                "recipient_wallet": "0x" + "f" * 40,
                "reference_id": "DUP-123",
            },
            headers=headers
        )
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_get_payment_link_by_id(self, client: AsyncClient, db_session):
        """Test getting payment link by ID."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id
        )
        
        headers = get_auth_headers(user)
        response = await client.get(f"/api/v1/payment-links/{link.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == link.id
        assert data["title"] == link.title
        assert "statistics" in data
    
    @pytest.mark.asyncio
    async def test_get_payment_link_by_short_code_public(self, client: AsyncClient, db_session):
        """Test getting payment link by short code (public endpoint)."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id
        )
        
        # No auth headers needed for public endpoint
        response = await client.get(f"/api/v1/payment-links/by-short-code/{link.short_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == link.id
        assert data["title"] == link.title
        assert data["amount"] == link.amount
    
    @pytest.mark.asyncio
    async def test_update_payment_link(self, client: AsyncClient, db_session):
        """Test updating payment link."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id
        )
        
        headers = get_auth_headers(user)
        update_data = {
            "title": "Updated Payment",
            "description": "Updated description",
        }
        
        response = await client.put(
            f"/api/v1/payment-links/{link.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_cannot_update_paid_link(self, client: AsyncClient, db_session):
        """Test cannot update a paid payment link."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            status=PaymentLinkStatus.PAID
        )
        
        headers = get_auth_headers(user)
        response = await client.put(
            f"/api/v1/payment-links/{link.id}",
            json={"title": "Should Not Update"},
            headers=headers
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_archive_payment_link(self, client: AsyncClient, db_session):
        """Test archiving a payment link."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id
        )
        
        headers = get_auth_headers(user)
        response = await client.delete(f"/api/v1/payment-links/{link.id}", headers=headers)
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_duplicate_payment_link(self, client: AsyncClient, db_session):
        """Test duplicating a payment link."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        original = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            title="Original Payment",
            amount=123.45
        )
        
        headers = get_auth_headers(user)
        response = await client.post(
            f"/api/v1/payment-links/{original.id}/duplicate",
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == f"{original.title} (Copy)"
        assert data["amount"] == original.amount
        assert data["id"] != original.id
        assert data["short_code"] != original.short_code
    
    @pytest.mark.asyncio
    async def test_list_active_payment_links(self, client: AsyncClient, db_session):
        """Test listing only active payment links."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        # Create mixed status links
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            status=PaymentLinkStatus.ACTIVE
        )
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            status=PaymentLinkStatus.PAID
        )
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            status=PaymentLinkStatus.ACTIVE
        )
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        response = await client.get("/api/v1/payment-links/active", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(link["status"] == "ACTIVE" for link in data)
    
    @pytest.mark.asyncio
    async def test_search_payment_links(self, client: AsyncClient, db_session):
        """Test searching payment links with filters."""
        user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, user)
        
        # Create links with different properties
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            title="Invoice Payment",
            amount=100.00
        )
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            title="Service Fee",
            amount=200.00
        )
        await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=user.id,
            title="Product Payment",
            amount=150.00
        )
        
        headers = get_auth_headers(user)
        headers["X-Organization-ID"] = org.id
        
        # Search by query
        response = await client.get(
            "/api/v1/payment-links/search",
            params={"query": "Payment"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Invoice Payment and Product Payment
        
        # Search by amount range
        response = await client.get(
            "/api/v1/payment-links/search",
            params={"min_amount": 150, "max_amount": 250},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 150 and 200
    
    @pytest.mark.asyncio
    async def test_payment_link_permissions(self, client: AsyncClient, db_session):
        """Test payment link access permissions."""
        owner, _ = await UserFactory.create_user_with_wallet(db_session)
        other_user, _ = await UserFactory.create_user_with_wallet(db_session)
        org, _ = await OrganizationFactory.create_organization_with_owner(db_session, owner)
        
        link = await PaymentFactory.create_payment_link(
            db_session,
            organization_id=org.id,
            user_id=owner.id
        )
        
        # Other user cannot access
        headers = get_auth_headers(other_user)
        response = await client.get(f"/api/v1/payment-links/{link.id}", headers=headers)
        
        assert response.status_code == 403
        
        # Other user cannot update
        response = await client.put(
            f"/api/v1/payment-links/{link.id}",
            json={"title": "Hacked"},
            headers=headers
        )
        
        assert response.status_code == 403 