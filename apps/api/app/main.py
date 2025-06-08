"""
Wedi Pay API - Main Application Module

This module initializes the FastAPI application with all middleware,
routers, and configurations needed for the payment orchestration platform.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import init_db, close_db
from app.events.config import shutdown_event_publisher, startup_event_publisher
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.multi_tenancy import MultiTenancyMiddleware
from app.middleware.request_id import RequestIDMiddleware

# Import routers when they exist
# from app.api.v1 import auth, organizations, users, payment_links, payment_orders

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles initialization and cleanup of:
    - Database connections
    - Event publisher (Redpanda/Kafka)
    - Background tasks
    - External service connections
    """
    # Startup
    logger.info("Starting Wedi Pay API...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize event publisher
        await startup_event_publisher()
        logger.info("Event publisher initialized")
        
        # TODO: Initialize other services
        # - Redis for caching
        # - Background task workers
        # - External API clients
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Wedi Pay API...")
    
    try:
        # Shutdown event publisher
        await shutdown_event_publisher()
        logger.info("Event publisher shut down")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        # TODO: Cleanup other services
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Wedi Pay API",
        description="AI-native payment orchestration platform API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )
    
    # Add middleware stack (order matters - applied in reverse)
    
    # Request ID middleware (should be first to process)
    app.add_middleware(RequestIDMiddleware)
    
    # JWT Authentication middleware
    app.add_middleware(JWTAuthMiddleware)
    
    # Multi-tenancy middleware (after auth to use user context)
    app.add_middleware(MultiTenancyMiddleware)
    
    # Trusted host middleware for security
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # Setup exception handlers
    register_exception_handlers(app)
    
    # Register API routers
    # TODO: Uncomment as routers are implemented
    # from app.api.v1 import auth, organizations, users, agents, payment_links, payment_orders, customers, products, webhooks
    
    # API v1 routes
    # app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    # app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
    # app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    # app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    # app.include_router(payment_links.router, prefix="/api/v1/payment-links", tags=["Payment Links"])
    # app.include_router(payment_orders.router, prefix="/api/v1/payment-orders", tags=["Payment Orders"])
    # app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
    # app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
    # app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
    
    # Root endpoints
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        """Root endpoint."""
        return {
            "name": "Wedi Pay API",
            "version": settings.APP_VERSION,
            "status": "running",
            "environment": settings.ENVIRONMENT,
        }
    
    @app.get("/health", include_in_schema=False)
    async def health_check() -> JSONResponse:
        """
        Health check endpoint.
        
        Returns basic service health status.
        TODO: Add database and service connectivity checks.
        """
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "wedi-pay-api",
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )
    
    @app.get("/api/v1/status", tags=["System"])
    async def api_status() -> dict:
        """
        API status endpoint with more detailed information.
        
        Returns:
            Detailed API status including version and capabilities
        """
        return {
            "status": "operational",
            "version": settings.APP_VERSION,
            "api_version": "v1",
            "features": {
                "authentication": True,
                "multi_tenancy": True,
                "event_streaming": True,
                "webhooks": True,
            },
            "supported_payment_providers": [
                "yoint",
                "trubit",
            ],
            "supported_countries": {
                "collection": ["CO"],
                "payout": ["MX"],
            }
        }
    
    return app


# Create the application instance
app = create_application()

# For debugging in development
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug" if settings.ENVIRONMENT == "development" else "info",
    ) 