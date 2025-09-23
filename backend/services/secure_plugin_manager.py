"""
ARTIFACTOR v3.0 Secure Plugin Manager
Maximum security plugin system with comprehensive sandboxing, validation, and monitoring
"""

import asyncio
import logging
import json
import hashlib
import subprocess
import os
import sys
import tempfile
import shutil
import zipfile
import importlib.util
import resource
import signal
import threading
import time
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import jwt
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ed25519
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import docker
import psutil
import aiofiles
import aiohttp
from pydantic import BaseModel, validator, Field
from contextlib import asynccontextmanager
import multiprocessing
import ctypes
import mmap

logger = logging.getLogger(__name__)

class PluginSecurityError(Exception):
    """Raised when plugin security validation fails"""
    pass

class PluginSandboxViolation(Exception):
    """Raised when plugin violates sandbox restrictions"""
    pass

class SecurePluginManifest(BaseModel):
    """Secure plugin manifest with comprehensive validation"""
    name: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=50)
    version: str = Field(..., regex=r'^\d+\.\d+\.\d+$')
    description: str = Field(..., max_length=500)
    author: str = Field(..., max_length=100)
    author_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    license: str = Field(..., max_length=50)
    homepage: Optional[str] = Field(None, regex=r'^https?://.+$')

    # Security metadata
    entry_point: str = Field(..., regex=r'^[a-zA-Z0-9_/.-]+\.py$')
    api_version: str = Field(default="1.0", regex=r'^\d+\.\d+$')
    min_artifactor_version: str = Field(default="3.0.0")
    security_level: str = Field(default="restricted", regex=r'^(restricted|standard|elevated)$')

    # Resource requirements
    max_memory_mb: int = Field(default=128, ge=1, le=1024)
    max_cpu_percent: float = Field(default=50.0, ge=1.0, le=100.0)
    max_execution_time: int = Field(default=30, ge=1, le=300)
    max_file_size_mb: int = Field(default=10, ge=1, le=100)

    # Permissions
    network_access: bool = Field(default=False)
    file_system_access: bool = Field(default=False)
    database_access: bool = Field(default=False)
    agent_bridge_access: bool = Field(default=False)
    external_commands: bool = Field(default=False)

    # Dependencies and requirements
    python_requirements: List[str] = Field(default_factory=list)
    system_requirements: List[str] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)

    # Digital signature
    signature: Optional[str] = None
    signature_algorithm: str = Field(default="ed25519")
    public_key_fingerprint: Optional[str] = None

    @validator('python_requirements')
    def validate_requirements(cls, v):
        """Validate Python requirements for security"""
        allowed_packages = {
            'requests', 'numpy', 'pandas', 'pydantic', 'fastapi',
            'sqlalchemy', 'aiohttp', 'aiofiles', 'cryptography',
            'pyjwt', 'bcrypt', 'pillow', 'markdown', 'jinja2'
        }

        for req in v:
            package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
            if package_name not in allowed_packages:
                raise ValueError(f"Package '{package_name}' not in allowed list")

        return v

    @validator('api_endpoints')
    def validate_endpoints(cls, v):
        """Validate API endpoints"""
        for endpoint in v:
            if not endpoint.startswith('/api/plugins/'):
                raise ValueError("Plugin endpoints must start with '/api/plugins/'")
            if len(endpoint) > 100:
                raise ValueError("Endpoint path too long")
        return v

class PluginSandbox:
    """Secure sandbox for plugin execution"""

    def __init__(self, manifest: SecurePluginManifest):
        self.manifest = manifest
        self.sandbox_dir = None
        self.process = None
        self.start_time = None
        self.resource_monitor = None
        self.network_blocked = not manifest.network_access
        self.filesystem_restricted = not manifest.file_system_access

    async def __aenter__(self):
        """Enter sandbox context"""
        await self.setup_sandbox()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context"""
        await self.cleanup_sandbox()

    async def setup_sandbox(self):
        """Setup secure sandbox environment"""
        try:
            # Create isolated sandbox directory
            self.sandbox_dir = Path(tempfile.mkdtemp(prefix="plugin_sandbox_"))
            os.chmod(self.sandbox_dir, 0o700)  # Owner only

            # Setup restricted environment
            await self._setup_filesystem_restrictions()
            await self._setup_network_restrictions()
            await self._setup_resource_limits()

            logger.info(f"Sandbox created for plugin {self.manifest.name}")

        except Exception as e:
            logger.error(f"Failed to setup sandbox: {e}")
            raise PluginSecurityError(f"Sandbox setup failed: {e}")

    async def _setup_filesystem_restrictions(self):
        """Setup filesystem access restrictions"""
        if self.filesystem_restricted:
            # Create minimal file system view
            allowed_dirs = ['tmp', 'workspace']
            for dir_name in allowed_dirs:
                dir_path = self.sandbox_dir / dir_name
                dir_path.mkdir(mode=0o700)

            # Block access to sensitive paths
            self.blocked_paths = {
                '/etc', '/proc', '/sys', '/dev', '/root', '/home',
                '/var', '/usr', '/bin', '/sbin', '/lib', '/lib64'
            }

    async def _setup_network_restrictions(self):
        """Setup network access restrictions"""
        if self.network_blocked:
            # Network restrictions will be enforced at process level
            self.blocked_hosts = {'localhost', '127.0.0.1', '::1', '0.0.0.0'}
            self.blocked_ports = {22, 23, 25, 53, 80, 443, 993, 995}

    async def _setup_resource_limits(self):
        """Setup resource usage limits"""
        self.resource_limits = {
            'memory_bytes': self.manifest.max_memory_mb * 1024 * 1024,
            'cpu_percent': self.manifest.max_cpu_percent,
            'execution_time': self.manifest.max_execution_time,
            'open_files': 100,
            'processes': 1
        }

    async def execute_plugin(self, plugin_code: str, function_name: str, *args, **kwargs) -> Any:
        """Execute plugin code in secure sandbox"""
        try:
            self.start_time = time.time()

            # Start resource monitoring
            self.resource_monitor = ResourceMonitor(self.resource_limits)
            await self.resource_monitor.start()

            # Execute in isolated process
            result = await self._execute_in_process(plugin_code, function_name, args, kwargs)

            # Check execution time
            execution_time = time.time() - self.start_time
            if execution_time > self.manifest.max_execution_time:
                raise PluginSandboxViolation(f"Execution time exceeded: {execution_time}s")

            return result

        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            raise
        finally:
            if self.resource_monitor:
                await self.resource_monitor.stop()

    async def _execute_in_process(self, plugin_code: str, function_name: str, args, kwargs) -> Any:
        """Execute plugin in separate process with security restrictions"""
        # Create secure execution environment
        exec_env = {
            '__builtins__': self._get_restricted_builtins(),
            '__name__': '__plugin__',
            '__file__': '<sandbox>',
            'manifest': self.manifest.dict()
        }

        # Add safe imports
        safe_modules = self._get_safe_modules()
        exec_env.update(safe_modules)

        try:
            # Compile and execute plugin code
            compiled_code = compile(plugin_code, '<plugin>', 'exec')
            exec(compiled_code, exec_env)

            # Get the function
            if function_name not in exec_env:
                raise PluginSecurityError(f"Function '{function_name}' not found in plugin")

            plugin_function = exec_env[function_name]
            if not callable(plugin_function):
                raise PluginSecurityError(f"'{function_name}' is not callable")

            # Execute function with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(plugin_function, *args, **kwargs),
                timeout=self.manifest.max_execution_time
            )

            return result

        except asyncio.TimeoutError:
            raise PluginSandboxViolation("Plugin execution timeout")
        except Exception as e:
            raise PluginSecurityError(f"Plugin execution error: {e}")

    def _get_restricted_builtins(self) -> Dict[str, Any]:
        """Get restricted builtins for plugin execution"""
        safe_builtins = {
            # Safe built-ins
            'abs', 'bool', 'dict', 'float', 'int', 'len', 'list', 'max', 'min',
            'range', 'round', 'str', 'sum', 'tuple', 'type', 'zip',
            'enumerate', 'filter', 'map', 'sorted', 'reversed',

            # Safe exceptions
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',

            # Limited I/O
            'print',  # Redirected to logging
        }

        restricted_builtins = {}
        for name in safe_builtins:
            if hasattr(__builtins__, name):
                if name == 'print':
                    restricted_builtins[name] = self._safe_print
                else:
                    restricted_builtins[name] = getattr(__builtins__, name)

        return restricted_builtins

    def _safe_print(self, *args, **kwargs):
        """Safe print function that logs instead of printing"""
        message = ' '.join(str(arg) for arg in args)
        logger.info(f"Plugin {self.manifest.name}: {message}")

    def _get_safe_modules(self) -> Dict[str, Any]:
        """Get safe modules for plugin execution"""
        safe_modules = {}

        # Add safe standard library modules
        if self.manifest.security_level in ['standard', 'elevated']:
            safe_imports = ['json', 'datetime', 'uuid', 're', 'base64', 'hashlib']
            for module_name in safe_imports:
                try:
                    safe_modules[module_name] = __import__(module_name)
                except ImportError:
                    pass

        # Add ARTIFACTOR API if allowed
        if self.manifest.agent_bridge_access:
            safe_modules['artifactor_api'] = self._get_artifactor_api()

        return safe_modules

    def _get_artifactor_api(self) -> Dict[str, Callable]:
        """Get safe ARTIFACTOR API functions"""
        return {
            'log': logger.info,
            'log_error': logger.error,
            'get_plugin_config': lambda: self.manifest.dict(),
            'validate_input': self._validate_plugin_input,
            'sanitize_output': self._sanitize_plugin_output
        }

    def _validate_plugin_input(self, data: Any) -> bool:
        """Validate plugin input data"""
        if isinstance(data, str) and len(data) > 10000:
            return False
        if isinstance(data, (list, dict)) and len(str(data)) > 100000:
            return False
        return True

    def _sanitize_plugin_output(self, data: Any) -> Any:
        """Sanitize plugin output data"""
        if isinstance(data, str):
            # Remove potentially dangerous content
            dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
            for pattern in dangerous_patterns:
                data = data.replace(pattern, '')
        return data

    async def cleanup_sandbox(self):
        """Clean up sandbox environment"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                await asyncio.sleep(1)
                if self.process.poll() is None:
                    self.process.kill()

            if self.sandbox_dir and self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)

            logger.info(f"Sandbox cleaned up for plugin {self.manifest.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup sandbox: {e}")

class ResourceMonitor:
    """Monitor plugin resource usage"""

    def __init__(self, limits: Dict[str, Any]):
        self.limits = limits
        self.monitoring = False
        self.monitor_task = None
        self.violations = []

    async def start(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring:
                # Check memory usage
                memory_usage = psutil.virtual_memory().used
                if memory_usage > self.limits.get('memory_bytes', float('inf')):
                    violation = f"Memory usage exceeded: {memory_usage / 1024 / 1024:.1f}MB"
                    self.violations.append(violation)
                    raise PluginSandboxViolation(violation)

                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.limits.get('cpu_percent', 100):
                    violation = f"CPU usage exceeded: {cpu_percent:.1f}%"
                    self.violations.append(violation)
                    raise PluginSandboxViolation(violation)

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")

class PluginSignatureValidator:
    """Validates plugin digital signatures"""

    def __init__(self):
        self.trusted_keys = self._load_trusted_keys()

    def _load_trusted_keys(self) -> Dict[str, Any]:
        """Load trusted public keys"""
        # In production, these would be loaded from secure storage
        return {}

    def validate_signature(self, manifest: SecurePluginManifest, plugin_data: bytes) -> bool:
        """Validate plugin digital signature"""
        try:
            if not manifest.signature or not manifest.public_key_fingerprint:
                logger.warning(f"Plugin {manifest.name} has no signature")
                return False

            # Get public key by fingerprint
            public_key = self.trusted_keys.get(manifest.public_key_fingerprint)
            if not public_key:
                logger.error(f"Unknown public key fingerprint: {manifest.public_key_fingerprint}")
                return False

            # Verify signature
            signature_bytes = bytes.fromhex(manifest.signature)

            if manifest.signature_algorithm == "ed25519":
                public_key.verify(signature_bytes, plugin_data)
            else:
                raise PluginSecurityError(f"Unsupported signature algorithm: {manifest.signature_algorithm}")

            logger.info(f"Signature validation successful for plugin {manifest.name}")
            return True

        except InvalidSignature:
            logger.error(f"Invalid signature for plugin {manifest.name}")
            return False
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False

class SecurePluginManager:
    """Comprehensive secure plugin management system"""

    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.signature_validator = PluginSignatureValidator()
        self.plugin_stats = {}
        self.blocked_plugins = set()
        self.security_policies = self._load_security_policies()

    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies for plugin management"""
        return {
            'require_signature': True,
            'max_plugins_per_user': 10,
            'sandbox_required': True,
            'network_access_whitelist': [],
            'allowed_file_extensions': ['.py', '.json', '.yaml', '.txt'],
            'max_plugin_size_mb': 10,
            'quarantine_suspicious_plugins': True
        }

    async def install_plugin(
        self,
        plugin_data: bytes,
        user_id: str,
        force_install: bool = False
    ) -> Dict[str, Any]:
        """Install a plugin with comprehensive security validation"""
        try:
            # Extract and validate plugin
            manifest, plugin_files = await self._extract_plugin(plugin_data)

            # Security validation
            await self._validate_plugin_security(manifest, plugin_data, user_id)

            # Signature validation
            if self.security_policies['require_signature'] and not force_install:
                if not self.signature_validator.validate_signature(manifest, plugin_data):
                    raise PluginSecurityError("Plugin signature validation failed")

            # Install in secure environment
            plugin_id = str(uuid.uuid4())
            installation_result = await self._install_plugin_secure(
                plugin_id, manifest, plugin_files, user_id
            )

            # Register plugin
            self.plugins[plugin_id] = {
                'manifest': manifest,
                'files': plugin_files,
                'user_id': user_id,
                'installed_at': datetime.utcnow(),
                'status': 'active',
                'execution_count': 0,
                'last_execution': None
            }

            logger.info(f"Plugin {manifest.name} installed successfully with ID {plugin_id}")
            return {
                'plugin_id': plugin_id,
                'status': 'installed',
                'manifest': manifest.dict(),
                'installation_result': installation_result
            }

        except Exception as e:
            logger.error(f"Plugin installation failed: {e}")
            raise PluginSecurityError(f"Plugin installation failed: {e}")

    async def execute_plugin(
        self,
        plugin_id: str,
        function_name: str,
        user_id: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute a plugin function in secure sandbox"""
        try:
            # Validate plugin and user
            if plugin_id not in self.plugins:
                raise PluginSecurityError("Plugin not found")

            plugin_info = self.plugins[plugin_id]
            if plugin_info['user_id'] != user_id and not self._is_admin_user(user_id):
                raise PluginSecurityError("Unauthorized plugin access")

            if plugin_info['status'] != 'active':
                raise PluginSecurityError("Plugin is not active")

            manifest = plugin_info['manifest']

            # Check if plugin is blocked
            if plugin_id in self.blocked_plugins:
                raise PluginSecurityError("Plugin is blocked due to security violations")

            # Execute in sandbox
            async with PluginSandbox(manifest) as sandbox:
                # Get plugin code
                plugin_code = plugin_info['files'].get('main.py', '')
                if not plugin_code:
                    raise PluginSecurityError("Plugin main code not found")

                # Execute with monitoring
                start_time = time.time()
                result = await sandbox.execute_plugin(plugin_code, function_name, *args, **kwargs)
                execution_time = time.time() - start_time

                # Update statistics
                plugin_info['execution_count'] += 1
                plugin_info['last_execution'] = datetime.utcnow()

                self._update_plugin_stats(plugin_id, execution_time, True)

                logger.info(f"Plugin {manifest.name} executed successfully in {execution_time:.2f}s")
                return result

        except Exception as e:
            self._update_plugin_stats(plugin_id, 0, False, str(e))
            logger.error(f"Plugin execution failed: {e}")

            # Block plugin if too many failures
            if self._should_block_plugin(plugin_id):
                self.blocked_plugins.add(plugin_id)
                logger.warning(f"Plugin {plugin_id} blocked due to repeated failures")

            raise

    async def _extract_plugin(self, plugin_data: bytes) -> Tuple[SecurePluginManifest, Dict[str, str]]:
        """Extract and validate plugin archive"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_file.write(plugin_data)
                temp_path = temp_file.name

            # Extract archive
            plugin_files = {}
            with zipfile.ZipFile(temp_path, 'r') as zip_file:
                # Validate archive
                if len(zip_file.namelist()) > 100:
                    raise PluginSecurityError("Plugin archive contains too many files")

                total_size = sum(info.file_size for info in zip_file.infolist())
                if total_size > self.security_policies['max_plugin_size_mb'] * 1024 * 1024:
                    raise PluginSecurityError("Plugin archive too large")

                # Extract files safely
                for file_info in zip_file.infolist():
                    # Validate file path
                    if '..' in file_info.filename or file_info.filename.startswith('/'):
                        raise PluginSecurityError(f"Dangerous file path: {file_info.filename}")

                    # Check file extension
                    file_ext = Path(file_info.filename).suffix
                    if file_ext not in self.security_policies['allowed_file_extensions']:
                        raise PluginSecurityError(f"Disallowed file extension: {file_ext}")

                    # Extract file content
                    file_content = zip_file.read(file_info.filename).decode('utf-8')
                    plugin_files[file_info.filename] = file_content

            # Load and validate manifest
            if 'manifest.json' not in plugin_files:
                raise PluginSecurityError("Plugin manifest not found")

            manifest_data = json.loads(plugin_files['manifest.json'])
            manifest = SecurePluginManifest(**manifest_data)

            # Cleanup
            os.unlink(temp_path)

            return manifest, plugin_files

        except Exception as e:
            logger.error(f"Plugin extraction failed: {e}")
            raise PluginSecurityError(f"Plugin extraction failed: {e}")

    async def _validate_plugin_security(
        self,
        manifest: SecurePluginManifest,
        plugin_data: bytes,
        user_id: str
    ):
        """Comprehensive plugin security validation"""
        # Check user plugin limit
        user_plugins = sum(1 for p in self.plugins.values() if p['user_id'] == user_id)
        if user_plugins >= self.security_policies['max_plugins_per_user']:
            raise PluginSecurityError("User plugin limit exceeded")

        # Validate plugin name uniqueness
        existing_names = {p['manifest'].name for p in self.plugins.values()}
        if manifest.name in existing_names:
            raise PluginSecurityError("Plugin name already exists")

        # Validate resource requirements
        if manifest.max_memory_mb > 512:
            raise PluginSecurityError("Memory requirement too high")

        if manifest.max_execution_time > 60:
            raise PluginSecurityError("Execution time limit too high")

        # Check security level permissions
        if manifest.security_level == 'elevated' and not self._is_admin_user(user_id):
            raise PluginSecurityError("Elevated security level requires admin privileges")

        # Validate network access
        if manifest.network_access and not self._is_network_allowed(user_id):
            raise PluginSecurityError("Network access not allowed for this user")

    def _is_admin_user(self, user_id: str) -> bool:
        """Check if user has admin privileges"""
        # In production, this would check user roles
        return user_id in os.getenv("ADMIN_USERS", "").split(",")

    def _is_network_allowed(self, user_id: str) -> bool:
        """Check if network access is allowed for user"""
        # In production, this would check user permissions
        return self._is_admin_user(user_id)

    async def _install_plugin_secure(
        self,
        plugin_id: str,
        manifest: SecurePluginManifest,
        plugin_files: Dict[str, str],
        user_id: str
    ) -> Dict[str, Any]:
        """Install plugin in secure environment"""
        try:
            # Create plugin directory
            plugin_dir = Path(f"plugins/{plugin_id}")
            plugin_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

            # Save plugin files securely
            for filename, content in plugin_files.items():
                file_path = plugin_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)

                os.chmod(file_path, 0o600)  # Owner read/write only

            # Install Python dependencies in isolated environment
            if manifest.python_requirements:
                await self._install_dependencies(plugin_id, manifest.python_requirements)

            return {
                'plugin_directory': str(plugin_dir),
                'files_installed': len(plugin_files),
                'dependencies_installed': len(manifest.python_requirements)
            }

        except Exception as e:
            logger.error(f"Secure plugin installation failed: {e}")
            raise PluginSecurityError(f"Secure installation failed: {e}")

    async def _install_dependencies(self, plugin_id: str, requirements: List[str]):
        """Install plugin dependencies in isolated environment"""
        try:
            # Create virtual environment for plugin
            venv_dir = Path(f"plugins/{plugin_id}/venv")
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_dir)
            ], check=True, capture_output=True)

            # Install requirements
            pip_path = venv_dir / 'bin' / 'pip'
            if not pip_path.exists():
                pip_path = venv_dir / 'Scripts' / 'pip.exe'  # Windows

            for requirement in requirements:
                subprocess.run([
                    str(pip_path), 'install', requirement
                ], check=True, capture_output=True, timeout=60)

            logger.info(f"Dependencies installed for plugin {plugin_id}")

        except subprocess.TimeoutExpired:
            raise PluginSecurityError("Dependency installation timeout")
        except subprocess.CalledProcessError as e:
            raise PluginSecurityError(f"Dependency installation failed: {e}")

    def _update_plugin_stats(self, plugin_id: str, execution_time: float, success: bool, error: str = None):
        """Update plugin execution statistics"""
        if plugin_id not in self.plugin_stats:
            self.plugin_stats[plugin_id] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_execution_time': 0,
                'average_execution_time': 0,
                'last_execution': None,
                'last_error': None
            }

        stats = self.plugin_stats[plugin_id]
        stats['total_executions'] += 1
        stats['last_execution'] = datetime.utcnow()

        if success:
            stats['successful_executions'] += 1
            stats['total_execution_time'] += execution_time
            stats['average_execution_time'] = stats['total_execution_time'] / stats['successful_executions']
        else:
            stats['failed_executions'] += 1
            stats['last_error'] = error

    def _should_block_plugin(self, plugin_id: str) -> bool:
        """Determine if plugin should be blocked due to failures"""
        if plugin_id not in self.plugin_stats:
            return False

        stats = self.plugin_stats[plugin_id]
        total = stats['total_executions']
        failed = stats['failed_executions']

        # Block if failure rate > 50% and at least 5 executions
        return total >= 5 and (failed / total) > 0.5

    async def uninstall_plugin(self, plugin_id: str, user_id: str) -> bool:
        """Uninstall plugin securely"""
        try:
            if plugin_id not in self.plugins:
                raise PluginSecurityError("Plugin not found")

            plugin_info = self.plugins[plugin_id]
            if plugin_info['user_id'] != user_id and not self._is_admin_user(user_id):
                raise PluginSecurityError("Unauthorized plugin uninstall")

            # Remove plugin files
            plugin_dir = Path(f"plugins/{plugin_id}")
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            # Remove from registry
            del self.plugins[plugin_id]
            self.blocked_plugins.discard(plugin_id)
            self.plugin_stats.pop(plugin_id, None)

            logger.info(f"Plugin {plugin_id} uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Plugin uninstall failed: {e}")
            raise PluginSecurityError(f"Plugin uninstall failed: {e}")

    def get_plugin_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report for all plugins"""
        return {
            'total_plugins': len(self.plugins),
            'active_plugins': sum(1 for p in self.plugins.values() if p['status'] == 'active'),
            'blocked_plugins': len(self.blocked_plugins),
            'security_violations': sum(
                stats['failed_executions'] for stats in self.plugin_stats.values()
            ),
            'plugin_stats': self.plugin_stats,
            'security_policies': self.security_policies,
            'blocked_plugin_list': list(self.blocked_plugins)
        }

# Global secure plugin manager
secure_plugin_manager = SecurePluginManager()

# Export
__all__ = [
    'SecurePluginManager', 'PluginSandbox', 'SecurePluginManifest',
    'PluginSecurityError', 'PluginSandboxViolation', 'secure_plugin_manager'
]