#!/usr/bin/env python3
"""
ARTIFACTOR v2.0 System Health Checker
MONITOR Agent: Comprehensive system health validation and diagnostics

This module provides health checking capabilities for the ARTIFACTOR system,
validating agent coordination, virtual environment, dependencies, and performance.
"""

import subprocess
import sys
import os
import time
import json
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging


@dataclass
class HealthCheck:
    """Health check result data structure"""
    name: str
    status: str  # "pass", "warning", "fail"
    message: str
    details: Dict[str, Any]
    duration_ms: float


class SystemHealthChecker:
    """
    Comprehensive system health checker for ARTIFACTOR v2.0

    Validates:
    - Agent coordination system
    - Virtual environment integrity
    - Dependency availability
    - Performance metrics
    - System resources
    """

    def __init__(self):
        self.logger = logging.getLogger('health_checker')
        self.artifactor_root = Path(__file__).parent
        self.venv_path = Path.home() / '.claude-artifacts' / 'venv'

    def run_all_checks(self) -> List[HealthCheck]:
        """Run all health checks and return results"""
        checks = [
            self._check_python_environment,
            self._check_virtual_environment,
            self._check_core_scripts,
            self._check_dependencies,
            self._check_agent_coordination,
            self._check_system_resources,
            self._check_performance_baseline,
            self._check_optimization_status
        ]

        results = []
        for check_func in checks:
            try:
                start_time = time.time()
                result = check_func()
                duration = (time.time() - start_time) * 1000
                result.duration_ms = duration
                results.append(result)
            except Exception as e:
                results.append(HealthCheck(
                    name=check_func.__name__,
                    status="fail",
                    message=f"Check failed with exception: {e}",
                    details={"exception": str(e)},
                    duration_ms=0
                ))

        return results

    def _check_python_environment(self) -> HealthCheck:
        """Check Python environment"""
        python_version = sys.version_info
        python_path = sys.executable

        details = {
            "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "executable": python_path,
            "platform": sys.platform
        }

        if python_version >= (3, 7):
            return HealthCheck(
                name="Python Environment",
                status="pass",
                message=f"Python {details['version']} is supported",
                details=details,
                duration_ms=0
            )
        else:
            return HealthCheck(
                name="Python Environment",
                status="fail",
                message=f"Python {details['version']} is not supported (requires >=3.7)",
                details=details,
                duration_ms=0
            )

    def _check_virtual_environment(self) -> HealthCheck:
        """Check virtual environment status"""
        venv_python = self.venv_path / 'bin' / 'python'
        venv_pip = self.venv_path / 'bin' / 'pip'

        details = {
            "venv_path": str(self.venv_path),
            "venv_exists": self.venv_path.exists(),
            "python_executable": venv_python.exists(),
            "pip_executable": venv_pip.exists()
        }

        if self.venv_path.exists() and venv_python.exists():
            # Test virtual environment
            try:
                result = subprocess.run([
                    str(venv_python), '-c',
                    'import sys; print(sys.prefix)'
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    details["venv_prefix"] = result.stdout.strip()
                    return HealthCheck(
                        name="Virtual Environment",
                        status="pass",
                        message="Virtual environment is functional",
                        details=details,
                        duration_ms=0
                    )
                else:
                    details["error"] = result.stderr
                    return HealthCheck(
                        name="Virtual Environment",
                        status="fail",
                        message="Virtual environment is not functional",
                        details=details,
                        duration_ms=0
                    )
            except subprocess.TimeoutExpired:
                return HealthCheck(
                    name="Virtual Environment",
                    status="fail",
                    message="Virtual environment test timed out",
                    details=details,
                    duration_ms=0
                )
        else:
            return HealthCheck(
                name="Virtual Environment",
                status="fail",
                message="Virtual environment not found or incomplete",
                details=details,
                duration_ms=0
            )

    def _check_core_scripts(self) -> HealthCheck:
        """Check core ARTIFACTOR scripts"""
        required_scripts = [
            'artifactor',
            'claude-artifact-coordinator.py',
            'claude-artifact-downloader.py',
            'claude-artifact-launcher.py',
            'claude-artifact-venv-manager.py'
        ]

        details = {}
        missing_scripts = []

        for script in required_scripts:
            script_path = self.artifactor_root / script
            exists = script_path.exists()
            details[script] = {
                "exists": exists,
                "path": str(script_path),
                "executable": script_path.is_file() and os.access(script_path, os.X_OK) if exists else False
            }

            if not exists:
                missing_scripts.append(script)

        if not missing_scripts:
            return HealthCheck(
                name="Core Scripts",
                status="pass",
                message="All core scripts are present",
                details=details,
                duration_ms=0
            )
        else:
            return HealthCheck(
                name="Core Scripts",
                status="fail",
                message=f"Missing scripts: {', '.join(missing_scripts)}",
                details=details,
                duration_ms=0
            )

    def _check_dependencies(self) -> HealthCheck:
        """Check Python dependencies"""
        if not self.venv_path.exists():
            return HealthCheck(
                name="Dependencies",
                status="fail",
                message="Cannot check dependencies: virtual environment not found",
                details={},
                duration_ms=0
            )

        venv_python = self.venv_path / 'bin' / 'python'
        required_packages = [
            'requests', 'urllib3', 'psutil', 'tkinter'
        ]

        details = {}
        missing_packages = []

        for package in required_packages:
            try:
                if package == 'tkinter':
                    # tkinter is built-in
                    test_cmd = f'import {package}'
                else:
                    test_cmd = f'import {package}; print({package}.__version__)'

                result = subprocess.run([
                    str(venv_python), '-c', test_cmd
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    version = result.stdout.strip() if result.stdout.strip() else "built-in"
                    details[package] = {
                        "available": True,
                        "version": version
                    }
                else:
                    details[package] = {
                        "available": False,
                        "error": result.stderr.strip()
                    }
                    missing_packages.append(package)

            except subprocess.TimeoutExpired:
                details[package] = {
                    "available": False,
                    "error": "Import test timed out"
                }
                missing_packages.append(package)

        if not missing_packages:
            return HealthCheck(
                name="Dependencies",
                status="pass",
                message="All required dependencies are available",
                details=details,
                duration_ms=0
            )
        else:
            return HealthCheck(
                name="Dependencies",
                status="fail",
                message=f"Missing dependencies: {', '.join(missing_packages)}",
                details=details,
                duration_ms=0
            )

    def _check_agent_coordination(self) -> HealthCheck:
        """Check agent coordination system"""
        test_script = self.artifactor_root / 'test-agent-coordination.py'

        if not test_script.exists():
            return HealthCheck(
                name="Agent Coordination",
                status="fail",
                message="Agent coordination test script not found",
                details={"test_script": str(test_script)},
                duration_ms=0
            )

        try:
            # Run agent coordination test
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=30, cwd=self.artifactor_root)

            # Parse output for success indicators
            output_lines = result.stdout.split('\n')
            success_indicators = [
                line for line in output_lines
                if 'test completed successfully' in line.lower() or
                   'tests passed' in line.lower()
            ]

            # Extract performance data
            performance_data = {}
            for line in output_lines:
                if 'Total execution time:' in line:
                    try:
                        time_str = line.split(':')[1].strip().replace('s', '')
                        performance_data['execution_time_s'] = float(time_str)
                    except (IndexError, ValueError):
                        pass
                elif 'Success rate:' in line:
                    try:
                        rate_str = line.split(':')[1].strip().replace('%', '')
                        performance_data['success_rate_percent'] = float(rate_str)
                    except (IndexError, ValueError):
                        pass

            details = {
                "test_exit_code": result.returncode,
                "performance": performance_data,
                "success_indicators": success_indicators,
                "output_length": len(result.stdout)
            }

            if result.returncode == 0 and success_indicators:
                return HealthCheck(
                    name="Agent Coordination",
                    status="pass",
                    message="Agent coordination system is functional",
                    details=details,
                    duration_ms=0
                )
            else:
                return HealthCheck(
                    name="Agent Coordination",
                    status="fail",
                    message="Agent coordination test failed",
                    details={**details, "stderr": result.stderr[:500]},
                    duration_ms=0
                )

        except subprocess.TimeoutExpired:
            return HealthCheck(
                name="Agent Coordination",
                status="fail",
                message="Agent coordination test timed out",
                details={"timeout_seconds": 30},
                duration_ms=0
            )

    def _check_system_resources(self) -> HealthCheck:
        """Check system resource availability"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            details = {
                "cpu_percent": cpu_percent,
                "memory_total_mb": memory.total / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "memory_used_percent": memory.percent,
                "disk_total_gb": disk.total / 1024 / 1024 / 1024,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "disk_used_percent": (disk.used / disk.total) * 100
            }

            # Check thresholds
            warnings = []
            if cpu_percent > 90:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 90:
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            if details["disk_used_percent"] > 90:
                warnings.append(f"High disk usage: {details['disk_used_percent']:.1f}%")

            if warnings:
                return HealthCheck(
                    name="System Resources",
                    status="warning",
                    message=f"Resource warnings: {'; '.join(warnings)}",
                    details=details,
                    duration_ms=0
                )
            else:
                return HealthCheck(
                    name="System Resources",
                    status="pass",
                    message="System resources are healthy",
                    details=details,
                    duration_ms=0
                )

        except Exception as e:
            return HealthCheck(
                name="System Resources",
                status="fail",
                message=f"Failed to check system resources: {e}",
                details={"error": str(e)},
                duration_ms=0
            )

    def _check_performance_baseline(self) -> HealthCheck:
        """Check performance against baseline"""
        # Read recent performance data from logs if available
        log_file = self.artifactor_root / 'agent_coordination.log'

        details = {}
        if log_file.exists():
            try:
                # Read last 100 lines of log
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]

                # Look for timing information
                timing_data = []
                for line in lines:
                    if 'Total execution time:' in line and 'test completed' in line:
                        # Extract timing from test output
                        try:
                            time_part = line.split('Total execution time:')[1].split('s')[0].strip()
                            timing_data.append(float(time_part))
                        except (IndexError, ValueError):
                            pass

                if timing_data:
                    avg_time = sum(timing_data) / len(timing_data)
                    details = {
                        "recent_tests": len(timing_data),
                        "avg_execution_time_s": avg_time,
                        "baseline_comparison": {
                            "target_ms": 10,  # OPTIMIZER target
                            "actual_ms": avg_time * 1000
                        }
                    }

                    # Check against OPTIMIZER targets
                    if avg_time * 1000 <= 50:  # Allow 50ms for full test
                        return HealthCheck(
                            name="Performance Baseline",
                            status="pass",
                            message=f"Performance within targets: {avg_time*1000:.1f}ms",
                            details=details,
                            duration_ms=0
                        )
                    else:
                        return HealthCheck(
                            name="Performance Baseline",
                            status="warning",
                            message=f"Performance above target: {avg_time*1000:.1f}ms",
                            details=details,
                            duration_ms=0
                        )
                else:
                    return HealthCheck(
                        name="Performance Baseline",
                        status="warning",
                        message="No recent performance data found",
                        details={"log_lines_checked": len(lines)},
                        duration_ms=0
                    )

            except Exception as e:
                return HealthCheck(
                    name="Performance Baseline",
                    status="fail",
                    message=f"Failed to read performance data: {e}",
                    details={"error": str(e)},
                    duration_ms=0
                )
        else:
            return HealthCheck(
                name="Performance Baseline",
                status="warning",
                message="No performance log file found",
                details={"expected_log": str(log_file)},
                duration_ms=0
            )

    def _check_optimization_status(self) -> HealthCheck:
        """Check OPTIMIZER improvements status"""
        optimized_file = self.artifactor_root / 'claude-artifact-coordinator-optimized.py'
        results_file = self.artifactor_root / 'OPTIMIZATION_RESULTS_SUMMARY.md'

        details = {
            "optimized_coordinator_exists": optimized_file.exists(),
            "results_summary_exists": results_file.exists()
        }

        if optimized_file.exists() and results_file.exists():
            # Check if optimization is deployed
            original_file = self.artifactor_root / 'claude-artifact-coordinator.py'
            optimized_size = optimized_file.stat().st_size
            original_size = original_file.stat().st_size

            details.update({
                "optimized_file_size": optimized_size,
                "original_file_size": original_size,
                "size_difference": optimized_size - original_size
            })

            # Read optimization results
            try:
                with open(results_file, 'r') as f:
                    content = f.read()
                    if "✅ OPTIMIZATION TARGETS ACHIEVED" in content:
                        details["optimization_targets_achieved"] = True
                        return HealthCheck(
                            name="Optimization Status",
                            status="pass",
                            message="OPTIMIZER improvements completed and documented",
                            details=details,
                            duration_ms=0
                        )
                    else:
                        details["optimization_targets_achieved"] = False
                        return HealthCheck(
                            name="Optimization Status",
                            status="warning",
                            message="Optimization completed but targets not confirmed",
                            details=details,
                            duration_ms=0
                        )
            except Exception as e:
                details["read_error"] = str(e)
                return HealthCheck(
                    name="Optimization Status",
                    status="warning",
                    message="Could not read optimization results",
                    details=details,
                    duration_ms=0
                )
        else:
            return HealthCheck(
                name="Optimization Status",
                status="fail",
                message="OPTIMIZER improvements not found",
                details=details,
                duration_ms=0
            )

    def generate_health_report(self, checks: List[HealthCheck]) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks if c.status == "pass")
        warning_checks = sum(1 for c in checks if c.status == "warning")
        failed_checks = sum(1 for c in checks if c.status == "fail")

        # Overall health status
        if failed_checks > 0:
            overall_status = "unhealthy"
        elif warning_checks > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        # Performance summary
        performance_checks = [c for c in checks if "performance" in c.name.lower()]
        total_duration = sum(c.duration_ms for c in checks)

        return {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "warnings": warning_checks,
                "failed": failed_checks,
                "success_rate_percent": (passed_checks / total_checks) * 100,
                "total_duration_ms": total_duration
            },
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "duration_ms": c.duration_ms,
                    "details": c.details
                }
                for c in checks
            ],
            "recommendations": self._generate_recommendations(checks)
        }

    def _generate_recommendations(self, checks: List[HealthCheck]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []

        for check in checks:
            if check.status == "fail":
                if "Virtual Environment" in check.name:
                    recommendations.append("Run './artifactor setup --force' to rebuild virtual environment")
                elif "Dependencies" in check.name:
                    recommendations.append("Install missing dependencies using pip in the virtual environment")
                elif "Agent Coordination" in check.name:
                    recommendations.append("Check agent coordination system and run diagnostics")
                elif "Core Scripts" in check.name:
                    recommendations.append("Ensure all ARTIFACTOR files are present and executable")

            elif check.status == "warning":
                if "System Resources" in check.name:
                    recommendations.append("Monitor system resource usage and close unnecessary processes")
                elif "Performance" in check.name:
                    recommendations.append("Consider running performance optimization or check for system load")

        # General recommendations
        if not any("optimization" in r.lower() for r in recommendations):
            opt_check = next((c for c in checks if "optimization" in c.name.lower()), None)
            if opt_check and opt_check.status == "pass":
                recommendations.append("System is optimized and running well - continue monitoring")

        return recommendations


def main():
    """CLI interface for health checking"""
    import argparse

    parser = argparse.ArgumentParser(description='ARTIFACTOR System Health Checker')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick health check (essential checks only)')
    parser.add_argument('--export', type=str,
                       help='Export health report to file')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    checker = SystemHealthChecker()

    print("🏥 ARTIFACTOR System Health Check")
    print("=" * 50)

    # Run health checks
    checks = checker.run_all_checks()
    report = checker.generate_health_report(checks)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        # Human-readable output
        print(f"\n📊 Overall Status: {report['overall_status'].upper()}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        print(f"🎯 Success Rate: {report['summary']['success_rate_percent']:.1f}%")
        print(f"⏱️  Total Duration: {report['summary']['total_duration_ms']:.1f}ms")

        print("\n📋 Check Results:")
        print("-" * 50)
        for check in checks:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}[check.status]
            print(f"{status_icon} {check.name}: {check.message}")
            if check.duration_ms > 100:  # Show duration for slow checks
                print(f"   Duration: {check.duration_ms:.1f}ms")

        if report['recommendations']:
            print("\n💡 Recommendations:")
            print("-" * 50)
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")

    if args.export:
        with open(args.export, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📁 Health report exported to {args.export}")

    # Exit code based on health status
    if report['overall_status'] == "unhealthy":
        return 1
    elif report['overall_status'] == "warning":
        return 2
    else:
        return 0


if __name__ == '__main__':
    exit(main())