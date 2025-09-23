"""
Performance Benchmarking and Validation Suite
Comprehensive performance testing, monitoring, and validation system
"""

import asyncio
import time
import psutil
import logging
import json
import statistics
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Individual benchmark test result"""
    test_name: str
    duration: float
    memory_peak: int
    memory_average: int
    cpu_peak: float
    cpu_average: float
    success: bool
    error_message: Optional[str] = None
    iterations: int = 1
    throughput: float = 0.0  # operations per second
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemSnapshot:
    """System state snapshot for before/after comparison"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: Dict[str, int]
    network_io: Dict[str, int]
    process_count: int
    load_average: Tuple[float, float, float]

class PerformanceMonitor:
    """Real-time performance monitoring during benchmarks"""

    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.monitoring = False
        self.samples: List[Dict[str, Any]] = []
        self.monitor_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.samples.clear()
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        return self._aggregate_samples()

    async def _monitor_loop(self):
        """Monitor performance metrics continuously"""
        current_process = psutil.Process()

        while self.monitoring:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()

                # Process metrics
                process_memory = current_process.memory_info()
                process_cpu = current_process.cpu_percent()

                sample = {
                    'timestamp': time.time(),
                    'system_cpu': cpu_percent,
                    'system_memory_percent': memory.percent,
                    'system_memory_available': memory.available,
                    'process_memory_rss': process_memory.rss,
                    'process_memory_vms': process_memory.vms,
                    'process_cpu': process_cpu,
                    'process_threads': current_process.num_threads()
                }

                self.samples.append(sample)
                await asyncio.sleep(self.sample_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    def _aggregate_samples(self) -> Dict[str, Any]:
        """Aggregate monitoring samples into metrics"""
        if not self.samples:
            return {}

        # Extract time series data
        cpu_values = [s['process_cpu'] for s in self.samples]
        memory_values = [s['process_memory_rss'] for s in self.samples]
        system_cpu_values = [s['system_cpu'] for s in self.samples]

        return {
            'sample_count': len(self.samples),
            'duration': self.samples[-1]['timestamp'] - self.samples[0]['timestamp'],
            'cpu_peak': max(cpu_values) if cpu_values else 0,
            'cpu_average': statistics.mean(cpu_values) if cpu_values else 0,
            'memory_peak': max(memory_values) if memory_values else 0,
            'memory_average': statistics.mean(memory_values) if memory_values else 0,
            'system_cpu_peak': max(system_cpu_values) if system_cpu_values else 0,
            'system_cpu_average': statistics.mean(system_cpu_values) if system_cpu_values else 0
        }

class BenchmarkSuite:
    """Comprehensive benchmark suite for performance testing"""

    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Test registry
        self.tests: Dict[str, Callable] = {}
        self.test_configs: Dict[str, Dict[str, Any]] = {}

        # Results storage
        self.results: List[BenchmarkResult] = []

        # Performance monitor
        self.monitor = PerformanceMonitor()

        # System state tracking
        self.baseline_snapshot: Optional[SystemSnapshot] = None

    def register_test(
        self,
        name: str,
        test_func: Callable,
        config: Optional[Dict[str, Any]] = None
    ):
        """Register a benchmark test"""
        self.tests[name] = test_func
        self.test_configs[name] = config or {}
        logger.info(f"Registered benchmark test: {name}")

    async def run_single_test(
        self,
        test_name: str,
        iterations: int = 1,
        warmup_iterations: int = 0
    ) -> BenchmarkResult:
        """Run a single benchmark test"""
        if test_name not in self.tests:
            raise ValueError(f"Test '{test_name}' not found")

        test_func = self.tests[test_name]
        config = self.test_configs[test_name]

        logger.info(f"Running benchmark test: {test_name}")

        # Warmup runs
        if warmup_iterations > 0:
            logger.info(f"Performing {warmup_iterations} warmup iterations...")
            for i in range(warmup_iterations):
                try:
                    if asyncio.iscoroutinefunction(test_func):
                        await test_func(**config)
                    else:
                        test_func(**config)
                except Exception as e:
                    logger.warning(f"Warmup iteration {i+1} failed: {e}")

        # Actual test runs
        durations = []
        latencies = []
        errors = []

        for iteration in range(iterations):
            logger.debug(f"Running iteration {iteration + 1}/{iterations}")

            # Start monitoring
            await self.monitor.start_monitoring()

            # Garbage collect before test
            gc.collect()

            start_time = time.time()
            success = True
            error_message = None

            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func(**config)
                else:
                    result = test_func(**config)

                # Extract custom metrics if returned
                custom_metrics = {}
                if isinstance(result, dict):
                    custom_metrics = result

            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Test iteration {iteration + 1} failed: {e}")
                errors.append(e)

            end_time = time.time()
            duration = end_time - start_time
            durations.append(duration)

            # Stop monitoring and get metrics
            monitor_metrics = await self.monitor.stop_monitoring()

            # Record latency for throughput calculations
            latencies.append(duration)

        # Calculate aggregated metrics
        total_duration = sum(durations)
        avg_duration = statistics.mean(durations) if durations else 0
        throughput = iterations / total_duration if total_duration > 0 else 0

        # Calculate latency percentiles
        latencies.sort()
        latency_p50 = self._percentile(latencies, 50) if latencies else 0
        latency_p95 = self._percentile(latencies, 95) if latencies else 0
        latency_p99 = self._percentile(latencies, 99) if latencies else 0

        # Create result
        result = BenchmarkResult(
            test_name=test_name,
            duration=total_duration,
            memory_peak=monitor_metrics.get('memory_peak', 0),
            memory_average=monitor_metrics.get('memory_average', 0),
            cpu_peak=monitor_metrics.get('cpu_peak', 0),
            cpu_average=monitor_metrics.get('cpu_average', 0),
            success=len(errors) == 0,
            error_message='; '.join(str(e) for e in errors) if errors else None,
            iterations=iterations,
            throughput=throughput,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            custom_metrics=custom_metrics if 'custom_metrics' in locals() else {}
        )

        self.results.append(result)
        logger.info(f"Test '{test_name}' completed: {result.duration:.3f}s, "
                   f"throughput: {result.throughput:.2f} ops/s")

        return result

    async def run_all_tests(
        self,
        iterations: int = 3,
        warmup_iterations: int = 1
    ) -> List[BenchmarkResult]:
        """Run all registered tests"""
        logger.info(f"Running {len(self.tests)} benchmark tests...")

        # Take baseline system snapshot
        self.baseline_snapshot = self._take_system_snapshot()

        results = []
        for test_name in self.tests:
            try:
                result = await self.run_single_test(
                    test_name,
                    iterations=iterations,
                    warmup_iterations=warmup_iterations
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to run test '{test_name}': {e}")

        # Save results
        await self._save_results()

        return results

    async def run_performance_regression_test(
        self,
        baseline_file: Optional[str] = None,
        threshold_percent: float = 10.0
    ) -> Dict[str, Any]:
        """Run performance regression testing against baseline"""
        current_results = await self.run_all_tests()

        if not baseline_file:
            baseline_file = str(self.output_dir / "baseline_results.json")

        # Load baseline results if available
        baseline_results = self._load_baseline_results(baseline_file)
        if not baseline_results:
            logger.warning("No baseline results found, saving current as baseline")
            self._save_baseline_results(current_results, baseline_file)
            return {"status": "baseline_created", "tests": len(current_results)}

        # Compare results
        regressions = []
        improvements = []

        for current in current_results:
            baseline = self._find_baseline_result(baseline_results, current.test_name)
            if not baseline:
                continue

            # Check for performance regression
            throughput_change = (
                (current.throughput - baseline['throughput']) / baseline['throughput'] * 100
                if baseline['throughput'] > 0 else 0
            )

            latency_change = (
                (current.latency_p95 - baseline['latency_p95']) / baseline['latency_p95'] * 100
                if baseline['latency_p95'] > 0 else 0
            )

            memory_change = (
                (current.memory_peak - baseline['memory_peak']) / baseline['memory_peak'] * 100
                if baseline['memory_peak'] > 0 else 0
            )

            test_analysis = {
                'test_name': current.test_name,
                'throughput_change': throughput_change,
                'latency_change': latency_change,
                'memory_change': memory_change,
                'baseline_throughput': baseline['throughput'],
                'current_throughput': current.throughput,
                'baseline_latency_p95': baseline['latency_p95'],
                'current_latency_p95': current.latency_p95
            }

            # Check for regressions
            if (throughput_change < -threshold_percent or
                latency_change > threshold_percent or
                memory_change > threshold_percent):
                regressions.append(test_analysis)

            # Check for improvements
            elif (throughput_change > threshold_percent or
                  latency_change < -threshold_percent or
                  memory_change < -threshold_percent):
                improvements.append(test_analysis)

        return {
            'status': 'completed',
            'regressions': regressions,
            'improvements': improvements,
            'total_tests': len(current_results),
            'threshold_percent': threshold_percent
        }

    def _take_system_snapshot(self) -> SystemSnapshot:
        """Take system state snapshot"""
        memory = psutil.virtual_memory()
        disk_usage = {}
        network_io = {}

        try:
            # Disk usage for root partition
            disk = psutil.disk_usage('/')
            disk_usage = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free
            }

            # Network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                network_io = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }

        except Exception as e:
            logger.warning(f"Error collecting system metrics: {e}")

        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=memory.percent,
            memory_available=memory.available,
            disk_usage=disk_usage,
            network_io=network_io,
            process_count=len(psutil.pids()),
            load_average=psutil.getloadavg()
        )

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0

        k = (len(values) - 1) * percentile / 100
        f = int(k)
        c = k - f

        if f == len(values) - 1:
            return values[f]
        else:
            return values[f] * (1 - c) + values[f + 1] * c

    async def _save_results(self):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"benchmark_results_{timestamp}.json"

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'baseline_snapshot': asdict(self.baseline_snapshot) if self.baseline_snapshot else None,
            'results': [asdict(result) for result in self.results]
        }

        # Convert datetime objects to strings for JSON serialization
        for result in results_data['results']:
            result['timestamp'] = result['timestamp'].isoformat()

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        logger.info(f"Benchmark results saved to {results_file}")

    def _load_baseline_results(self, baseline_file: str) -> Optional[List[Dict[str, Any]]]:
        """Load baseline results from file"""
        baseline_path = Path(baseline_file)
        if not baseline_path.exists():
            return None

        try:
            with open(baseline_path) as f:
                data = json.load(f)
                return data.get('results', [])
        except Exception as e:
            logger.error(f"Failed to load baseline results: {e}")
            return None

    def _save_baseline_results(self, results: List[BenchmarkResult], baseline_file: str):
        """Save current results as baseline"""
        baseline_data = {
            'timestamp': datetime.now().isoformat(),
            'results': [asdict(result) for result in results]
        }

        # Convert datetime objects to strings
        for result in baseline_data['results']:
            result['timestamp'] = result['timestamp'].isoformat()

        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)

        logger.info(f"Baseline results saved to {baseline_file}")

    def _find_baseline_result(
        self,
        baseline_results: List[Dict[str, Any]],
        test_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find baseline result for specific test"""
        for result in baseline_results:
            if result['test_name'] == test_name:
                return result
        return None

    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.results:
            return "No benchmark results available"

        report_lines = [
            "# Performance Benchmark Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Tests: {len(self.results)}",
            "",
            "## Test Results Summary",
            ""
        ]

        # Summary table
        report_lines.extend([
            "| Test Name | Duration (s) | Throughput (ops/s) | P95 Latency (s) | Memory Peak (MB) | Success |",
            "|-----------|--------------|--------------------|-----------------|-----------------|---------| "
        ])

        for result in self.results:
            memory_mb = result.memory_peak / (1024 * 1024) if result.memory_peak else 0
            report_lines.append(
                f"| {result.test_name} | {result.duration:.3f} | {result.throughput:.2f} | "
                f"{result.latency_p95:.3f} | {memory_mb:.1f} | {'✅' if result.success else '❌'} |"
            )

        # Detailed results
        report_lines.extend([
            "",
            "## Detailed Results",
            ""
        ])

        for result in self.results:
            report_lines.extend([
                f"### {result.test_name}",
                f"- **Duration**: {result.duration:.3f} seconds",
                f"- **Iterations**: {result.iterations}",
                f"- **Throughput**: {result.throughput:.2f} operations/second",
                f"- **Latency P50**: {result.latency_p50:.3f} seconds",
                f"- **Latency P95**: {result.latency_p95:.3f} seconds",
                f"- **Latency P99**: {result.latency_p99:.3f} seconds",
                f"- **Memory Peak**: {result.memory_peak / (1024*1024):.1f} MB",
                f"- **Memory Average**: {result.memory_average / (1024*1024):.1f} MB",
                f"- **CPU Peak**: {result.cpu_peak:.1f}%",
                f"- **CPU Average**: {result.cpu_average:.1f}%",
                f"- **Success**: {'Yes' if result.success else 'No'}",
                ""
            ])

            if result.error_message:
                report_lines.extend([
                    f"- **Error**: {result.error_message}",
                    ""
                ])

            if result.custom_metrics:
                report_lines.extend([
                    "- **Custom Metrics**:",
                    ""
                ])
                for key, value in result.custom_metrics.items():
                    report_lines.append(f"  - {key}: {value}")
                report_lines.append("")

        return "\n".join(report_lines)

# Global benchmark suite instance
benchmark_suite = BenchmarkSuite()

# Built-in benchmark tests
async def test_async_performance():
    """Test async operation performance"""
    async def async_operation():
        await asyncio.sleep(0.001)  # Simulate async work
        return True

    start_time = time.time()
    tasks = [async_operation() for _ in range(1000)]
    results = await asyncio.gather(*tasks)
    end_time = time.time()

    return {
        'operations_completed': len(results),
        'total_time': end_time - start_time,
        'success_rate': sum(1 for r in results if r) / len(results) * 100
    }

def test_cpu_intensive():
    """Test CPU-intensive operations"""
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)

    start_time = time.time()
    result = fibonacci(25)  # CPU-intensive calculation
    end_time = time.time()

    return {
        'fibonacci_result': result,
        'calculation_time': end_time - start_time
    }

async def test_memory_allocation():
    """Test memory allocation patterns"""
    import gc

    gc.collect()
    initial_objects = len(gc.get_objects())

    # Allocate memory
    large_list = [i for i in range(100000)]
    large_dict = {str(i): i for i in range(10000)}

    peak_objects = len(gc.get_objects())

    # Cleanup
    del large_list
    del large_dict
    gc.collect()

    final_objects = len(gc.get_objects())

    return {
        'initial_objects': initial_objects,
        'peak_objects': peak_objects,
        'final_objects': final_objects,
        'objects_leaked': final_objects - initial_objects
    }

# Register built-in tests
benchmark_suite.register_test("async_performance", test_async_performance)
benchmark_suite.register_test("cpu_intensive", test_cpu_intensive)
benchmark_suite.register_test("memory_allocation", test_memory_allocation)

# Utility functions
async def run_benchmark(test_name: str, **kwargs) -> BenchmarkResult:
    """Run single benchmark test"""
    return await benchmark_suite.run_single_test(test_name, **kwargs)

async def run_all_benchmarks(**kwargs) -> List[BenchmarkResult]:
    """Run all registered benchmark tests"""
    return await benchmark_suite.run_all_tests(**kwargs)

async def run_regression_test(**kwargs) -> Dict[str, Any]:
    """Run performance regression testing"""
    return await benchmark_suite.run_performance_regression_test(**kwargs)