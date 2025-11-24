"""Rate limiting configuration using slowapi."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from backend.core.config import settings


def get_limiter_key(request: Request) -> str:
    """Get rate limiter key from request.
    
    Priority:
    1. User ID from JWT token (if authenticated)
    2. IP address (fallback)
    """
    # TODO: Extract user_id from JWT token if available
    # For now, use IP address
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
)


def setup_rate_limiter(app):
    """Setup rate limiter on FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



