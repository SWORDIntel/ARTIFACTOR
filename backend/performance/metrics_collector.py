"""
Performance Metrics Collector
Real-time monitoring, metrics collection, and performance analytics
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import json
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_usage_percent: float
    disk_read_bytes: int
    disk_write_bytes: int
    network_sent_bytes: int
    network_recv_bytes: int
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    process_count: int
    thread_count: int
    open_files: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics"""
    request_count: int = 0
    request_rate: float = 0.0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    db_query_count: int = 0
    db_avg_time: float = 0.0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    uptime: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """High-performance metrics collection and monitoring system"""

    def __init__(
        self,
        collection_interval: float = 1.0,
        retention_period: int = 3600,  # 1 hour
        max_points_per_metric: int = 10000
    ):
        self.collection_interval = collection_interval
        self.retention_period = retention_period
        self.max_points_per_metric = max_points_per_metric

        # Metric storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # System metrics
        self.system_metrics: deque = deque(maxlen=max_points_per_metric)
        self.app_metrics: deque = deque(maxlen=max_points_per_metric)

        # Performance tracking
        self.start_time = time.time()
        self.collection_errors = 0
        self.last_collection_time = 0.0

        # Collection control
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = threading.RLock()

        # Custom collectors
        self.custom_collectors: List[Callable] = []

    async def start_collection(self):
        """Start metrics collection"""
        if self._running:
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")

    async def stop_collection(self):
        """Stop metrics collection"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        logger.info("Metrics collection stopped")

    async def _collection_loop(self):
        """Main collection loop"""
        while self._running:
            try:
                start_time = time.time()

                # Collect system metrics
                await self._collect_system_metrics()

                # Collect application metrics
                await self._collect_application_metrics()

                # Run custom collectors
                await self._run_custom_collectors()

                # Clean old metrics
                self._cleanup_old_metrics()

                # Update collection time
                self.last_collection_time = time.time() - start_time

                # Sleep until next collection
                sleep_time = max(0, self.collection_interval - self.last_collection_time)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.collection_errors += 1
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # Network metrics
            network_io = psutil.net_io_counters()

            # Load average
            load_avg = psutil.getloadavg()

            # Process metrics
            process_count = len(psutil.pids())
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            open_files = len(current_process.open_files())

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_available=memory.available,
                disk_usage_percent=disk.percent,
                disk_read_bytes=disk_io.read_bytes if disk_io else 0,
                disk_write_bytes=disk_io.write_bytes if disk_io else 0,
                network_sent_bytes=network_io.bytes_sent if network_io else 0,
                network_recv_bytes=network_io.bytes_recv if network_io else 0,
                load_average_1m=load_avg[0],
                load_average_5m=load_avg[1],
                load_average_15m=load_avg[2],
                process_count=process_count,
                thread_count=thread_count,
                open_files=open_files
            )

            with self._lock:
                self.system_metrics.append(metrics)

        except Exception as e:
            logger.error(f"System metrics collection error: {e}")

    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            # Calculate request rate
            request_rate = self._calculate_rate('request_count')

            # Calculate error rate
            error_rate = self._calculate_error_rate()

            # Get current process info
            process = psutil.Process()
            memory_info = process.memory_info()

            metrics = ApplicationMetrics(
                request_count=int(self.counters.get('request_count', 0)),
                request_rate=request_rate,
                avg_response_time=self._calculate_average('response_time'),
                error_rate=error_rate,
                active_connections=int(self.gauges.get('active_connections', 0)),
                cache_hit_rate=self._calculate_cache_hit_rate(),
                db_query_count=int(self.counters.get('db_query_count', 0)),
                db_avg_time=self._calculate_average('db_query_time'),
                memory_usage=memory_info.rss,
                cpu_usage=process.cpu_percent(),
                uptime=time.time() - self.start_time
            )

            with self._lock:
                self.app_metrics.append(metrics)

        except Exception as e:
            logger.error(f"Application metrics collection error: {e}")

    async def _run_custom_collectors(self):
        """Run custom metric collectors"""
        for collector in self.custom_collectors:
            try:
                if asyncio.iscoroutinefunction(collector):
                    await collector(self)
                else:
                    collector(self)
            except Exception as e:
                logger.error(f"Custom collector error: {e}")

    def add_custom_collector(self, collector: Callable):
        """Add custom metrics collector"""
        self.custom_collectors.append(collector)

    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            self.counters[name] += value
            self._add_metric_point(name, value, MetricType.COUNTER, tags)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        with self._lock:
            self.gauges[name] = value
            self._add_metric_point(name, value, MetricType.GAUGE, tags)

    def add_histogram_value(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add value to histogram metric"""
        with self._lock:
            if len(self.histograms[name]) >= 1000:  # Limit histogram size
                self.histograms[name] = self.histograms[name][-500:]  # Keep last 500 values
            self.histograms[name].append(value)
            self._add_metric_point(name, value, MetricType.HISTOGRAM, tags)

    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record timer metric"""
        with self._lock:
            if len(self.timers[name]) >= 1000:  # Limit timer size
                self.timers[name] = self.timers[name][-500:]  # Keep last 500 values
            self.timers[name].append(duration)
            self._add_metric_point(name, duration, MetricType.TIMER, tags)

    @asynccontextmanager
    async def timer_context(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, tags)

    def _add_metric_point(self, name: str, value: float, metric_type: MetricType, tags: Optional[Dict[str, str]]):
        """Add metric point to storage"""
        point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {}
        )
        self.metrics[name].append(point)

    def _calculate_rate(self, metric_name: str, window_seconds: int = 60) -> float:
        """Calculate rate per second for a counter metric"""
        if metric_name not in self.metrics:
            return 0.0

        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        points = [p for p in self.metrics[metric_name] if p.timestamp >= cutoff]
        if len(points) < 2:
            return 0.0

        total_value = sum(p.value for p in points)
        time_span = (points[-1].timestamp - points[0].timestamp).total_seconds()

        return total_value / max(time_span, 1.0)

    def _calculate_average(self, metric_name: str, window_seconds: int = 60) -> float:
        """Calculate average value for a metric"""
        if metric_name not in self.metrics:
            return 0.0

        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        points = [p for p in self.metrics[metric_name] if p.timestamp >= cutoff]
        if not points:
            return 0.0

        return sum(p.value for p in points) / len(points)

    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        total_requests = self.counters.get('request_count', 0)
        error_requests = self.counters.get('error_count', 0)

        if total_requests == 0:
            return 0.0

        return (error_requests / total_requests) * 100.0

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        cache_hits = self.counters.get('cache_hits', 0)
        cache_total = self.counters.get('cache_total', 0)

        if cache_total == 0:
            return 0.0

        return (cache_hits / cache_total) * 100.0

    def _cleanup_old_metrics(self):
        """Remove old metric points"""
        cutoff = datetime.now() - timedelta(seconds=self.retention_period)

        with self._lock:
            # Clean metric points
            for name, points in self.metrics.items():
                while points and points[0].timestamp < cutoff:
                    points.popleft()

            # Clean system metrics
            while (self.system_metrics and
                   self.system_metrics[0].timestamp < cutoff):
                self.system_metrics.popleft()

            # Clean application metrics
            while (self.app_metrics and
                   self.app_metrics[0].timestamp < cutoff):
                self.app_metrics.popleft()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self._lock:
            # Latest system metrics
            latest_system = self.system_metrics[-1] if self.system_metrics else None

            # Latest application metrics
            latest_app = self.app_metrics[-1] if self.app_metrics else None

            # Metric statistics
            metric_stats = {}
            for name, points in self.metrics.items():
                if points:
                    values = [p.value for p in points]
                    metric_stats[name] = {
                        'count': len(values),
                        'latest': values[-1],
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'rate_per_minute': self._calculate_rate(name, 60) * 60
                    }

            return {
                'collection_status': {
                    'running': self._running,
                    'uptime': time.time() - self.start_time,
                    'collection_errors': self.collection_errors,
                    'last_collection_time': self.last_collection_time,
                    'total_metrics': len(self.metrics)
                },
                'system_metrics': asdict(latest_system) if latest_system else None,
                'application_metrics': asdict(latest_app) if latest_app else None,
                'metric_statistics': metric_stats,
                'counters': dict(self.counters),
                'gauges': dict(self.gauges)
            }

    def get_metric_history(
        self,
        metric_name: str,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        if metric_name not in self.metrics:
            return []

        cutoff = datetime.now() - timedelta(hours=hours)
        points = [
            asdict(p) for p in self.metrics[metric_name]
            if p.timestamp >= cutoff
        ]

        # Convert datetime to ISO string for JSON serialization
        for point in points:
            point['timestamp'] = point['timestamp'].isoformat()

        return points

    def export_metrics(self, format_type: str = 'json') -> str:
        """Export metrics in various formats"""
        summary = self.get_metrics_summary()

        if format_type == 'json':
            # Convert datetime objects to strings
            if summary['system_metrics']:
                summary['system_metrics']['timestamp'] = summary['system_metrics']['timestamp'].isoformat()
            if summary['application_metrics']:
                summary['application_metrics']['timestamp'] = summary['application_metrics']['timestamp'].isoformat()

            return json.dumps(summary, indent=2, default=str)

        elif format_type == 'prometheus':
            # Export in Prometheus format
            lines = []
            for name, value in self.counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")

            for name, value in self.gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            return '\n'.join(lines)

        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
            self.system_metrics.clear()
            self.app_metrics.clear()
            self.collection_errors = 0
            self.start_time = time.time()

        logger.info("All metrics reset")

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Decorator for automatic metrics collection
def collect_metrics(metric_name: str, metric_type: str = 'timer'):
    """Decorator for automatic metrics collection"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            if metric_type == 'timer':
                async with metrics_collector.timer_context(f"{metric_name}_duration"):
                    result = await func(*args, **kwargs)
                metrics_collector.increment_counter(f"{metric_name}_count")
                return result
            else:
                result = await func(*args, **kwargs)
                metrics_collector.increment_counter(metric_name)
                return result

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                if metric_type == 'timer':
                    duration = time.time() - start_time
                    metrics_collector.record_timer(f"{metric_name}_duration", duration)
                metrics_collector.increment_counter(f"{metric_name}_count")
                return result
            except Exception as e:
                metrics_collector.increment_counter(f"{metric_name}_errors")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator