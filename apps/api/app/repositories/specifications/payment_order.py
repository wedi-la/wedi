"""
PaymentOrder-specific query specifications.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.models.generated import KycStatus, PaymentOrder, PaymentOrderStatus
from app.repositories.specifications.base import (
    AndSpecification,
    BetweenSpecification,
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


class PaymentOrderByStatusSpec(InSpecification[PaymentOrder]):
    """Specification for payment orders by status."""
    
    def __init__(self, statuses: List[PaymentOrderStatus]):
        """Initialize with status list.
        
        Args:
            statuses: List of payment order statuses
        """
        super().__init__("status", statuses)


class PaymentOrderByOrganizationSpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by organization."""
    
    def __init__(self, organization_id: str):
        """Initialize with organization ID.
        
        Args:
            organization_id: Organization ID
        """
        super().__init__("organization_id", organization_id)


class PaymentOrderByPaymentLinkSpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by payment link."""
    
    def __init__(self, payment_link_id: str):
        """Initialize with payment link ID.
        
        Args:
            payment_link_id: Payment link ID
        """
        super().__init__("payment_link_id", payment_link_id)


class PaymentOrderByCustomerSpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by customer."""
    
    def __init__(self, customer_id: str):
        """Initialize with customer ID.
        
        Args:
            customer_id: Customer ID
        """
        super().__init__("customer_id", customer_id)


class PaymentOrderByNumberSpec(EqualSpecification[PaymentOrder]):
    """Specification for payment order by order number."""
    
    def __init__(self, order_number: str):
        """Initialize with order number.
        
        Args:
            order_number: Order number
        """
        super().__init__("order_number", order_number)


class PaymentOrderByCurrencySpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by currency."""
    
    def __init__(self, currency: str):
        """Initialize with currency.
        
        Args:
            currency: Currency code (e.g., USD, EUR)
        """
        super().__init__("requested_currency", currency.upper())


class PaymentOrderByAmountRangeSpec(BetweenSpecification[PaymentOrder]):
    """Specification for payment orders within amount range."""
    
    def __init__(self, min_amount: Decimal, max_amount: Decimal):
        """Initialize with amount range.
        
        Args:
            min_amount: Minimum amount (inclusive)
            max_amount: Maximum amount (inclusive)
        """
        super().__init__("requested_amount", min_amount, max_amount)


class PaymentOrderAboveAmountSpec(GreaterThanSpecification[PaymentOrder]):
    """Specification for payment orders above certain amount."""
    
    def __init__(self, amount: Decimal):
        """Initialize with minimum amount.
        
        Args:
            amount: Minimum amount (exclusive)
        """
        super().__init__("requested_amount", amount)


class PaymentOrderBelowAmountSpec(LessThanSpecification[PaymentOrder]):
    """Specification for payment orders below certain amount."""
    
    def __init__(self, amount: Decimal):
        """Initialize with maximum amount.
        
        Args:
            amount: Maximum amount (exclusive)
        """
        super().__init__("requested_amount", amount)


class PaymentOrderByDateRangeSpec(BetweenSpecification[PaymentOrder]):
    """Specification for payment orders within date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        """Initialize with date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """
        super().__init__("created_at", start_date, end_date)


class PaymentOrderByKycStatusSpec(InSpecification[PaymentOrder]):
    """Specification for payment orders by KYC status."""
    
    def __init__(self, kyc_statuses: List[KycStatus]):
        """Initialize with KYC status list.
        
        Args:
            kyc_statuses: List of KYC statuses
        """
        super().__init__("kyc_status", kyc_statuses)


class PaymentOrderByEmailSpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by customer email."""
    
    def __init__(self, email: str):
        """Initialize with email.
        
        Args:
            email: Customer email
        """
        super().__init__("customer_email", email.lower())


class PaymentOrderByCountrySpec(EqualSpecification[PaymentOrder]):
    """Specification for payment orders by customer country."""
    
    def __init__(self, country_code: str):
        """Initialize with country code.
        
        Args:
            country_code: ISO country code
        """
        super().__init__("customer_country", country_code.upper())


class PaymentOrderByRiskScoreSpec(Specification[PaymentOrder]):
    """Specification for payment orders by risk score range."""
    
    def __init__(self, min_score: Optional[int] = None, max_score: Optional[int] = None):
        """Initialize with risk score range.
        
        Args:
            min_score: Minimum risk score (inclusive)
            max_score: Maximum risk score (inclusive)
        """
        self.min_score = min_score
        self.max_score = max_score
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        specs = []
        
        if self.min_score is not None:
            specs.append(GreaterThanSpecification[PaymentOrder](
                "risk_score", self.min_score - 1
            ))
        
        if self.max_score is not None:
            specs.append(LessThanSpecification[PaymentOrder](
                "risk_score", self.max_score + 1
            ))
        
        if not specs:
            return lambda model: True
        elif len(specs) == 1:
            return specs[0].to_expression()
        else:
            return AndSpecification(*specs).to_expression()


class FailedPaymentOrdersSpec(Specification[PaymentOrder]):
    """Specification for failed payment orders."""
    
    def __init__(self, include_refunded: bool = False, include_cancelled: bool = False):
        """Initialize specification.
        
        Args:
            include_refunded: Include refunded orders
            include_cancelled: Include cancelled orders
        """
        self.include_refunded = include_refunded
        self.include_cancelled = include_cancelled
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        statuses = [PaymentOrderStatus.FAILED]
        
        if self.include_refunded:
            statuses.append(PaymentOrderStatus.REFUNDED)
        
        if self.include_cancelled:
            statuses.append(PaymentOrderStatus.CANCELLED)
        
        return PaymentOrderByStatusSpec(statuses).to_expression()


class PendingPaymentOrdersSpec(InSpecification[PaymentOrder]):
    """Specification for pending payment orders."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("status", [
            PaymentOrderStatus.CREATED,
            PaymentOrderStatus.AWAITING_PAYMENT,
            PaymentOrderStatus.PROCESSING,
            PaymentOrderStatus.REQUIRES_ACTION
        ])


class CompletedPaymentOrdersSpec(EqualSpecification[PaymentOrder]):
    """Specification for completed payment orders."""
    
    def __init__(self):
        """Initialize specification."""
        super().__init__("status", PaymentOrderStatus.COMPLETED)


class RetryablePaymentOrdersSpec(Specification[PaymentOrder]):
    """Specification for payment orders that can be retried."""
    
    def __init__(self, max_retries: int = 3):
        """Initialize with max retry count.
        
        Args:
            max_retries: Maximum number of retries allowed
        """
        self.max_retries = max_retries
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: AndSpecification(
            EqualSpecification[PaymentOrder]("status", PaymentOrderStatus.FAILED),
            LessThanSpecification[PaymentOrder]("retry_count", self.max_retries)
        ).to_expression()(model)


class PaymentOrderSearchSpec(Specification[PaymentOrder]):
    """Specification for searching payment orders."""
    
    def __init__(self, search_term: str):
        """Initialize with search term.
        
        Args:
            search_term: Term to search for
        """
        self.search_term = search_term
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        # Search in multiple fields
        like_term = f"%{self.search_term}%"
        
        return lambda model: OrSpecification(
            LikeSpecification[PaymentOrder]("order_number", like_term),
            LikeSpecification[PaymentOrder]("customer_email", like_term),
            LikeSpecification[PaymentOrder]("customer_name", like_term),
            LikeSpecification[PaymentOrder]("customer_wallet", like_term)
        ).to_expression()(model)


class HighValuePaymentOrdersSpec(Specification[PaymentOrder]):
    """Specification for high-value payment orders requiring extra scrutiny."""
    
    def __init__(self, threshold: Decimal = Decimal("10000")):
        """Initialize with value threshold.
        
        Args:
            threshold: Minimum amount to consider high-value
        """
        self.threshold = threshold
    
    def to_expression(self):
        """Convert to SQLAlchemy expression."""
        return lambda model: OrSpecification(
            GreaterThanSpecification[PaymentOrder]("requested_amount", self.threshold),
            GreaterThanSpecification[PaymentOrder]("settled_amount", self.threshold)
        ).to_expression()(model) 