"""
Performance Integration Module
Central integration point for all performance optimizations
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .cache_manager import cache_manager
from .async_optimizer import (
    connection_pool,
    concurrent_processor,
    batch_processor,
    performance_monitor,
    optimize_async_operations,
    cleanup_async_operations
)
from .database_optimizer import db_optimizer
from .metrics_collector import metrics_collector
from .venv_optimizer import venv_manager

logger = logging.getLogger(__name__)

class PerformanceIntegrator:
    """Central performance optimization coordinator"""

    def __init__(self):
        self.initialized = False
        self.components = {
            'cache_manager': cache_manager,
            'connection_pool': connection_pool,
            'concurrent_processor': concurrent_processor,
            'batch_processor': batch_processor,
            'performance_monitor': performance_monitor,
            'db_optimizer': db_optimizer,
            'metrics_collector': metrics_collector,
            'venv_manager': venv_manager
        }

    async def initialize_all(self, config: Optional[Dict[str, Any]] = None):
        """Initialize all performance optimization components"""
        if self.initialized:
            return

        config = config or {}
        logger.info("Initializing performance optimization suite...")

        try:
            # Initialize cache manager
            cache_config = config.get('cache', {})
            await cache_manager.initialize()
            logger.info("✅ Cache manager initialized")

            # Initialize async optimizations
            await optimize_async_operations()
            logger.info("✅ Async optimizations initialized")

            # Initialize database optimizer
            db_config = config.get('database', {})
            if db_config.get('url'):
                db_optimizer.database_url = db_config['url']
                await db_optimizer.initialize()
                logger.info("✅ Database optimizer initialized")

            # Initialize metrics collector
            await metrics_collector.start_collection()
            logger.info("✅ Metrics collector started")

            # Setup performance monitoring
            await self._setup_performance_monitoring()
            logger.info("✅ Performance monitoring configured")

            self.initialized = True
            logger.info("🚀 Performance optimization suite fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize performance optimizations: {e}")
            raise

    async def shutdown_all(self):
        """Shutdown all performance optimization components"""
        if not self.initialized:
            return

        logger.info("Shutting down performance optimization suite...")

        try:
            # Stop metrics collection
            await metrics_collector.stop_collection()
            logger.info("✅ Metrics collector stopped")

            # Cleanup async operations
            await cleanup_async_operations()
            logger.info("✅ Async operations cleaned up")

            # Cleanup database optimizer
            await db_optimizer.cleanup()
            logger.info("✅ Database optimizer cleaned up")

            # Cleanup cache manager
            await cache_manager.cleanup()
            logger.info("✅ Cache manager cleaned up")

            self.initialized = False
            logger.info("🔄 Performance optimization suite shutdown complete")

        except Exception as e:
            logger.error(f"Error during performance optimization shutdown: {e}")

    async def _setup_performance_monitoring(self):
        """Setup comprehensive performance monitoring"""
        # Add custom metrics collectors
        def collect_cache_metrics(collector):
            stats = cache_manager.get_stats()
            collector.set_gauge('cache_hit_rate', stats['hit_rate'])
            collector.set_gauge('cache_memory_usage', stats['memory_usage'])
            collector.set_gauge('cache_entry_count', stats['entry_count'])

        def collect_connection_metrics(collector):
            conn_stats = connection_pool.metrics
            collector.set_gauge('connection_pool_active', conn_stats.current_concurrent)
            collector.set_gauge('connection_pool_peak', conn_stats.concurrent_peak)
            collector.increment_counter('connection_pool_requests', conn_stats.total_requests)

        def collect_processor_metrics(collector):
            proc_stats = concurrent_processor.metrics
            collector.set_gauge('processor_active_tasks', proc_stats.current_concurrent)
            collector.set_gauge('processor_peak_tasks', proc_stats.concurrent_peak)
            collector.increment_counter('processor_total_tasks', proc_stats.total_requests)

        # Register custom collectors
        metrics_collector.add_custom_collector(collect_cache_metrics)
        metrics_collector.add_custom_collector(collect_connection_metrics)
        metrics_collector.add_custom_collector(collect_processor_metrics)

    async def get_performance_status(self) -> Dict[str, Any]:
        """Get comprehensive performance status"""
        if not self.initialized:
            return {'status': 'not_initialized'}

        try:
            status = {
                'initialized': self.initialized,
                'components': {},
                'overall_metrics': {},
                'health_check': True
            }

            # Cache manager status
            cache_stats = cache_manager.get_stats()
            status['components']['cache'] = {
                'available': True,
                'hit_rate': cache_stats['hit_rate'],
                'memory_usage': cache_stats['memory_usage'],
                'entry_count': cache_stats['entry_count']
            }

            # Connection pool status
            conn_stats = connection_pool.metrics
            status['components']['connection_pool'] = {
                'available': True,
                'active_connections': conn_stats.current_concurrent,
                'peak_connections': conn_stats.concurrent_peak,
                'total_requests': conn_stats.total_requests
            }

            # Database optimizer status
            if hasattr(db_optimizer, 'get_query_performance_stats'):
                db_stats = await db_optimizer.get_query_performance_stats()
                status['components']['database'] = {
                    'available': True,
                    'total_queries': db_stats.get('total_queries', 0),
                    'slow_queries': len(db_stats.get('slow_queries', [])),
                    'pool_status': db_stats.get('pool_metrics', {})
                }

            # Metrics collector status
            metrics_summary = metrics_collector.get_metrics_summary()
            status['components']['metrics'] = {
                'available': metrics_collector._running,
                'collection_status': metrics_summary.get('collection_status', {}),
                'metric_count': metrics_summary.get('collection_status', {}).get('total_metrics', 0)
            }

            # Overall system metrics
            if metrics_summary.get('system_metrics'):
                sys_metrics = metrics_summary['system_metrics']
                status['overall_metrics'] = {
                    'cpu_usage': sys_metrics.get('cpu_percent', 0),
                    'memory_usage': sys_metrics.get('memory_percent', 0),
                    'load_average': sys_metrics.get('load_average_1m', 0)
                }

            return status

        except Exception as e:
            logger.error(f"Error getting performance status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'initialized': self.initialized
            }

    async def run_performance_optimization(self):
        """Run automatic performance optimization"""
        if not self.initialized:
            await self.initialize_all()

        logger.info("Running automatic performance optimization...")

        try:
            # Optimize database connections
            if hasattr(db_optimizer, 'optimize_connection_pool'):
                await db_optimizer.optimize_connection_pool()

            # Optimize cache performance
            cache_stats = cache_manager.get_stats()
            if cache_stats['hit_rate'] < 0.8:  # Less than 80% hit rate
                logger.info("Cache hit rate below 80%, analyzing patterns...")
                # Could implement cache warming strategies here

            # Optimize virtual environments
            await venv_manager.cleanup_old_venvs(max_age_days=7)
            await venv_manager.optimize_cache()

            logger.info("✅ Automatic performance optimization completed")

        except Exception as e:
            logger.error(f"Error during performance optimization: {e}")
            raise

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get performance optimization recommendations"""
        recommendations = {
            'cache': [],
            'database': [],
            'system': [],
            'application': []
        }

        try:
            # Cache recommendations
            cache_stats = cache_manager.get_stats()
            if cache_stats['hit_rate'] < 0.8:
                recommendations['cache'].append({
                    'type': 'low_hit_rate',
                    'message': f"Cache hit rate is {cache_stats['hit_rate']:.1%}, consider increasing TTL or cache size",
                    'priority': 'medium'
                })

            if cache_stats['memory_utilization'] > 0.9:
                recommendations['cache'].append({
                    'type': 'high_memory_usage',
                    'message': "Cache memory usage above 90%, consider increasing cache limit",
                    'priority': 'high'
                })

            # Database recommendations
            # This would require database stats to be available
            # Could analyze slow queries, connection pool usage, etc.

            # System recommendations
            metrics_summary = metrics_collector.get_metrics_summary()
            if metrics_summary.get('system_metrics'):
                sys_metrics = metrics_summary['system_metrics']

                if sys_metrics.get('cpu_percent', 0) > 80:
                    recommendations['system'].append({
                        'type': 'high_cpu_usage',
                        'message': f"CPU usage at {sys_metrics['cpu_percent']:.1f}%, consider scaling",
                        'priority': 'high'
                    })

                if sys_metrics.get('memory_percent', 0) > 85:
                    recommendations['system'].append({
                        'type': 'high_memory_usage',
                        'message': f"Memory usage at {sys_metrics['memory_percent']:.1f}%, consider optimization",
                        'priority': 'high'
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {'error': str(e)}

# Global performance integrator instance
performance_integrator = PerformanceIntegrator()

# Convenience functions for FastAPI integration
async def initialize_performance(config: Optional[Dict[str, Any]] = None):
    """Initialize performance optimizations"""
    await performance_integrator.initialize_all(config)

async def shutdown_performance():
    """Shutdown performance optimizations"""
    await performance_integrator.shutdown_all()

async def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    return await performance_integrator.get_performance_status()

def get_performance_recommendations() -> Dict[str, Any]:
    """Get performance optimization recommendations"""
    return performance_integrator.get_optimization_recommendations()

# Decorators for automatic performance monitoring
def monitor_performance(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with performance_monitor.monitor(operation_name):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return wrapper
    return decorator

# Context manager for performance tracking
class PerformanceContext:
    """Context manager for performance tracking"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name

    async def __aenter__(self):
        self.context = performance_monitor.monitor(self.operation_name)
        await self.context.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.context.__aexit__(exc_type, exc_val, exc_tb)