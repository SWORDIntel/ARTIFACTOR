"""
Async Performance Optimizer
Advanced async patterns, connection pooling, and concurrent processing optimization
"""

import asyncio
import aiohttp
import time
import logging
from typing import Any, Callable, List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import functools
import weakref

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    concurrent_peak: int = 0
    current_concurrent: int = 0

    def update(self, execution_time: float, success: bool = True):
        """Update metrics with new request data"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.total_requests

    def start_request(self):
        """Mark start of concurrent request"""
        self.current_concurrent += 1
        self.concurrent_peak = max(self.concurrent_peak, self.current_concurrent)

    def end_request(self):
        """Mark end of concurrent request"""
        self.current_concurrent = max(0, self.current_concurrent - 1)

class AsyncConnectionPool:
    """High-performance async connection pool"""

    def __init__(
        self,
        max_connections: int = 100,
        max_connections_per_host: int = 30,
        timeout: float = 30.0,
        keepalive_timeout: float = 30.0
    ):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout
        self.keepalive_timeout = keepalive_timeout

        # Connection pools
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._db_pools: Dict[str, Any] = {}

        # Performance tracking
        self.metrics = PerformanceMetrics()

    async def initialize(self):
        """Initialize connection pools"""
        # HTTP connection pool
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections_per_host,
            keepalive_timeout=self.keepalive_timeout,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ttl_dns_cache=300
        )

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        self._http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'ARTIFACTOR/3.0 AsyncOptimizer'}
        )

        logger.info("Async connection pools initialized")

    @asynccontextmanager
    async def http_request(self, method: str, url: str, **kwargs):
        """Context manager for HTTP requests with metrics"""
        start_time = time.time()
        self.metrics.start_request()

        try:
            if not self._http_session:
                await self.initialize()

            async with self._http_session.request(method, url, **kwargs) as response:
                execution_time = time.time() - start_time
                self.metrics.update(execution_time, True)
                yield response

        except Exception as e:
            execution_time = time.time() - start_time
            self.metrics.update(execution_time, False)
            logger.error(f"HTTP request failed: {e}")
            raise
        finally:
            self.metrics.end_request()

    async def cleanup(self):
        """Cleanup connection pools"""
        if self._http_session:
            await self._http_session.close()

        for pool in self._db_pools.values():
            if hasattr(pool, 'close'):
                await pool.close()

        logger.info("Async connection pools cleaned up")

class ConcurrentProcessor:
    """High-performance concurrent task processor"""

    def __init__(
        self,
        max_workers: int = 10,
        max_concurrent_tasks: int = 100,
        batch_size: int = 20
    ):
        self.max_workers = max_workers
        self.max_concurrent_tasks = max_concurrent_tasks
        self.batch_size = batch_size

        # Thread pool for CPU-bound tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # Semaphore for controlling concurrency
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Performance tracking
        self.metrics = PerformanceMetrics()

    async def process_concurrent(
        self,
        tasks: List[Callable],
        *args,
        return_exceptions: bool = True,
        **kwargs
    ) -> List[Any]:
        """Process tasks concurrently with controlled concurrency"""
        async def run_task(task):
            async with self.semaphore:
                start_time = time.time()
                self.metrics.start_request()

                try:
                    if asyncio.iscoroutinefunction(task):
                        result = await task(*args, **kwargs)
                    else:
                        # Run CPU-bound task in thread pool
                        result = await asyncio.get_event_loop().run_in_executor(
                            self.thread_pool, task, *args, **kwargs
                        )

                    execution_time = time.time() - start_time
                    self.metrics.update(execution_time, True)
                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    self.metrics.update(execution_time, False)
                    if return_exceptions:
                        return e
                    raise
                finally:
                    self.metrics.end_request()

        # Process tasks in batches to avoid overwhelming the system
        results = []
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[run_task(task) for task in batch],
                return_exceptions=return_exceptions
            )
            results.extend(batch_results)

        return results

    async def map_concurrent(
        self,
        func: Callable,
        items: List[Any],
        return_exceptions: bool = True
    ) -> List[Any]:
        """Map function over items concurrently"""
        tasks = [functools.partial(func, item) for item in items]
        return await self.process_concurrent(tasks, return_exceptions=return_exceptions)

    def cleanup(self):
        """Cleanup thread pool"""
        self.thread_pool.shutdown(wait=True)

class AsyncBatchProcessor:
    """Batch processor for optimizing bulk operations"""

    def __init__(
        self,
        batch_size: int = 100,
        max_wait_time: float = 1.0,
        max_retries: int = 3
    ):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.max_retries = max_retries

        # Batch queues
        self._batches: Dict[str, List[Any]] = {}
        self._batch_tasks: Dict[str, asyncio.Task] = {}
        self._batch_results: Dict[str, asyncio.Future] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def add_to_batch(
        self,
        batch_key: str,
        item: Any,
        processor: Callable
    ) -> Any:
        """Add item to batch and get result when batch is processed"""
        async with self._lock:
            # Initialize batch if not exists
            if batch_key not in self._batches:
                self._batches[batch_key] = []
                self._batch_results[batch_key] = asyncio.Future()

            # Add item to batch
            self._batches[batch_key].append(item)

            # Start batch processor if needed
            if batch_key not in self._batch_tasks:
                self._batch_tasks[batch_key] = asyncio.create_task(
                    self._process_batch(batch_key, processor)
                )

            # Trigger immediate processing if batch is full
            if len(self._batches[batch_key]) >= self.batch_size:
                self._batch_tasks[batch_key].cancel()
                self._batch_tasks[batch_key] = asyncio.create_task(
                    self._process_batch_immediate(batch_key, processor)
                )

        # Wait for batch result
        try:
            results = await self._batch_results[batch_key]
            # Find result for this item (by index)
            item_index = len(self._batches[batch_key]) - 1
            return results[item_index] if item_index < len(results) else None
        except Exception as e:
            logger.error(f"Batch processing error for {batch_key}: {e}")
            raise

    async def _process_batch(self, batch_key: str, processor: Callable):
        """Process batch after wait time"""
        await asyncio.sleep(self.max_wait_time)
        await self._process_batch_immediate(batch_key, processor)

    async def _process_batch_immediate(self, batch_key: str, processor: Callable):
        """Process batch immediately"""
        async with self._lock:
            if batch_key not in self._batches or not self._batches[batch_key]:
                return

            batch_items = self._batches[batch_key].copy()
            result_future = self._batch_results[batch_key]

            # Clear batch for next use
            self._batches[batch_key].clear()
            del self._batch_tasks[batch_key]
            del self._batch_results[batch_key]

        # Process batch
        try:
            if asyncio.iscoroutinefunction(processor):
                results = await processor(batch_items)
            else:
                results = processor(batch_items)

            result_future.set_result(results)

        except Exception as e:
            result_future.set_exception(e)

class PerformanceMonitor:
    """Real-time performance monitoring"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.active_operations: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def monitor(self, operation_name: str):
        """Context manager for monitoring operation performance"""
        start_time = time.time()
        operation_id = f"{operation_name}_{id(asyncio.current_task())}"

        async with self._lock:
            if operation_name not in self.metrics:
                self.metrics[operation_name] = PerformanceMetrics()

            self.metrics[operation_name].start_request()
            self.active_operations[operation_id] = start_time

        try:
            yield
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            async with self._lock:
                self.metrics[operation_name].update(execution_time, success)
                self.metrics[operation_name].end_request()
                self.active_operations.pop(operation_id, None)

    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if operation_name:
            if operation_name in self.metrics:
                return {
                    'operation': operation_name,
                    'metrics': self.metrics[operation_name]
                }
            return {'operation': operation_name, 'metrics': None}

        return {
            'operations': {
                name: metrics for name, metrics in self.metrics.items()
            },
            'active_operations': len(self.active_operations),
            'total_operations': len(self.metrics)
        }

    def reset_metrics(self, operation_name: Optional[str] = None):
        """Reset performance metrics"""
        if operation_name:
            self.metrics.pop(operation_name, None)
        else:
            self.metrics.clear()
            self.active_operations.clear()

# Global instances
connection_pool = AsyncConnectionPool()
concurrent_processor = ConcurrentProcessor()
batch_processor = AsyncBatchProcessor()
performance_monitor = PerformanceMonitor()

# Decorator for monitoring function performance
def monitor_performance(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with performance_monitor.monitor(operation_name):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return wrapper
    return decorator

# Decorator for adding retry logic with exponential backoff
def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """Decorator for async retry with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

async def optimize_async_operations():
    """Initialize and configure async optimizations"""
    await connection_pool.initialize()
    logger.info("Async performance optimizations initialized")

async def cleanup_async_operations():
    """Cleanup async optimization resources"""
    await connection_pool.cleanup()
    concurrent_processor.cleanup()
    logger.info("Async performance optimizations cleaned up")