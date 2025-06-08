"""
Database session management using SQLAlchemy 2.0 with async support.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str):
        """Initialize the database manager.
        
        Args:
            database_url: PostgreSQL connection URL with asyncpg driver
        """
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            # Use NullPool for serverless environments
            poolclass=NullPool if settings.ENVIRONMENT == "production" else None,
        )
        
        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Don't auto-flush before queries
            autocommit=False,  # Use transactions
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope for database operations.
        
        Yields:
            AsyncSession: Database session
            
        Example:
            async with db_manager.session() as session:
                # Use session for database operations
                result = await session.execute(select(User))
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager(settings.DATABASE_URL)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    This is used in FastAPI dependency injection.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session
    """
    async with db_manager.session() as session:
        yield session 