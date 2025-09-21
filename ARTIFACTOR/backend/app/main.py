"""
ARTIFACTOR v3.0 - FastAPI Backend Application
Enterprise-grade Claude.ai artifact management platform
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import create_db_and_tables, engine
from app.core.logging import setup_logging
from app.core.redis import redis_client
from app.services.ml_service import MLService

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Log request
        logger.info(
            f"Request: {request.method} {request.url}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            }
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "method": request.method,
                "url": str(request.url),
            }
        )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting ARTIFACTOR v3.0 Backend...")

    try:
        # Initialize database
        logger.info("Initializing database...")
        await create_db_and_tables()

        # Initialize Redis
        logger.info("Connecting to Redis...")
        await redis_client.ping()
        logger.info("Redis connection established")

        # Initialize ML Service
        if settings.ENABLE_ML_CLASSIFICATION:
            logger.info("Initializing ML services...")
            ml_service = MLService()
            await ml_service.initialize()
            app.state.ml_service = ml_service
            logger.info("ML services initialized")

        logger.info("Application startup completed successfully")

        yield

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    finally:
        # Cleanup
        logger.info("Shutting down application...")

        # Close database connections
        if hasattr(engine, 'dispose'):
            await engine.dispose()

        # Close Redis connections
        await redis_client.close()

        # Cleanup ML service
        if hasattr(app.state, 'ml_service'):
            await app.state.ml_service.cleanup()

        logger.info("Application shutdown completed")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Enterprise-grade Claude.ai artifact management platform",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # Add middleware (order matters!)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately in production
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(LoggingMiddleware)

    # Add Prometheus metrics
    if settings.ENABLE_METRICS:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            excluded_handlers=["/health", "/metrics"],
        )
        instrumentator.instrument(app).expose(app, endpoint="/metrics")

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


# Create application instance
app = create_application()


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        # Check database
        db_status = "healthy"
        try:
            # Simple query to check database connectivity
            # This would use your database connection
            pass
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check Redis
        redis_status = "healthy"
        try:
            await redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        # Check ML service
        ml_status = "disabled"
        if settings.ENABLE_ML_CLASSIFICATION and hasattr(app.state, 'ml_service'):
            try:
                ml_status = "healthy" if app.state.ml_service.is_ready() else "initializing"
            except Exception as e:
                ml_status = f"unhealthy: {str(e)}"

        # Overall status
        overall_status = "healthy"
        if "unhealthy" in [db_status, redis_status, ml_status]:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": db_status,
                "redis": redis_status,
                "ml_service": ml_status,
            },
            "features": {
                "ml_classification": settings.ENABLE_ML_CLASSIFICATION,
                "semantic_search": settings.ENABLE_SEMANTIC_SEARCH,
                "metrics": settings.ENABLE_METRICS,
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": settings.VERSION,
            }
        )


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "message": "ARTIFACTOR v3.0 - Enterprise Claude.ai Artifact Management Platform",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "metrics": "/metrics" if settings.ENABLE_METRICS else None,
        "features": {
            "ml_classification": settings.ENABLE_ML_CLASSIFICATION,
            "semantic_search": settings.ENABLE_SEMANTIC_SEARCH,
            "real_time_collaboration": True,
            "plugin_system": True,
            "mobile_pwa": True,
        },
        "api": {
            "base_url": settings.API_V1_STR,
            "endpoints": {
                "authentication": f"{settings.API_V1_STR}/auth",
                "artifacts": f"{settings.API_V1_STR}/artifacts",
                "users": f"{settings.API_V1_STR}/users",
                "collaboration": f"{settings.API_V1_STR}/collaboration",
                "plugins": f"{settings.API_V1_STR}/plugins",
                "ml": f"{settings.API_V1_STR}/ml",
                "websocket": f"{settings.API_V1_STR}/ws",
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting ARTIFACTOR v{settings.VERSION} in {settings.ENVIRONMENT} mode")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )