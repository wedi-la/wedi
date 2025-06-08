"""
Customer repository with payment method management.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Customer,
    CustomerPaymentMethod,
    KycStatus,
    PaymentMethodType,
    PaymentOrder,
)
from app.repositories.base import BaseRepository, DuplicateError, NotFoundError
from app.schemas.customer import (
    CustomerCreate,
    CustomerFilter,
    CustomerUpdate,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)


class CustomerRepository(BaseRepository[Customer, CustomerCreate, CustomerUpdate]):
    """Repository for customer-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Customer)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Customers are scoped to organizations."""
        return "organization_id"
    
    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
        organization_id: str
    ) -> Optional[Customer]:
        """
        Get customer by email within an organization.
        
        Args:
            db: Database session
            email: Customer email
            organization_id: Organization ID
            
        Returns:
            Customer or None if not found
        """
        query = select(Customer).where(
            and_(
                Customer.email == email.lower(),
                Customer.organization_id == organization_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_external_id(
        self,
        db: AsyncSession,
        *,
        external_id: str,
        organization_id: str
    ) -> Optional[Customer]:
        """
        Get customer by external ID (merchant's reference).
        
        Args:
            db: Database session
            external_id: External customer ID
            organization_id: Organization ID
            
        Returns:
            Customer or None if not found
        """
        query = select(Customer).where(
            and_(
                Customer.external_id == external_id,
                Customer.organization_id == organization_id
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_or_create(
        self,
        db: AsyncSession,
        *,
        email: str,
        organization_id: str,
        defaults: Optional[dict] = None
    ) -> tuple[Customer, bool]:
        """
        Get existing customer or create new one.
        
        Args:
            db: Database session
            email: Customer email
            organization_id: Organization ID
            defaults: Default values for new customer
            
        Returns:
            Tuple of (customer, created) where created is True if new
        """
        # Try to get existing customer
        customer = await self.get_by_email(
            db,
            email=email,
            organization_id=organization_id
        )
        
        if customer:
            return customer, False
        
        # Create new customer
        create_data = CustomerCreate(
            email=email,
            **(defaults or {})
        )
        
        customer = await self.create(
            db,
            obj_in=create_data,
            organization_id=organization_id
        )
        
        return customer, True
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: CustomerFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Customer]:
        """
        Search customers with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching customers
        """
        query = select(Customer).where(
            Customer.organization_id == organization_id
        )
        
        # Apply filters
        if filters.email:
            query = query.where(Customer.email.ilike(f"%{filters.email}%"))
        
        if filters.name:
            query = query.where(Customer.name.ilike(f"%{filters.name}%"))
        
        if filters.country:
            query = query.where(Customer.country == filters.country.upper())
        
        if filters.kyc_status:
            query = query.where(Customer.kyc_status == filters.kyc_status)
        
        if filters.created_after:
            query = query.where(Customer.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(Customer.created_at <= filters.created_before)
        
        if filters.has_payment_methods is not None:
            subquery = select(CustomerPaymentMethod.customer_id).distinct()
            if filters.has_payment_methods:
                query = query.where(Customer.id.in_(subquery))
            else:
                query = query.where(~Customer.id.in_(subquery))
        
        # Apply ordering and pagination
        query = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_with_payment_methods(
        self,
        db: AsyncSession,
        *,
        customer_id: str
    ) -> Optional[Customer]:
        """
        Get customer with payment methods eagerly loaded.
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            Customer with payment methods or None
        """
        query = select(Customer).where(
            Customer.id == customer_id
        ).options(
            selectinload(Customer.payment_methods)
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    # Payment Method Management
    
    async def add_payment_method(
        self,
        db: AsyncSession,
        *,
        customer_id: str,
        payment_method: PaymentMethodCreate
    ) -> CustomerPaymentMethod:
        """
        Add a payment method to a customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
            payment_method: Payment method data
            
        Returns:
            Created payment method
        """
        # Verify customer exists
        customer = await self.get_or_404(db, id=customer_id)
        
        # Create masked/safe values based on type
        safe_data = self._create_safe_payment_method_data(payment_method)
        
        # If this is the first payment method or marked as default, update others
        if payment_method.is_default:
            await self._unset_default_payment_methods(db, customer_id)
        
        # Create payment method
        db_obj = CustomerPaymentMethod(
            customer_id=customer_id,
            **safe_data
        )
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        
        # If this is the only payment method, make it default
        if not payment_method.is_default:
            count_query = select(func.count(CustomerPaymentMethod.id)).where(
                CustomerPaymentMethod.customer_id == customer_id
            )
            result = await db.execute(count_query)
            if result.scalar_one() == 1:
                db_obj.is_default = True
                db.add(db_obj)
                await db.flush()
        
        return db_obj
    
    async def update_payment_method(
        self,
        db: AsyncSession,
        *,
        payment_method_id: str,
        customer_id: str,
        update_data: PaymentMethodUpdate
    ) -> CustomerPaymentMethod:
        """
        Update a customer's payment method.
        
        Args:
            db: Database session
            payment_method_id: Payment method ID
            customer_id: Customer ID (for verification)
            update_data: Update data
            
        Returns:
            Updated payment method
        """
        # Get payment method
        query = select(CustomerPaymentMethod).where(
            and_(
                CustomerPaymentMethod.id == payment_method_id,
                CustomerPaymentMethod.customer_id == customer_id
            )
        )
        
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            raise NotFoundError(f"Payment method {payment_method_id} not found")
        
        # Handle default status change
        if update_data.is_default and not payment_method.is_default:
            await self._unset_default_payment_methods(db, customer_id)
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(payment_method, field, value)
        
        db.add(payment_method)
        await db.flush()
        await db.refresh(payment_method)
        
        return payment_method
    
    async def remove_payment_method(
        self,
        db: AsyncSession,
        *,
        payment_method_id: str,
        customer_id: str
    ) -> bool:
        """
        Remove a payment method from a customer.
        
        Args:
            db: Database session
            payment_method_id: Payment method ID
            customer_id: Customer ID (for verification)
            
        Returns:
            True if removed successfully
        """
        # Get payment method
        query = select(CustomerPaymentMethod).where(
            and_(
                CustomerPaymentMethod.id == payment_method_id,
                CustomerPaymentMethod.customer_id == customer_id
            )
        )
        
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            return False
        
        # Check if this payment method is used in any pending orders
        order_query = select(func.count(PaymentOrder.id)).where(
            and_(
                PaymentOrder.customer_id == customer_id,
                PaymentOrder.status.in_(["PENDING", "PROCESSING"])
                # Note: Would check payment_method_id if tracked in orders
            )
        )
        
        order_result = await db.execute(order_query)
        if order_result.scalar_one() > 0:
            raise ValueError("Cannot remove payment method with pending orders")
        
        # Delete the payment method
        await db.delete(payment_method)
        await db.flush()
        
        # If this was the default, set another as default
        if payment_method.is_default:
            await self._set_new_default_payment_method(db, customer_id)
        
        return True
    
    async def get_payment_methods(
        self,
        db: AsyncSession,
        *,
        customer_id: str,
        type_filter: Optional[PaymentMethodType] = None
    ) -> List[CustomerPaymentMethod]:
        """
        Get all payment methods for a customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
            type_filter: Optional filter by payment method type
            
        Returns:
            List of payment methods
        """
        query = select(CustomerPaymentMethod).where(
            CustomerPaymentMethod.customer_id == customer_id
        )
        
        if type_filter:
            query = query.where(CustomerPaymentMethod.type == type_filter)
        
        query = query.order_by(
            CustomerPaymentMethod.is_default.desc(),
            CustomerPaymentMethod.created_at.desc()
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_default_payment_method(
        self,
        db: AsyncSession,
        *,
        customer_id: str
    ) -> Optional[CustomerPaymentMethod]:
        """
        Get the default payment method for a customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            Default payment method or None
        """
        query = select(CustomerPaymentMethod).where(
            and_(
                CustomerPaymentMethod.customer_id == customer_id,
                CustomerPaymentMethod.is_default == True
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def verify_payment_method(
        self,
        db: AsyncSession,
        *,
        payment_method_id: str,
        customer_id: str
    ) -> CustomerPaymentMethod:
        """
        Mark a payment method as verified.
        
        Args:
            db: Database session
            payment_method_id: Payment method ID
            customer_id: Customer ID (for verification)
            
        Returns:
            Updated payment method
        """
        payment_method = await self.update_payment_method(
            db,
            payment_method_id=payment_method_id,
            customer_id=customer_id,
            update_data=PaymentMethodUpdate(
                is_verified=True,
                verified_at=datetime.utcnow()
            )
        )
        
        return payment_method
    
    # Helper methods
    
    def _create_safe_payment_method_data(
        self,
        payment_method: PaymentMethodCreate
    ) -> dict:
        """
        Create safe/masked payment method data for storage.
        
        Args:
            payment_method: Payment method creation data
            
        Returns:
            Dictionary with safe data
        """
        safe_data = {
            "type": payment_method.type,
            "label": payment_method.label,
            "is_default": payment_method.is_default,
            "metadata": payment_method.metadata,
            "is_verified": False,
            "expires_at": None,
        }
        
        if payment_method.type == PaymentMethodType.CARD:
            # Mask card details
            if payment_method.card_number:
                safe_data["card_last4"] = payment_method.card_number[-4:]
                # Would determine brand from BIN in production
                safe_data["card_brand"] = "visa"  # Placeholder
            
            # Calculate expiration
            if payment_method.card_exp_month and payment_method.card_exp_year:
                from calendar import monthrange
                last_day = monthrange(
                    payment_method.card_exp_year,
                    payment_method.card_exp_month
                )[1]
                safe_data["expires_at"] = datetime(
                    payment_method.card_exp_year,
                    payment_method.card_exp_month,
                    last_day,
                    23, 59, 59
                )
        
        elif payment_method.type == PaymentMethodType.BANK_ACCOUNT:
            # Mask bank details
            if payment_method.bank_account_number:
                safe_data["bank_last4"] = payment_method.bank_account_number[-4:]
            safe_data["bank_name"] = payment_method.bank_name
        
        elif payment_method.type == PaymentMethodType.WALLET:
            # Store wallet address (public info)
            safe_data["wallet_address"] = payment_method.wallet_address
        
        return safe_data
    
    async def _unset_default_payment_methods(
        self,
        db: AsyncSession,
        customer_id: str
    ) -> None:
        """
        Unset all default payment methods for a customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
        """
        query = select(CustomerPaymentMethod).where(
            and_(
                CustomerPaymentMethod.customer_id == customer_id,
                CustomerPaymentMethod.is_default == True
            )
        )
        
        result = await db.execute(query)
        for pm in result.scalars().all():
            pm.is_default = False
            db.add(pm)
    
    async def _set_new_default_payment_method(
        self,
        db: AsyncSession,
        customer_id: str
    ) -> None:
        """
        Set a new default payment method for a customer.
        
        Args:
            db: Database session
            customer_id: Customer ID
        """
        # Get the most recently verified payment method
        query = select(CustomerPaymentMethod).where(
            CustomerPaymentMethod.customer_id == customer_id
        ).order_by(
            CustomerPaymentMethod.is_verified.desc(),
            CustomerPaymentMethod.created_at.desc()
        ).limit(1)
        
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if payment_method:
            payment_method.is_default = True
            db.add(payment_method) 