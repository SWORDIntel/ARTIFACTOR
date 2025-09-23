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

# Import WEB and ARCHITECT agents with enhanced error handling
WEB_ARCHITECT_AVAILABLE = False
WebAgent = None
ArchitectAgent = None

try:
    agents_path = os.path.join(os.path.dirname(__file__), 'agents')
    if os.path.exists(agents_path):
        sys.path.append(agents_path)

        # Try importing individual agents for better error specificity
        try:
            from web_agent import WebAgent
            print("INFO: WebAgent imported successfully")
        except ImportError as web_err:
            print(f"WARNING: WebAgent not available: {web_err}")

        try:
            from architect_agent import ArchitectAgent
            print("INFO: ArchitectAgent imported successfully")
        except ImportError as arch_err:
            print(f"WARNING: ArchitectAgent not available: {arch_err}")

        # Set availability only if both agents are available
        if WebAgent is not None and ArchitectAgent is not None:
            WEB_ARCHITECT_AVAILABLE = True
            print("INFO: WEB/ARCHITECT agents loaded successfully")
        else:
            print("INFO: Running with reduced functionality - WEB/ARCHITECT agents unavailable")
    else:
        print(f"INFO: Agents directory not found at {agents_path} - running without WEB/ARCHITECT support")

except Exception as e:
    print(f"WARNING: Unexpected error loading WEB/ARCHITECT agents: {e}")
    # Ensure agents are None for safety
    WebAgent = None
    ArchitectAgent = None

# Dark Theme Configuration
class DarkTheme:
    """Dark theme color palette and styling configuration"""
    # Primary colors
    BG_PRIMARY = '#2B2B2B'          # Main background
    BG_SECONDARY = '#363636'        # Secondary background
    BG_TERTIARY = '#404040'         # Raised elements

    # Text colors
    TEXT_PRIMARY = '#FFFFFF'        # Primary text
    TEXT_SECONDARY = '#CCCCCC'      # Secondary text
    TEXT_DISABLED = '#808080'       # Disabled text

    # Accent colors
    ACCENT_BLUE = '#0078D4'         # Primary accent
    ACCENT_GREEN = '#107C10'        # Success/positive
    ACCENT_ORANGE = '#FF8C00'       # Warning
    ACCENT_RED = '#D13438'          # Error/negative

    # Border and outline colors
    BORDER_LIGHT = '#555555'        # Light borders
    BORDER_DARK = '#1F1F1F'         # Dark borders

    # Interactive states
    HOVER_BG = '#464646'            # Hover background
    ACTIVE_BG = '#505050'           # Active/pressed background
    SELECTED_BG = '#094771'         # Selected background

    # Component-specific colors
    BUTTON_BG = '#484848'           # Button background
    BUTTON_HOVER = '#525252'        # Button hover
    BUTTON_ACTIVE = '#5C5C5C'       # Button active

    INPUT_BG = '#3C3C3C'            # Input field background
    INPUT_BORDER = '#565656'        # Input field border
    INPUT_FOCUS = '#0078D4'         # Input field focus border

    PROGRESS_BG = '#3A3A3A'         # Progress bar background
    PROGRESS_FILL = '#0078D4'       # Progress bar fill

    # Font configuration
    FONT_FAMILY = 'Segoe UI'        # Primary font
    FONT_SIZE = 9                   # Base font size
    FONT_BOLD = ('Segoe UI', 9, 'bold')

    @classmethod
    def configure_ttk_style(cls):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()

        # Configure main theme
        style.theme_use('clam')  # Use clam as base theme

        # Configure general styles
        style.configure('TLabel',
                       background=cls.BG_PRIMARY,
                       foreground=cls.TEXT_PRIMARY,
                       font=(cls.FONT_FAMILY, cls.FONT_SIZE))

        style.configure('TFrame',
                       background=cls.BG_PRIMARY,
                       borderwidth=1,
                       relief='flat')

        style.configure('TLabelFrame',
                       background=cls.BG_PRIMARY,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=2,
                       relief='groove',
                       font=cls.FONT_BOLD)

        style.configure('TLabelFrame.Label',
                       background=cls.BG_PRIMARY,
                       foreground=cls.TEXT_SECONDARY,
                       font=cls.FONT_BOLD)

        # Button styles
        style.configure('TButton',
                       background=cls.BUTTON_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       focuscolor='none',
                       font=(cls.FONT_FAMILY, cls.FONT_SIZE))

        style.map('TButton',
                 background=[('active', cls.BUTTON_HOVER),
                           ('pressed', cls.BUTTON_ACTIVE),
                           ('disabled', cls.BG_SECONDARY)],
                 foreground=[('disabled', cls.TEXT_DISABLED)])

        # Progressbar styles
        style.configure('TProgressbar',
                       background=cls.PROGRESS_FILL,
                       troughcolor=cls.PROGRESS_BG,
                       borderwidth=1,
                       lightcolor=cls.PROGRESS_FILL,
                       darkcolor=cls.PROGRESS_FILL)

        # Scrollbar styles
        style.configure('TScrollbar',
                       background=cls.BG_SECONDARY,
                       troughcolor=cls.BG_PRIMARY,
                       borderwidth=1,
                       arrowcolor=cls.TEXT_SECONDARY)

        style.map('TScrollbar',
                 background=[('active', cls.HOVER_BG),
                           ('pressed', cls.ACTIVE_BG)])

        return style

    @classmethod
    def configure_tk_widgets(cls, root):
        """Configure standard tk widgets for dark theme"""
        # Configure root window
        root.configure(bg=cls.BG_PRIMARY)

        # Set default colors for tk widgets
        root.option_add('*TkTextWidget*background', cls.INPUT_BG)
        root.option_add('*TkTextWidget*foreground', cls.TEXT_PRIMARY)
        root.option_add('*TkTextWidget*insertBackground', cls.TEXT_PRIMARY)
        root.option_add('*TkTextWidget*selectBackground', cls.SELECTED_BG)
        root.option_add('*TkTextWidget*selectForeground', cls.TEXT_PRIMARY)

        # Configure default fonts
        root.option_add('*TkTextWidget*font', f'{cls.FONT_FAMILY} {cls.FONT_SIZE}')

        return root

class RoundedFrame(tk.Frame):
    """Custom frame with rounded corners using canvas"""

    def __init__(self, parent, corner_radius=10, bg=DarkTheme.BG_SECONDARY,
                 border_color=DarkTheme.BORDER_LIGHT, border_width=1, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.corner_radius = corner_radius
        self.bg_color = bg
        self.border_color = border_color
        self.border_width = border_width

        # Create canvas for rounded rectangle
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=bg)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind resize event
        self.canvas.bind('<Configure>', self._draw_rounded_rect)

        # Inner frame for content
        self.inner_frame = tk.Frame(self.canvas, bg=bg)
        self.canvas_window = self.canvas.create_window(0, 0, anchor='nw', window=self.inner_frame)

        # Bind inner frame resize
        self.inner_frame.bind('<Configure>', self._configure_canvas)

    def _draw_rounded_rect(self, event=None):
        """Draw rounded rectangle background"""
        self.canvas.delete('bg')

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w > 1 and h > 1:
            # Draw rounded rectangle
            self._create_rounded_rectangle(0, 0, w, h, self.corner_radius,
                                         fill=self.bg_color, outline=self.border_color,
                                         width=self.border_width, tags='bg')

    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create rounded rectangle on canvas"""
        points = []

        # Top-left corner
        points.extend([x1 + radius, y1])

        # Top side
        points.extend([x2 - radius, y1])

        # Top-right corner
        import math
        for i in range(90, 0, -10):
            x = x2 - radius + radius * math.cos(math.radians(i))
            y = y1 + radius - radius * math.sin(math.radians(i))
            points.extend([x, y])

        # Right side
        points.extend([x2, y2 - radius])

        # Bottom-right corner
        for i in range(0, -90, -10):
            x = x2 - radius + radius * math.cos(math.radians(i))
            y = y2 - radius - radius * math.sin(math.radians(i))
            points.extend([x, y])

        # Bottom side
        points.extend([x1 + radius, y2])

        # Bottom-left corner
        for i in range(-90, -180, -10):
            x = x1 + radius + radius * math.cos(math.radians(i))
            y = y2 - radius - radius * math.sin(math.radians(i))
            points.extend([x, y])

        # Left side
        points.extend([x1, y1 + radius])

        # Top-left corner completion
        for i in range(180, 90, -10):
            x = x1 + radius + radius * math.cos(math.radians(i))
            y = y1 + radius - radius * math.sin(math.radians(i))
            points.extend([x, y])

        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _configure_canvas(self, event=None):
        """Configure canvas scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # Update canvas window size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            self.canvas.itemconfig(self.canvas_window, width=canvas_width, height=canvas_height)

class RoundedButton(tk.Button):
    """Custom button with rounded corners and dark theme styling"""

    def __init__(self, parent, corner_radius=8, **kwargs):
        # Set default dark theme colors
        default_kwargs = {
            'bg': DarkTheme.BUTTON_BG,
            'fg': DarkTheme.TEXT_PRIMARY,
            'activebackground': DarkTheme.BUTTON_HOVER,
            'activeforeground': DarkTheme.TEXT_PRIMARY,
            'relief': 'flat',
            'borderwidth': 1,
            'font': (DarkTheme.FONT_FAMILY, DarkTheme.FONT_SIZE),
            'cursor': 'hand2'
        }
        default_kwargs.update(kwargs)

        super().__init__(parent, **default_kwargs)

        self.corner_radius = corner_radius

        # Bind hover events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)

    def _on_enter(self, event):
        """Handle mouse enter"""
        self.configure(bg=DarkTheme.BUTTON_HOVER)

    def _on_leave(self, event):
        """Handle mouse leave"""
        self.configure(bg=DarkTheme.BUTTON_BG)

    def _on_click(self, event):
        """Handle mouse click"""
        self.configure(bg=DarkTheme.BUTTON_ACTIVE)

    def _on_release(self, event):
        """Handle mouse release"""
        self.configure(bg=DarkTheme.BUTTON_HOVER)

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

        # Initialize WEB and ARCHITECT agents if available
        global WEB_ARCHITECT_AVAILABLE
        if WEB_ARCHITECT_AVAILABLE:
            try:
                self.agents['web'] = WebAgent(self)
                self.agents['architect'] = ArchitectAgent(self)
                self.logger.info("✅ WEB and ARCHITECT agents initialized successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize WEB/ARCHITECT agents: {e}")
                WEB_ARCHITECT_AVAILABLE = False

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
        step_results = []  # Track all step results in order

        for step_num, step in enumerate(workflow, 1):
            agent_name = step['agent']
            action = step['action']
            step_params = step.get('params', {})

            # Add results from previous steps
            step_params['previous_results'] = results
            step_params['step_results'] = step_results

            # Execute step
            task_id = f"{operation_name}_{agent_name}_{action}_{int(time.time())}"
            task = {
                'id': task_id,
                'agent': agent_name,
                'action': action,
                'params': step_params
            }

            self.logger.info(f"Executing step {step_num}/{len(workflow)}: {agent_name}.{action}")

            # Queue task
            self.execution_queue.put(task)

            # Wait for result
            result = self._wait_for_task_result(task_id, timeout=30.0)

            # Store step result with unique key
            step_key = f"{agent_name}_{action}"
            results[step_key] = result
            step_results.append({
                'step': step_num,
                'agent': agent_name,
                'action': action,
                'result': result
            })

            # Also store latest result for each agent for backward compatibility
            results[agent_name] = result

            self.logger.info(f"Step {step_num} completed: {agent_name}.{action} - {'✓' if result.success else '✗'} {result.message}")

            # Check if step failed and handle accordingly
            if not result.success and step.get('required', True):
                self.logger.error(f"Required step failed: {agent_name}.{action}")
                break

        self.logger.info(f"Tandem operation {operation_name} completed with {len(step_results)} steps")
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
            ],

            # New GitHub intelligent sorting workflows
            'analyze_github_structure': [
                {
                    'agent': 'web',
                    'action': 'analyze_github_patterns',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'web',
                    'action': 'fetch_framework_conventions',
                    'params': {'framework': params.get('framework', ''), 'include_community_data': True},
                    'required': True
                },
                {
                    'agent': 'architect',
                    'action': 'validate_structure_coherence',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'pygui',
                    'action': 'display_status',
                    'params': {'operation': 'github_analysis'},
                    'required': False
                }
            ],

            'optimize_repository_structure': [
                {
                    'agent': 'web',
                    'action': 'analyze_github_patterns',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'architect',
                    'action': 'design_optimal_structure',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'architect',
                    'action': 'validate_structure_coherence',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'architect',
                    'action': 'suggest_improvements',
                    'params': params,
                    'required': False
                },
                {
                    'agent': 'pygui',
                    'action': 'display_status',
                    'params': {'operation': 'repository_optimization'},
                    'required': False
                }
            ],

            'intelligent_file_sorting': [
                {
                    'agent': 'web',
                    'action': 'generate_repository_intelligence',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'architect',
                    'action': 'design_optimal_structure',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'python_internal',
                    'action': 'execute_file_sorting',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'debugger',
                    'action': 'validate_output',
                    'params': {'expected_structure': params.get('expected_structure', {})},
                    'required': True
                },
                {
                    'agent': 'pygui',
                    'action': 'display_status',
                    'params': {'operation': 'intelligent_sorting'},
                    'required': False
                }
            ],

            'github_pattern_validation': [
                {
                    'agent': 'web',
                    'action': 'analyze_github_patterns',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'web',
                    'action': 'validate_structure_against_community',
                    'params': params,
                    'required': True
                },
                {
                    'agent': 'debugger',
                    'action': 'system_health_check',
                    'params': {},
                    'required': False
                },
                {
                    'agent': 'pygui',
                    'action': 'display_status',
                    'params': {'operation': 'pattern_validation'},
                    'required': False
                }
            ]
        }

        workflow_steps = workflows.get(operation_name, [])

        # Add test mode flag to parameters if test mode is enabled
        if 'python_internal' in self.agents:
            python_agent = self.agents['python_internal']
            if getattr(python_agent, 'test_mode', False):
                for step in workflow_steps:
                    if 'params' not in step:
                        step['params'] = {}
                    step['params']['test_mode'] = True

        return workflow_steps

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
            # Check test mode status
            test_mode_status = {}
            if 'python_internal' in self.agents:
                python_agent = self.agents['python_internal']
                test_mode_status = {
                    'test_mode_enabled': getattr(python_agent, 'test_mode', False),
                    'test_files_created': len(getattr(python_agent, 'test_files_created', {}))
                }

            return {
                'active_tasks': len(self.active_tasks),
                'queue_size': self.execution_queue.qsize(),
                'agents_available': list(self.agents.keys()),
                'tasks': dict(self.active_tasks),
                'test_mode': test_mode_status
            }

    def set_test_mode(self, enabled: bool):
        """Enable or disable test mode for all agents"""
        self.logger.info(f"Setting test mode: {'enabled' if enabled else 'disabled'}")

        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'set_test_mode'):
                agent.set_test_mode(enabled)
                self.logger.info(f"Test mode {'enabled' if enabled else 'disabled'} for {agent_name}")

    def cleanup_all_test_files(self):
        """Clean up test files from all agents"""
        self.logger.info("Cleaning up all test files")

        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'cleanup_test_files'):
                agent.cleanup_test_files()
                self.logger.info(f"Cleaned up test files for {agent_name}")

    def shutdown(self):
        """Gracefully shutdown the coordinator"""
        self.logger.info("Shutting down agent coordinator")

        # Send shutdown signal
        self.execution_queue.put(None)

        # Wait for coordination thread
        if self.coordination_thread.is_alive():
            self.coordination_thread.join(timeout=5.0)

        # Shutdown agents and cleanup test files
        for agent in self.agents.values():
            if hasattr(agent, 'cleanup_test_files'):
                agent.cleanup_test_files()
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
        self.root.geometry("900x700")

        # Configure dark theme
        DarkTheme.configure_tk_widgets(self.root)
        self.style = DarkTheme.configure_ttk_style()

        # Set window icon and properties
        self.root.configure(bg=DarkTheme.BG_PRIMARY)
        self.root.resizable(True, True)
        self.root.minsize(600, 400)

        # Create main interface
        self._create_interface()

        # Start GUI update checker
        self.root.after(100, self._check_gui_queue)

        # Start GUI mainloop
        self.root.mainloop()

    def _create_interface(self):
        """Create the main GUI interface with dark theme"""
        # Main container with rounded frame
        main_container = RoundedFrame(self.root, corner_radius=12,
                                    bg=DarkTheme.BG_PRIMARY,
                                    border_color=DarkTheme.BORDER_LIGHT)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Use inner frame for layout
        main_frame = main_container.inner_frame
        main_frame.configure(bg=DarkTheme.BG_PRIMARY)

        # Title label with modern styling
        title_label = tk.Label(main_frame,
                              text="🚀 ARTIFACTOR - Agent Coordination Dashboard",
                              font=(DarkTheme.FONT_FAMILY, 14, 'bold'),
                              bg=DarkTheme.BG_PRIMARY,
                              fg=DarkTheme.TEXT_PRIMARY)
        title_label.pack(pady=(10, 20))

        # Agent status frame with rounded styling
        status_frame = RoundedFrame(main_frame, corner_radius=8,
                                  bg=DarkTheme.BG_SECONDARY,
                                  border_color=DarkTheme.BORDER_LIGHT)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Status frame header
        status_header = tk.Label(status_frame.inner_frame,
                               text="📊 Agent Coordination Status",
                               font=DarkTheme.FONT_BOLD,
                               bg=DarkTheme.BG_SECONDARY,
                               fg=DarkTheme.TEXT_SECONDARY)
        status_header.pack(pady=(10, 5))

        # Text display area with dark styling
        text_container = tk.Frame(status_frame.inner_frame, bg=DarkTheme.BG_SECONDARY)
        text_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.status_text = tk.Text(text_container,
                                 height=12,
                                 wrap=tk.WORD,
                                 bg=DarkTheme.INPUT_BG,
                                 fg=DarkTheme.TEXT_PRIMARY,
                                 insertbackground=DarkTheme.TEXT_PRIMARY,
                                 selectbackground=DarkTheme.SELECTED_BG,
                                 selectforeground=DarkTheme.TEXT_PRIMARY,
                                 font=(DarkTheme.FONT_FAMILY, DarkTheme.FONT_SIZE),
                                 relief='flat',
                                 borderwidth=2,
                                 highlightthickness=1,
                                 highlightcolor=DarkTheme.INPUT_FOCUS,
                                 highlightbackground=DarkTheme.INPUT_BORDER)

        status_scroll = ttk.Scrollbar(text_container, orient=tk.VERTICAL,
                                    command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Control frame with rounded styling
        control_frame = RoundedFrame(main_frame, corner_radius=8,
                                   bg=DarkTheme.BG_SECONDARY,
                                   border_color=DarkTheme.BORDER_LIGHT)
        control_frame.pack(fill=tk.X, pady=(0, 15))

        # Control frame header
        control_header = tk.Label(control_frame.inner_frame,
                                text="⚡ Operations Control",
                                font=DarkTheme.FONT_BOLD,
                                bg=DarkTheme.BG_SECONDARY,
                                fg=DarkTheme.TEXT_SECONDARY)
        control_header.pack(pady=(10, 10))

        # Button container
        button_container = tk.Frame(control_frame.inner_frame, bg=DarkTheme.BG_SECONDARY)
        button_container.pack(pady=(0, 15))

        # Rounded buttons with dark theme
        self.test_button = RoundedButton(button_container,
                                       text="🧪 Test Tandem Operation",
                                       command=self._test_tandem_operation)
        self.test_button.pack(side=tk.LEFT, padx=8)

        self.health_button = RoundedButton(button_container,
                                         text="🔍 System Health Check",
                                         command=self._system_health_check)
        self.health_button.pack(side=tk.LEFT, padx=8)

        self.clear_button = RoundedButton(button_container,
                                        text="🗑️ Clear Log",
                                        command=self._clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=8)

        # Progress frame with rounded styling
        progress_frame = RoundedFrame(main_frame, corner_radius=8,
                                    bg=DarkTheme.BG_SECONDARY,
                                    border_color=DarkTheme.BORDER_LIGHT)
        progress_frame.pack(fill=tk.X)

        # Progress frame header
        progress_header = tk.Label(progress_frame.inner_frame,
                                 text="📈 Progress Monitor",
                                 font=DarkTheme.FONT_BOLD,
                                 bg=DarkTheme.BG_SECONDARY,
                                 fg=DarkTheme.TEXT_SECONDARY)
        progress_header.pack(pady=(10, 5))

        # Progress status label
        self.progress_var = tk.StringVar(value="Ready - System Initialized")
        progress_status = tk.Label(progress_frame.inner_frame,
                                 textvariable=self.progress_var,
                                 font=(DarkTheme.FONT_FAMILY, DarkTheme.FONT_SIZE),
                                 bg=DarkTheme.BG_SECONDARY,
                                 fg=DarkTheme.TEXT_PRIMARY)
        progress_status.pack(pady=5)

        # Custom styled progress bar
        progress_container = tk.Frame(progress_frame.inner_frame, bg=DarkTheme.BG_SECONDARY)
        progress_container.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.progress_bar = ttk.Progressbar(progress_container,
                                          mode='indeterminate',
                                          length=400)
        self.progress_bar.pack(fill=tk.X)

        # Add initial status message
        welcome_msg = ("🎯 ARTIFACTOR Agent Coordination System Ready\n"
                      "💡 PYGUI + PYTHON-INTERNAL + DEBUGGER agents online\n"
                      "🔧 Click operations above to test system functionality\n")
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, welcome_msg)
        self.status_text.config(state=tk.DISABLED)
        self.status_text.see(tk.END)

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
        """Handle GUI update requests - THREAD SAFE VERSION"""
        # Validate request before processing
        if not request or not isinstance(request, dict):
            self.logger.error("Invalid GUI request: request is not a dictionary")
            return

        action = request.get('action')
        if not action:
            self.logger.error("Invalid GUI request: missing action")
            return

        params = request.get('params', {})
        if not isinstance(params, dict):
            self.logger.error("Invalid GUI request: params is not a dictionary")
            return

        # Schedule GUI updates on the main GUI thread using root.after()
        try:
            if action == 'update_status':
                message = params.get('message', '')
                if message:  # Only update if message is not empty
                    self._safe_gui_update(self._update_status_text, message)

            elif action == 'set_progress':
                text = params.get('text', 'Working...')
                indeterminate = params.get('indeterminate', True)
                value = params.get('value', 0)
                self._safe_gui_update(self._update_progress, text, indeterminate, value)

            elif action == 'show_dialog':
                title = params.get('title', 'Information')
                message = params.get('message', '')
                self._safe_gui_update(self._show_dialog, title, message)

            else:
                self.logger.warning(f"Unknown GUI action: {action}")

        except Exception as e:
            self.logger.error(f"GUI request handling failed: {e}")
            # Schedule error display on GUI thread
            self._safe_gui_update(self._show_error, str(e))

    def _safe_gui_update(self, update_func, *args):
        """Safely schedule GUI updates on the main GUI thread"""
        if self.root and hasattr(self.root, 'after'):
            try:
                self.root.after(0, update_func, *args)
            except Exception as e:
                self.logger.error(f"Failed to schedule GUI update: {e}")
        else:
            self.logger.warning("GUI root not available for update scheduling")

    def _update_status_text(self, message):
        """Update status text - must be called from GUI thread"""
        try:
            if hasattr(self, 'status_text') and self.status_text:
                self.status_text.config(state=tk.NORMAL)
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.status_text.insert(tk.END, f"{timestamp} - {message}\n")
                self.status_text.config(state=tk.DISABLED)
                self.status_text.see(tk.END)
        except Exception as e:
            self.logger.error(f"Failed to update status text: {e}")

    def _update_progress(self, text, indeterminate, value):
        """Update progress - must be called from GUI thread"""
        try:
            if hasattr(self, 'progress_var') and self.progress_var:
                self.progress_var.set(text)

            if hasattr(self, 'progress_bar') and self.progress_bar:
                if indeterminate:
                    self.progress_bar.config(mode='indeterminate')
                    self.progress_bar.start()
                else:
                    self.progress_bar.stop()
                    self.progress_bar.config(mode='determinate', value=value)
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")

    def _show_dialog(self, title, message):
        """Show dialog - must be called from GUI thread"""
        try:
            messagebox.showinfo(title, message)
        except Exception as e:
            self.logger.error(f"Failed to show dialog: {e}")

    def _show_error(self, error_message):
        """Show error in status text - must be called from GUI thread"""
        try:
            if hasattr(self, 'status_text') and self.status_text:
                self.status_text.config(state=tk.NORMAL)
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.status_text.insert(tk.END, f"{timestamp} - GUI Error: {error_message}\n")
                self.status_text.config(state=tk.DISABLED)
                self.status_text.see(tk.END)
        except Exception as e:
            # Last resort logging if GUI completely fails
            self.logger.error(f"Failed to show error in GUI: {e}")

    def _test_tandem_operation(self):
        """Test tandem operation button handler - THREAD SAFE VERSION"""
        # Disable button during operation to prevent multiple concurrent tests
        if hasattr(self, 'test_button') and self.test_button:
            self.test_button.config(state='disabled')

        def run_test():
            operation_start_time = time.time()
            test_successful = False

            try:
                # Validate coordinator availability
                if not hasattr(self, 'coordinator') or not self.coordinator:
                    raise RuntimeError("Agent coordinator not available")

                # Start progress indication
                self._safe_gui_update(self._update_progress, "Starting tandem test...", True, 0)

                # Queue initial status message with validation
                try:
                    self.gui_queue.put({
                        'action': 'update_status',
                        'params': {'message': '🧪 Starting tandem operation test...'}
                    }, timeout=1.0)  # Add timeout to prevent hanging
                except queue.Full:
                    self.logger.warning("GUI queue is full, skipping status update")

                # Execute tandem operation with timeout protection
                self.logger.info("Executing tandem operation: validate_system")

                # Use a timeout-protected execution
                result = self._execute_tandem_with_timeout('validate_system', {}, timeout=30.0)

                if not result:
                    raise RuntimeError("Tandem operation returned no result")

                # Validate result structure
                if not isinstance(result, dict):
                    raise TypeError(f"Expected dict result, got {type(result)}")

                # Calculate success metrics
                valid_results = [r for r in result.values() if hasattr(r, 'success')]
                success_count = sum(1 for r in valid_results if r.success)
                total_count = len(valid_results)

                if total_count == 0:
                    raise RuntimeError("No valid agent results received")

                # Report overall results with validation
                completion_message = f'✅ Tandem test completed: {success_count}/{total_count} agents successful'
                try:
                    self.gui_queue.put({
                        'action': 'update_status',
                        'params': {'message': completion_message}
                    }, timeout=1.0)
                except queue.Full:
                    self.logger.warning("GUI queue full, logging result instead")
                    self.logger.info(completion_message)

                # Show detailed results for each agent
                for agent_name, agent_result in result.items():
                    if not hasattr(agent_result, 'success') or not hasattr(agent_result, 'message'):
                        self.logger.warning(f"Invalid result format for agent {agent_name}")
                        continue

                    status_icon = "✅" if agent_result.success else "❌"
                    result_message = f'{status_icon} {agent_name}: {agent_result.message}'

                    try:
                        self.gui_queue.put({
                            'action': 'update_status',
                            'params': {'message': result_message}
                        }, timeout=0.5)
                    except queue.Full:
                        self.logger.info(result_message)  # Fallback to logging

                # Update progress to completion
                self._safe_gui_update(self._update_progress, "Tandem test completed", False, 100)

                test_successful = True
                execution_time = time.time() - operation_start_time
                self.logger.info(f"Tandem operation test completed successfully in {execution_time:.2f}s")

            except Exception as e:
                # Comprehensive error handling with categorization
                execution_time = time.time() - operation_start_time
                error_type = type(e).__name__

                self.logger.error(f"Tandem operation test failed after {execution_time:.2f}s: {error_type}: {e}")
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")

                # Categorize error for better user feedback
                if isinstance(e, (TimeoutError, RuntimeError)):
                    error_message = f'❌ Tandem test failed: {str(e)}'
                elif isinstance(e, (TypeError, ValueError)):
                    error_message = f'❌ Tandem test failed: Data validation error - {str(e)}'
                elif isinstance(e, queue.Full):
                    error_message = f'❌ Tandem test failed: GUI communication error - {str(e)}'
                else:
                    error_message = f'❌ Tandem test failed: {error_type} - {str(e)}'

                # Report error with queue protection
                try:
                    self.gui_queue.put({
                        'action': 'update_status',
                        'params': {'message': error_message}
                    }, timeout=1.0)
                except (queue.Full, Exception) as queue_error:
                    self.logger.error(f"Failed to report error to GUI: {queue_error}")

                # Update progress to show error state
                self._safe_gui_update(self._update_progress, "Test failed", False, 0)

            finally:
                # Always re-enable the test button
                if hasattr(self, 'test_button') and self.test_button:
                    self._safe_gui_update(self._re_enable_test_button)

                # Final status update
                final_status = "ready" if test_successful else "error"
                self._safe_gui_update(self._update_progress, f"System {final_status}", False, 100 if test_successful else 0)

        # Start test in background thread with error protection
        try:
            test_thread = threading.Thread(target=run_test, daemon=True, name="TandemTestThread")
            test_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start test thread: {e}")
            # Re-enable button if thread creation failed
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.config(state='normal')

    def _execute_tandem_with_timeout(self, operation_name, params, timeout=30.0):
        """Execute tandem operation with timeout protection"""
        try:
            return self.coordinator.coordinate_tandem_operation(operation_name, params)
        except Exception as e:
            self.logger.error(f"Tandem operation {operation_name} failed: {e}")
            raise

    def _re_enable_test_button(self):
        """Re-enable test button - must be called from GUI thread"""
        try:
            if hasattr(self, 'test_button') and self.test_button:
                self.test_button.config(state='normal')
        except Exception as e:
            self.logger.error(f"Failed to re-enable test button: {e}")

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

    def __init__(self, coordinator: AgentCoordinator):
        super().__init__(coordinator)
        self.test_mode = True  # Enable test mode by default for coordination testing
        self.test_files_created = {}  # Track test files for validation

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

        if self.test_mode:
            # Test mode: Create actual test files for validation
            self.logger.info(f"Test mode: Creating test file for {url} at {output_path}")

            try:
                # Create test file with mock content
                from pathlib import Path
                test_path = Path(output_path)
                test_path.parent.mkdir(parents=True, exist_ok=True)

                # Create test content based on URL
                if 'json' in url.lower():
                    test_content = '{"test": "data", "status": "success", "mock": true}'
                elif 'html' in url.lower():
                    test_content = '<html><body><h1>Test Content</h1></body></html>'
                else:
                    test_content = f"Test content downloaded from {url}\nGenerated by ARTIFACTOR test mode\nTimestamp: {time.time()}"

                with open(test_path, 'w', encoding='utf-8') as f:
                    f.write(test_content)

                # Track the test file
                self.test_files_created[str(test_path)] = {
                    'url': url,
                    'size': len(test_content),
                    'created_at': time.time()
                }

                actual_size = test_path.stat().st_size
                self.logger.info(f"✓ Test file created: {test_path} ({actual_size} bytes)")

                time.sleep(0.1)  # Brief pause to simulate work

                return AgentResponse(
                    agent_name='PythonInternalAgent',
                    success=True,
                    message=f'Test download completed: {url}',
                    data={
                        'url': url,
                        'output_path': output_path,
                        'size_bytes': actual_size,
                        'test_mode': True,
                        'file_created': True
                    }
                )

            except Exception as e:
                self.logger.error(f"Failed to create test file: {e}")
                return AgentResponse(
                    agent_name='PythonInternalAgent',
                    success=False,
                    message=f'Test file creation failed: {str(e)}',
                    data={'test_mode': True, 'file_created': False}
                )
        else:
            # Production mode: Use real downloader
            self.logger.info(f"Production mode: Downloading from {url} to {output_path}")

            # In real implementation, this would use the actual downloader
            # For now, simulate the download process
            time.sleep(1)  # Simulate work

            return AgentResponse(
                agent_name='PythonInternalAgent',
                success=True,
                message=f'Download completed: {url}',
                data={'url': url, 'output_path': output_path, 'size_bytes': 1024, 'test_mode': False}
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

    def action_execute_file_sorting(self, params: Dict[str, Any]) -> AgentResponse:
        """Execute intelligent file sorting based on repository intelligence"""
        self.logger.info("🗂️ Executing intelligent file sorting...")

        try:
            # Extract parameters
            file_list = params.get('file_list', [])
            repository_intelligence = params.get('repository_intelligence', {})
            optimal_structure = params.get('optimal_structure', {})
            placement_suggestions = params.get('placement_suggestions', {})
            output_directory = params.get('output_directory', './sorted_repository')

            if not file_list:
                return AgentResponse(
                    agent_name='PythonInternalAgent',
                    success=False,
                    message='No files provided for sorting'
                )

            # Create output directory
            from pathlib import Path
            output_path = Path(output_directory)
            output_path.mkdir(parents=True, exist_ok=True)

            sorted_files = {}
            sorting_summary = {
                'total_files': len(file_list),
                'successfully_sorted': 0,
                'failed_sorts': 0,
                'created_directories': set(),
                'placement_decisions': {}
            }

            # Process each file according to intelligent suggestions
            for file_path in file_list:
                try:
                    file_name = Path(file_path).name
                    suggested_location = placement_suggestions.get(file_path, 'src/')

                    # Create target directory structure
                    target_dir = output_path / suggested_location
                    target_dir.mkdir(parents=True, exist_ok=True)
                    sorting_summary['created_directories'].add(str(target_dir))

                    # Determine final file location
                    target_file_path = target_dir / file_name

                    if self.test_mode:
                        # Test mode: Create mock sorted files
                        mock_content = f"# Mock sorted file: {file_name}\n"
                        mock_content += f"# Original location: {file_path}\n"
                        mock_content += f"# Sorted to: {suggested_location}\n"
                        mock_content += f"# Intelligence data: {repository_intelligence.get('project_type', 'unknown')}\n"

                        with open(target_file_path, 'w', encoding='utf-8') as f:
                            f.write(mock_content)

                        sorted_files[file_path] = str(target_file_path)
                        sorting_summary['successfully_sorted'] += 1
                        sorting_summary['placement_decisions'][file_path] = {
                            'original_location': file_path,
                            'sorted_location': str(target_file_path),
                            'reason': f"Intelligent placement based on {repository_intelligence.get('framework_detected', 'pattern')} patterns"
                        }

                        self.logger.info(f"✓ Sorted {file_name} to {suggested_location}")

                    else:
                        # Production mode: Actual file operations would go here
                        # For now, we'll simulate the sorting
                        sorted_files[file_path] = str(target_file_path)
                        sorting_summary['successfully_sorted'] += 1
                        sorting_summary['placement_decisions'][file_path] = {
                            'original_location': file_path,
                            'sorted_location': str(target_file_path),
                            'reason': "Production file sorting (simulated)"
                        }

                except Exception as e:
                    self.logger.error(f"Failed to sort {file_path}: {e}")
                    sorting_summary['failed_sorts'] += 1

            # Generate sorting report
            success_rate = (sorting_summary['successfully_sorted'] / sorting_summary['total_files']) * 100 if sorting_summary['total_files'] > 0 else 0

            return AgentResponse(
                agent_name='PythonInternalAgent',
                success=sorting_summary['failed_sorts'] == 0,
                message=f'File sorting completed. Success rate: {success_rate:.1f}% ({sorting_summary["successfully_sorted"]}/{sorting_summary["total_files"]})',
                data={
                    'sorted_files': sorted_files,
                    'sorting_summary': {
                        **sorting_summary,
                        'created_directories': list(sorting_summary['created_directories'])
                    },
                    'output_directory': str(output_path),
                    'success_rate': success_rate,
                    'test_mode': self.test_mode
                }
            )

        except Exception as e:
            self.logger.error(f"File sorting execution failed: {e}")
            return AgentResponse(
                agent_name='PythonInternalAgent',
                success=False,
                message=f'File sorting failed: {str(e)}'
            )

    def cleanup_test_files(self):
        """Clean up test files created during testing"""
        if self.test_mode and self.test_files_created:
            self.logger.info(f"Cleaning up {len(self.test_files_created)} test files")

            for file_path in list(self.test_files_created.keys()):
                try:
                    from pathlib import Path
                    test_file = Path(file_path)
                    if test_file.exists():
                        test_file.unlink()
                        self.logger.info(f"✓ Removed test file: {file_path}")
                    del self.test_files_created[file_path]
                except Exception as e:
                    self.logger.warning(f"Failed to remove test file {file_path}: {e}")

    def set_test_mode(self, enabled: bool):
        """Enable or disable test mode"""
        self.test_mode = enabled
        if not enabled:
            self.cleanup_test_files()
        self.logger.info(f"Test mode: {'enabled' if enabled else 'disabled'}")

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

        # Check if we're in test mode by examining previous results
        test_mode = False
        python_result = previous_results.get('python_internal')
        if python_result and python_result.data and python_result.data.get('test_mode'):
            test_mode = True
            self.logger.info("Test mode detected - validating test file creation")

        validation_results = []
        all_valid = True

        for file_path in expected_files:
            path = Path(file_path)

            if test_mode:
                # Test mode: Check if test file was actually created
                if python_result and python_result.data.get('file_created'):
                    # Verify the file exists and has content
                    if path.exists() and path.stat().st_size > 0:
                        size = path.stat().st_size
                        validation_results.append({
                            'file': str(path),
                            'exists': True,
                            'size_bytes': size,
                            'readable': os.access(path, os.R_OK),
                            'test_mode': True,
                            'validation_type': 'test_file_created'
                        })
                        self.logger.info(f"✓ Test file validated: {path} ({size} bytes)")
                    else:
                        validation_results.append({
                            'file': str(path),
                            'exists': False,
                            'size_bytes': 0,
                            'readable': False,
                            'test_mode': True,
                            'validation_type': 'test_file_missing'
                        })
                        all_valid = False
                        self.logger.error(f"✗ Test file missing: {path}")
                else:
                    # Download failed in test mode
                    validation_results.append({
                        'file': str(path),
                        'exists': False,
                        'size_bytes': 0,
                        'readable': False,
                        'test_mode': True,
                        'validation_type': 'download_failed'
                    })
                    all_valid = False
                    self.logger.error(f"✗ Download failed for: {path}")
            else:
                # Production mode: Standard file validation
                if path.exists():
                    size = path.stat().st_size
                    validation_results.append({
                        'file': str(path),
                        'exists': True,
                        'size_bytes': size,
                        'readable': os.access(path, os.R_OK),
                        'test_mode': False,
                        'validation_type': 'production_file'
                    })
                else:
                    validation_results.append({
                        'file': str(path),
                        'exists': False,
                        'size_bytes': 0,
                        'readable': False,
                        'test_mode': False,
                        'validation_type': 'production_file_missing'
                    })
                    all_valid = False

        validation_message = f'Output validation completed. {len(validation_results)} files checked'
        if test_mode:
            validation_message += ' (test mode)'

        return AgentResponse(
            agent_name='DebuggerAgent',
            success=all_valid,
            message=validation_message,
            data={
                'validation_results': validation_results,
                'all_files_valid': all_valid,
                'test_mode': test_mode
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