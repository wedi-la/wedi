"""
User-specific query specifications.
"""
from datetime import datetime
from typing import List, Optional

from app.models.generated import AuthProvider, User
from app.repositories.specifications.base import (
    AndSpecification,
    EqualSpecification,
    GreaterThanSpecification,
    InSpecification,
    IsNotNullSpecification,
    IsNullSpecification,
    LessThanSpecification,
    LikeSpecification,
    OrSpecification,
    Specification,
)


class UserByEmailSpec(EqualSpecification[User]):
    """Specification for finding user by email."""
    
    def __init__(self, email: str):
        """Initialize with email.
        
        Args:
            email: User email address
        """
        super().__init__("email", email.lower())


class UserByAuthProviderSpec(Specification[User]):
    """Specification for finding user by auth provider."""
    
    def __init__(self, provider: AuthProvider, provider_id: str):
        """Initialize with auth provider details.
        
        Args:
            provider: Auth provider type
            provider_id: Provider-specific ID
        """
        self.provider = provider
        self.provider_id = provider_id
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: AndSpecification(
            EqualSpecification[User]("auth_provider", self.provider),
            EqualSpecification[User]("auth_provider_id", self.provider_id)
        ).to_expression()(model)


class UserByWalletSpec(EqualSpecification[User]):
    """Specification for finding user by primary wallet."""
    
    def __init__(self, wallet_id: str):
        """Initialize with wallet ID.
        
        Args:
            wallet_id: Primary wallet ID
        """
        super().__init__("primary_wallet_id", wallet_id)


class VerifiedUsersSpec(EqualSpecification[User]):
    """Specification for verified users."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("email_verified", True)


class UnverifiedUsersSpec(EqualSpecification[User]):
    """Specification for unverified users."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("email_verified", False)


class UsersWithWalletSpec(IsNotNullSpecification[User]):
    """Specification for users with a primary wallet."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("primary_wallet_id")


class UsersWithoutWalletSpec(IsNullSpecification[User]):
    """Specification for users without a primary wallet."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("primary_wallet_id")


class ActiveUsersSpec(Specification[User]):
    """Specification for active users (logged in recently)."""
    
    def __init__(self, days: int = 30):
        """Initialize with activity period.
        
        Args:
            days: Number of days to consider as active
        """
        self.days = days
        self.cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        # Go back 'days' days
        from datetime import timedelta
        self.cutoff_date = self.cutoff_date - timedelta(days=days)
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: GreaterThanSpecification[User](
            "last_login_at", self.cutoff_date
        ).to_expression()(model)


class InactiveUsersSpec(Specification[User]):
    """Specification for inactive users."""
    
    def __init__(self, days: int = 30):
        """Initialize with inactivity period.
        
        Args:
            days: Number of days of inactivity
        """
        self.days = days
        self.cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        self.cutoff_date = self.cutoff_date - timedelta(days=days)
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: OrSpecification(
            LessThanSpecification[User]("last_login_at", self.cutoff_date),
            IsNullSpecification[User]("last_login_at")
        ).to_expression()(model)


class UserSearchSpec(Specification[User]):
    """Specification for searching users by name or email."""
    
    def __init__(self, search_term: str):
        """Initialize with search term.
        
        Args:
            search_term: Term to search for
        """
        self.search_term = f"%{search_term}%"
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: OrSpecification(
            LikeSpecification[User]("email", self.search_term),
            LikeSpecification[User]("name", self.search_term)
        ).to_expression()(model)


class UsersByAuthProviderSpec(InSpecification[User]):
    """Specification for users by auth provider list."""
    
    def __init__(self, providers: List[AuthProvider]):
        """Initialize with auth provider list.
        
        Args:
            providers: List of auth providers
        """
        super().__init__("auth_provider", providers)


class UsersCreatedBetweenSpec(Specification[User]):
    """Specification for users created in a date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        """Initialize with date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """
        self.start_date = start_date
        self.end_date = end_date
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        from app.repositories.specifications.base import BetweenSpecification
        return lambda model: BetweenSpecification[User](
            "created_at", self.start_date, self.end_date
        ).to_expression()(model) 