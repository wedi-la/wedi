"""
Application configuration settings.
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Wedi API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/wedi"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis (for caching/sessions)
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    
    # Frontend
    FRONTEND_URL: str = "localhost:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or console
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # External services
    REDPANDA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    # Payment providers
    YOINT_API_URL: str = "https://api.yoint.com"
    YOINT_API_KEY: Optional[str] = None
    
    TRUBIT_API_URL: str = "https://api.trubit.com"
    TRUBIT_API_KEY: Optional[str] = None
    

    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        
        # Allow extra fields from environment
        extra = "allow"


# Create a singleton instance
settings = Settings()


# Validate critical settings
def validate_settings():
    """Validate that critical settings are configured."""
    errors = []
    
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "your-secret-key-here":
            errors.append("SECRET_KEY must be set in production")
        
        if not settings.DATABASE_URL:
            errors.append("DATABASE_URL must be set")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")



# Run validation on import in production
if settings.ENVIRONMENT == "production":
    validate_settings() 