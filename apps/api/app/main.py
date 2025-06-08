"""
Wedi Pay API - Main Application Module
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from .models import Base

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    print("Starting Wedi Pay API...")
    # Initialize database connections, Redis, Kafka, etc.
    
    yield
    
    # Shutdown
    print("Shutting down Wedi Pay API...")
    # Close database connections, Redis, Kafka, etc.


app = FastAPI(
    title="Wedi Pay API",
    description="AI-native payment orchestration platform API",
    version="0.0.1",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Wedi Pay API",
        "version": "0.0.1",
        "status": "running"
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "wedi-pay-api",
            "version": "0.0.1"
        }
    )


# Import and include routers here
# from app.routers import auth, organizations, payments, webhooks
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
# app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
# app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"]) 