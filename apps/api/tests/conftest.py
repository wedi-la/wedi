"""
Global test configuration and fixtures for FastAPI testing.
"""
import asyncio
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import NullPool, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.main import create_application

# Override settings for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    test_settings = settings
    test_settings.DATABASE_URL = TEST_DATABASE_URL
    test_settings.DEBUG = True
    test_settings.JWT_SECRET_KEY = "test-secret-key"
    test_settings.FRONTEND_URL = "http://localhost:3000"
    test_settings.ALLOWED_HOSTS = ["testserver"]
    return test_settings


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
def sync_engine():
    """Create a synchronous test database engine for factories."""
    engine = create_engine(
        TEST_SYNC_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    return engine


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def sync_db_session(sync_engine) -> Generator[Session, None, None]:
    """Create a synchronous database session for factories."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest_asyncio.fixture(scope="function")
async def app(test_settings, db_session):
    """Create a test FastAPI application."""
    app = create_application()
    
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for making requests."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Generate test user data."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "display_name": "Test User",
        "wallet_address": f"0x{uuid.uuid4().hex[:40]}",
    }


@pytest.fixture
def test_organization_data():
    """Generate test organization data."""
    return {
        "name": f"Test Org {uuid.uuid4().hex[:8]}",
        "display_name": "Test Organization",
        "description": "A test organization",
        "settings": {
            "currency": "USD",
            "timezone": "UTC",
        },
    }


@pytest.fixture
def test_payment_link_data():
    """Generate test payment link data."""
    return {
        "title": "Test Payment",
        "description": "Test payment description",
        "amount": 100.00,
        "currency": "USD",
        "recipient_wallet": f"0x{uuid.uuid4().hex[:40]}",
        "metadata": {
            "test": True,
        },
    }


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for a test user."""
    # This would be implemented with actual JWT generation
    # For now, returning a mock header
    return {
        "Authorization": f"Bearer test-token-{test_user.id}"
    }


# Import get_db from the correct location
from app.db.session import get_db 