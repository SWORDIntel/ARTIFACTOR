#!/usr/bin/env python3
"""
Claude Artifact Downloader - Tandem Agent Coordination
Demonstrates PYGUI + PYTHON-INTERNAL + DEBUGGER agent coordination
with comprehensive error handling and validation.
"""

import os
import sys
import json
import time
import threading
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import queue
import logging

# Agent coordination imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: GUI not available, running in CLI mode")

@dataclass
class AgentResponse:
    """Standardized agent response format"""
    agent_name: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class AgentCoordinator:
    """Coordinates PYGUI, PYTHON-INTERNAL, and DEBUGGER agents in tandem"""

    def __init__(self, log_level=logging.INFO):
        self.agents = {}
        self.execution_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.active_tasks = {}
        self.coordination_lock = threading.RLock()

        # Setup logging
        self.logger = self._setup_logging(log_level)

        # Initialize agents
        self._initialize_agents()

        # Start coordination thread
        self.coordination_thread = threading.Thread(
            target=self._coordination_loop,
            daemon=True
        )
        self.coordination_thread.start()

    def _setup_logging(self, level):
        """Setup structured logging for agent coordination"""
        logger = logging.getLogger('agent_coordinator')
        logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # File handler
        file_handler = logging.FileHandler('agent_coordination.log')
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _initialize_agents(self):
        """Initialize all agent handlers"""
        self.agents = {
            'pygui': PyGUIAgent(self),
            'python_internal': PythonInternalAgent(self),
            'debugger': DebuggerAgent(self)
        }

        self.logger.info("Initialized agents: " + ", ".join(self.agents.keys()))

    def _coordination_loop(self):
        """Main coordination loop for agent tasks"""
        while True:
            try:
                # Get next task from queue (blocks until available)
                task = self.execution_queue.get(timeout=1.0)

                if task is None:  # Shutdown signal
                    break

                # Execute task
                self._execute_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Coordination loop error: {e}")
                self.logger.debug(traceback.format_exc())

    def _execute_task(self, task):
        """Execute a coordinated task"""
        task_id = task.get('id', f"task_{int(time.time())}")
        agent_name = task.get('agent', 'unknown')
        action = task.get('action', 'unknown')

        self.logger.info(f"Executing task {task_id}: {agent_name}.{action}")

        try:
            with self.coordination_lock:
                self.active_tasks[task_id] = {
                    'agent': agent_name,
                    'action': action,
                    'start_time': time.time(),
                    'status': 'running'
                }

            # Execute agent action
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                result = agent.execute_action(action, task.get('params', {}))

                # Store result
                with self.coordination_lock:
                    self.active_tasks[task_id]['status'] = 'completed'
                    self.active_tasks[task_id]['result'] = result

                self.results_queue.put({
                    'task_id': task_id,
                    'result': result
                })

            else:
                error_result = AgentResponse(
                    agent_name=agent_name,
                    success=False,
                    message=f"Unknown agent: {agent_name}"
                )

                with self.coordination_lock:
                    self.active_tasks[task_id]['status'] = 'failed'
                    self.active_tasks[task_id]['result'] = error_result

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            error_result = AgentResponse(
                agent_name=agent_name,
                success=False,
                message=f"Execution error: {str(e)}"
            )

            with self.coordination_lock:
                self.active_tasks[task_id]['status'] = 'error'
                self.active_tasks[task_id]['result'] = error_result

    def coordinate_tandem_operation(self, operation_name: str, params: Dict[str, Any]) -> Dict[str, AgentResponse]:
        """Coordinate all three agents in tandem for a specific operation"""

        self.logger.info(f"Starting tandem operation: {operation_name}")

        # Define coordination workflow
        workflow = self._get_tandem_workflow(operation_name, params)
        results = {}

        for step in workflow:
            agent_name = step['agent']
            action = step['action']
            step_params = step.get('params', {})

            # Add results from previous steps
            step_params['previous_results'] = results

            # Execute step
            task_id = f"{operation_name}_{agent_name}_{int(time.time())}"
            task = {
                'id': task_id,
                'agent': agent_name,
                'action': action,
                'params': step_params
            }

            # Queue task
            self.execution_queue.put(task)

            # Wait for result
            result = self._wait_for_task_result(task_id, timeout=30.0)
            results[agent_name] = result

            # Check if step failed and handle accordingly
            if not result.success and step.get('required', True):
                self.logger.error(f"Required step failed: {agent_name}.{action}")
                break

        self.logger.info(f"Tandem operation {operation_name} completed")
        return results

    def _get_tandem_workflow(self, operation_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Define workflow steps for tandem operations"""

        workflows = {
            'download_artifact': [
                {
                    'agent': 'debugger',
                    'action': 'validate_input',
                    'params': {'input_data': params},
                    'required': True
                },
                {
                    'agent': 'python_internal',
                    'action': 'prepare_environment',
                    'params': {'requirements': ['requests', 'urllib3']},
                    'required': True
                },
                {
                    'agent': 'pygui',
                    'action': 'show_progress',
                    'params': {'operation': 'download_artifact'},
                    'required': False
                },
                {
                    'agent': 'python_internal',
                    'action': 'execute_download',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'debugger',
                    'action': 'validate_output',
                    'params': {'expected_files': params.get('expected_files', [])},
                    'required': True
                }
            ],

            'validate_system': [
                {
                    'agent': 'debugger',
                    'action': 'system_health_check',
                    'params': {},
                    'required': True
                },
                {
                    'agent': 'python_internal',
                    'action': 'dependency_check',
                    'params': {},
                    'required': True
                },
                {
                    'agent': 'pygui',
                    'action': 'display_status',
                    'params': {},
                    'required': False
                }
            ],

            'error_recovery': [
                {
                    'agent': 'debugger',
                    'action': 'analyze_error',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'python_internal',
                    'action': 'attempt_fix',
                    'params': params,
                    'required': False
                },
                {
                    'agent': 'pygui',
                    'action': 'show_recovery_options',
                    'params': params,
                    'required': False
                }
            ]
        }

        return workflows.get(operation_name, [])

    def _wait_for_task_result(self, task_id: str, timeout: float = 30.0) -> AgentResponse:
        """Wait for a specific task to complete and return its result"""

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if task is completed
            with self.coordination_lock:
                if task_id in self.active_tasks:
                    task_info = self.active_tasks[task_id]
                    if task_info['status'] in ['completed', 'failed', 'error']:
                        return task_info.get('result', AgentResponse(
                            agent_name='unknown',
                            success=False,
                            message='No result available'
                        ))

            time.sleep(0.1)

        # Timeout
        return AgentResponse(
            agent_name='coordinator',
            success=False,
            message=f'Task {task_id} timed out after {timeout} seconds'
        )

    def get_coordination_status(self) -> Dict[str, Any]:
        """Get current coordination status"""
        with self.coordination_lock:
            return {
                'active_tasks': len(self.active_tasks),
                'queue_size': self.execution_queue.qsize(),
                'agents_available': list(self.agents.keys()),
                'tasks': dict(self.active_tasks)
            }

    def shutdown(self):
        """Gracefully shutdown the coordinator"""
        self.logger.info("Shutting down agent coordinator")

        # Send shutdown signal
        self.execution_queue.put(None)

        # Wait for coordination thread
        if self.coordination_thread.is_alive():
            self.coordination_thread.join(timeout=5.0)

        # Shutdown agents
        for agent in self.agents.values():
            if hasattr(agent, 'shutdown'):
                agent.shutdown()

class BaseAgent:
    """Base class for all agents"""

    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator
        self.logger = coordinator.logger

    def execute_action(self, action: str, params: Dict[str, Any]) -> AgentResponse:
        """Execute an agent action"""
        start_time = time.time()

        try:
            # Get action method
            method_name = f"action_{action}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(params)

                execution_time = time.time() - start_time

                if isinstance(result, AgentResponse):
                    result.execution_time = execution_time
                    return result
                else:
                    return AgentResponse(
                        agent_name=self.__class__.__name__,
                        success=True,
                        message=f"Action {action} completed",
                        data=result,
                        execution_time=execution_time
                    )
            else:
                return AgentResponse(
                    agent_name=self.__class__.__name__,
                    success=False,
                    message=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.error(f"Agent action failed: {e}")
            return AgentResponse(
                agent_name=self.__class__.__name__,
                success=False,
                message=f"Action failed: {str(e)}",
                execution_time=time.time() - start_time
            )

class PyGUIAgent(BaseAgent):
    """PyGUI Agent - Handles all GUI operations"""

    def __init__(self, coordinator: AgentCoordinator):
        super().__init__(coordinator)
        self.gui_queue = queue.Queue()
        self.gui_responses = queue.Queue()

        if GUI_AVAILABLE:
            self.root = None
            self.gui_thread = threading.Thread(target=self._gui_loop, daemon=True)
            self.gui_thread.start()

    def _gui_loop(self):
        """Main GUI event loop"""
        self.root = tk.Tk()
        self.root.title("Claude Artifact Downloader - Agent Coordination")
        self.root.geometry("800x600")

        # Create main interface
        self._create_interface()

        # Start GUI update checker
        self.root.after(100, self._check_gui_queue)

        # Start GUI mainloop
        self.root.mainloop()

    def _create_interface(self):
        """Create the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Agent status frame
        status_frame = ttk.LabelFrame(main_frame, text="Agent Coordination Status")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        status_scroll = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Operations")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Buttons
        ttk.Button(control_frame, text="Test Tandem Operation",
                  command=self._test_tandem_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="System Health Check",
                  command=self._system_health_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Log",
                  command=self._clear_log).pack(side=tk.LEFT, padx=5)

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress")
        progress_frame.pack(fill=tk.X)

        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

    def _check_gui_queue(self):
        """Check for GUI update requests"""
        try:
            while True:
                request = self.gui_queue.get_nowait()
                self._handle_gui_request(request)
        except queue.Empty:
            pass

        # Schedule next check
        if self.root:
            self.root.after(100, self._check_gui_queue)

    def _handle_gui_request(self, request):
        """Handle GUI update requests"""
        action = request.get('action')
        params = request.get('params', {})

        if action == 'update_status':
            message = params.get('message', '')
            self.status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.status_text.see(tk.END)

        elif action == 'set_progress':
            self.progress_var.set(params.get('text', 'Working...'))
            if params.get('indeterminate', True):
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start()
            else:
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate', value=params.get('value', 0))

        elif action == 'show_dialog':
            messagebox.showinfo(
                params.get('title', 'Information'),
                params.get('message', '')
            )

    def _test_tandem_operation(self):
        """Test tandem operation button handler"""
        # Queue a tandem operation test
        def run_test():
            self.coordinator.coordinate_tandem_operation('validate_system', {})

        threading.Thread(target=run_test, daemon=True).start()

    def _system_health_check(self):
        """System health check button handler"""
        def run_check():
            status = self.coordinator.get_coordination_status()
            self.gui_queue.put({
                'action': 'update_status',
                'params': {'message': f"System status: {status}"}
            })

        threading.Thread(target=run_check, daemon=True).start()

    def _clear_log(self):
        """Clear the status log"""
        self.status_text.delete(1.0, tk.END)

    # Agent action methods
    def action_show_progress(self, params: Dict[str, Any]) -> AgentResponse:
        """Show progress indication"""
        operation = params.get('operation', 'Unknown')

        if GUI_AVAILABLE and self.root:
            self.gui_queue.put({
                'action': 'set_progress',
                'params': {'text': f'Running {operation}...', 'indeterminate': True}
            })

            self.gui_queue.put({
                'action': 'update_status',
                'params': {'message': f'Started operation: {operation}'}
            })

        return AgentResponse(
            agent_name='PyGUIAgent',
            success=True,
            message=f'Progress indication started for {operation}'
        )

    def action_display_status(self, params: Dict[str, Any]) -> AgentResponse:
        """Display system status"""
        previous_results = params.get('previous_results', {})

        status_message = "System Status:\n"
        for agent, result in previous_results.items():
            status = "✓" if result.success else "✗"
            status_message += f"{status} {agent}: {result.message}\n"

        if GUI_AVAILABLE and self.root:
            self.gui_queue.put({
                'action': 'update_status',
                'params': {'message': status_message}
            })

        return AgentResponse(
            agent_name='PyGUIAgent',
            success=True,
            message='Status displayed'
        )

    def action_show_recovery_options(self, params: Dict[str, Any]) -> AgentResponse:
        """Show error recovery options"""
        error_info = params.get('error_info', 'Unknown error')

        if GUI_AVAILABLE and self.root:
            self.gui_queue.put({
                'action': 'show_dialog',
                'params': {
                    'title': 'Error Recovery',
                    'message': f'Error detected: {error_info}\n\nRecovery options will be displayed here.'
                }
            })

        return AgentResponse(
            agent_name='PyGUIAgent',
            success=True,
            message='Recovery options displayed'
        )

class PythonInternalAgent(BaseAgent):
    """Python Internal Agent - Handles Python environment and execution"""

    def action_prepare_environment(self, params: Dict[str, Any]) -> AgentResponse:
        """Prepare Python environment"""
        requirements = params.get('requirements', [])

        self.logger.info(f"Preparing environment with requirements: {requirements}")

        # Check if requirements are available
        missing_modules = []
        for module in requirements:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            return AgentResponse(
                agent_name='PythonInternalAgent',
                success=False,
                message=f'Missing required modules: {missing_modules}',
                data={'missing_modules': missing_modules}
            )

        return AgentResponse(
            agent_name='PythonInternalAgent',
            success=True,
            message='Environment prepared successfully',
            data={'available_modules': requirements}
        )

    def action_dependency_check(self, params: Dict[str, Any]) -> AgentResponse:
        """Check Python dependencies"""
        self.logger.info("Checking Python dependencies")

        # Check critical modules
        critical_modules = ['os', 'sys', 'json', 'threading', 'time', 'pathlib']
        optional_modules = ['tkinter', 'requests', 'urllib3']

        available = []
        missing = []

        for module in critical_modules + optional_modules:
            try:
                __import__(module)
                available.append(module)
            except ImportError:
                missing.append(module)

        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        return AgentResponse(
            agent_name='PythonInternalAgent',
            success=len(missing) == 0 or all(m in optional_modules for m in missing),
            message=f'Dependency check completed. Python {python_version}',
            data={
                'python_version': python_version,
                'available_modules': available,
                'missing_modules': missing,
                'critical_missing': [m for m in missing if m in critical_modules]
            }
        )

    def action_execute_download(self, params: Dict[str, Any]) -> AgentResponse:
        """Execute download operation"""
        url = params.get('url', '')
        output_path = params.get('output_path', '')

        if not url:
            return AgentResponse(
                agent_name='PythonInternalAgent',
                success=False,
                message='No URL provided'
            )

        # Simulate download (placeholder)
        self.logger.info(f"Simulating download from {url} to {output_path}")

        # In real implementation, this would use the downloader
        time.sleep(1)  # Simulate work

        return AgentResponse(
            agent_name='PythonInternalAgent',
            success=True,
            message=f'Download completed: {url}',
            data={'url': url, 'output_path': output_path, 'size_bytes': 1024}
        )

    def action_attempt_fix(self, params: Dict[str, Any]) -> AgentResponse:
        """Attempt to fix detected issues"""
        error_info = params.get('error_info', {})

        self.logger.info(f"Attempting to fix error: {error_info}")

        # Placeholder fix attempt
        fix_suggestions = [
            "Check file permissions",
            "Verify network connectivity",
            "Validate input parameters",
            "Restart the operation"
        ]

        return AgentResponse(
            agent_name='PythonInternalAgent',
            success=True,
            message='Fix suggestions generated',
            data={'suggestions': fix_suggestions}
        )

class DebuggerAgent(BaseAgent):
    """Debugger Agent - Handles validation and error analysis"""

    def action_validate_input(self, params: Dict[str, Any]) -> AgentResponse:
        """Validate input parameters"""
        input_data = params.get('input_data', {})

        self.logger.info("Validating input parameters")

        validation_results = []
        is_valid = True

        # Check required fields
        required_fields = ['url', 'output_path']
        for field in required_fields:
            if field not in input_data:
                validation_results.append(f"Missing required field: {field}")
                is_valid = False
            elif not input_data[field]:
                validation_results.append(f"Empty required field: {field}")
                is_valid = False

        # Validate URL format
        if 'url' in input_data:
            url = input_data['url']
            if not (url.startswith('http://') or url.startswith('https://')):
                validation_results.append("URL must start with http:// or https://")
                is_valid = False

        # Validate output path
        if 'output_path' in input_data:
            output_path = input_data['output_path']
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                validation_results.append(f"Invalid output path: {e}")
                is_valid = False

        return AgentResponse(
            agent_name='DebuggerAgent',
            success=is_valid,
            message='Input validation completed',
            data={
                'is_valid': is_valid,
                'validation_results': validation_results,
                'checked_fields': list(input_data.keys())
            }
        )

    def action_system_health_check(self, params: Dict[str, Any]) -> AgentResponse:
        """Perform system health check"""
        self.logger.info("Performing system health check")

        health_data = {}
        issues = []

        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            health_data['disk_space'] = {
                'total_gb': round(total / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'free_percent': round(free_percent, 2)
            }

            if free_percent < 10:
                issues.append("Low disk space (< 10%)")

        except Exception as e:
            issues.append(f"Could not check disk space: {e}")

        # Check memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            health_data['memory'] = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent_used': memory.percent
            }

            if memory.percent > 90:
                issues.append("High memory usage (> 90%)")

        except ImportError:
            issues.append("psutil not available for memory check")
        except Exception as e:
            issues.append(f"Could not check memory: {e}")

        # Check Python environment
        health_data['python'] = {
            'version': sys.version,
            'executable': sys.executable,
            'path': sys.path[:3]  # First 3 paths only
        }

        return AgentResponse(
            agent_name='DebuggerAgent',
            success=len(issues) == 0,
            message=f'Health check completed. {len(issues)} issues found.',
            data={
                'health_data': health_data,
                'issues': issues,
                'overall_status': 'healthy' if len(issues) == 0 else 'issues_detected'
            }
        )

    def action_validate_output(self, params: Dict[str, Any]) -> AgentResponse:
        """Validate operation output"""
        expected_files = params.get('expected_files', [])
        previous_results = params.get('previous_results', {})

        self.logger.info(f"Validating output files: {expected_files}")

        validation_results = []
        all_valid = True

        for file_path in expected_files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                validation_results.append({
                    'file': str(path),
                    'exists': True,
                    'size_bytes': size,
                    'readable': os.access(path, os.R_OK)
                })
            else:
                validation_results.append({
                    'file': str(path),
                    'exists': False,
                    'size_bytes': 0,
                    'readable': False
                })
                all_valid = False

        return AgentResponse(
            agent_name='DebuggerAgent',
            success=all_valid,
            message=f'Output validation completed. {len(validation_results)} files checked.',
            data={
                'validation_results': validation_results,
                'all_files_valid': all_valid
            }
        )

    def action_analyze_error(self, params: Dict[str, Any]) -> AgentResponse:
        """Analyze error conditions"""
        error_info = params.get('error_info', 'No error information provided')

        self.logger.info(f"Analyzing error: {error_info}")

        # Simple error categorization
        error_categories = {
            'network': ['connection', 'timeout', 'dns', 'ssl', 'certificate'],
            'filesystem': ['permission', 'disk', 'directory', 'file not found'],
            'memory': ['memory', 'ram', 'allocation'],
            'python': ['import', 'module', 'syntax', 'type'],
            'validation': ['invalid', 'missing', 'format', 'parameter']
        }

        detected_categories = []
        error_lower = str(error_info).lower()

        for category, keywords in error_categories.items():
            if any(keyword in error_lower for keyword in keywords):
                detected_categories.append(category)

        # Generate recommendations
        recommendations = []
        if 'network' in detected_categories:
            recommendations.extend([
                "Check internet connection",
                "Verify URL accessibility",
                "Check firewall settings"
            ])

        if 'filesystem' in detected_categories:
            recommendations.extend([
                "Check file/directory permissions",
                "Verify disk space availability",
                "Ensure parent directories exist"
            ])

        if 'python' in detected_categories:
            recommendations.extend([
                "Check Python environment",
                "Verify module installations",
                "Review syntax and imports"
            ])

        return AgentResponse(
            agent_name='DebuggerAgent',
            success=True,
            message='Error analysis completed',
            data={
                'error_info': error_info,
                'detected_categories': detected_categories,
                'recommendations': recommendations,
                'severity': 'high' if len(detected_categories) > 2 else 'medium'
            }
        )

def main():
    """Main function to demonstrate tandem agent coordination"""
    print("Claude Artifact Downloader - Tandem Agent Coordination")
    print("=" * 60)

    # Create coordinator
    coordinator = AgentCoordinator(log_level=logging.INFO)

    try:
        # Test individual agents
        print("\n1. Testing individual agent responses...")

        # Test DEBUGGER
        result = coordinator.agents['debugger'].execute_action('system_health_check', {})
        print(f"DEBUGGER: {result.message} (Success: {result.success})")

        # Test PYTHON-INTERNAL
        result = coordinator.agents['python_internal'].execute_action('dependency_check', {})
        print(f"PYTHON-INTERNAL: {result.message} (Success: {result.success})")

        # Test PYGUI
        result = coordinator.agents['pygui'].execute_action('show_progress', {'operation': 'test'})
        print(f"PYGUI: {result.message} (Success: {result.success})")

        # Test tandem coordination
        print("\n2. Testing tandem coordination...")

        test_params = {
            'url': 'https://example.com/test.txt',
            'output_path': '/tmp/test_download.txt',
            'expected_files': ['/tmp/test_download.txt']
        }

        results = coordinator.coordinate_tandem_operation('download_artifact', test_params)

        print("\nTandem operation results:")
        for agent_name, result in results.items():
            status = "✓" if result.success else "✗"
            print(f"{status} {agent_name}: {result.message}")
            if result.data:
                print(f"   Data: {json.dumps(result.data, indent=2)}")

        # Show coordination status
        print("\n3. Coordination status:")
        status = coordinator.get_coordination_status()

        # Convert AgentResponse objects to dictionaries for JSON serialization
        serializable_status = {}
        for key, value in status.items():
            if key == 'tasks':
                serializable_tasks = {}
                for task_id, task_info in value.items():
                    task_copy = dict(task_info)
                    if 'result' in task_copy and hasattr(task_copy['result'], '__dict__'):
                        task_copy['result'] = asdict(task_copy['result'])
                    serializable_tasks[task_id] = task_copy
                serializable_status[key] = serializable_tasks
            else:
                serializable_status[key] = value

        print(json.dumps(serializable_status, indent=2))

        # Keep GUI running if available
        if GUI_AVAILABLE:
            print("\n4. GUI is running. Close the window to exit.")
            try:
                # Keep main thread alive while GUI runs
                while coordinator.agents['pygui'].root and coordinator.agents['pygui'].root.winfo_exists():
                    time.sleep(0.1)
            except tk.TclError:
                pass  # GUI window was closed
        else:
            print("\n4. GUI not available, continuing in CLI mode.")
            time.sleep(5)  # Give some time to see results

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"\nError in main: {e}")
        traceback.print_exc()
    finally:
        # Shutdown coordinator
        coordinator.shutdown()
        print("Agent coordination shutdown complete.")

if __name__ == '__main__':
    main()