"""
Base specification pattern implementation for complex queries.
"""
from abc import ABC, abstractmethod
from typing import Any, Generic, List, TypeVar

from sqlalchemy import and_, not_, or_
from sqlalchemy.sql import ClauseElement

from app.models import Base as SQLAlchemyBase

ModelType = TypeVar("ModelType", bound=SQLAlchemyBase)


class Specification(ABC, Generic[ModelType]):
    """
    Abstract base class for specifications.
    
    Specifications encapsulate query logic and can be combined
    using logical operators.
    """
    
    @abstractmethod
    def to_expression(self) -> ClauseElement:
        """Convert specification to SQLAlchemy expression.
        
        Returns:
            SQLAlchemy clause element
        """
        pass
    
    def and_(self, other: "Specification[ModelType]") -> "AndSpecification[ModelType]":
        """Create AND specification.
        
        Args:
            other: Another specification
            
        Returns:
            Combined AND specification
        """
        return AndSpecification(self, other)
    
    def or_(self, other: "Specification[ModelType]") -> "OrSpecification[ModelType]":
        """Create OR specification.
        
        Args:
            other: Another specification
            
        Returns:
            Combined OR specification
        """
        return OrSpecification(self, other)
    
    def not_(self) -> "NotSpecification[ModelType]":
        """Create NOT specification.
        
        Returns:
            Negated specification
        """
        return NotSpecification(self)
    
    def __and__(self, other: "Specification[ModelType]") -> "AndSpecification[ModelType]":
        """Support & operator."""
        return self.and_(other)
    
    def __or__(self, other: "Specification[ModelType]") -> "OrSpecification[ModelType]":
        """Support | operator."""
        return self.or_(other)
    
    def __invert__(self) -> "NotSpecification[ModelType]":
        """Support ~ operator."""
        return self.not_()


class CompositeSpecification(Specification[ModelType], ABC):
    """Base class for composite specifications."""
    
    def __init__(self, *specs: Specification[ModelType]):
        """Initialize with specifications.
        
        Args:
            *specs: Variable number of specifications
        """
        self.specifications = list(specs)
    
    def add(self, spec: Specification[ModelType]) -> None:
        """Add specification to composite.
        
        Args:
            spec: Specification to add
        """
        self.specifications.append(spec)


class AndSpecification(CompositeSpecification[ModelType]):
    """AND composite specification."""
    
    def to_expression(self) -> ClauseElement:
        """Convert to SQLAlchemy AND expression."""
        if not self.specifications:
            return True  # Empty AND is true
        
        expressions = [spec.to_expression() for spec in self.specifications]
        return and_(*expressions)


class OrSpecification(CompositeSpecification[ModelType]):
    """OR composite specification."""
    
    def to_expression(self) -> ClauseElement:
        """Convert to SQLAlchemy OR expression."""
        if not self.specifications:
            return False  # Empty OR is false
        
        expressions = [spec.to_expression() for spec in self.specifications]
        return or_(*expressions)


class NotSpecification(Specification[ModelType]):
    """NOT specification."""
    
    def __init__(self, spec: Specification[ModelType]):
        """Initialize with specification to negate.
        
        Args:
            spec: Specification to negate
        """
        self.specification = spec
    
    def to_expression(self) -> ClauseElement:
        """Convert to SQLAlchemy NOT expression."""
        return not_(self.specification.to_expression())


class TrueSpecification(Specification[ModelType]):
    """Always true specification."""
    
    def to_expression(self) -> ClauseElement:
        """Return true expression."""
        return True


class FalseSpecification(Specification[ModelType]):
    """Always false specification."""
    
    def to_expression(self) -> ClauseElement:
        """Return false expression."""
        return False


class FieldSpecification(Specification[ModelType]):
    """Base class for field-based specifications."""
    
    def __init__(self, field_name: str, value: Any):
        """Initialize with field name and value.
        
        Args:
            field_name: Name of the field
            value: Value to compare
        """
        self.field_name = field_name
        self.value = value
    
    @abstractmethod
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model.
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            Model field
        """
        pass


class EqualSpecification(FieldSpecification[ModelType]):
    """Equality specification."""
    
    def __init__(self, field_name: str, value: Any):
        """Initialize with field name and value."""
        super().__init__(field_name, value)
        self._model_class = None
    
    def set_model(self, model_class: type[ModelType]) -> "EqualSpecification[ModelType]":
        """Set the model class for this specification."""
        self._model_class = model_class
        return self
    
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model."""
        return getattr(model, self.field_name)
    
    def to_expression(self) -> ClauseElement:
        """Convert to equality expression."""
        # If model is set, return the actual expression
        if self._model_class:
            return getattr(self._model_class, self.field_name) == self.value
        # Otherwise return a callable that expects the model
        return lambda model: getattr(model, self.field_name) == self.value


class GreaterThanSpecification(FieldSpecification[ModelType]):
    """Greater than specification."""
    
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model."""
        return getattr(model, self.field_name)
    
    def to_expression(self) -> ClauseElement:
        """Convert to greater than expression."""
        return lambda model: getattr(model, self.field_name) > self.value


class LessThanSpecification(FieldSpecification[ModelType]):
    """Less than specification."""
    
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model."""
        return getattr(model, self.field_name)
    
    def to_expression(self) -> ClauseElement:
        """Convert to less than expression."""
        return lambda model: getattr(model, self.field_name) < self.value


class InSpecification(FieldSpecification[ModelType]):
    """IN specification for checking if value is in a list."""
    
    def __init__(self, field_name: str, values: List[Any]):
        """Initialize with field name and list of values.
        
        Args:
            field_name: Name of the field
            values: List of values to check
        """
        super().__init__(field_name, values)
    
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model."""
        return getattr(model, self.field_name)
    
    def to_expression(self) -> ClauseElement:
        """Convert to IN expression."""
        return lambda model: getattr(model, self.field_name).in_(self.value)


class LikeSpecification(FieldSpecification[ModelType]):
    """LIKE specification for pattern matching."""
    
    def get_field(self, model: type[ModelType]) -> Any:
        """Get field from model."""
        return getattr(model, self.field_name)
    
    def to_expression(self) -> ClauseElement:
        """Convert to LIKE expression."""
        return lambda model: getattr(model, self.field_name).like(self.value)


class BetweenSpecification(Specification[ModelType]):
    """BETWEEN specification for range queries."""
    
    def __init__(self, field_name: str, min_value: Any, max_value: Any):
        """Initialize with field name and range.
        
        Args:
            field_name: Name of the field
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
        """
        self.field_name = field_name
        self.min_value = min_value
        self.max_value = max_value
    
    def to_expression(self) -> ClauseElement:
        """Convert to BETWEEN expression."""
        return lambda model: getattr(model, self.field_name).between(
            self.min_value, self.max_value
        )


class IsNullSpecification(Specification[ModelType]):
    """IS NULL specification."""
    
    def __init__(self, field_name: str):
        """Initialize with field name.
        
        Args:
            field_name: Name of the field to check for NULL
        """
        self.field_name = field_name
    
    def to_expression(self) -> ClauseElement:
        """Convert to IS NULL expression."""
        return lambda model: getattr(model, self.field_name).is_(None)


class IsNotNullSpecification(Specification[ModelType]):
    """IS NOT NULL specification."""
    
    def __init__(self, field_name: str):
        """Initialize with field name.
        
        Args:
            field_name: Name of the field to check for NOT NULL
        """
        self.field_name = field_name
    
    def to_expression(self) -> ClauseElement:
        """Convert to IS NOT NULL expression."""
        return lambda model: getattr(model, self.field_name).isnot(None) 