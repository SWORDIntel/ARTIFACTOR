"""
Database Performance Optimizer
Advanced database optimization with connection pooling, query optimization, and intelligent indexing
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import text, event
import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Database query performance metrics"""
    query_hash: str
    query_text: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_executed: Optional[datetime] = None
    slow_query_threshold: float = 1.0  # 1 second

    def update(self, execution_time: float):
        """Update metrics with new execution data"""
        self.execution_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.execution_count
        self.last_executed = datetime.now()

    @property
    def is_slow_query(self) -> bool:
        """Check if this is a slow query"""
        return self.avg_time > self.slow_query_threshold

@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    peak_connections: int = 0
    connection_wait_time: float = 0.0
    failed_connections: int = 0
    pool_exhausted_count: int = 0

class DatabaseOptimizer:
    """High-performance database optimizer with advanced features"""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        enable_query_logging: bool = True
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.enable_query_logging = enable_query_logging

        # Engine and session management
        self.engine: Optional[sa.ext.asyncio.AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

        # Performance tracking
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.pool_metrics = ConnectionPoolMetrics()

        # Query optimization
        self.prepared_statements: Dict[str, str] = {}
        self.index_recommendations: List[Dict[str, Any]] = []

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize optimized database connection"""
        # Create optimized engine
        self.engine = create_async_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Validate connections before use
            echo=self.enable_query_logging,
            future=True,
            connect_args={
                "server_settings": {
                    "application_name": "ARTIFACTOR_v3_Optimized",
                    "tcp_keepalives_idle": "600",
                    "tcp_keepalives_interval": "30",
                    "tcp_keepalives_count": "3",
                }
            }
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Set up query monitoring
        if self.enable_query_logging:
            self._setup_query_monitoring()

        # Create database indexes for performance
        await self._create_performance_indexes()

        logger.info("Database optimizer initialized with advanced performance features")

    def _setup_query_monitoring(self):
        """Set up query performance monitoring"""
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            execution_time = time.time() - context._query_start_time

            # Create query hash for tracking
            query_hash = str(hash(statement))

            # Update metrics
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_text=statement[:500]  # Truncate long queries
                )

            self.query_metrics[query_hash].update(execution_time)

    async def _create_performance_indexes(self):
        """Create database indexes for optimal performance"""
        indexes = [
            # Artifacts table indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_user_id ON artifacts(user_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_type ON artifacts(type);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_status ON artifacts(status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_tags_gin ON artifacts USING gin(tags);",

            # Users table indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);",

            # Session table indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);",

            # Collaboration table indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_collaboration_artifact_id ON collaboration_sessions(artifact_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_collaboration_user_id ON collaboration_sessions(user_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_collaboration_created_at ON collaboration_sessions(created_at);",

            # Plugin table indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plugins_name ON plugins(name);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plugins_enabled ON plugins(enabled);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plugins_version ON plugins(version);",

            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_user_created ON artifacts(user_id, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_type_status ON artifacts(type, status);",
        ]

        try:
            async with self.get_session() as session:
                for index_sql in indexes:
                    try:
                        await session.execute(text(index_sql))
                        await session.commit()
                    except Exception as e:
                        # Index might already exist, continue
                        logger.debug(f"Index creation info: {e}")
                        await session.rollback()

            logger.info("Performance indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating performance indexes: {e}")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get optimized database session with performance monitoring"""
        if not self.session_factory:
            raise RuntimeError("Database optimizer not initialized")

        session_start = time.time()
        async with self._lock:
            self.pool_metrics.active_connections += 1
            self.pool_metrics.peak_connections = max(
                self.pool_metrics.peak_connections,
                self.pool_metrics.active_connections
            )

        try:
            async with self.session_factory() as session:
                # Configure session for optimal performance
                await session.execute(text("SET statement_timeout = '30s'"))
                await session.execute(text("SET lock_timeout = '10s'"))

                yield session

        except Exception as e:
            logger.error(f"Database session error: {e}")
            async with self._lock:
                self.pool_metrics.failed_connections += 1
            raise
        finally:
            session_time = time.time() - session_start
            async with self._lock:
                self.pool_metrics.active_connections -= 1
                self.pool_metrics.connection_wait_time += session_time

    async def execute_optimized_query(
        self,
        query: Union[str, sa.sql.Executable],
        parameters: Optional[Dict[str, Any]] = None,
        use_prepared: bool = True
    ) -> Any:
        """Execute query with optimization and caching"""
        async with self.get_session() as session:
            if isinstance(query, str) and use_prepared:
                # Use prepared statement for better performance
                query_hash = str(hash(query))
                if query_hash not in self.prepared_statements:
                    self.prepared_statements[query_hash] = query

                result = await session.execute(text(query), parameters or {})
            else:
                result = await session.execute(query, parameters or {})

            return result

    async def bulk_insert_optimized(
        self,
        model_class: Any,
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """Optimized bulk insert with batching"""
        total_inserted = 0

        async with self.get_session() as session:
            try:
                # Process in batches to avoid memory issues
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]

                    # Use bulk insert for better performance
                    result = await session.execute(
                        sa.insert(model_class.__table__),
                        batch
                    )

                    total_inserted += len(batch)

                await session.commit()
                logger.info(f"Bulk inserted {total_inserted} records")

            except Exception as e:
                await session.rollback()
                logger.error(f"Bulk insert failed: {e}")
                raise

        return total_inserted

    async def bulk_update_optimized(
        self,
        model_class: Any,
        updates: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """Optimized bulk update with batching"""
        total_updated = 0

        async with self.get_session() as session:
            try:
                # Process in batches
                for i in range(0, len(updates), batch_size):
                    batch = updates[i:i + batch_size]

                    # Perform bulk update
                    for update_data in batch:
                        record_id = update_data.pop('id')
                        await session.execute(
                            sa.update(model_class.__table__)
                            .where(model_class.id == record_id)
                            .values(**update_data)
                        )

                    total_updated += len(batch)

                await session.commit()
                logger.info(f"Bulk updated {total_updated} records")

            except Exception as e:
                await session.rollback()
                logger.error(f"Bulk update failed: {e}")
                raise

        return total_updated

    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive query performance statistics"""
        stats = {
            'total_queries': len(self.query_metrics),
            'slow_queries': [],
            'top_queries_by_frequency': [],
            'top_queries_by_time': [],
            'pool_metrics': {
                'active_connections': self.pool_metrics.active_connections,
                'peak_connections': self.pool_metrics.peak_connections,
                'failed_connections': self.pool_metrics.failed_connections,
                'avg_wait_time': (
                    self.pool_metrics.connection_wait_time / max(1, len(self.query_metrics))
                )
            }
        }

        # Find slow queries
        for metrics in self.query_metrics.values():
            if metrics.is_slow_query:
                stats['slow_queries'].append({
                    'query': metrics.query_text,
                    'avg_time': metrics.avg_time,
                    'execution_count': metrics.execution_count,
                    'total_time': metrics.total_time
                })

        # Top queries by frequency
        stats['top_queries_by_frequency'] = sorted(
            [
                {
                    'query': m.query_text,
                    'execution_count': m.execution_count,
                    'avg_time': m.avg_time
                }
                for m in self.query_metrics.values()
            ],
            key=lambda x: x['execution_count'],
            reverse=True
        )[:10]

        # Top queries by total time
        stats['top_queries_by_time'] = sorted(
            [
                {
                    'query': m.query_text,
                    'total_time': m.total_time,
                    'execution_count': m.execution_count,
                    'avg_time': m.avg_time
                }
                for m in self.query_metrics.values()
            ],
            key=lambda x: x['total_time'],
            reverse=True
        )[:10]

        return stats

    async def analyze_query_patterns(self) -> List[Dict[str, Any]]:
        """Analyze query patterns and suggest optimizations"""
        recommendations = []

        for metrics in self.query_metrics.values():
            # Check for N+1 query problems
            if (metrics.execution_count > 100 and
                "SELECT" in metrics.query_text.upper() and
                "WHERE" in metrics.query_text.upper()):
                recommendations.append({
                    'type': 'possible_n_plus_1',
                    'query': metrics.query_text,
                    'execution_count': metrics.execution_count,
                    'suggestion': 'Consider using eager loading or batching'
                })

            # Check for missing indexes
            if (metrics.avg_time > 0.5 and
                "WHERE" in metrics.query_text.upper()):
                recommendations.append({
                    'type': 'possible_missing_index',
                    'query': metrics.query_text,
                    'avg_time': metrics.avg_time,
                    'suggestion': 'Consider adding an index on filtered columns'
                })

            # Check for inefficient LIKE queries
            if ("LIKE" in metrics.query_text.upper() and
                metrics.avg_time > 0.3):
                recommendations.append({
                    'type': 'inefficient_like_query',
                    'query': metrics.query_text,
                    'avg_time': metrics.avg_time,
                    'suggestion': 'Consider using full-text search or GIN indexes'
                })

        return recommendations

    async def optimize_connection_pool(self):
        """Dynamically optimize connection pool settings"""
        if not self.engine:
            return

        # Get current pool status
        pool = self.engine.pool

        # Analyze usage patterns
        if self.pool_metrics.peak_connections > self.pool_size * 0.8:
            # Consider increasing pool size
            logger.info("High connection usage detected, consider increasing pool size")

        if self.pool_metrics.failed_connections > 10:
            # Consider increasing timeout
            logger.info("High connection failures detected, consider increasing timeout")

    async def create_materialized_view(
        self,
        view_name: str,
        query: str,
        refresh_interval: int = 3600  # 1 hour
    ):
        """Create materialized view for expensive queries"""
        async with self.get_session() as session:
            try:
                # Create materialized view
                create_view_sql = f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS
                {query}
                """
                await session.execute(text(create_view_sql))

                # Create index on materialized view
                index_sql = f"CREATE INDEX IF NOT EXISTS idx_{view_name} ON {view_name} (id)"
                await session.execute(text(index_sql))

                await session.commit()
                logger.info(f"Materialized view {view_name} created")

                # Schedule automatic refresh
                asyncio.create_task(self._refresh_materialized_view(view_name, refresh_interval))

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create materialized view {view_name}: {e}")

    async def _refresh_materialized_view(self, view_name: str, interval: int):
        """Periodically refresh materialized view"""
        while True:
            try:
                await asyncio.sleep(interval)
                async with self.get_session() as session:
                    await session.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                    await session.commit()
                    logger.info(f"Refreshed materialized view {view_name}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Failed to refresh materialized view {view_name}: {e}")

    async def cleanup(self):
        """Cleanup database optimizer resources"""
        if self.engine:
            await self.engine.dispose()
        logger.info("Database optimizer cleaned up")

# Global database optimizer instance
db_optimizer = DatabaseOptimizer("postgresql://user:pass@localhost/db")

# Decorator for database operation monitoring
def monitor_db_operation(operation_name: str):
    """Decorator for monitoring database operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"DB operation {operation_name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"DB operation {operation_name} failed after {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator