"""
ARTIFACTOR v3.0 - Configuration Management
Centralized configuration using Pydantic Settings
"""

import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, Field, validator


class Settings(BaseSettings):
    """Application settings"""

    # =====================================
    # PROJECT INFORMATION
    # =====================================
    PROJECT_NAME: str = "ARTIFACTOR"
    VERSION: str = "3.0.0"
    DESCRIPTION: str = "Enterprise Claude.ai Artifact Management Platform"
    API_V1_STR: str = "/api/v1"

    # =====================================
    # ENVIRONMENT
    # =====================================
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")

    # =====================================
    # SECURITY
    # =====================================
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=10080, env="REFRESH_TOKEN_EXPIRE_MINUTES")  # 7 days
    ALGORITHM: str = "HS256"

    # =====================================
    # DATABASE
    # =====================================
    DATABASE_URL: str = Field(
        default="postgresql://artifactor:artifactor123@localhost:5432/artifactor",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")

    # =====================================
    # REDIS
    # =====================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=20, env="REDIS_POOL_SIZE")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")

    # =====================================
    # CORS SETTINGS
    # =====================================
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "https://artifactor.app",
        ],
        env="BACKEND_CORS_ORIGINS"
    )

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # =====================================
    # OAUTH SETTINGS
    # =====================================
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None, env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None, env="GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = Field(
        default="http://localhost:3000/auth/callback",
        env="GITHUB_REDIRECT_URI"
    )

    # =====================================
    # FILE STORAGE
    # =====================================
    UPLOAD_PATH: str = Field(default="/app/uploads", env="UPLOAD_PATH")
    DOWNLOAD_PATH: str = Field(default="/app/downloads", env="DOWNLOAD_PATH")
    MAX_UPLOAD_SIZE: int = Field(default=104857600, env="MAX_UPLOAD_SIZE")  # 100MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[
            ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
            ".json", ".yaml", ".yml", ".xml", ".md", ".txt", ".csv",
            ".sql", ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
            ".dockerfile", ".dockerignore", ".gitignore", ".env",
            ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".php",
            ".rb", ".go", ".rs", ".swift", ".kt", ".scala", ".clj",
            ".vim", ".lua", ".r", ".m", ".pl", ".pm", ".tcl",
            ".zip", ".tar", ".gz", ".7z", ".rar",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico",
            ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"
        ]
    )

    # =====================================
    # ML CONFIGURATION
    # =====================================
    ENABLE_ML_CLASSIFICATION: bool = Field(default=True, env="ENABLE_ML_CLASSIFICATION")
    ENABLE_SEMANTIC_SEARCH: bool = Field(default=True, env="ENABLE_SEMANTIC_SEARCH")
    ML_MODEL_PATH: str = Field(default="/app/models", env="ML_MODEL_PATH")
    ML_SERVICE_URL: str = Field(default="http://ml-service:8001", env="ML_SERVICE_URL")

    # Classification Models
    CLASSIFICATION_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="CLASSIFICATION_MODEL"
    )
    CLASSIFICATION_THRESHOLD: float = Field(default=0.75, env="CLASSIFICATION_THRESHOLD")

    # Search Configuration
    SEARCH_INDEX_PATH: str = Field(default="/app/search_index", env="SEARCH_INDEX_PATH")
    SEARCH_EMBEDDING_DIM: int = Field(default=384, env="SEARCH_EMBEDDING_DIM")
    FAISS_INDEX_TYPE: str = Field(default="IVFFlat", env="FAISS_INDEX_TYPE")
    FAISS_NLIST: int = Field(default=100, env="FAISS_NLIST")

    # =====================================
    # WEBSOCKET SETTINGS
    # =====================================
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    WEBSOCKET_TIMEOUT: int = Field(default=60, env="WEBSOCKET_TIMEOUT")

    # =====================================
    # WORKER CONFIGURATION
    # =====================================
    WORKERS: int = Field(default=4, env="WORKERS")
    MAX_WORKERS: int = Field(default=16, env="MAX_WORKERS")
    WORKER_CONNECTIONS: int = Field(default=1000, env="WORKER_CONNECTIONS")
    KEEPALIVE: int = Field(default=2, env="KEEPALIVE")

    # =====================================
    # CELERY CONFIGURATION
    # =====================================
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/2", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/3", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    # =====================================
    # MONITORING & METRICS
    # =====================================
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # =====================================
    # RATE LIMITING
    # =====================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")

    # =====================================
    # CACHE SETTINGS
    # =====================================
    CACHE_DEFAULT_TIMEOUT: int = Field(default=300, env="CACHE_DEFAULT_TIMEOUT")  # 5 minutes
    CACHE_ML_RESULTS_TIMEOUT: int = Field(default=3600, env="CACHE_ML_RESULTS_TIMEOUT")  # 1 hour
    CACHE_SEARCH_RESULTS_TIMEOUT: int = Field(default=1800, env="CACHE_SEARCH_RESULTS_TIMEOUT")  # 30 minutes

    # =====================================
    # EMAIL CONFIGURATION
    # =====================================
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, env="EMAILS_FROM_NAME")

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    # =====================================
    # PLUGIN SYSTEM
    # =====================================
    PLUGIN_DIRECTORY: str = Field(default="/app/plugins", env="PLUGIN_DIRECTORY")
    PLUGIN_SANDBOX_ENABLED: bool = Field(default=True, env="PLUGIN_SANDBOX_ENABLED")
    PLUGIN_MAX_EXECUTION_TIME: int = Field(default=300, env="PLUGIN_MAX_EXECUTION_TIME")  # 5 minutes
    PLUGIN_MAX_MEMORY: str = Field(default="512m", env="PLUGIN_MAX_MEMORY")

    # =====================================
    # BACKUP CONFIGURATION
    # =====================================
    BACKUP_ENABLED: bool = Field(default=True, env="BACKUP_ENABLED")
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = Field(default=30, env="BACKUP_RETENTION_DAYS")

    # =====================================
    # CLOUD STORAGE (S3-compatible)
    # =====================================
    S3_ENDPOINT: Optional[str] = Field(default=None, env="S3_ENDPOINT")
    S3_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(default=None, env="S3_SECRET_KEY")
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")

    # =====================================
    # LEGACY INTEGRATION
    # =====================================
    LEGACY_DOWNLOADER_ENABLED: bool = Field(default=True, env="LEGACY_DOWNLOADER_ENABLED")
    LEGACY_DOWNLOADER_PATH: str = Field(default="/app/legacy/simple-claude-downloader.py")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()