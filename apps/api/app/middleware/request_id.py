"""
Request ID middleware for request tracking and correlation.
"""
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import bind_request_context, logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request IDs to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add request ID.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with X-Request-ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Get user info from request if available
        user_id = None
        organization_id = None
        
        # This would be populated by authentication middleware
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        if hasattr(request.state, "organization_id"):
            organization_id = request.state.organization_id
        
        # Bind logging context
        request_logger = bind_request_context(
            request_id=request_id,
            user_id=user_id,
            organization_id=organization_id
        )
        
        # Log request
        request_logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            request_logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            
            return response
            
        except Exception as e:
            # Log error
            request_logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__
            )
            raise 