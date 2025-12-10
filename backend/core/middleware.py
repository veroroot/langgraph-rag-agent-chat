"""Custom middleware for FastAPI."""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.logging import logger, structured_logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request and response details."""
    
    # Paths to exclude from logging or log at DEBUG level
    HEALTH_CHECK_PATHS = ["/health", "/"]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        
        # Skip logging for health check endpoints (or log at DEBUG level)
        is_health_check = path in self.HEALTH_CHECK_PATHS
        
        request_id = getattr(request.state, 'request_id', None)
        client_host = request.client.host if request.client else 'unknown'
        
        if not is_health_check:
            # Log request with structured fields
            structured_logger.info(
                "Incoming request",
                method=request.method,
                path=path,
                client=client_host,
                request_id=request_id,
            )
        else:
            # Log health checks at DEBUG level only
            logger.debug(
                f"Health check: {request.method} {path}"
            )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        
        if not is_health_check:
            structured_logger.info(
                "Request completed",
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration=f"{process_time:.3f}s",
                request_id=request_id,
            )
        else:
            logger.debug(
                f"Health check response: {response.status_code} - Time: {process_time:.3f}s"
            )
        
        return response



