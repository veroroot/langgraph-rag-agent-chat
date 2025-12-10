"""FastAPI application entry point."""
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.db import init_db, get_session
from backend.core.limiter import setup_rate_limiter
from backend.core.middleware import RequestIDMiddleware, LoggingMiddleware
from backend.core.logging import logger
from backend.core.metrics import setup_metrics
from backend.api.v1.routers import api_router

# Suppress Pydantic V1 compatibility warning for Python 3.14+
# This is safe as LangChain uses Pydantic V2 for actual functionality
warnings.filterwarnings(
    "ignore",
    message=".*Core Pydantic V1 functionality isn't compatible with Python 3.14.*",
    category=UserWarning,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down application...")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="LangChain LangGraph Agent API",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.openapi_schema = custom_openapi()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# Setup rate limiting
setup_rate_limiter(app)

# Setup Prometheus metrics
setup_metrics(app)

# Include routers
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LangChain LangGraph Agent API",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )



