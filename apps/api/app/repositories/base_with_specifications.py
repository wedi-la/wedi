"""
Base repository with specification pattern support.
"""
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType
from app.repositories.specifications.base import Specification


class SpecificationRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced base repository with specification pattern support.
    
    Extends BaseRepository to support complex queries using specifications.
    """
    
    def _apply_specification(
        self,
        query: Select,
        specification: Specification[ModelType]
    ) -> Select:
        """Apply specification to query.
        
        Args:
            query: SQLAlchemy select query
            specification: Specification to apply
            
        Returns:
            Modified query with specification applied
        """
        # Get the expression from specification
        expr = specification.to_expression()
        
        # If it's a callable (lambda), call it with the model
        if callable(expr):
            expr = expr(self.model)
        
        # Apply to query
        if expr is not True and expr is not False:
            query = query.where(expr)
        elif expr is False:
            # False specification - no results
            query = query.where(False)
        # True specification - no filtering needed
        
        return query
    
    async def find_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[List[Any]] = None,
        load_options: Optional[List[Any]] = None,
        organization_id: Optional[str] = None
    ) -> List[ModelType]:
        """Find entities matching specification.
        
        Args:
            db: Database session
            specification: Specification to match
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: List of order_by clauses
            load_options: SQLAlchemy load options
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            List of matching entities
        """
        from sqlalchemy import select
        
        query = select(self.model)
        
        # Apply organization filter if needed
        query = self._apply_organization_filter(query, organization_id)
        
        # Apply specification
        query = self._apply_specification(query, specification)
        
        # Apply ordering
        if order_by:
            query = query.order_by(*order_by)
        else:
            # Default ordering by created_at if available
            if hasattr(self.model, "created_at"):
                query = query.order_by(self.model.created_at.desc())
        
        # Apply load options
        if load_options:
            for option in load_options:
                query = query.options(option)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def find_one_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        load_options: Optional[List[Any]] = None,
        organization_id: Optional[str] = None
    ) -> Optional[ModelType]:
        """Find single entity matching specification.
        
        Args:
            db: Database session
            specification: Specification to match
            load_options: SQLAlchemy load options
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            Matching entity or None
        """
        entities = await self.find_by_specification(
            db,
            specification=specification,
            limit=1,
            load_options=load_options,
            organization_id=organization_id
        )
        
        return entities[0] if entities else None
    
    async def count_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        organization_id: Optional[str] = None
    ) -> int:
        """Count entities matching specification.
        
        Args:
            db: Database session
            specification: Specification to match
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            Count of matching entities
        """
        from sqlalchemy import func, select
        
        query = select(func.count()).select_from(self.model)
        
        # Apply organization filter if needed
        query = self._apply_organization_filter(query, organization_id)
        
        # Apply specification
        query = self._apply_specification(query, specification)
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def exists_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        organization_id: Optional[str] = None
    ) -> bool:
        """Check if any entity matches specification.
        
        Args:
            db: Database session
            specification: Specification to match
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            True if at least one entity matches
        """
        count = await self.count_by_specification(
            db,
            specification=specification,
            organization_id=organization_id
        )
        return count > 0
    
    async def delete_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        organization_id: Optional[str] = None
    ) -> int:
        """Delete entities matching specification.
        
        Args:
            db: Database session
            specification: Specification to match
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            Number of entities deleted
        """
        from sqlalchemy import delete
        
        query = delete(self.model)
        
        # Apply organization filter if needed
        if self._organization_id_field and organization_id:
            query = query.where(
                getattr(self.model, self._organization_id_field) == organization_id
            )
        
        # Apply specification
        expr = specification.to_expression()
        if callable(expr):
            expr = expr(self.model)
        
        if expr is not True:
            query = query.where(expr)
        
        result = await db.execute(query)
        await db.flush()
        
        return result.rowcount
    
    async def update_by_specification(
        self,
        db: AsyncSession,
        *,
        specification: Specification[ModelType],
        values: Dict[str, Any],
        organization_id: Optional[str] = None
    ) -> int:
        """Update entities matching specification.
        
        Args:
            db: Database session
            specification: Specification to match
            values: Values to update
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            Number of entities updated
        """
        from sqlalchemy import update
        
        query = update(self.model)
        
        # Apply organization filter if needed
        if self._organization_id_field and organization_id:
            query = query.where(
                getattr(self.model, self._organization_id_field) == organization_id
            )
        
        # Apply specification
        expr = specification.to_expression()
        if callable(expr):
            expr = expr(self.model)
        
        if expr is not True:
            query = query.where(expr)
        
        # Set values
        query = query.values(**values)
        
        result = await db.execute(query)
        await db.flush()
        
        return result.rowcount 