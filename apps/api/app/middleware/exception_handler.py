"""
Exception handler middleware for FastAPI.
"""
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    WediException,
    NotFoundError,
    DuplicateError,
    ValidationError as WediValidationError,
)
from app.core.logging import logger, sanitize_sensitive_data


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracing
        
    Returns:
        JSONResponse with error details
    """
    content = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    if request_id:
        content["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def wedi_exception_handler(request: Request, exc: WediException) -> JSONResponse:
    """Handle WediException and its subclasses.
    
    Args:
        request: FastAPI request
        exc: WediException instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID from headers or generate one
    request_id = request.headers.get("X-Request-ID", str(request.state.request_id))
    
    # Log the exception
    logger.error(
        "wedi_exception",
        error_code=exc.code,
        error_message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return create_error_response(
        error_code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with validation error details
    """
    request_id = request.headers.get("X-Request-ID", str(request.state.request_id))
    
    # Extract validation errors
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = {
            "type": error["type"],
            "message": error["msg"]
        }
    
    # Log validation error
    logger.warning(
        "validation_error",
        errors=errors,
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Invalid request data",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        request_id=request_id
    )


async def http_exception_handler_custom(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle FastAPI HTTPException.
    
    Args:
        request: FastAPI request
        exc: HTTPException instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.headers.get("X-Request-ID", str(request.state.request_id))
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # Log the exception
    log_level = "error" if exc.status_code >= 500 else "warning"
    getattr(logger, log_level)(
        "http_exception",
        error_code=error_code,
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return create_error_response(
        error_code=error_code,
        message=exc.detail,
        status_code=exc.status_code,
        request_id=request_id
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy exceptions.
    
    Args:
        request: FastAPI request
        exc: SQLAlchemyError instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.headers.get("X-Request-ID", str(request.state.request_id))
    
    # Handle specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        # Extract constraint information if available
        constraint_info = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        
        # Log the error
        logger.error(
            "database_integrity_error",
            error=constraint_info,
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        # Check for common constraint violations
        if "duplicate key" in constraint_info.lower():
            return create_error_response(
                error_code="DUPLICATE_RESOURCE",
                message="Resource already exists",
                status_code=status.HTTP_409_CONFLICT,
                details={"constraint": constraint_info},
                request_id=request_id
            )
        elif "foreign key" in constraint_info.lower():
            return create_error_response(
                error_code="INVALID_REFERENCE",
                message="Referenced resource does not exist",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"constraint": constraint_info},
                request_id=request_id
            )
    
    # Generic database error
    logger.error(
        "database_error",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return create_error_response(
        error_code="DATABASE_ERROR",
        message="A database error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.headers.get("X-Request-ID", str(request.state.request_id))
    
    # Log the unexpected error with full traceback
    logger.error(
        "unexpected_error",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    # Don't expose internal errors in production
    message = "An unexpected error occurred"
    details = None
    
    from app.config import settings
    if settings.ENVIRONMENT != "production":
        message = str(exc)
        details = {"error_type": type(exc).__name__}
    
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom exceptions
    app.add_exception_handler(WediException, wedi_exception_handler)
    
    # FastAPI exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler_custom)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler_custom)
    
    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # General exception handler (catch-all)
    app.add_exception_handler(Exception, general_exception_handler) 