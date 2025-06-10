"""
Organization factory for generating test data.
"""
import uuid
from datetime import datetime, timezone

from app.models import Organization, Membership, Role


class OrganizationFactory:
    """Factory for creating test organizations."""
    
    @staticmethod
    def create_organization_data(**overrides):
        """Generate organization data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "name": f"test_org_{uuid.uuid4().hex[:8]}",
            "display_name": "Test Organization",
            "description": "A test organization",
            "settings": {
                "currency": "USD",
                "timezone": "UTC",
                "notification_email": f"org_{uuid.uuid4().hex[:8]}@example.com",
            },
            "features": {
                "payment_links": True,
                "webhooks": True,
                "api_access": True,
            },
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def create_membership_data(user_id: str, organization_id: str, **overrides):
        """Generate membership data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "organization_id": organization_id,
            "role": Role.OWNER,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        return data
    
    @staticmethod
    async def create_organization(db_session, **overrides):
        """Create and persist a test organization."""
        org_data = OrganizationFactory.create_organization_data(**overrides)
        organization = Organization(**org_data)
        db_session.add(organization)
        await db_session.commit()
        await db_session.refresh(organization)
        return organization
    
    @staticmethod
    async def create_organization_with_owner(db_session, user, **org_overrides):
        """Create an organization with an owner."""
        # Set owner_id if not provided
        if "owner_id" not in org_overrides:
            org_overrides["owner_id"] = user.id
            
        organization = await OrganizationFactory.create_organization(
            db_session, **org_overrides
        )
        
        # Create membership
        membership_data = OrganizationFactory.create_membership_data(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.OWNER,
        )
        membership = Membership(**membership_data)
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)
        
        return organization, membership
    
    @staticmethod
    async def add_member(db_session, organization, user, role=Role.MEMBER):
        """Add a member to an organization."""
        membership_data = OrganizationFactory.create_membership_data(
            user_id=user.id,
            organization_id=organization.id,
            role=role,
        )
        membership = Membership(**membership_data)
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)
        return membership 