"""
ARTIFACTOR v3.0 Backend
FastAPI application with PostgreSQL integration and agent coordination bridge
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Optional

from .config import settings
from .database import init_db, get_database
from .routers import auth, artifacts, users, plugins, ml_classification, semantic_search, collaboration
from .models import User, Artifact
from .services.agent_bridge import AgentCoordinationBridge
from .services.plugin_manager import PluginManager
from .services.ml_pipeline import ml_pipeline
from .services.websocket_manager import websocket_manager
from .services.presence_tracker import PresenceTracker
from .services.notification_service import NotificationService
from .middleware.security import SecurityMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service instances
agent_bridge: Optional[AgentCoordinationBridge] = None
plugin_manager: Optional[PluginManager] = None
presence_tracker: Optional[PresenceTracker] = None
notification_service: Optional[NotificationService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks"""
    global agent_bridge, plugin_manager, presence_tracker, notification_service

    # Startup
    logger.info("Starting ARTIFACTOR v3.0 Backend...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize collaboration services
    presence_tracker = PresenceTracker()
    await presence_tracker.initialize()
    logger.info("Presence tracker initialized")

    notification_service = NotificationService()
    await notification_service.initialize()
    logger.info("Notification service initialized")

    # Initialize WebSocket manager
    await websocket_manager.initialize()
    logger.info("WebSocket manager initialized")

    # Initialize agent coordination bridge
    agent_bridge = AgentCoordinationBridge()
    await agent_bridge.initialize()
    logger.info("Agent coordination bridge initialized")

    # Initialize plugin manager
    plugin_manager = PluginManager(agent_bridge)
    await plugin_manager.initialize()
    logger.info("Plugin manager initialized")

    # Initialize plugin router with dependencies
    await plugins.initialize_plugin_router(agent_bridge)
    logger.info("Plugin router initialized")

    # Initialize ML pipeline and services
    await ml_pipeline.initialize()
    logger.info("ML pipeline initialized")

    yield

    # Shutdown
    logger.info("Shutting down ARTIFACTOR v3.0 Backend...")
    if plugin_manager:
        await plugin_manager.cleanup()
    if agent_bridge:
        await agent_bridge.cleanup()
    if websocket_manager:
        await websocket_manager.cleanup()
    if presence_tracker:
        await presence_tracker.cleanup()
    if notification_service:
        await notification_service.cleanup()
    # Shutdown ML pipeline
    await ml_pipeline.shutdown()
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="ARTIFACTOR v3.0 API",
    description="Web-enabled artifact management system with agent coordination",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Security middleware
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(SecurityMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
app.include_router(ml_classification.router, prefix="/api/ml", tags=["ml-classification"])
app.include_router(semantic_search.router, prefix="/api/search", tags=["semantic-search"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["collaboration"])

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "ARTIFACTOR v3.0",
        "version": "3.0.0",
        "description": "Web-enabled artifact management system with plugin ecosystem",
        "status": "operational",
        "agent_bridge_status": "active" if agent_bridge and agent_bridge.is_active else "inactive",
        "plugin_system_status": "active" if plugin_manager else "inactive",
        "features": [
            "artifact_management",
            "agent_coordination",
            "plugin_ecosystem",
            "real_time_collaboration",
            "security_framework",
            "ml_classification",
            "semantic_search",
            "smart_tagging"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = await get_database()
        await db.execute("SELECT 1")

        # Check agent bridge
        bridge_status = agent_bridge.get_status() if agent_bridge else {"status": "inactive"}

        return {
            "status": "healthy",
            "database": "connected",
            "agent_bridge": bridge_status,
            "version": "3.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# WebSocket endpoints are now handled by the collaboration router

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )