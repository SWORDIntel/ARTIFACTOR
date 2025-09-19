"""
Configuration settings for ARTIFACTOR v3.0 Backend
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    APP_NAME: str = "ARTIFACTOR v3.0"
    VERSION: str = "3.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database settings
    DATABASE_URL: str = "postgresql://artifactor:artifactor@localhost/artifactor_v3"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # File storage settings
    UPLOAD_DIRECTORY: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".md", ".txt",
        ".json", ".yaml", ".yml", ".xml", ".csv", ".sql", ".sh", ".bat",
        ".dockerfile", ".env", ".gitignore", ".conf", ".ini"
    ]

    # Agent coordination settings
    AGENT_BRIDGE_ENABLED: bool = True
    AGENT_COORDINATION_TIMEOUT: int = 30
    AGENT_HEALTH_CHECK_INTERVAL: int = 60
    PRESERVE_V2_COMPATIBILITY: bool = True

    # Performance settings
    MAX_CONCURRENT_USERS: int = 100
    CACHE_TTL: int = 300  # 5 minutes
    WEBSOCKET_HEARTBEAT: int = 30

    # v2.0 Compatibility settings
    V2_COORDINATION_ENABLED: bool = True
    V2_OPTIMIZATION_LEVEL: float = 99.7  # Preserve 99.7% optimization
    PYGUI_BRIDGE_ENABLED: bool = True
    PYTHON_INTERNAL_BRIDGE_ENABLED: bool = True
    DEBUGGER_BRIDGE_ENABLED: bool = True

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "artifactor_v3.log"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Ensure upload directory exists
upload_path = Path(settings.UPLOAD_DIRECTORY)
upload_path.mkdir(exist_ok=True)

# Database URL validation and fallback
def get_database_url() -> str:
    """Get database URL with environment-specific fallbacks"""

    # Check for explicit DATABASE_URL
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    # Check for component-based database config
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "artifactor_v3")
    db_user = os.getenv("DB_USER", "artifactor")
    db_password = os.getenv("DB_PASSWORD", "artifactor")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Update settings with dynamic database URL
settings.DATABASE_URL = get_database_url()