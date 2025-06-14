"""
Extensions to generated SQLAlchemy models.

This module contains extensions to the auto-generated SQLAlchemy models to add
functionality specific to Clerk and Circle integration without modifying the
generated files.
"""

from sqlalchemy import Column, String
from app.models.generated import User

# Extend User model to include clerk_id
if hasattr(User, '__table__'):
    if 'clerk_id' not in User.__table__.columns:
        User.clerk_id = Column(String, nullable=True, index=True, unique=True)
        # Note: We can't add the foreign key constraint dynamically
        # This would need to be done in a migration

# Add custom methods to the User model
def get_clerk_user_data(self) -> dict:
    """Get user data for Clerk integration."""
    return {
        "id": self.id,
        "clerk_id": getattr(self, "clerk_id", None),
        "email": self.email,
        "name": f"{self.first_name} {self.last_name}".strip(),
        "first_name": self.first_name,
        "last_name": self.last_name,
        "is_active": self.is_active
    }

User.get_clerk_user_data = get_clerk_user_data
