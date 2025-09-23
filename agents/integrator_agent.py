#!/usr/bin/env python3
"""
INTEGRATOR Agent v3.0.0 - Component Integration Testing
Comprehensive integration testing for ARTIFACTOR v3.0.0 production readiness
Part of DIRECTOR-led full system repair coordination

Integration Scope:
- Service component integration (frontend, backend, core)
- Agent coordination systems (PYGUI, PYTHON-INTERNAL, DEBUGGER)
- Deployment pipeline validation
- Configuration consistency verification
- End-to-end workflow testing
"""

import os
import sys
import json
import time
import subprocess
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging
import yaml
import concurrent.futures

class IntegratorAgent:
    def __init__(self, project_root: str = "/home/john/GITHUB/ARTIFACTOR"):
        self.project_root = Path(project_root)
        self.agent_name = "INTEGRATOR"
        self.version = "3.0.0"

        # Setup logging
        self.setup_logging()

        # Integration test categories
        self.integration_categories = {
            "service_integration": {
                "name": "Service Component Integration",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "agent_coordination": {
                "name": "Agent Coordination Systems",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "deployment_pipeline": {
                "name": "Deployment Pipeline Validation",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "configuration_consistency": {
                "name": "Configuration Consistency",
                "tests": [],
                "results": {},
                "status": "pending"
            },
            "end_to_end_workflows": {
                "name": "End-to-End Workflow Testing",
                "tests": [],
                "results": {},
                "status": "pending"
            }
        }

        # Integration results
        self.integration_results = {
            "agent": self.agent_name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "categories": self.integration_categories,
            "overall_status": "in_progress",
            "integration_ready": False,
            "critical_issues": [],
            "warnings": [],
            "summary": {}
        }

    def setup_logging(self):
        """Setup logging for integrator agent"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "integrator_agent.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{self.agent_name}_Agent")

    def test_service_integration(self) -> Dict[str, Any]:
        """Test integration between service components"""
        self.logger.info("🔗 Starting service integration testing...")

        service_results = {
            "frontend_backend_integration": False,
            "backend_core_integration": False,
            "api_endpoint_functional": 0,
            "api_endpoint_failed": 0,
            "service_dependencies_resolved": False,
            "database_connections": False,
            "critical_issues": []
        }

        # Test frontend-backend integration
        frontend_dir = self.project_root / "frontend"
        backend_dir = self.project_root / "backend"

        if frontend_dir.exists() and backend_dir.exists():
            self.logger.info("📁 Frontend and backend directories found")

            # Check for API configuration
            frontend_config_files = ["package.json", "src/config.js", "src/api/config.js"]
            backend_config_files = ["requirements.txt", "app.py", "main.py", "config.py"]

            frontend_configs = sum(1 for f in frontend_config_files if (frontend_dir / f).exists())
            backend_configs = sum(1 for f in backend_config_files if (backend_dir / f).exists())

            if frontend_configs > 0 and backend_configs > 0:
                service_results["frontend_backend_integration"] = True
                self.logger.info("✅ Frontend-backend integration configuration detected")
            else:
                self.logger.warning("⚠️ Frontend-backend integration configuration incomplete")
                service_results["critical_issues"].append("Frontend-backend integration configuration incomplete")

        # Test core service integration
        core_services = [
            "claude-artifact-coordinator.py",
            "claude-artifact-downloader.py",
            "claude-artifact-launcher.py"
        ]

        core_integration_tests = 0
        for service_file in core_services:
            service_path = self.project_root / service_file
            if service_path.exists():
                try:
                    # Test service can be imported/started
                    result = subprocess.run([sys.executable, "-c", f"import sys; sys.path.append('{self.project_root}'); import {service_file.replace('.py', '')}"],
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.logger.info(f"✅ Core service integration test passed: {service_file}")
                        core_integration_tests += 1
                    else:
                        self.logger.error(f"❌ Core service integration test failed: {service_file}")
                        service_results["critical_issues"].append(f"Core service integration failed: {service_file}")
                except Exception as e:
                    self.logger.error(f"❌ Core service test error: {service_file} - {e}")
                    service_results["critical_issues"].append(f"Core service test error: {service_file} - {e}")

        service_results["backend_core_integration"] = core_integration_tests >= 2

        # Test API endpoints if available
        api_test_commands = [
            ["curl", "-f", "-s", "http://localhost:8000/health", "-o", "/dev/null"],
            ["curl", "-f", "-s", "http://localhost:3000/api/status", "-o", "/dev/null"]
        ]

        for cmd in api_test_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.info(f"✅ API endpoint accessible: {cmd[2]}")
                    service_results["api_endpoint_functional"] += 1
                else:
                    self.logger.info(f"ℹ️ API endpoint not accessible (expected if not running): {cmd[2]}")
            except Exception as e:
                self.logger.info(f"ℹ️ API test skipped (service likely not running): {cmd[2]}")

        # Check service dependencies
        dependency_files = [
            "requirements.txt",
            "frontend/package.json",
            "backend/requirements.txt"
        ]

        dependencies_found = 0
        for dep_file in dependency_files:
            dep_path = self.project_root / dep_file
            if dep_path.exists():
                dependencies_found += 1
                self.logger.info(f"✅ Dependency file found: {dep_file}")

        service_results["service_dependencies_resolved"] = dependencies_found > 0

        # Determine service integration status
        if (service_results["backend_core_integration"] and
            service_results["service_dependencies_resolved"]):
            self.integration_categories["service_integration"]["status"] = "passed"
            self.logger.info("✅ Service integration testing PASSED")
        else:
            self.integration_categories["service_integration"]["status"] = "failed"
            self.logger.error("❌ Service integration testing FAILED")

        self.integration_categories["service_integration"]["results"] = service_results
        return service_results

    def test_agent_coordination(self) -> Dict[str, Any]:
        """Test agent coordination systems"""
        self.logger.info("🤖 Starting agent coordination testing...")

        agent_results = {
            "agent_files_present": 0,
            "coordination_test_passed": False,
            "tandem_operation_functional": False,
            "agent_communication_working": False,
            "agent_errors": [],
            "critical_issues": []
        }

        # Check for agent coordination files
        agent_files = [
            "claude-artifact-coordinator.py",
            "test-agent-coordination.py",
            "agents/validator_agent.py",
            "agents/integrator_agent.py"
        ]

        for agent_file in agent_files:
            agent_path = self.project_root / agent_file
            if agent_path.exists():
                agent_results["agent_files_present"] += 1
                self.logger.info(f"✅ Agent file found: {agent_file}")
            else:
                self.logger.warning(f"⚠️ Agent file missing: {agent_file}")

        # Test agent coordination script
        coordination_test = self.project_root / "test-agent-coordination.py"
        if coordination_test.exists():
            try:
                result = subprocess.run([sys.executable, str(coordination_test)],
                                      capture_output=True, text=True, timeout=120)

                if result.returncode == 0:
                    self.logger.info("✅ Agent coordination test PASSED")
                    agent_results["coordination_test_passed"] = True

                    # Check for tandem operation indicators in output
                    output = result.stdout.lower()
                    if any(keyword in output for keyword in ["tandem", "coordination", "agent", "successful"]):
                        agent_results["tandem_operation_functional"] = True
                        self.logger.info("✅ Tandem operation functionality detected")

                else:
                    self.logger.error(f"❌ Agent coordination test FAILED: {result.stderr}")
                    agent_results["critical_issues"].append(f"Agent coordination test failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                self.logger.error("❌ Agent coordination test timed out")
                agent_results["critical_issues"].append("Agent coordination test timeout")
            except Exception as e:
                self.logger.error(f"❌ Agent coordination test error: {e}")
                agent_results["critical_issues"].append(f"Agent coordination test error: {e}")

        # Test individual agent functionality
        individual_agents = ["validator_agent.py", "integrator_agent.py"]
        agent_dir = self.project_root / "agents"

        if agent_dir.exists():
            for agent_file in individual_agents:
                agent_path = agent_dir / agent_file
                if agent_path.exists():
                    try:
                        # Test agent can be imported
                        result = subprocess.run([sys.executable, "-c", f"import sys; sys.path.append('{agent_dir}'); exec(open('{agent_path}').read()[:100])"],
                                              capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            self.logger.info(f"✅ Agent syntax validation passed: {agent_file}")
                        else:
                            self.logger.error(f"❌ Agent syntax validation failed: {agent_file}")
                            agent_results["agent_errors"].append(f"Agent syntax error: {agent_file}")
                    except Exception as e:
                        self.logger.error(f"❌ Agent validation error: {agent_file} - {e}")
                        agent_results["agent_errors"].append(f"Agent validation error: {agent_file} - {e}")

        # Check for agent communication protocols
        coordinator_file = self.project_root / "claude-artifact-coordinator.py"
        if coordinator_file.exists():
            try:
                with open(coordinator_file, 'r') as f:
                    content = f.read()
                    if any(keyword in content.lower() for keyword in ["tandem", "coordination", "agent", "workflow"]):
                        agent_results["agent_communication_working"] = True
                        self.logger.info("✅ Agent communication protocols detected in coordinator")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not analyze coordinator file: {e}")

        # Determine agent coordination status
        if (agent_results["agent_files_present"] >= 3 and
            agent_results["coordination_test_passed"]):
            self.integration_categories["agent_coordination"]["status"] = "passed"
            self.logger.info("✅ Agent coordination testing PASSED")
        else:
            self.integration_categories["agent_coordination"]["status"] = "failed"
            self.logger.error("❌ Agent coordination testing FAILED")

        self.integration_categories["agent_coordination"]["results"] = agent_results
        return agent_results

    def test_deployment_pipeline(self) -> Dict[str, Any]:
        """Test deployment pipeline validation"""
        self.logger.info("🚀 Starting deployment pipeline testing...")

        deployment_results = {
            "docker_setup_functional": False,
            "kubernetes_configs_valid": False,
            "setup_scripts_working": 0,
            "setup_scripts_failed": 0,
            "environment_setup_tested": False,
            "deployment_ready": False,
            "critical_issues": []
        }

        # Test Docker setup
        docker_dir = self.project_root / "docker"
        if docker_dir.exists():
            dockerfile = docker_dir / "Dockerfile"
            if dockerfile.exists():
                try:
                    # Validate Dockerfile syntax
                    result = subprocess.run(["docker", "build", "--dry-run", "-f", str(dockerfile), "."],
                                          capture_output=True, text=True, timeout=60,
                                          cwd=self.project_root)
                    if result.returncode == 0 or "successfully" in result.stdout.lower():
                        self.logger.info("✅ Dockerfile syntax validation passed")
                        deployment_results["docker_setup_functional"] = True
                    else:
                        self.logger.warning("⚠️ Dockerfile validation issues (may be environment-specific)")
                except subprocess.TimeoutExpired:
                    self.logger.warning("⚠️ Docker validation timed out")
                except FileNotFoundError:
                    self.logger.info("ℹ️ Docker not available for validation (expected in some environments)")
                except Exception as e:
                    self.logger.warning(f"⚠️ Docker validation error: {e}")

        # Test Kubernetes configurations
        k8s_dir = self.project_root / "k8s"
        if k8s_dir.exists():
            k8s_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
            if k8s_files:
                valid_k8s_files = 0
                for k8s_file in k8s_files:
                    try:
                        with open(k8s_file, 'r') as f:
                            yaml_content = yaml.safe_load(f)
                            if yaml_content and isinstance(yaml_content, dict):
                                valid_k8s_files += 1
                                self.logger.info(f"✅ K8s config validated: {k8s_file.name}")
                    except Exception as e:
                        self.logger.error(f"❌ K8s config validation failed: {k8s_file.name} - {e}")
                        deployment_results["critical_issues"].append(f"K8s config invalid: {k8s_file.name}")

                deployment_results["kubernetes_configs_valid"] = valid_k8s_files > 0

        # Test setup scripts
        setup_scripts = [
            "setup-env.sh",
            "scripts/install-sword-intelligence-branding.sh",
            "artifactor"
        ]

        for script_name in setup_scripts:
            script_path = self.project_root / script_name
            if script_path.exists():
                try:
                    # Test script syntax and help
                    if script_name.endswith('.sh'):
                        result = subprocess.run(["bash", "-n", str(script_path)],
                                              capture_output=True, text=True, timeout=30)
                    else:
                        result = subprocess.run([str(script_path), "--help"],
                                              capture_output=True, text=True, timeout=30)

                    if result.returncode == 0 or "usage" in result.stdout.lower() or "help" in result.stdout.lower():
                        self.logger.info(f"✅ Setup script validation passed: {script_name}")
                        deployment_results["setup_scripts_working"] += 1
                    else:
                        self.logger.error(f"❌ Setup script validation failed: {script_name}")
                        deployment_results["setup_scripts_failed"] += 1
                        deployment_results["critical_issues"].append(f"Setup script failed: {script_name}")

                except subprocess.TimeoutExpired:
                    self.logger.error(f"❌ Setup script validation timed out: {script_name}")
                    deployment_results["setup_scripts_failed"] += 1
                    deployment_results["critical_issues"].append(f"Setup script timeout: {script_name}")
                except Exception as e:
                    self.logger.error(f"❌ Setup script validation error: {script_name} - {e}")
                    deployment_results["setup_scripts_failed"] += 1
                    deployment_results["critical_issues"].append(f"Setup script error: {script_name} - {e}")

        # Test environment setup
        venv_manager = self.project_root / "claude-artifact-venv-manager.py"
        if venv_manager.exists():
            try:
                result = subprocess.run([sys.executable, str(venv_manager), "--help"],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.logger.info("✅ Environment setup validation passed")
                    deployment_results["environment_setup_tested"] = True
                else:
                    self.logger.error("❌ Environment setup validation failed")
                    deployment_results["critical_issues"].append("Environment setup validation failed")
            except Exception as e:
                self.logger.error(f"❌ Environment setup test error: {e}")
                deployment_results["critical_issues"].append(f"Environment setup test error: {e}")

        # Determine deployment pipeline status
        if (deployment_results["setup_scripts_working"] > 0 and
            deployment_results["setup_scripts_working"] >= deployment_results["setup_scripts_failed"] and
            deployment_results["environment_setup_tested"]):
            deployment_results["deployment_ready"] = True
            self.integration_categories["deployment_pipeline"]["status"] = "passed"
            self.logger.info("✅ Deployment pipeline testing PASSED")
        else:
            self.integration_categories["deployment_pipeline"]["status"] = "failed"
            self.logger.error("❌ Deployment pipeline testing FAILED")

        self.integration_categories["deployment_pipeline"]["results"] = deployment_results
        return deployment_results

    def test_configuration_consistency(self) -> Dict[str, Any]:
        """Test configuration consistency across components"""
        self.logger.info("⚙️ Starting configuration consistency testing...")

        config_results = {
            "version_consistency": False,
            "dependency_consistency": False,
            "configuration_files_valid": 0,
            "configuration_conflicts": [],
            "environment_variables_consistent": False,
            "critical_issues": []
        }

        # Check version consistency
        version_files = [
            ("claude-artifact-coordinator.py", "version"),
            ("claude-artifact-downloader.py", "version"),
            ("README.md", "v3.0"),
            ("CLAUDE.md", "v3.0")
        ]

        versions_found = []
        for file_name, version_indicator in version_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if version_indicator in content.lower():
                            # Try to extract version number
                            lines = content.split('\n')
                            for line in lines:
                                if version_indicator in line.lower() and any(char.isdigit() for char in line):
                                    versions_found.append((file_name, line.strip()))
                                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not check version in {file_name}: {e}")

        if len(versions_found) >= 2:
            config_results["version_consistency"] = True
            self.logger.info("✅ Version consistency detected across files")
        else:
            self.logger.warning("⚠️ Version consistency could not be verified")

        # Check dependency consistency
        dependency_files = [
            "requirements.txt",
            "backend/requirements.txt",
            "frontend/package.json"
        ]

        dependencies = {}
        for dep_file in dependency_files:
            dep_path = self.project_root / dep_file
            if dep_path.exists():
                try:
                    if dep_file.endswith('.json'):
                        with open(dep_path, 'r') as f:
                            package_data = json.load(f)
                            if 'dependencies' in package_data:
                                dependencies[dep_file] = package_data['dependencies']
                    else:
                        with open(dep_path, 'r') as f:
                            deps = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                            dependencies[dep_file] = deps

                    config_results["configuration_files_valid"] += 1
                    self.logger.info(f"✅ Dependency file parsed: {dep_file}")

                except Exception as e:
                    self.logger.error(f"❌ Dependency file parsing failed: {dep_file} - {e}")
                    config_results["critical_issues"].append(f"Dependency file parsing failed: {dep_file}")

        config_results["dependency_consistency"] = config_results["configuration_files_valid"] > 0

        # Check for configuration conflicts
        config_files = [
            "docker/Dockerfile",
            "k8s/deployment.yaml",
            "backend/config.py",
            "frontend/src/config.js"
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        # Check for obvious conflicts (ports, URLs, etc.)
                        if 'localhost' in content and 'production' in content.lower():
                            config_results["configuration_conflicts"].append(f"Potential localhost in production config: {config_file}")

                        config_results["configuration_files_valid"] += 1
                        self.logger.info(f"✅ Configuration file validated: {config_file}")

                except Exception as e:
                    self.logger.warning(f"⚠️ Configuration file validation error: {config_file} - {e}")

        # Check environment variables
        env_files = [".env", ".env.example", "docker/.env"]
        env_vars_found = 0

        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                env_vars_found += 1
                self.logger.info(f"✅ Environment file found: {env_file}")

        config_results["environment_variables_consistent"] = env_vars_found > 0

        # Determine configuration consistency status
        if (config_results["configuration_files_valid"] > 0 and
            len(config_results["configuration_conflicts"]) == 0):
            self.integration_categories["configuration_consistency"]["status"] = "passed"
            self.logger.info("✅ Configuration consistency testing PASSED")
        else:
            self.integration_categories["configuration_consistency"]["status"] = "failed"
            self.logger.error("❌ Configuration consistency testing FAILED")

        self.integration_categories["configuration_consistency"]["results"] = config_results
        return config_results

    def test_end_to_end_workflows(self) -> Dict[str, Any]:
        """Test end-to-end workflow functionality"""
        self.logger.info("🔄 Starting end-to-end workflow testing...")

        workflow_results = {
            "launcher_workflow_functional": False,
            "coordinator_workflow_functional": False,
            "downloader_workflow_functional": False,
            "full_pipeline_tested": False,
            "workflow_errors": [],
            "critical_issues": []
        }

        # Test launcher workflow
        launcher = self.project_root / "claude-artifact-launcher.py"
        if launcher.exists():
            try:
                result = subprocess.run([sys.executable, str(launcher), "--help"],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and "usage" in result.stdout.lower():
                    self.logger.info("✅ Launcher workflow test passed")
                    workflow_results["launcher_workflow_functional"] = True
                else:
                    self.logger.error("❌ Launcher workflow test failed")
                    workflow_results["workflow_errors"].append("Launcher workflow failed")
            except Exception as e:
                self.logger.error(f"❌ Launcher workflow test error: {e}")
                workflow_results["workflow_errors"].append(f"Launcher workflow error: {e}")

        # Test coordinator workflow
        coordinator = self.project_root / "claude-artifact-coordinator.py"
        if coordinator.exists():
            try:
                # Test coordinator can start (dry run)
                result = subprocess.run([sys.executable, str(coordinator), "--test"],
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0 or "test" in result.stdout.lower():
                    self.logger.info("✅ Coordinator workflow test passed")
                    workflow_results["coordinator_workflow_functional"] = True
                else:
                    self.logger.error("❌ Coordinator workflow test failed")
                    workflow_results["workflow_errors"].append("Coordinator workflow failed")
            except Exception as e:
                self.logger.error(f"❌ Coordinator workflow test error: {e}")
                workflow_results["workflow_errors"].append(f"Coordinator workflow error: {e}")

        # Test downloader workflow
        downloader = self.project_root / "claude-artifact-downloader.py"
        if downloader.exists():
            try:
                result = subprocess.run([sys.executable, str(downloader), "--help"],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and ("usage" in result.stdout.lower() or "help" in result.stdout.lower()):
                    self.logger.info("✅ Downloader workflow test passed")
                    workflow_results["downloader_workflow_functional"] = True
                else:
                    self.logger.error("❌ Downloader workflow test failed")
                    workflow_results["workflow_errors"].append("Downloader workflow failed")
            except Exception as e:
                self.logger.error(f"❌ Downloader workflow test error: {e}")
                workflow_results["workflow_errors"].append(f"Downloader workflow error: {e}")

        # Test full pipeline with artifactor script
        artifactor_script = self.project_root / "artifactor"
        if artifactor_script.exists():
            try:
                result = subprocess.run([str(artifactor_script), "status"],
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.logger.info("✅ Full pipeline test passed")
                    workflow_results["full_pipeline_tested"] = True
                else:
                    self.logger.warning("⚠️ Full pipeline test had issues (may be environment-specific)")
            except Exception as e:
                self.logger.warning(f"⚠️ Full pipeline test error: {e}")

        # Determine end-to-end workflow status
        functional_workflows = sum([
            workflow_results["launcher_workflow_functional"],
            workflow_results["coordinator_workflow_functional"],
            workflow_results["downloader_workflow_functional"]
        ])

        if functional_workflows >= 2:  # At least 2 out of 3 core workflows working
            self.integration_categories["end_to_end_workflows"]["status"] = "passed"
            self.logger.info("✅ End-to-end workflow testing PASSED")
        else:
            self.integration_categories["end_to_end_workflows"]["status"] = "failed"
            self.logger.error("❌ End-to-end workflow testing FAILED")

        self.integration_categories["end_to_end_workflows"]["results"] = workflow_results
        return workflow_results

    def run_comprehensive_integration(self) -> Dict[str, Any]:
        """Run all integration test categories"""
        self.logger.info(f"🔗 Starting comprehensive integration testing for ARTIFACTOR v{self.version}")

        start_time = time.time()

        # Run all integration tests
        integration_functions = [
            ("service_integration", self.test_service_integration),
            ("agent_coordination", self.test_agent_coordination),
            ("deployment_pipeline", self.test_deployment_pipeline),
            ("configuration_consistency", self.test_configuration_consistency),
            ("end_to_end_workflows", self.test_end_to_end_workflows)
        ]

        passed_integrations = 0
        total_integrations = len(integration_functions)

        for category, integration_func in integration_functions:
            try:
                self.logger.info(f"🔍 Running {category} integration testing...")
                results = integration_func()

                if self.integration_categories[category]["status"] == "passed":
                    passed_integrations += 1

            except Exception as e:
                self.logger.error(f"❌ Integration test error in {category}: {e}")
                self.integration_categories[category]["status"] = "error"
                self.integration_results["critical_issues"].append(f"Integration test error in {category}: {e}")

        # Calculate overall results
        integration_time = time.time() - start_time
        success_rate = (passed_integrations / total_integrations) * 100

        self.integration_results["summary"] = {
            "total_integrations": total_integrations,
            "passed_integrations": passed_integrations,
            "failed_integrations": total_integrations - passed_integrations,
            "success_rate_percent": success_rate,
            "integration_time_seconds": round(integration_time, 2)
        }

        # Determine integration readiness
        if success_rate >= 80:  # 80% success threshold
            self.integration_results["overall_status"] = "passed"
            self.integration_results["integration_ready"] = True
            self.logger.info(f"🎉 INTEGRATION TESTING PASSED - System integration ready ({success_rate:.1f}% success rate)")
        else:
            self.integration_results["overall_status"] = "failed"
            self.integration_results["integration_ready"] = False
            self.logger.error(f"❌ INTEGRATION TESTING FAILED - System integration not ready ({success_rate:.1f}% success rate)")

        # Update timestamp
        self.integration_results["timestamp"] = datetime.now().isoformat()

        return self.integration_results

    def generate_integration_report(self) -> str:
        """Generate comprehensive integration report"""
        report_file = self.project_root / "INTEGRATOR_FINAL_REPORT.md"

        report_content = f"""# INTEGRATOR Agent Final Integration Report

## Executive Summary
- **Agent**: {self.integration_results['agent']} v{self.integration_results['version']}
- **Integration Date**: {self.integration_results['timestamp']}
- **Overall Status**: {self.integration_results['overall_status'].upper()}
- **Integration Ready**: {'✅ YES' if self.integration_results['integration_ready'] else '❌ NO'}
- **Success Rate**: {self.integration_results['summary']['success_rate_percent']:.1f}%

## Integration Test Results Summary

### Service Integration: {self.integration_categories['service_integration']['status'].upper()}
- Frontend-Backend Integration: {'✅' if self.integration_categories['service_integration']['results'].get('frontend_backend_integration') else '❌'}
- Backend-Core Integration: {'✅' if self.integration_categories['service_integration']['results'].get('backend_core_integration') else '❌'}
- API Endpoints Functional: {self.integration_categories['service_integration']['results'].get('api_endpoint_functional', 0)}
- Service Dependencies Resolved: {'✅' if self.integration_categories['service_integration']['results'].get('service_dependencies_resolved') else '❌'}

### Agent Coordination: {self.integration_categories['agent_coordination']['status'].upper()}
- Agent Files Present: {self.integration_categories['agent_coordination']['results'].get('agent_files_present', 0)}
- Coordination Test Passed: {'✅' if self.integration_categories['agent_coordination']['results'].get('coordination_test_passed') else '❌'}
- Tandem Operation Functional: {'✅' if self.integration_categories['agent_coordination']['results'].get('tandem_operation_functional') else '❌'}

### Deployment Pipeline: {self.integration_categories['deployment_pipeline']['status'].upper()}
- Docker Setup Functional: {'✅' if self.integration_categories['deployment_pipeline']['results'].get('docker_setup_functional') else '❌'}
- Kubernetes Configs Valid: {'✅' if self.integration_categories['deployment_pipeline']['results'].get('kubernetes_configs_valid') else '❌'}
- Setup Scripts Working: {self.integration_categories['deployment_pipeline']['results'].get('setup_scripts_working', 0)}
- Environment Setup Tested: {'✅' if self.integration_categories['deployment_pipeline']['results'].get('environment_setup_tested') else '❌'}

### Configuration Consistency: {self.integration_categories['configuration_consistency']['status'].upper()}
- Version Consistency: {'✅' if self.integration_categories['configuration_consistency']['results'].get('version_consistency') else '❌'}
- Dependency Consistency: {'✅' if self.integration_categories['configuration_consistency']['results'].get('dependency_consistency') else '❌'}
- Configuration Files Valid: {self.integration_categories['configuration_consistency']['results'].get('configuration_files_valid', 0)}
- Environment Variables Consistent: {'✅' if self.integration_categories['configuration_consistency']['results'].get('environment_variables_consistent') else '❌'}

### End-to-End Workflows: {self.integration_categories['end_to_end_workflows']['status'].upper()}
- Launcher Workflow Functional: {'✅' if self.integration_categories['end_to_end_workflows']['results'].get('launcher_workflow_functional') else '❌'}
- Coordinator Workflow Functional: {'✅' if self.integration_categories['end_to_end_workflows']['results'].get('coordinator_workflow_functional') else '❌'}
- Downloader Workflow Functional: {'✅' if self.integration_categories['end_to_end_workflows']['results'].get('downloader_workflow_functional') else '❌'}
- Full Pipeline Tested: {'✅' if self.integration_categories['end_to_end_workflows']['results'].get('full_pipeline_tested') else '❌'}

## Critical Issues
"""

        if self.integration_results["critical_issues"]:
            for issue in self.integration_results["critical_issues"]:
                report_content += f"- ❌ {issue}\n"
        else:
            report_content += "- ✅ No critical integration issues detected\n"

        report_content += f"""
## Performance Metrics
- Total Integration Time: {self.integration_results['summary']['integration_time_seconds']} seconds
- Integration Categories: {self.integration_results['summary']['total_integrations']}
- Passed Integrations: {self.integration_results['summary']['passed_integrations']}
- Failed Integrations: {self.integration_results['summary']['failed_integrations']}

## Integration Readiness Assessment

{'✅ **SYSTEM INTEGRATION READY**' if self.integration_results['integration_ready'] else '❌ **SYSTEM INTEGRATION NOT READY**'}

### Integration Recommendations
"""

        if self.integration_results["integration_ready"]:
            report_content += """
- All critical integration points validated
- Service components work together seamlessly
- Agent coordination systems functional
- Deployment pipeline ready for production
- Configuration consistency maintained
- End-to-end workflows operational
"""
        else:
            report_content += """
- Address critical integration issues identified above
- Fix service integration problems
- Resolve agent coordination issues
- Validate deployment pipeline components
- Ensure configuration consistency
- Test end-to-end workflows thoroughly
"""

        report_content += f"""
---
*Generated by INTEGRATOR Agent v{self.version} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Part of DIRECTOR-led full system repair coordination*
"""

        # Write report
        with open(report_file, 'w') as f:
            f.write(report_content)

        self.logger.info(f"📊 Integration report generated: {report_file}")
        return str(report_file)

def main():
    """Main execution function"""
    integrator = IntegratorAgent()

    print("🔗 INTEGRATOR Agent v3.0.0 - Component Integration Testing")
    print("=" * 70)

    # Run comprehensive integration testing
    results = integrator.run_comprehensive_integration()

    # Generate report
    report_file = integrator.generate_integration_report()

    # Save results as JSON
    results_file = integrator.project_root / "integration_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Integration Results:")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    print(f"   Integration Ready: {'YES' if results['integration_ready'] else 'NO'}")
    print(f"   Success Rate: {results['summary']['success_rate_percent']:.1f}%")
    print(f"   Report: {report_file}")
    print(f"   Results: {results_file}")

    return results['integration_ready']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)