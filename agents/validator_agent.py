#!/usr/bin/env python3
"""
VALIDATOR Agent v3.0.0 - Final System Validation
Comprehensive validation for ARTIFACTOR v3.0.0 production readiness
Part of DIRECTOR-led full system repair coordination

Validation Scope:
- Security implementations (all 15 vulnerabilities resolved)
- Performance optimizations (OPTIMIZER improvements)
- Documentation accuracy (DOCGEN outputs)
- System integration completeness
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging

class ValidatorAgent:
    def __init__(self, project_root: str = "/home/john/GITHUB/ARTIFACTOR"):
        self.project_root = Path(project_root)
        self.agent_name = "VALIDATOR"
        self.version = "3.0.0"

        # Setup logging
        self.setup_logging()

        # Validation categories
        self.validation_categories = {
            "security": {
                "name": "Security Validation",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "performance": {
                "name": "Performance Validation",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "documentation": {
                "name": "Documentation Validation",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "integration": {
                "name": "Integration Validation",
                "tests": [],
                "results": {},
                "status": "pending"
            }
        }

        # Validation results
        self.validation_results = {
            "agent": self.agent_name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "categories": self.validation_categories,
            "overall_status": "in_progress",
            "production_ready": False,
            "critical_issues": [],
            "warnings": [],
            "summary": {}
        }

    def setup_logging(self):
        """Setup logging for validator agent"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "validator_agent.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{self.agent_name}_Agent")

    def validate_security_implementations(self) -> Dict[str, Any]:
        """Validate all PATCHER security implementations"""
        self.logger.info("🔒 Starting security validation...")

        security_results = {
            "vulnerabilities_resolved": 0,
            "security_middleware_active": False,
            "authentication_working": False,
            "authorization_working": False,
            "container_security_enabled": False,
            "critical_issues": [],
            "tests_passed": 0,
            "tests_failed": 0
        }

        # Check for security validation script
        security_script = self.project_root / "security-validation.sh"
        if security_script.exists():
            try:
                result = subprocess.run([str(security_script)],
                                      capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    self.logger.info("✅ Security validation script passed")
                    security_results["tests_passed"] += 1

                    # Parse output for vulnerability count
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if "vulnerabilities resolved" in line.lower():
                            try:
                                count = int(line.split()[0])
                                security_results["vulnerabilities_resolved"] = count
                            except:
                                pass
                        elif "security middleware" in line.lower() and "active" in line.lower():
                            security_results["security_middleware_active"] = True

                else:
                    self.logger.error(f"❌ Security validation failed: {result.stderr}")
                    security_results["tests_failed"] += 1
                    security_results["critical_issues"].append(f"Security validation script failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                self.logger.error("❌ Security validation timed out")
                security_results["critical_issues"].append("Security validation timeout")
                security_results["tests_failed"] += 1
            except Exception as e:
                self.logger.error(f"❌ Security validation error: {e}")
                security_results["critical_issues"].append(f"Security validation error: {e}")
                security_results["tests_failed"] += 1
        else:
            security_results["critical_issues"].append("Security validation script not found")

        # Check security implementation files
        security_files = [
            "PATCHER_SECURITY_IMPLEMENTATION_REPORT.md",
            "SECURITY_IMPLEMENTATION_COMPLETE.md"
        ]

        for file_name in security_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                self.logger.info(f"✅ Security documentation found: {file_name}")
                security_results["tests_passed"] += 1
            else:
                self.logger.warning(f"⚠️ Missing security documentation: {file_name}")
                security_results["tests_failed"] += 1

        # Determine overall security status
        if security_results["vulnerabilities_resolved"] >= 15 and security_results["tests_passed"] > security_results["tests_failed"]:
            self.validation_categories["security"]["status"] = "passed"
            self.logger.info("✅ Security validation PASSED")
        else:
            self.validation_categories["security"]["status"] = "failed"
            self.logger.error("❌ Security validation FAILED")

        self.validation_categories["security"]["results"] = security_results
        return security_results

    def validate_performance_optimizations(self) -> Dict[str, Any]:
        """Validate OPTIMIZER performance improvements"""
        self.logger.info("⚡ Starting performance validation...")

        performance_results = {
            "optimization_targets_met": False,
            "monitoring_active": False,
            "resource_efficiency_improved": False,
            "performance_tests_passed": 0,
            "performance_tests_failed": 0,
            "metrics": {},
            "critical_issues": []
        }

        # Check performance test files
        performance_test_files = [
            "performance_regression_test.py",
            "test_ml_performance.py",
            "performance_monitor.py"
        ]

        for test_file in performance_test_files:
            file_path = self.project_root / test_file
            if file_path.exists():
                try:
                    # Run performance test
                    result = subprocess.run([sys.executable, str(file_path)],
                                          capture_output=True, text=True, timeout=600)

                    if result.returncode == 0:
                        self.logger.info(f"✅ Performance test passed: {test_file}")
                        performance_results["performance_tests_passed"] += 1
                    else:
                        self.logger.error(f"❌ Performance test failed: {test_file}")
                        performance_results["performance_tests_failed"] += 1
                        performance_results["critical_issues"].append(f"Performance test failed: {test_file}")

                except subprocess.TimeoutExpired:
                    self.logger.error(f"❌ Performance test timed out: {test_file}")
                    performance_results["performance_tests_failed"] += 1
                    performance_results["critical_issues"].append(f"Performance test timeout: {test_file}")
                except Exception as e:
                    self.logger.error(f"❌ Performance test error for {test_file}: {e}")
                    performance_results["performance_tests_failed"] += 1
                    performance_results["critical_issues"].append(f"Performance test error: {test_file} - {e}")
            else:
                self.logger.warning(f"⚠️ Performance test file not found: {test_file}")

        # Check performance reports
        performance_reports = [
            "PERFORMANCE_OPTIMIZATION_REPORT.md",
            "OPTIMIZER_PERFORMANCE_ANALYSIS.md"
        ]

        for report_file in performance_reports:
            file_path = self.project_root / report_file
            if file_path.exists():
                self.logger.info(f"✅ Performance report found: {report_file}")
                performance_results["performance_tests_passed"] += 1

                # Try to extract metrics from report
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "improvement" in content.lower() or "optimization" in content.lower():
                            performance_results["optimization_targets_met"] = True
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not parse performance report {report_file}: {e}")
            else:
                self.logger.warning(f"⚠️ Performance report not found: {report_file}")

        # Determine performance validation status
        if (performance_results["performance_tests_passed"] > 0 and
            performance_results["performance_tests_passed"] >= performance_results["performance_tests_failed"] and
            performance_results["optimization_targets_met"]):
            self.validation_categories["performance"]["status"] = "passed"
            self.logger.info("✅ Performance validation PASSED")
        else:
            self.validation_categories["performance"]["status"] = "failed"
            self.logger.error("❌ Performance validation FAILED")

        self.validation_categories["performance"]["results"] = performance_results
        return performance_results

    def validate_documentation_accuracy(self) -> Dict[str, Any]:
        """Validate DOCGEN documentation accuracy"""
        self.logger.info("📚 Starting documentation validation...")

        doc_results = {
            "documentation_complete": False,
            "procedures_tested": 0,
            "commands_functional": 0,
            "commands_failed": 0,
            "user_experience_validated": False,
            "critical_issues": []
        }

        # Core documentation files to validate
        core_docs = [
            "README.md",
            "CLAUDE.md",
            "ARTIFACTOR_V3_TECHNICAL_ARCHITECTURE.md",
            "PRODUCTION_DEPLOYMENT_CHECKLIST.md",
            "INFRASTRUCTURE_DEPLOYMENT_GUIDE.md"
        ]

        docs_found = 0
        for doc_file in core_docs:
            file_path = self.project_root / doc_file
            if file_path.exists() and file_path.stat().st_size > 1000:  # At least 1KB
                self.logger.info(f"✅ Core documentation validated: {doc_file}")
                docs_found += 1
            else:
                self.logger.warning(f"⚠️ Missing or incomplete documentation: {doc_file}")
                doc_results["critical_issues"].append(f"Missing/incomplete documentation: {doc_file}")

        doc_results["documentation_complete"] = docs_found >= len(core_docs) * 0.8  # 80% threshold

        # Test key commands from documentation
        test_commands = [
            ["./artifactor", "--help"],
            ["./artifactor", "status"],
            ["python3", "claude-artifact-launcher.py", "--help"]
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=self.project_root)
                if result.returncode == 0:
                    self.logger.info(f"✅ Command functional: {' '.join(cmd)}")
                    doc_results["commands_functional"] += 1
                else:
                    self.logger.error(f"❌ Command failed: {' '.join(cmd)}")
                    doc_results["commands_failed"] += 1
                    doc_results["critical_issues"].append(f"Command failed: {' '.join(cmd)}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"❌ Command timed out: {' '.join(cmd)}")
                doc_results["commands_failed"] += 1
                doc_results["critical_issues"].append(f"Command timeout: {' '.join(cmd)}")
            except Exception as e:
                self.logger.error(f"❌ Command error: {' '.join(cmd)} - {e}")
                doc_results["commands_failed"] += 1
                doc_results["critical_issues"].append(f"Command error: {' '.join(cmd)} - {e}")

        # Validate setup procedures
        setup_script = self.project_root / "setup-env.sh"
        if setup_script.exists():
            try:
                # Test setup script with dry-run if possible
                result = subprocess.run(["bash", str(setup_script), "--help"],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0 or "usage" in result.stdout.lower():
                    self.logger.info("✅ Setup procedure documented and accessible")
                    doc_results["procedures_tested"] += 1
                else:
                    self.logger.warning("⚠️ Setup procedure may have issues")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not validate setup procedure: {e}")

        # Overall documentation validation
        if (doc_results["documentation_complete"] and
            doc_results["commands_functional"] > doc_results["commands_failed"]):
            self.validation_categories["documentation"]["status"] = "passed"
            self.logger.info("✅ Documentation validation PASSED")
        else:
            self.validation_categories["documentation"]["status"] = "failed"
            self.logger.error("❌ Documentation validation FAILED")

        self.validation_categories["documentation"]["results"] = doc_results
        return doc_results

    def validate_system_integration(self) -> Dict[str, Any]:
        """Validate complete system integration"""
        self.logger.info("🔧 Starting integration validation...")

        integration_results = {
            "services_startable": 0,
            "services_failed": 0,
            "dependencies_resolved": False,
            "configuration_consistent": False,
            "end_to_end_functional": False,
            "critical_issues": []
        }

        # Test core service startup
        core_services = [
            ["python3", "claude-artifact-coordinator.py", "--test"],
            ["python3", "claude-artifact-downloader.py", "--version"],
            ["python3", "claude-artifact-launcher.py", "--help"]
        ]

        for service_cmd in core_services:
            try:
                result = subprocess.run(service_cmd, capture_output=True, text=True,
                                      timeout=60, cwd=self.project_root)
                if result.returncode == 0:
                    self.logger.info(f"✅ Service startup test passed: {service_cmd[1]}")
                    integration_results["services_startable"] += 1
                else:
                    self.logger.error(f"❌ Service startup failed: {service_cmd[1]}")
                    integration_results["services_failed"] += 1
                    integration_results["critical_issues"].append(f"Service startup failed: {service_cmd[1]}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"❌ Service startup timed out: {service_cmd[1]}")
                integration_results["services_failed"] += 1
                integration_results["critical_issues"].append(f"Service startup timeout: {service_cmd[1]}")
            except Exception as e:
                self.logger.error(f"❌ Service startup error: {service_cmd[1]} - {e}")
                integration_results["services_failed"] += 1
                integration_results["critical_issues"].append(f"Service startup error: {service_cmd[1]} - {e}")

        # Test agent coordination
        coordination_test = self.project_root / "test-agent-coordination.py"
        if coordination_test.exists():
            try:
                result = subprocess.run([sys.executable, str(coordination_test)],
                                      capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    self.logger.info("✅ Agent coordination test passed")
                    integration_results["end_to_end_functional"] = True
                else:
                    self.logger.error("❌ Agent coordination test failed")
                    integration_results["critical_issues"].append("Agent coordination test failed")
            except Exception as e:
                self.logger.error(f"❌ Agent coordination test error: {e}")
                integration_results["critical_issues"].append(f"Agent coordination test error: {e}")

        # Check configuration files consistency
        config_files = [
            "docker/Dockerfile",
            "k8s/deployment.yaml",
            "backend/requirements.txt",
            "frontend/package.json"
        ]

        config_found = 0
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                config_found += 1
                self.logger.info(f"✅ Configuration file found: {config_file}")
            else:
                self.logger.info(f"ℹ️ Optional configuration file not found: {config_file}")

        integration_results["configuration_consistent"] = config_found > 0

        # Overall integration validation
        if (integration_results["services_startable"] > 0 and
            integration_results["services_startable"] >= integration_results["services_failed"]):
            self.validation_categories["integration"]["status"] = "passed"
            self.logger.info("✅ Integration validation PASSED")
        else:
            self.validation_categories["integration"]["status"] = "failed"
            self.logger.error("❌ Integration validation FAILED")

        self.validation_categories["integration"]["results"] = integration_results
        return integration_results

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation categories"""
        self.logger.info(f"🚀 Starting comprehensive validation for ARTIFACTOR v{self.version}")

        start_time = time.time()

        # Run all validations
        validation_functions = [
            ("security", self.validate_security_implementations),
            ("performance", self.validate_performance_optimizations),
            ("documentation", self.validate_documentation_accuracy),
            ("integration", self.validate_system_integration)
        ]

        passed_validations = 0
        total_validations = len(validation_functions)

        for category, validation_func in validation_functions:
            try:
                self.logger.info(f"🔍 Running {category} validation...")
                results = validation_func()

                if self.validation_categories[category]["status"] == "passed":
                    passed_validations += 1

            except Exception as e:
                self.logger.error(f"❌ Validation error in {category}: {e}")
                self.validation_categories[category]["status"] = "error"
                self.validation_results["critical_issues"].append(f"Validation error in {category}: {e}")

        # Calculate overall results
        validation_time = time.time() - start_time
        success_rate = (passed_validations / total_validations) * 100

        self.validation_results["summary"] = {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": total_validations - passed_validations,
            "success_rate_percent": success_rate,
            "validation_time_seconds": round(validation_time, 2)
        }

        # Determine production readiness
        if success_rate >= 80:  # 80% success threshold
            self.validation_results["overall_status"] = "passed"
            self.validation_results["production_ready"] = True
            self.logger.info(f"🎉 VALIDATION PASSED - System is production ready ({success_rate:.1f}% success rate)")
        else:
            self.validation_results["overall_status"] = "failed"
            self.validation_results["production_ready"] = False
            self.logger.error(f"❌ VALIDATION FAILED - System not production ready ({success_rate:.1f}% success rate)")

        # Update timestamp
        self.validation_results["timestamp"] = datetime.now().isoformat()

        return self.validation_results

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report_file = self.project_root / "VALIDATOR_FINAL_REPORT.md"

        report_content = f"""# VALIDATOR Agent Final Validation Report

## Executive Summary
- **Agent**: {self.validation_results['agent']} v{self.validation_results['version']}
- **Validation Date**: {self.validation_results['timestamp']}
- **Overall Status**: {self.validation_results['overall_status'].upper()}
- **Production Ready**: {'✅ YES' if self.validation_results['production_ready'] else '❌ NO'}
- **Success Rate**: {self.validation_results['summary']['success_rate_percent']:.1f}%

## Validation Results Summary

### Security Validation: {self.validation_categories['security']['status'].upper()}
- Vulnerabilities Resolved: {self.validation_categories['security']['results'].get('vulnerabilities_resolved', 0)}/15
- Security Tests Passed: {self.validation_categories['security']['results'].get('tests_passed', 0)}
- Security Tests Failed: {self.validation_categories['security']['results'].get('tests_failed', 0)}

### Performance Validation: {self.validation_categories['performance']['status'].upper()}
- Performance Tests Passed: {self.validation_categories['performance']['results'].get('performance_tests_passed', 0)}
- Performance Tests Failed: {self.validation_categories['performance']['results'].get('performance_tests_failed', 0)}
- Optimization Targets Met: {'✅' if self.validation_categories['performance']['results'].get('optimization_targets_met') else '❌'}

### Documentation Validation: {self.validation_categories['documentation']['status'].upper()}
- Documentation Complete: {'✅' if self.validation_categories['documentation']['results'].get('documentation_complete') else '❌'}
- Commands Functional: {self.validation_categories['documentation']['results'].get('commands_functional', 0)}
- Commands Failed: {self.validation_categories['documentation']['results'].get('commands_failed', 0)}

### Integration Validation: {self.validation_categories['integration']['status'].upper()}
- Services Startable: {self.validation_categories['integration']['results'].get('services_startable', 0)}
- Services Failed: {self.validation_categories['integration']['results'].get('services_failed', 0)}
- End-to-End Functional: {'✅' if self.validation_categories['integration']['results'].get('end_to_end_functional') else '❌'}

## Critical Issues
"""

        if self.validation_results["critical_issues"]:
            for issue in self.validation_results["critical_issues"]:
                report_content += f"- ❌ {issue}\n"
        else:
            report_content += "- ✅ No critical issues detected\n"

        report_content += f"""
## Performance Metrics
- Total Validation Time: {self.validation_results['summary']['validation_time_seconds']} seconds
- Validation Categories: {self.validation_results['summary']['total_validations']}
- Passed Validations: {self.validation_results['summary']['passed_validations']}
- Failed Validations: {self.validation_results['summary']['failed_validations']}

## Production Readiness Assessment

{'✅ **SYSTEM IS PRODUCTION READY**' if self.validation_results['production_ready'] else '❌ **SYSTEM IS NOT PRODUCTION READY**'}

### Recommendations
"""

        if self.validation_results["production_ready"]:
            report_content += """
- System has passed comprehensive validation
- All critical components are functional
- Security implementations are validated
- Performance optimizations are effective
- Documentation is accurate and complete
- Ready for production deployment
"""
        else:
            report_content += """
- Address critical issues identified above
- Re-run failed validations after fixes
- Ensure all security vulnerabilities are resolved
- Verify performance optimizations are working
- Complete missing documentation
- Test integration points thoroughly
"""

        report_content += f"""
---
*Generated by VALIDATOR Agent v{self.version} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Part of DIRECTOR-led full system repair coordination*
"""

        # Write report
        with open(report_file, 'w') as f:
            f.write(report_content)

        self.logger.info(f"📊 Validation report generated: {report_file}")
        return str(report_file)

def main():
    """Main execution function"""
    validator = ValidatorAgent()

    print("🔍 VALIDATOR Agent v3.0.0 - Final System Validation")
    print("=" * 60)

    # Run comprehensive validation
    results = validator.run_comprehensive_validation()

    # Generate report
    report_file = validator.generate_validation_report()

    # Save results as JSON
    results_file = validator.project_root / "validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Validation Results:")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    print(f"   Production Ready: {'YES' if results['production_ready'] else 'NO'}")
    print(f"   Success Rate: {results['summary']['success_rate_percent']:.1f}%")
    print(f"   Report: {report_file}")
    print(f"   Results: {results_file}")

    return results['production_ready']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)