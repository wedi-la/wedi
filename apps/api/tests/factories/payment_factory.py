"""
Payment factory for generating test data.
"""
import uuid
from datetime import datetime, timezone

from app.models import PaymentLink, PaymentLinkStatus


class PaymentFactory:
    """Factory for creating test payment-related entities."""
    
    @staticmethod
    def create_payment_link_data(organization_id: str, created_by_id: str, **overrides):
        """Generate payment link data dictionary."""
        data = {
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "created_by_id": created_by_id,
            "short_code": f"PAY{uuid.uuid4().hex[:8].upper()}",
            "title": "Test Payment",
            "description": "Test payment description",
            "amount": 100.00,
            "currency": "USD",
            "status": PaymentLinkStatus.ACTIVE,
            "recipient_wallet": f"0x{uuid.uuid4().hex[:40]}",
            "metadata": {
                "test": True,
                "created_for": "testing",
            },
            "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data=test",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        return data
    
    @staticmethod
    async def create_payment_link(db_session, organization_id: str, user_id: str, **overrides):
        """Create and persist a test payment link."""
        link_data = PaymentFactory.create_payment_link_data(
            organization_id=organization_id,
            created_by_id=user_id,
            **overrides
        )
        payment_link = PaymentLink(**link_data)
        db_session.add(payment_link)
        await db_session.commit()
        await db_session.refresh(payment_link)
        return payment_link 