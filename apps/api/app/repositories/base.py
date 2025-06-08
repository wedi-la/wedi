"""
Base repository abstract class with generic CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, and_, delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Base as SQLAlchemyBase

ModelType = TypeVar("ModelType", bound=SQLAlchemyBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryException(Exception):
    """Base exception for repository operations."""
    pass


class NotFoundError(RepositoryException):
    """Raised when an entity is not found."""
    pass


class DuplicateError(RepositoryException):
    """Raised when attempting to create a duplicate entity."""
    pass


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Abstract base repository with generic CRUD operations.
    
    Provides common database operations for SQLAlchemy models.
    """
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    @property
    @abstractmethod
    def _organization_id_field(self) -> Optional[str]:
        """Field name for organization ID (for multi-tenancy).
        
        Return None if the model doesn't support multi-tenancy.
        """
        pass
    
    def _apply_organization_filter(self, query: Select, organization_id: Optional[str]) -> Select:
        """Apply organization filter for multi-tenancy.
        
        Args:
            query: SQLAlchemy select query
            organization_id: Organization ID to filter by
            
        Returns:
            Filtered query
        """
        if self._organization_id_field and organization_id:
            return query.where(
                getattr(self.model, self._organization_id_field) == organization_id
            )
        return query
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        organization_id: Optional[str] = None,
        **kwargs: Any
    ) -> ModelType:
        """Create a new entity.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with creation data
            organization_id: Organization ID for multi-tenancy
            **kwargs: Additional fields to set
            
        Returns:
            Created model instance
            
        Raises:
            DuplicateError: If entity violates unique constraints
            RepositoryException: For other database errors
        """
        try:
            # Convert Pydantic model to dict
            obj_data = obj_in.model_dump(exclude_unset=True)
            
            # Add organization ID if applicable
            if self._organization_id_field and organization_id:
                obj_data[self._organization_id_field] = organization_id
            
            # Add any additional fields
            obj_data.update(kwargs)
            
            # Create model instance
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            if "unique" in str(e).lower():
                raise DuplicateError(f"Entity already exists: {e}")
            raise RepositoryException(f"Database integrity error: {e}")
        except SQLAlchemyError as e:
            await db.rollback()
            raise RepositoryException(f"Database error: {e}")
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: Any,
        organization_id: Optional[str] = None,
        load_options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        """Get entity by ID.
        
        Args:
            db: Database session
            id: Entity ID
            organization_id: Organization ID for multi-tenancy
            load_options: SQLAlchemy load options (e.g., selectinload)
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        
        # Apply organization filter
        query = self._apply_organization_filter(query, organization_id)
        
        # Apply load options
        if load_options:
            for option in load_options:
                query = query.options(option)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_or_404(
        self,
        db: AsyncSession,
        *,
        id: Any,
        organization_id: Optional[str] = None,
        load_options: Optional[List[Any]] = None
    ) -> ModelType:
        """Get entity by ID or raise NotFoundError.
        
        Args:
            db: Database session
            id: Entity ID
            organization_id: Organization ID for multi-tenancy
            load_options: SQLAlchemy load options
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If entity not found
        """
        obj = await self.get(
            db,
            id=id,
            organization_id=organization_id,
            load_options=load_options
        )
        if not obj:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return obj
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None,
        load_options: Optional[List[Any]] = None
    ) -> List[ModelType]:
        """Get multiple entities with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            organization_id: Organization ID for multi-tenancy
            filters: Additional filters as field:value dict
            order_by: List of order_by clauses
            load_options: SQLAlchemy load options
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply organization filter
        query = self._apply_organization_filter(query, organization_id)
        
        # Apply additional filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    filter_clauses.append(getattr(self.model, field) == value)
            if filter_clauses:
                query = query.where(and_(*filter_clauses))
        
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
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        partial: bool = True
    ) -> ModelType:
        """Update an entity.
        
        Args:
            db: Database session
            db_obj: Model instance to update
            obj_in: Pydantic schema with update data
            partial: If True, only update provided fields
            
        Returns:
            Updated model instance
            
        Raises:
            RepositoryException: For database errors
        """
        try:
            # Get update data
            if partial:
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in.model_dump()
            
            # Update model attributes
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise RepositoryException(f"Database error: {e}")
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: Any,
        organization_id: Optional[str] = None
    ) -> bool:
        """Delete an entity by ID.
        
        Args:
            db: Database session
            id: Entity ID
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryException: For database errors
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            
            # Apply organization filter
            if self._organization_id_field and organization_id:
                query = query.where(
                    getattr(self.model, self._organization_id_field) == organization_id
                )
            
            result = await db.execute(query)
            await db.flush()
            
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            raise RepositoryException(f"Database error: {e}")
    
    async def count(
        self,
        db: AsyncSession,
        *,
        organization_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count entities.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenancy
            filters: Additional filters as field:value dict
            
        Returns:
            Count of entities
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply organization filter
        query = self._apply_organization_filter(query, organization_id)
        
        # Apply additional filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    filter_clauses.append(getattr(self.model, field) == value)
            if filter_clauses:
                query = query.where(and_(*filter_clauses))
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def exists(
        self,
        db: AsyncSession,
        *,
        id: Any,
        organization_id: Optional[str] = None
    ) -> bool:
        """Check if entity exists.
        
        Args:
            db: Database session
            id: Entity ID
            organization_id: Organization ID for multi-tenancy
            
        Returns:
            True if exists, False otherwise
        """
        query = select(func.count()).select_from(self.model).where(
            self.model.id == id
        )
        
        # Apply organization filter
        query = self._apply_organization_filter(query, organization_id)
        
        result = await db.execute(query)
        count = result.scalar_one()
        return count > 0 