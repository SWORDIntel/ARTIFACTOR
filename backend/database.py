"""
Database configuration and models for ARTIFACTOR v3.0
PostgreSQL with SQLAlchemy async support
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import asyncio
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    poolclass=NullPool if settings.DEBUG else None,
    echo=settings.DEBUG,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from . import models  # noqa

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def get_database() -> AsyncSession:
    """Get database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db():
    """Close database connections"""
    await engine.dispose()

# Migration utilities
class Migration:
    """Database migration utilities for v2.0 to v3.0 transition"""

    @staticmethod
    async def migrate_from_v2(v2_data_path: str = None):
        """Migrate data from v2.0 file-based system to PostgreSQL"""
        try:
            logger.info("Starting migration from v2.0 to v3.0...")

            # Import v2.0 data structures
            from .migration.v2_importer import V2DataImporter

            importer = V2DataImporter(v2_data_path)

            async with AsyncSessionLocal() as session:
                # Migrate artifacts
                artifacts_migrated = await importer.migrate_artifacts(session)
                logger.info(f"Migrated {artifacts_migrated} artifacts")

                # Migrate user data
                users_migrated = await importer.migrate_users(session)
                logger.info(f"Migrated {users_migrated} users")

                # Migrate settings and configurations
                configs_migrated = await importer.migrate_configurations(session)
                logger.info(f"Migrated {configs_migrated} configurations")

                await session.commit()

            logger.info("Migration completed successfully")
            return {
                "status": "success",
                "artifacts_migrated": artifacts_migrated,
                "users_migrated": users_migrated,
                "configs_migrated": configs_migrated
            }

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    @staticmethod
    async def validate_migration():
        """Validate migration integrity"""
        try:
            async with AsyncSessionLocal() as session:
                # Count migrated data
                from .models import Artifact, User
                from sqlalchemy import select

                artifact_count = await session.scalar(select(func.count(Artifact.id)))
                user_count = await session.scalar(select(func.count(User.id)))

                logger.info(f"Validation: {artifact_count} artifacts, {user_count} users")

                return {
                    "artifact_count": artifact_count,
                    "user_count": user_count,
                    "status": "valid"
                }

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            raise

# Performance monitoring
class DatabaseMonitor:
    """Database performance monitoring"""

    @staticmethod
    async def get_performance_stats():
        """Get database performance statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Get connection pool stats
                pool = engine.pool

                stats = {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid(),
                }

                # Test query performance
                import time
                start_time = time.time()
                await session.execute("SELECT 1")
                query_time = time.time() - start_time

                stats["query_response_time"] = query_time

                return stats

        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {"error": str(e)}

# Database health check
async def check_database_health():
    """Check database connection and health"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}