"""
Example usage of the specification pattern with repositories.

This file demonstrates how to use specifications for complex queries.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated import PaymentOrder, PaymentOrderStatus, User
from app.repositories.base_with_specifications import SpecificationRepository
from app.repositories.specifications.payment_order import (
    CompletedPaymentOrdersSpec,
    HighValuePaymentOrdersSpec,
    PaymentOrderByCountrySpec,
    PaymentOrderByCurrencySpec,
    PaymentOrderByDateRangeSpec,
    PaymentOrderSearchSpec,
)
from app.repositories.specifications.user import (
    ActiveUsersSpec,
    UserSearchSpec,
    VerifiedUsersSpec,
)


class ExampleUserRepository(SpecificationRepository[User, None, None]):
    """Example user repository using specifications."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(User)
    
    async def find_active_verified_users(
        self,
        db: AsyncSession,
        organization_id: str,
        days: int = 30
    ) -> List[User]:
        """Find users who are both active and verified.
        
        Example of combining specifications with AND operator.
        """
        # Create individual specifications
        active_spec = ActiveUsersSpec(days=days)
        verified_spec = VerifiedUsersSpec()
        
        # Combine with AND
        combined_spec = active_spec & verified_spec
        
        # Execute query
        return await self.find_by_specification(
            db,
            specification=combined_spec,
            organization_id=organization_id
        )
    
    async def search_users_with_filters(
        self,
        db: AsyncSession,
        search_term: str,
        only_verified: bool = False,
        organization_id: str = None
    ) -> List[User]:
        """Search users with optional filters.
        
        Example of conditional specification building.
        """
        # Start with search specification
        spec = UserSearchSpec(search_term)
        
        # Add verified filter if requested
        if only_verified:
            spec = spec & VerifiedUsersSpec()
        
        return await self.find_by_specification(
            db,
            specification=spec,
            organization_id=organization_id
        )


class ExamplePaymentOrderRepository(SpecificationRepository[PaymentOrder, None, None]):
    """Example payment order repository using specifications."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(PaymentOrder)
    
    async def find_high_value_orders_by_country(
        self,
        db: AsyncSession,
        country_code: str,
        threshold: Decimal,
        organization_id: str
    ) -> List[PaymentOrder]:
        """Find high-value orders from a specific country.
        
        Example of combining multiple specifications.
        """
        # Create specifications
        country_spec = PaymentOrderByCountrySpec(country_code)
        high_value_spec = HighValuePaymentOrdersSpec(threshold)
        completed_spec = CompletedPaymentOrdersSpec()
        
        # Combine: completed AND high-value AND from country
        combined_spec = completed_spec & high_value_spec & country_spec
        
        return await self.find_by_specification(
            db,
            specification=combined_spec,
            organization_id=organization_id
        )
    
    async def find_orders_for_reconciliation(
        self,
        db: AsyncSession,
        date: datetime,
        currency: str,
        organization_id: str
    ) -> List[PaymentOrder]:
        """Find orders for daily reconciliation.
        
        Example of date range and currency filtering.
        """
        # Orders completed on the specific date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)
        
        # Create specifications
        date_spec = PaymentOrderByDateRangeSpec(start_of_day, end_of_day)
        currency_spec = PaymentOrderByCurrencySpec(currency)
        completed_spec = CompletedPaymentOrdersSpec()
        
        # Combine all specifications
        combined_spec = date_spec & currency_spec & completed_spec
        
        return await self.find_by_specification(
            db,
            specification=combined_spec,
            organization_id=organization_id,
            order_by=[PaymentOrder.completed_at]
        )
    
    async def complex_search_example(
        self,
        db: AsyncSession,
        search_term: str,
        countries: List[str],
        min_amount: Decimal,
        organization_id: str
    ) -> List[PaymentOrder]:
        """Complex search with OR conditions.
        
        Example: Find orders that match search term OR are from specific countries
        AND have amount above threshold.
        """
        # Search specification
        search_spec = PaymentOrderSearchSpec(search_term)
        
        # Create OR specification for countries
        country_specs = [PaymentOrderByCountrySpec(country) for country in countries]
        countries_spec = country_specs[0]
        for spec in country_specs[1:]:
            countries_spec = countries_spec | spec
        
        # Amount specification
        from app.repositories.specifications.payment_order import PaymentOrderAboveAmountSpec
        amount_spec = PaymentOrderAboveAmountSpec(min_amount)
        
        # Combine: (search OR countries) AND amount
        combined_spec = (search_spec | countries_spec) & amount_spec
        
        return await self.find_by_specification(
            db,
            specification=combined_spec,
            organization_id=organization_id
        )
    
    async def count_orders_by_specification(
        self,
        db: AsyncSession,
        organization_id: str
    ) -> Dict[str, int]:
        """Count orders using different specifications.
        
        Example of using count_by_specification.
        """
        # Count completed orders
        completed_count = await self.count_by_specification(
            db,
            specification=CompletedPaymentOrdersSpec(),
            organization_id=organization_id
        )
        
        # Count high-value orders
        high_value_count = await self.count_by_specification(
            db,
            specification=HighValuePaymentOrdersSpec(Decimal("10000")),
            organization_id=organization_id
        )
        
        # Count orders from Mexico
        mexico_count = await self.count_by_specification(
            db,
            specification=PaymentOrderByCountrySpec("MX"),
            organization_id=organization_id
        )
        
        return {
            "completed": completed_count,
            "high_value": high_value_count,
            "from_mexico": mexico_count
        }


# Usage examples in API endpoints
async def example_endpoint(
    db: AsyncSession,
    organization_id: str
):
    """Example of using specifications in an API endpoint."""
    # Initialize repository
    repo = ExamplePaymentOrderRepository()
    
    # Example 1: Simple specification
    completed_orders = await repo.find_by_specification(
        db,
        specification=CompletedPaymentOrdersSpec(),
        organization_id=organization_id,
        limit=50
    )
    
    # Example 2: Complex specification with multiple conditions
    high_value_mexico_orders = await repo.find_high_value_orders_by_country(
        db,
        country_code="MX",
        threshold=Decimal("5000"),
        organization_id=organization_id
    )
    
    # Example 3: Check if any orders match criteria
    has_high_value = await repo.exists_by_specification(
        db,
        specification=HighValuePaymentOrdersSpec(Decimal("100000")),
        organization_id=organization_id
    )
    
    # Example 4: Update orders matching specification
    from app.repositories.specifications.payment_order import RetryablePaymentOrdersSpec
    
    updated_count = await repo.update_by_specification(
        db,
        specification=RetryablePaymentOrdersSpec(max_retries=3),
        values={"retry_scheduled_at": datetime.utcnow() + timedelta(minutes=30)},
        organization_id=organization_id
    )
    
    return {
        "completed_orders": len(completed_orders),
        "high_value_mexico_orders": len(high_value_mexico_orders),
        "has_high_value": has_high_value,
        "scheduled_for_retry": updated_count
    } 