#!/usr/bin/env python3
"""
Etherscan API Debug Dashboard
Comprehensive monitoring and debugging interface for the Etherscan API deployment
"""

import asyncio
import json
import time
import subprocess
import requests
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from pathlib import Path

class EtherscanDebugDashboard:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.prometheus_url = "http://localhost:9090"
        self.redis_host = "localhost"
        self.redis_port = 6379

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def check_docker_containers(self) -> Dict[str, Any]:
        """Check status of all Docker containers"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )

            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))

            status = {
                "total_containers": len(containers),
                "running_containers": len([c for c in containers if c.get("State") == "running"]),
                "containers": containers,
                "status": "healthy" if len(containers) >= 8 else "degraded"
            }

            return status

        except subprocess.CalledProcessError as e:
            return {"error": f"Docker check failed: {e}", "status": "error"}

    def check_api_health(self) -> Dict[str, Any]:
        """Check API server health and performance"""
        try:
            # Health check
            health_response = requests.get(f"{self.base_url}/health", timeout=5)

            # Test API endpoint
            test_response = requests.get(
                f"{self.base_url}/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9",
                timeout=10
            )

            # Get metrics
            metrics_response = requests.get(f"{self.base_url}/metrics", timeout=5)

            return {
                "health_status": health_response.status_code,
                "api_status": test_response.status_code,
                "metrics_available": metrics_response.status_code == 200,
                "response_time": test_response.elapsed.total_seconds(),
                "status": "healthy" if all([
                    health_response.status_code == 200,
                    test_response.status_code == 200,
                    test_response.elapsed.total_seconds() < 5.0
                ]) else "degraded"
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"API check failed: {e}", "status": "error"}

    def check_redis_status(self) -> Dict[str, Any]:
        """Check Redis cache status"""
        try:
            import redis
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)

            info = r.info()
            keys = r.dbsize()
            memory_usage = info.get('used_memory_human', 'Unknown')

            return {
                "connected": True,
                "keys_count": keys,
                "memory_usage": memory_usage,
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "status": "healthy"
            }

        except Exception as e:
            return {"error": f"Redis check failed: {e}", "status": "error"}

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "status": "healthy" if all([
                    cpu_percent < 80,
                    memory.percent < 85,
                    disk.percent < 90
                ]) else "warning"
            }

        except Exception as e:
            return {"error": f"System check failed: {e}", "status": "error"}

    def get_prometheus_metrics(self) -> Dict[str, Any]:
        """Get metrics from Prometheus"""
        try:
            queries = {
                "request_rate": "rate(http_requests_total[5m])",
                "error_rate": "rate(http_requests_total{status!~'2..'}[5m])",
                "response_time": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "cache_hit_rate": "rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])"
            }

            metrics = {}
            for name, query in queries.items():
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("result"):
                        value = data["data"]["result"][0]["value"][1]
                        metrics[name] = float(value)
                    else:
                        metrics[name] = 0.0
                else:
                    metrics[name] = "error"

            return {"metrics": metrics, "status": "healthy"}

        except Exception as e:
            return {"error": f"Prometheus check failed: {e}", "status": "error"}

    def run_diagnostic_tests(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic tests"""
        tests = {
            "etherscan_api_key": self.test_etherscan_api(),
            "rate_limiting": self.test_rate_limiting(),
            "caching": self.test_caching_behavior(),
            "error_handling": self.test_error_handling()
        }

        return {
            "tests": tests,
            "status": "passed" if all(t.get("passed", False) for t in tests.values()) else "failed"
        }

    def test_etherscan_api(self) -> Dict[str, Any]:
        """Test direct Etherscan API connectivity"""
        try:
            response = requests.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "balance",
                    "address": "0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9",
                    "tag": "latest",
                    "apikey": "SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "passed": data.get("status") == "1",
                    "response_time": response.elapsed.total_seconds(),
                    "message": data.get("message", "Unknown")
                }
            else:
                return {
                    "passed": False,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test API rate limiting behavior"""
        try:
            start_time = time.time()
            responses = []

            # Make 6 rapid requests (should hit rate limit)
            for i in range(6):
                response = requests.get(
                    f"{self.base_url}/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9",
                    timeout=5
                )
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay

            elapsed = time.time() - start_time
            rate_limited = any(status == 429 for status in responses)

            return {
                "passed": rate_limited,  # Rate limiting should kick in
                "responses": responses,
                "elapsed_seconds": round(elapsed, 2),
                "rate_limited": rate_limited
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_caching_behavior(self) -> Dict[str, Any]:
        """Test Redis caching functionality"""
        try:
            # First request (should hit Etherscan)
            start1 = time.time()
            response1 = requests.get(
                f"{self.base_url}/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9",
                timeout=10
            )
            time1 = time.time() - start1

            # Second request (should hit cache)
            start2 = time.time()
            response2 = requests.get(
                f"{self.base_url}/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9",
                timeout=10
            )
            time2 = time.time() - start2

            cache_working = time2 < time1 * 0.5  # Cached should be much faster

            return {
                "passed": cache_working and response1.status_code == 200,
                "first_request_time": round(time1, 3),
                "second_request_time": round(time2, 3),
                "cache_speedup": round(time1 / time2, 2) if time2 > 0 else "N/A"
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def test_error_handling(self) -> Dict[str, Any]:
        """Test API error handling"""
        try:
            # Test invalid address
            response = requests.get(
                f"{self.base_url}/api/balance/invalid_address",
                timeout=5
            )

            error_handled = response.status_code == 400

            return {
                "passed": error_handled,
                "status_code": response.status_code,
                "error_response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def generate_debug_report(self) -> Dict[str, Any]:
        """Generate comprehensive debug report"""
        timestamp = datetime.now().isoformat()

        report = {
            "timestamp": timestamp,
            "docker_status": self.check_docker_containers(),
            "api_health": self.check_api_health(),
            "redis_status": self.check_redis_status(),
            "system_resources": self.check_system_resources(),
            "prometheus_metrics": self.get_prometheus_metrics(),
            "diagnostic_tests": self.run_diagnostic_tests()
        }

        # Calculate overall health
        statuses = [
            report["docker_status"].get("status"),
            report["api_health"].get("status"),
            report["redis_status"].get("status"),
            report["system_resources"].get("status"),
            report["prometheus_metrics"].get("status"),
            report["diagnostic_tests"].get("status")
        ]

        if "error" in statuses:
            overall_status = "error"
        elif "degraded" in statuses or "failed" in statuses:
            overall_status = "degraded"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        report["overall_status"] = overall_status

        return report

    def print_dashboard(self):
        """Print formatted dashboard to console"""
        report = self.generate_debug_report()

        print("=" * 80)
        print(f"🔧 ETHERSCAN API DEBUG DASHBOARD - {report['timestamp']}")
        print("=" * 80)

        # Overall Status
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "degraded": "🟡",
            "error": "❌"
        }

        print(f"\n🎯 OVERALL STATUS: {status_emoji.get(report['overall_status'], '❓')} {report['overall_status'].upper()}")

        # Docker Status
        docker = report["docker_status"]
        print(f"\n🐳 DOCKER CONTAINERS: {status_emoji.get(docker.get('status'), '❓')}")
        if "error" not in docker:
            print(f"   Running: {docker.get('running_containers', 0)}/{docker.get('total_containers', 0)}")
            for container in docker.get("containers", [])[:5]:  # Show first 5
                print(f"   • {container.get('Names', 'Unknown')}: {container.get('State', 'Unknown')}")
        else:
            print(f"   Error: {docker.get('error', 'Unknown')}")

        # API Health
        api = report["api_health"]
        print(f"\n🌐 API SERVER: {status_emoji.get(api.get('status'), '❓')}")
        if "error" not in api:
            print(f"   Health: HTTP {api.get('health_status', 'Unknown')}")
            print(f"   API Test: HTTP {api.get('api_status', 'Unknown')}")
            print(f"   Response Time: {api.get('response_time', 'Unknown')}s")
        else:
            print(f"   Error: {api.get('error', 'Unknown')}")

        # Redis Status
        redis = report["redis_status"]
        print(f"\n🗄️ REDIS CACHE: {status_emoji.get(redis.get('status'), '❓')}")
        if "error" not in redis:
            print(f"   Keys: {redis.get('keys_count', 0)}")
            print(f"   Memory: {redis.get('memory_usage', 'Unknown')}")
            print(f"   Uptime: {redis.get('uptime_seconds', 0)}s")
        else:
            print(f"   Error: {redis.get('error', 'Unknown')}")

        # System Resources
        system = report["system_resources"]
        print(f"\n💻 SYSTEM RESOURCES: {status_emoji.get(system.get('status'), '❓')}")
        if "error" not in system:
            print(f"   CPU: {system.get('cpu_percent', 0)}%")
            print(f"   Memory: {system.get('memory_percent', 0)}% ({system.get('memory_available_gb', 0)}GB free)")
            print(f"   Disk: {system.get('disk_percent', 0)}% ({system.get('disk_free_gb', 0)}GB free)")
        else:
            print(f"   Error: {system.get('error', 'Unknown')}")

        # Prometheus Metrics
        prom = report["prometheus_metrics"]
        print(f"\n📊 PROMETHEUS METRICS: {status_emoji.get(prom.get('status'), '❓')}")
        if "error" not in prom and "metrics" in prom:
            metrics = prom["metrics"]
            print(f"   Request Rate: {metrics.get('request_rate', 'N/A')}/s")
            print(f"   Error Rate: {metrics.get('error_rate', 'N/A')}/s")
            print(f"   95th Percentile Response: {metrics.get('response_time', 'N/A')}s")
            print(f"   Cache Hit Rate: {metrics.get('cache_hit_rate', 'N/A')}")
        else:
            print(f"   Error: {prom.get('error', 'Metrics unavailable')}")

        # Diagnostic Tests
        tests = report["diagnostic_tests"]
        print(f"\n🧪 DIAGNOSTIC TESTS: {status_emoji.get(tests.get('status'), '❓')}")
        for test_name, test_result in tests.get("tests", {}).items():
            status = "✅" if test_result.get("passed", False) else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
            if not test_result.get("passed", False) and "error" in test_result:
                print(f"      Error: {test_result['error']}")

        print("\n" + "=" * 80)

        # Save report to file
        report_file = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📁 Detailed report saved: {report_file}")

        return report

def main():
    """Main function for running the debug dashboard"""
    dashboard = EtherscanDebugDashboard()

    try:
        while True:
            dashboard.print_dashboard()
            print("\n⏱️  Refreshing in 30 seconds... (Ctrl+C to exit)")
            time.sleep(30)
            print("\033[2J\033[H")  # Clear screen

    except KeyboardInterrupt:
        print("\n👋 Debug dashboard stopped.")

if __name__ == "__main__":
    main()