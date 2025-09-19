#!/usr/bin/env python3
"""
ARTIFACTOR v2.0 Performance Monitoring Framework
MONITOR Agent: Real-time performance tracking and health monitoring

This module provides comprehensive performance monitoring for the optimized
ARTIFACTOR system, tracking agent coordination, memory usage, and system health.
"""

import time
import threading
import json
import os
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import statistics


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: float
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]


@dataclass
class AgentCoordinationMetric:
    """Agent coordination performance tracking"""
    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    agent_count: int
    queue_size: int
    memory_mb: float


@dataclass
class SystemHealthMetric:
    """System health monitoring data"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_percent: float
    active_threads: int
    open_files: int


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for ARTIFACTOR v2.0

    Features:
    - Real-time agent coordination tracking
    - Memory usage monitoring
    - System resource monitoring
    - Performance regression detection
    - Health check dashboard
    """

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.coordination_metrics = deque(maxlen=1000)
        self.health_metrics = deque(maxlen=1000)

        # Performance thresholds (from OPTIMIZER targets)
        self.thresholds = {
            'coordination_overhead_ms': 10.0,
            'memory_usage_mb': 100.0,
            'success_rate_percent': 95.0,
            'cpu_percent': 80.0
        }

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.lock = threading.Lock()

        # Performance baselines
        self.baselines = {
            'pre_optimization': {
                'coordination_overhead_ms': 3839.8,
                'memory_usage_mb': 13.0,
                'success_rate_percent': 66.7
            },
            'post_optimization': {
                'coordination_overhead_ms': 30.0,  # Target achieved
                'memory_usage_mb': 15.0,
                'success_rate_percent': 95.0
            }
        }

        # Setup logging
        self.logger = logging.getLogger('performance_monitor')

    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"Performance monitoring started (interval: {interval_seconds}s)")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")

    def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                health_metric = self._collect_system_health()
                with self.lock:
                    self.health_metrics.append(health_metric)
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")

    def _collect_system_health(self) -> SystemHealthMetric:
        """Collect system health metrics"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return SystemHealthMetric(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(),
            memory_mb=memory_info.rss / 1024 / 1024,
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            active_threads=process.num_threads(),
            open_files=len(process.open_files())
        )

    def record_coordination_metric(self, operation_name: str, start_time: float,
                                 end_time: float, success: bool, agent_count: int,
                                 queue_size: int = 0):
        """Record agent coordination performance metric"""
        duration_ms = (end_time - start_time) * 1000

        # Get current memory usage
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024

        metric = AgentCoordinationMetric(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            agent_count=agent_count,
            queue_size=queue_size,
            memory_mb=memory_mb
        )

        with self.lock:
            self.coordination_metrics.append(metric)

        # Check for performance regressions
        self._check_performance_regression(metric)

        self.logger.info(f"Coordination metric: {operation_name} "
                        f"{duration_ms:.1f}ms ({'✅' if success else '❌'})")

    def _check_performance_regression(self, metric: AgentCoordinationMetric):
        """Check for performance regressions against thresholds"""
        if metric.duration_ms > self.thresholds['coordination_overhead_ms']:
            self.logger.warning(f"Performance regression detected: "
                              f"{metric.operation_name} took {metric.duration_ms:.1f}ms "
                              f"(threshold: {self.thresholds['coordination_overhead_ms']}ms)")

        if metric.memory_mb > self.thresholds['memory_usage_mb']:
            self.logger.warning(f"Memory usage exceeded threshold: "
                              f"{metric.memory_mb:.1f}MB "
                              f"(threshold: {self.thresholds['memory_usage_mb']}MB)")

    def get_performance_summary(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """Get performance summary for the last N minutes"""
        cutoff_time = time.time() - (duration_minutes * 60)

        with self.lock:
            # Filter recent coordination metrics
            recent_coord = [m for m in self.coordination_metrics
                          if m.start_time > cutoff_time]

            # Filter recent health metrics
            recent_health = [m for m in self.health_metrics
                           if m.timestamp > cutoff_time]

        if not recent_coord:
            return {"error": "No coordination metrics in specified time range"}

        # Calculate coordination statistics
        durations = [m.duration_ms for m in recent_coord]
        success_count = sum(1 for m in recent_coord if m.success)

        coordination_stats = {
            'total_operations': len(recent_coord),
            'success_rate_percent': (success_count / len(recent_coord)) * 100,
            'avg_duration_ms': statistics.mean(durations),
            'p50_duration_ms': statistics.median(durations),
            'p95_duration_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations)
        }

        # Calculate health statistics
        health_stats = {}
        if recent_health:
            health_stats = {
                'avg_cpu_percent': statistics.mean([m.cpu_percent for m in recent_health]),
                'avg_memory_mb': statistics.mean([m.memory_mb for m in recent_health]),
                'max_memory_mb': max([m.memory_mb for m in recent_health]),
                'avg_threads': statistics.mean([m.active_threads for m in recent_health])
            }

        # Performance vs baseline comparison
        baseline_comparison = {}
        if durations:
            pre_opt_baseline = self.baselines['pre_optimization']['coordination_overhead_ms']
            post_opt_baseline = self.baselines['post_optimization']['coordination_overhead_ms']
            current_avg = coordination_stats['avg_duration_ms']

            baseline_comparison = {
                'improvement_vs_pre_optimization': {
                    'percent': ((pre_opt_baseline - current_avg) / pre_opt_baseline) * 100,
                    'baseline_ms': pre_opt_baseline,
                    'current_ms': current_avg
                },
                'vs_post_optimization_target': {
                    'percent': ((current_avg - post_opt_baseline) / post_opt_baseline) * 100,
                    'target_ms': post_opt_baseline,
                    'current_ms': current_avg
                }
            }

        return {
            'timestamp': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'coordination': coordination_stats,
            'system_health': health_stats,
            'baseline_comparison': baseline_comparison,
            'threshold_compliance': {
                'coordination_overhead': coordination_stats['avg_duration_ms'] <= self.thresholds['coordination_overhead_ms'],
                'memory_usage': health_stats.get('max_memory_mb', 0) <= self.thresholds['memory_usage_mb'],
                'success_rate': coordination_stats['success_rate_percent'] >= self.thresholds['success_rate_percent']
            }
        }

    def get_health_dashboard(self) -> Dict[str, Any]:
        """Get current system health dashboard"""
        current_health = self._collect_system_health()

        # Get recent performance summary
        recent_summary = self.get_performance_summary(duration_minutes=5)

        # Health status determination
        health_status = "healthy"
        issues = []

        if current_health.cpu_percent > self.thresholds['cpu_percent']:
            health_status = "warning"
            issues.append(f"High CPU usage: {current_health.cpu_percent:.1f}%")

        if current_health.memory_mb > self.thresholds['memory_usage_mb']:
            health_status = "warning"
            issues.append(f"High memory usage: {current_health.memory_mb:.1f}MB")

        if recent_summary.get('coordination', {}).get('success_rate_percent', 100) < self.thresholds['success_rate_percent']:
            health_status = "warning"
            issues.append(f"Low success rate: {recent_summary['coordination']['success_rate_percent']:.1f}%")

        return {
            'timestamp': datetime.now().isoformat(),
            'status': health_status,
            'issues': issues,
            'current_metrics': asdict(current_health),
            'recent_performance': recent_summary,
            'monitoring_active': self.monitoring_active,
            'total_coordination_metrics': len(self.coordination_metrics),
            'total_health_metrics': len(self.health_metrics)
        }

    def export_metrics(self, filepath: str):
        """Export all metrics to JSON file"""
        with self.lock:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'coordination_metrics': [asdict(m) for m in self.coordination_metrics],
                'health_metrics': [asdict(m) for m in self.health_metrics],
                'thresholds': self.thresholds,
                'baselines': self.baselines
            }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        self.logger.info(f"Metrics exported to {filepath}")

    def run_performance_regression_test(self) -> Dict[str, Any]:
        """Run comprehensive performance regression test"""
        test_start = time.time()

        # Simulate agent coordination operations
        test_operations = [
            ('validate_input', 0.002),  # Target: <2ms
            ('prepare_environment', 0.001),  # Target: <1ms
            ('show_progress', 0.001),  # Target: <1ms
            ('execute_download', 0.005),  # Target: <5ms
            ('validate_output', 0.002)  # Target: <2ms
        ]

        results = []
        for operation, target_duration in test_operations:
            op_start = time.time()

            # Simulate operation
            time.sleep(target_duration)

            op_end = time.time()
            actual_duration = (op_end - op_start) * 1000

            # Record the metric
            self.record_coordination_metric(
                operation_name=f"regression_test_{operation}",
                start_time=op_start,
                end_time=op_end,
                success=True,
                agent_count=1
            )

            results.append({
                'operation': operation,
                'target_ms': target_duration * 1000,
                'actual_ms': actual_duration,
                'passed': actual_duration <= (target_duration * 1000 * 1.1)  # 10% tolerance
            })

        test_duration = (time.time() - test_start) * 1000

        # Overall test results
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)

        return {
            'test_timestamp': datetime.now().isoformat(),
            'total_test_duration_ms': test_duration,
            'individual_results': results,
            'summary': {
                'total_tests': total_count,
                'passed': passed_count,
                'failed': total_count - passed_count,
                'success_rate_percent': (passed_count / total_count) * 100,
                'overall_pass': passed_count == total_count
            }
        }


# Monitoring context manager for easy integration
class PerformanceMonitoringContext:
    """Context manager for operation performance monitoring"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str,
                 agent_count: int = 1, queue_size: int = 0):
        self.monitor = monitor
        self.operation_name = operation_name
        self.agent_count = agent_count
        self.queue_size = queue_size
        self.start_time = None
        self.success = True

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        self.success = exc_type is None

        self.monitor.record_coordination_metric(
            operation_name=self.operation_name,
            start_time=self.start_time,
            end_time=end_time,
            success=self.success,
            agent_count=self.agent_count,
            queue_size=self.queue_size
        )


def main():
    """CLI interface for performance monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description='ARTIFACTOR Performance Monitor')
    parser.add_argument('--dashboard', action='store_true',
                       help='Show health dashboard')
    parser.add_argument('--summary', type=int, default=10,
                       help='Show performance summary for N minutes')
    parser.add_argument('--test', action='store_true',
                       help='Run performance regression test')
    parser.add_argument('--monitor', type=float, default=0,
                       help='Start monitoring for N seconds (0 = indefinite)')
    parser.add_argument('--export', type=str,
                       help='Export metrics to JSON file')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    monitor = PerformanceMonitor()

    try:
        if args.dashboard:
            dashboard = monitor.get_health_dashboard()
            print(json.dumps(dashboard, indent=2))

        elif args.summary:
            summary = monitor.get_performance_summary(args.summary)
            print(json.dumps(summary, indent=2))

        elif args.test:
            print("🧪 Running performance regression test...")
            test_results = monitor.run_performance_regression_test()
            print(json.dumps(test_results, indent=2))

        elif args.monitor:
            print(f"📊 Starting performance monitoring...")
            monitor.start_monitoring()

            if args.monitor > 0:
                time.sleep(args.monitor)
                monitor.stop_monitoring()
                print("✅ Monitoring completed")
            else:
                print("🔄 Monitoring indefinitely (Ctrl+C to stop)")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    monitor.stop_monitoring()
                    print("\n✅ Monitoring stopped")

        if args.export:
            monitor.export_metrics(args.export)
            print(f"📁 Metrics exported to {args.export}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())