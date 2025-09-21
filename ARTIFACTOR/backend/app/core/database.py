"""
ARTIFACTOR v3.0 - Database Configuration
SQLAlchemy with PostgreSQL and async support
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# =====================================
# DATABASE ENGINE CONFIGURATION
# =====================================

# Convert sync DATABASE_URL to async for asyncpg
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Async engine for FastAPI
async_engine = create_async_engine(
    async_database_url,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Sync engine for migrations and maintenance
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# =====================================
# BASE MODEL CONFIGURATION
# =====================================

# Naming convention for constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

# =====================================
# DATABASE UTILITIES
# =====================================

async def create_db_and_tables():
    """Create database tables"""
    try:
        async with async_engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import (  # noqa: F401
                user,
                artifact,
                collaboration,
                plugin,
                ml_model,
                search_index,
            )

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


def get_sync_session():
    """
    Get sync database session for migrations and maintenance
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


# =====================================
# DATABASE HEALTH CHECK
# =====================================

async def check_database_health() -> bool:
    """
    Check database connectivity and health
    """
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            row = result.fetchone()
            return row is not None and row[0] == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# =====================================
# DATABASE MIGRATION UTILITIES
# =====================================

def run_migrations():
    """
    Run database migrations (called from CLI or startup)
    """
    try:
        from alembic import command
        from alembic.config import Config

        # Load Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


# =====================================
# DATABASE BACKUP UTILITIES
# =====================================

async def backup_database(backup_path: str) -> bool:
    """
    Create database backup
    """
    try:
        import subprocess
        import os
        from urllib.parse import urlparse

        # Parse database URL
        parsed = urlparse(settings.DATABASE_URL)

        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password

        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading slash
            '-f', backup_path,
            '--verbose',
            '--compress=9',
        ]

        # Execute backup
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Database backup created successfully: {backup_path}")
            return True
        else:
            logger.error(f"Database backup failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Database backup error: {e}")
        return False


async def restore_database(backup_path: str) -> bool:
    """
    Restore database from backup
    """
    try:
        import subprocess
        import os
        from urllib.parse import urlparse

        # Parse database URL
        parsed = urlparse(settings.DATABASE_URL)

        # Build psql command
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password

        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading slash
            '-f', backup_path,
            '--verbose',
        ]

        # Execute restore
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Database restored successfully from: {backup_path}")
            return True
        else:
            logger.error(f"Database restore failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Database restore error: {e}")
        return False


# =====================================
# CONNECTION POOL MONITORING
# =====================================

def get_connection_pool_status():
    """
    Get connection pool status for monitoring
    """
    try:
        pool = async_engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    except Exception as e:
        logger.error(f"Failed to get connection pool status: {e}")
        return None