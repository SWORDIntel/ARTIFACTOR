"""
ARTIFACTOR v3.0 Secure Configuration
Complete security overhaul for the configuration system
This file replaces the existing config.py with comprehensive security measures
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os
import secrets
import logging
import re
from pathlib import Path
from datetime import datetime

# Setup security logging
logger = logging.getLogger(__name__)

class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    pass

class SecureSettings(BaseSettings):
    """Secure application settings with comprehensive validation"""

    # Application settings
    APP_NAME: str = "ARTIFACTOR v3.0"
    VERSION: str = "3.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Environment detection (CRITICAL for security)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    PRODUCTION_MODE: bool = property(lambda self: self.ENVIRONMENT == "production")

    # Database settings - NO DEFAULT CREDENTIALS
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_SSL_MODE: str = os.getenv("DATABASE_SSL_MODE", "require")
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", "30"))
    DATABASE_ENCRYPT: bool = os.getenv("DATABASE_ENCRYPT", "true").lower() == "true"

    # Security settings - ZERO DEFAULTS FOR PRODUCTION
    SECRET_KEY: str = ""  # Will be validated and set
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "1"))

    # Advanced JWT Security
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "ARTIFACTOR-v3")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "artifactor-api")
    ENABLE_JWT_BLACKLIST: bool = os.getenv("ENABLE_JWT_BLACKLIST", "true").lower() == "true"
    JWT_REQUIRE_CLAIMS: List[str] = ["iss", "aud", "exp", "iat", "sub"]

    # Password security (OWASP compliant)
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "14"))
    PASSWORD_REQUIRE_UPPER: bool = os.getenv("PASSWORD_REQUIRE_UPPER", "true").lower() == "true"
    PASSWORD_REQUIRE_LOWER: bool = os.getenv("PASSWORD_REQUIRE_LOWER", "true").lower() == "true"
    PASSWORD_REQUIRE_DIGITS: bool = os.getenv("PASSWORD_REQUIRE_DIGITS", "true").lower() == "true"
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    PASSWORD_HISTORY_SIZE: int = int(os.getenv("PASSWORD_HISTORY_SIZE", "5"))
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "14"))  # Increased for security

    # Session security
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_CONCURRENT_SESSIONS: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "2"))
    ENABLE_SESSION_ENCRYPTION: bool = os.getenv("ENABLE_SESSION_ENCRYPTION", "true").lower() == "true"

    # CORS settings - Secure by default
    ALLOWED_ORIGINS: List[str] = []  # Will be set from environment
    ALLOWED_ORIGIN_REGEX: str = os.getenv("ALLOWED_ORIGIN_REGEX", "")
    CORS_MAX_AGE: int = int(os.getenv("CORS_MAX_AGE", "86400"))

    # Security headers configuration
    ENABLE_HSTS: bool = os.getenv("ENABLE_HSTS", "true").lower() == "true"
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year
    ENABLE_CSP: bool = os.getenv("ENABLE_CSP", "true").lower() == "true"
    CSP_REPORT_URI: str = os.getenv("CSP_REPORT_URI", "/api/security/csp-report")
    CSP_ENFORCE: bool = os.getenv("CSP_ENFORCE", "true").lower() == "true"

    # File upload security (HEAVILY RESTRICTED)
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    MAX_FILES_PER_USER: int = int(os.getenv("MAX_FILES_PER_USER", "100"))
    MAX_TOTAL_STORAGE_MB: int = int(os.getenv("MAX_TOTAL_STORAGE_MB", "1000"))
    ENABLE_VIRUS_SCANNING: bool = os.getenv("ENABLE_VIRUS_SCANNING", "true").lower() == "true"
    QUARANTINE_DIRECTORY: str = os.getenv("QUARANTINE_DIRECTORY", "quarantine")
    ENABLE_FILE_CONTENT_VALIDATION: bool = os.getenv("ENABLE_FILE_CONTENT_VALIDATION", "true").lower() == "true"

    # Severely restricted file extensions
    ALLOWED_EXTENSIONS: List[str] = [
        ".txt", ".md", ".json", ".yaml", ".yml", ".xml", ".csv",
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css",
        ".dockerfile", ".conf"
    ]

    # Comprehensive blocked extensions
    BLOCKED_EXTENSIONS: List[str] = [
        # Executables
        ".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".msi", ".reg",
        ".app", ".deb", ".rpm", ".dmg", ".iso", ".img",
        # Scripts
        ".sh", ".bash", ".zsh", ".ps1", ".vbs", ".jar", ".class",
        # Security sensitive
        ".sql", ".env", ".key", ".pem", ".p12", ".pfx", ".crt", ".cer",
        ".ssh", ".aws", ".config", ".ini", ".conf", ".properties",
        # Archives (potential zip bombs)
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
        # Documents (potential macro attacks)
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf"
    ]

    # Rate limiting configuration (DDoS protection)
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "30"))
    RATE_LIMIT_REQUESTS_PER_HOUR: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "500"))
    RATE_LIMIT_BURST_SIZE: int = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
    DDoS_PROTECTION_ENABLED: bool = os.getenv("DDoS_PROTECTION_ENABLED", "true").lower() == "true"

    # Redis settings for session storage (secure)
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "true").lower() == "true"
    REDIS_SSL_VERIFY: bool = os.getenv("REDIS_SSL_VERIFY", "true").lower() == "true"

    # Agent coordination settings (secure)
    AGENT_BRIDGE_ENABLED: bool = os.getenv("AGENT_BRIDGE_ENABLED", "true").lower() == "true"
    AGENT_COORDINATION_TIMEOUT: int = int(os.getenv("AGENT_COORDINATION_TIMEOUT", "30"))
    AGENT_HEALTH_CHECK_INTERVAL: int = int(os.getenv("AGENT_HEALTH_CHECK_INTERVAL", "60"))
    PRESERVE_V2_COMPATIBILITY: bool = os.getenv("PRESERVE_V2_COMPATIBILITY", "false").lower() == "true"
    AGENT_AUTHENTICATION_REQUIRED: bool = os.getenv("AGENT_AUTHENTICATION_REQUIRED", "true").lower() == "true"

    # Performance settings
    MAX_CONCURRENT_USERS: int = int(os.getenv("MAX_CONCURRENT_USERS", "50"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    WEBSOCKET_HEARTBEAT: int = int(os.getenv("WEBSOCKET_HEARTBEAT", "30"))

    # Logging settings (security focused)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "artifactor_v3.log")
    SECURITY_LOG_FILE: Optional[str] = os.getenv("SECURITY_LOG_FILE", "security.log")
    AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "90"))
    ENABLE_LOG_ENCRYPTION: bool = os.getenv("ENABLE_LOG_ENCRYPTION", "false").lower() == "true"

    # Plugin security settings
    PLUGIN_SYSTEM_ENABLED: bool = os.getenv("PLUGIN_SYSTEM_ENABLED", "false").lower() == "true"
    PLUGIN_SANDBOX_ENABLED: bool = os.getenv("PLUGIN_SANDBOX_ENABLED", "true").lower() == "true"
    PLUGIN_SIGNATURE_VERIFICATION: bool = os.getenv("PLUGIN_SIGNATURE_VERIFICATION", "true").lower() == "true"
    PLUGIN_WHITELIST_ONLY: bool = os.getenv("PLUGIN_WHITELIST_ONLY", "true").lower() == "true"
    PLUGIN_MAX_EXECUTION_TIME: int = int(os.getenv("PLUGIN_MAX_EXECUTION_TIME", "30"))
    PLUGIN_MAX_MEMORY_MB: int = int(os.getenv("PLUGIN_MAX_MEMORY_MB", "128"))

    # Backup and recovery
    ENABLE_AUTOMATED_BACKUPS: bool = os.getenv("ENABLE_AUTOMATED_BACKUPS", "true").lower() == "true"
    BACKUP_ENCRYPTION_ENABLED: bool = os.getenv("BACKUP_ENCRYPTION_ENABLED", "true").lower() == "true"
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    # Monitoring and alerting
    ENABLE_SECURITY_MONITORING: bool = os.getenv("ENABLE_SECURITY_MONITORING", "true").lower() == "true"
    SECURITY_ALERT_EMAIL: str = os.getenv("SECURITY_ALERT_EMAIL", "")
    ENABLE_INTRUSION_DETECTION: bool = os.getenv("ENABLE_INTRUSION_DETECTION", "true").lower() == "true"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_configuration()
        self._setup_secure_defaults()

    def _validate_security_configuration(self):
        """Comprehensive security validation"""
        errors = []
        warnings = []

        # Critical environment check
        if self.ENVIRONMENT not in ["development", "staging", "production"]:
            errors.append(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}")

        # Production security requirements
        if self.ENVIRONMENT == "production":
            self._validate_production_security(errors, warnings)

        # Development security warnings
        elif self.ENVIRONMENT == "development":
            self._validate_development_security(warnings)

        self._validate_common_security(errors, warnings)

        # Log all issues
        for error in errors:
            logger.error(f"SECURITY ERROR: {error}")
        for warning in warnings:
            logger.warning(f"SECURITY WARNING: {warning}")

        # Fail fast for critical errors
        if errors:
            raise SecurityValidationError(f"Critical security errors: {'; '.join(errors)}")

    def _validate_production_security(self, errors: List[str], warnings: List[str]):
        """Validate production-specific security requirements"""
        required_vars = [
            "SECRET_KEY", "DATABASE_URL", "REDIS_URL"
        ]

        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing required production variable: {var}")

        # SECRET_KEY validation
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters in production")
        elif self._is_weak_secret(secret_key):
            errors.append("SECRET_KEY appears to be weak or default")

        # Database security
        db_url = os.getenv("DATABASE_URL", "")
        if not self._is_secure_database_url(db_url):
            warnings.append("Database URL may not be using secure connection")

        # HTTPS enforcement
        if not self.ENABLE_HSTS:
            warnings.append("HSTS disabled in production")

        # Debug mode check
        if self.DEBUG:
            errors.append("DEBUG mode must be disabled in production")

    def _validate_development_security(self, warnings: List[str]):
        """Validate development-specific security settings"""
        if not os.getenv("SECRET_KEY"):
            warnings.append("SECRET_KEY not set in development")

        if self.DEBUG and self.ENVIRONMENT != "development":
            warnings.append("DEBUG mode enabled outside development")

    def _validate_common_security(self, errors: List[str], warnings: List[str]):
        """Validate common security settings"""
        # Password policy validation
        if self.PASSWORD_MIN_LENGTH < 12:
            warnings.append("Password minimum length should be at least 12 characters")

        if self.BCRYPT_ROUNDS < 12:
            warnings.append("BCrypt rounds should be at least 12 for security")

        # Token expiration validation
        if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
            warnings.append("Access token expiration is longer than recommended")

        if self.REFRESH_TOKEN_EXPIRE_DAYS > 7:
            warnings.append("Refresh token expiration is longer than recommended")

        # CORS validation
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if "*" in allowed_origins and self.ENVIRONMENT == "production":
            errors.append("Wildcard CORS origins not allowed in production")

    def _setup_secure_defaults(self):
        """Setup secure defaults based on environment"""
        # Generate SECRET_KEY if missing in development
        if not os.getenv("SECRET_KEY") and self.ENVIRONMENT == "development":
            self.SECRET_KEY = secrets.token_urlsafe(32)
            logger.warning("Generated temporary SECRET_KEY for development")
        else:
            self.SECRET_KEY = os.getenv("SECRET_KEY", "")

        # Setup CORS origins
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            self.ALLOWED_ORIGINS = [
                origin.strip() for origin in origins_env.split(",")
                if origin.strip()
            ]
        elif self.ENVIRONMENT == "development":
            self.ALLOWED_ORIGINS = [
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        else:
            self.ALLOWED_ORIGINS = []

        # Secure database URL construction
        if not self.DATABASE_URL and self.ENVIRONMENT == "development":
            self.DATABASE_URL = self._build_secure_dev_database_url()

    def _is_weak_secret(self, secret: str) -> bool:
        """Check if secret key is weak"""
        weak_patterns = [
            "secret", "password", "key", "change-me", "default",
            "your-secret-key", "test", "dev", "development"
        ]
        return any(pattern in secret.lower() for pattern in weak_patterns)

    def _is_secure_database_url(self, url: str) -> bool:
        """Check if database URL uses secure connection"""
        if not url:
            return False
        return "sslmode=require" in url or "ssl=true" in url

    def _build_secure_dev_database_url(self) -> str:
        """Build secure database URL for development"""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "artifactor_v3_dev")
        db_user = os.getenv("DB_USER", "artifactor_dev")
        db_password = os.getenv("DB_PASSWORD", secrets.token_urlsafe(16))

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={self.DATABASE_SSL_MODE}"

def setup_secure_directories(settings_instance):
    """Setup directories with secure permissions"""
    directories = [
        settings_instance.UPLOAD_DIRECTORY,
        settings_instance.QUARANTINE_DIRECTORY,
        "logs",
        "backups"
    ]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True, mode=0o750)

        # Create security notice
        security_notice = dir_path / ".security_notice"
        if not security_notice.exists():
            security_notice.write_text(
                f"# ARTIFACTOR v3.0 Secure Directory\n"
                f"# Created: {datetime.now().isoformat()}\n"
                f"# Permissions: 0o750 (owner: rwx, group: r-x, other: ---)\n"
                f"# This directory contains sensitive data - do not modify permissions\n"
            )
            security_notice.chmod(0o640)

def generate_secure_key() -> str:
    """Generate a cryptographically secure key"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str, settings_instance) -> tuple[bool, List[str]]:
    """Validate password against security policy"""
    errors = []

    if len(password) < settings_instance.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings_instance.PASSWORD_MIN_LENGTH} characters")

    if settings_instance.PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letters")

    if settings_instance.PASSWORD_REQUIRE_LOWER and not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letters")

    if settings_instance.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
        errors.append("Password must contain digits")

    if settings_instance.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain special characters")

    # Check for common weak patterns
    weak_patterns = [
        r'(.)\1{2,}',  # Repeated characters
        r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk)',  # Sequential letters
        r'(password|123456|qwerty|admin|root|user)',  # Common passwords
    ]

    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common weak patterns")
            break

    return len(errors) == 0, errors

# Initialize secure settings
try:
    logger.info("Initializing secure configuration...")
    settings = SecureSettings()
    setup_secure_directories(settings)
    logger.info("Secure configuration initialized successfully")
except SecurityValidationError as e:
    logger.error(f"Security configuration failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error in secure configuration: {e}")
    raise

# Export utilities
__all__ = [
    'settings', 'SecureSettings', 'SecurityValidationError',
    'generate_secure_key', 'validate_password_strength',
    'setup_secure_directories'
]