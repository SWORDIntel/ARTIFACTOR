"""
ARTIFACTOR v3.0 Plugin Manager
Secure plugin management system with signature verification, sandboxing, and performance monitoring
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
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import docker
import psutil
import aiofiles
import aiohttp
from pydantic import BaseModel, validator

from ..config import settings
from ..models import Plugin, PerformanceMetric, User
from ..database import get_database
from .agent_bridge import AgentCoordinationBridge

logger = logging.getLogger(__name__)

class PluginManifest(BaseModel):
    """Plugin manifest schema for validation"""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: Optional[str] = None

    # Plugin metadata
    entry_point: str
    api_version: str = "1.0"
    min_artifactor_version: str = "3.0.0"

    # Dependencies and requirements
    dependencies: List[str] = []
    python_requirements: List[str] = []
    system_requirements: List[str] = []

    # Security and permissions
    permissions: List[str] = []
    sandbox_mode: bool = True
    network_access: bool = False
    file_system_access: List[str] = []

    # Agent integration
    agent_integration: bool = False
    supported_agents: List[str] = []

    # UI integration
    ui_components: List[Dict[str, Any]] = []
    menu_items: List[Dict[str, Any]] = []

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Plugin name must be alphanumeric with hyphens or underscores')
        return v

    @validator('version')
    def validate_version(cls, v):
        # Simple semver validation
        parts = v.split('.')
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError('Version must be in semver format (x.y.z)')
        return v

class PluginSecurityManager:
    """Handles plugin security verification and sandboxing"""

    def __init__(self):
        self.trusted_keys = {}
        self.sandbox_containers = {}
        self.docker_client = None

    async def initialize(self):
        """Initialize security manager"""
        try:
            # Initialize Docker client for sandboxing
            self.docker_client = docker.from_env()

            # Load trusted signing keys
            await self._load_trusted_keys()

            logger.info("Plugin security manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize plugin security manager: {e}")

    async def _load_trusted_keys(self):
        """Load trusted plugin signing keys"""
        try:
            keys_dir = Path(settings.PLUGIN_TRUSTED_KEYS_DIR)
            if keys_dir.exists():
                for key_file in keys_dir.glob("*.pem"):
                    with open(key_file, 'rb') as f:
                        public_key = serialization.load_pem_public_key(f.read())
                        self.trusted_keys[key_file.stem] = public_key

            logger.info(f"Loaded {len(self.trusted_keys)} trusted signing keys")

        except Exception as e:
            logger.error(f"Error loading trusted keys: {e}")

    async def verify_plugin_signature(self, plugin_path: Path, signature_path: Path) -> bool:
        """Verify plugin signature against trusted keys"""
        try:
            # Read plugin file and signature
            with open(plugin_path, 'rb') as f:
                plugin_data = f.read()

            with open(signature_path, 'rb') as f:
                signature = f.read()

            # Try verification with all trusted keys
            for key_name, public_key in self.trusted_keys.items():
                try:
                    public_key.verify(
                        signature,
                        plugin_data,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                    logger.info(f"Plugin signature verified with key: {key_name}")
                    return True

                except InvalidSignature:
                    continue

            logger.warning("Plugin signature verification failed")
            return False

        except Exception as e:
            logger.error(f"Error verifying plugin signature: {e}")
            return False

    async def scan_plugin_security(self, plugin_path: Path) -> Dict[str, Any]:
        """Scan plugin for security issues"""
        try:
            security_results = {
                "safe": True,
                "issues": [],
                "warnings": [],
                "risk_level": "low"
            }

            # Extract and analyze plugin code
            with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                temp_dir = Path(tempfile.mkdtemp())
                zip_ref.extractall(temp_dir)

                try:
                    # Scan for dangerous patterns
                    dangerous_patterns = [
                        'os.system',
                        'subprocess.call',
                        'eval(',
                        'exec(',
                        '__import__',
                        'open(',
                        'file(',
                        'input(',
                        'raw_input(',
                    ]

                    for py_file in temp_dir.rglob("*.py"):
                        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for pattern in dangerous_patterns:
                            if pattern in content:
                                security_results["issues"].append({
                                    "type": "dangerous_function",
                                    "pattern": pattern,
                                    "file": str(py_file.relative_to(temp_dir)),
                                    "severity": "high"
                                })
                                security_results["safe"] = False
                                security_results["risk_level"] = "high"

                    # Check for network access patterns
                    network_patterns = ['requests.', 'urllib.', 'socket.', 'http.']
                    for py_file in temp_dir.rglob("*.py"):
                        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for pattern in network_patterns:
                            if pattern in content:
                                security_results["warnings"].append({
                                    "type": "network_access",
                                    "pattern": pattern,
                                    "file": str(py_file.relative_to(temp_dir)),
                                    "severity": "medium"
                                })

                finally:
                    shutil.rmtree(temp_dir)

            return security_results

        except Exception as e:
            logger.error(f"Error scanning plugin security: {e}")
            return {
                "safe": False,
                "issues": [{"type": "scan_error", "message": str(e)}],
                "warnings": [],
                "risk_level": "unknown"
            }

    async def create_sandbox(self, plugin_name: str, manifest: PluginManifest) -> str:
        """Create Docker sandbox for plugin execution"""
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")

            # Create sandbox container
            container_name = f"artifactor-plugin-{plugin_name}-{uuid.uuid4().hex[:8]}"

            # Build sandbox image with restricted permissions
            dockerfile_content = f"""
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 pluginuser

# Install minimal requirements
RUN pip install --no-cache-dir {' '.join(manifest.python_requirements)}

# Set working directory
WORKDIR /plugin

# Copy plugin files
COPY . /plugin/

# Switch to non-root user
USER pluginuser

# Set security limits
RUN ulimit -n 1024 -u 256 -m 512000

ENTRYPOINT ["python", "-m", "plugin_runner"]
"""

            # Create temporary directory for sandbox build
            sandbox_dir = Path(tempfile.mkdtemp())
            try:
                dockerfile_path = sandbox_dir / "Dockerfile"
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)

                # Build sandbox image
                image, logs = self.docker_client.images.build(
                    path=str(sandbox_dir),
                    tag=f"artifactor-sandbox-{plugin_name}",
                    rm=True
                )

                # Create container with resource limits
                container = self.docker_client.containers.create(
                    image.id,
                    name=container_name,
                    mem_limit="512m",
                    cpuset_cpus="0",
                    network_mode="none" if not manifest.network_access else "bridge",
                    read_only=True,
                    cap_drop=["ALL"],
                    security_opt=["no-new-privileges"]
                )

                self.sandbox_containers[plugin_name] = container_name
                logger.info(f"Created sandbox for plugin {plugin_name}: {container_name}")
                return container_name

            finally:
                shutil.rmtree(sandbox_dir)

        except Exception as e:
            logger.error(f"Error creating sandbox for {plugin_name}: {e}")
            raise

    async def cleanup_sandbox(self, plugin_name: str):
        """Cleanup plugin sandbox"""
        try:
            container_name = self.sandbox_containers.get(plugin_name)
            if container_name and self.docker_client:
                try:
                    container = self.docker_client.containers.get(container_name)
                    container.stop()
                    container.remove()
                    logger.info(f"Cleaned up sandbox for {plugin_name}")
                except docker.errors.NotFound:
                    pass

            if plugin_name in self.sandbox_containers:
                del self.sandbox_containers[plugin_name]

        except Exception as e:
            logger.error(f"Error cleaning up sandbox for {plugin_name}: {e}")

class PluginManager:
    """Main plugin management system"""

    def __init__(self, agent_bridge: AgentCoordinationBridge):
        self.agent_bridge = agent_bridge
        self.security_manager = PluginSecurityManager()
        self.installed_plugins = {}
        self.enabled_plugins = {}
        self.plugin_registry = {}
        self.performance_monitors = {}

    async def initialize(self):
        """Initialize plugin manager"""
        try:
            logger.info("Initializing Plugin Manager...")

            # Initialize security manager
            await self.security_manager.initialize()

            # Load installed plugins
            await self._load_installed_plugins()

            # Initialize plugin registry
            await self._initialize_plugin_registry()

            logger.info("Plugin Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Plugin Manager: {e}")

    async def _load_installed_plugins(self):
        """Load installed plugins from database"""
        try:
            db = await get_database()
            plugins = await db.fetch("SELECT * FROM plugins WHERE is_enabled = true")

            for plugin_row in plugins:
                plugin_data = dict(plugin_row)
                self.installed_plugins[plugin_data['name']] = plugin_data

                # Load plugin if enabled
                if plugin_data['is_enabled']:
                    await self._load_plugin(plugin_data['name'])

            logger.info(f"Loaded {len(self.installed_plugins)} installed plugins")

        except Exception as e:
            logger.error(f"Error loading installed plugins: {e}")

    async def _initialize_plugin_registry(self):
        """Initialize plugin registry for discovery"""
        try:
            # Load from external registry (GitHub, etc.)
            registry_urls = getattr(settings, 'PLUGIN_REGISTRY_URLS', [])

            for registry_url in registry_urls:
                await self._load_registry_from_url(registry_url)

            logger.info(f"Loaded {len(self.plugin_registry)} plugins from registry")

        except Exception as e:
            logger.error(f"Error initializing plugin registry: {e}")

    async def _load_registry_from_url(self, registry_url: str):
        """Load plugin registry from external URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(registry_url) as response:
                    if response.status == 200:
                        registry_data = await response.json()

                        for plugin_info in registry_data.get('plugins', []):
                            self.plugin_registry[plugin_info['name']] = plugin_info

        except Exception as e:
            logger.error(f"Error loading registry from {registry_url}: {e}")

    async def install_plugin(self, plugin_source: Union[str, Path], user_id: str) -> Dict[str, Any]:
        """Install plugin from source (URL, file path, or registry name)"""
        try:
            logger.info(f"Installing plugin from source: {plugin_source}")

            # Download plugin if it's a URL
            plugin_path = await self._download_plugin(plugin_source)

            # Extract and validate plugin
            temp_dir = Path(tempfile.mkdtemp())
            try:
                with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Load and validate manifest
                manifest_path = temp_dir / "plugin.json"
                if not manifest_path.exists():
                    raise Exception("Plugin manifest (plugin.json) not found")

                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest(**manifest_data)

                # Security verification
                signature_path = temp_dir / "plugin.sig"
                if signature_path.exists():
                    if not await self.security_manager.verify_plugin_signature(plugin_path, signature_path):
                        raise Exception("Plugin signature verification failed")
                else:
                    logger.warning(f"No signature found for plugin {manifest.name}")

                # Security scanning
                security_results = await self.security_manager.scan_plugin_security(plugin_path)
                if not security_results["safe"]:
                    raise Exception(f"Plugin failed security scan: {security_results['issues']}")

                # Check dependencies
                await self._check_plugin_dependencies(manifest)

                # Install plugin
                plugin_install_dir = Path(settings.PLUGINS_DIR) / manifest.name
                plugin_install_dir.mkdir(parents=True, exist_ok=True)

                # Copy plugin files
                shutil.copytree(temp_dir, plugin_install_dir, dirs_exist_ok=True)

                # Store plugin in database
                db = await get_database()
                plugin_id = await db.fetchval("""
                    INSERT INTO plugins (
                        name, version, description, author, config_schema,
                        default_config, install_path, dependencies, requirements
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, manifest.name, manifest.version, manifest.description,
                    manifest.author, manifest.dict(), {}, str(plugin_install_dir),
                    manifest.dependencies, manifest.dict())

                # Create sandbox if required
                if manifest.sandbox_mode:
                    await self.security_manager.create_sandbox(manifest.name, manifest)

                # Register with agent bridge if needed
                if manifest.agent_integration:
                    await self._register_plugin_with_agents(manifest)

                result = {
                    "success": True,
                    "plugin_id": str(plugin_id),
                    "name": manifest.name,
                    "version": manifest.version,
                    "installed_at": datetime.now().isoformat(),
                    "security_scan": security_results
                }

                logger.info(f"Successfully installed plugin: {manifest.name} v{manifest.version}")
                return result

            finally:
                shutil.rmtree(temp_dir)
                if plugin_path != plugin_source:
                    os.unlink(plugin_path)

        except Exception as e:
            logger.error(f"Error installing plugin: {e}")
            return {"success": False, "error": str(e)}

    async def _download_plugin(self, plugin_source: Union[str, Path]) -> Path:
        """Download plugin from URL or return local path"""
        try:
            if isinstance(plugin_source, str) and plugin_source.startswith(('http://', 'https://')):
                # Download from URL
                temp_file = Path(tempfile.mktemp(suffix='.zip'))

                async with aiohttp.ClientSession() as session:
                    async with session.get(plugin_source) as response:
                        if response.status == 200:
                            async with aiofiles.open(temp_file, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            return temp_file
                        else:
                            raise Exception(f"Failed to download plugin: HTTP {response.status}")
            else:
                # Local file path
                return Path(plugin_source)

        except Exception as e:
            logger.error(f"Error downloading plugin: {e}")
            raise

    async def _check_plugin_dependencies(self, manifest: PluginManifest):
        """Check plugin dependencies"""
        try:
            # Check system requirements
            for requirement in manifest.system_requirements:
                if not shutil.which(requirement):
                    raise Exception(f"Missing system requirement: {requirement}")

            # Check Python requirements
            for requirement in manifest.python_requirements:
                try:
                    importlib.import_module(requirement.split('==')[0].split('>=')[0].split('<=')[0])
                except ImportError:
                    logger.warning(f"Python requirement not found: {requirement}")

            # Check plugin dependencies
            for dependency in manifest.dependencies:
                if dependency not in self.installed_plugins:
                    raise Exception(f"Missing plugin dependency: {dependency}")

        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            raise

    async def _register_plugin_with_agents(self, manifest: PluginManifest):
        """Register plugin with agent coordination system"""
        try:
            if self.agent_bridge.is_active:
                registration_data = {
                    "plugin_name": manifest.name,
                    "supported_agents": manifest.supported_agents,
                    "capabilities": manifest.permissions
                }

                result = await self.agent_bridge.invoke_agent("COORDINATOR", {
                    "task_type": "register_plugin",
                    "plugin_data": registration_data
                })

                if result.get("success"):
                    logger.info(f"Plugin {manifest.name} registered with agent system")
                else:
                    logger.warning(f"Failed to register plugin with agents: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error registering plugin with agents: {e}")

    async def enable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Enable installed plugin"""
        try:
            if plugin_name not in self.installed_plugins:
                return {"success": False, "error": "Plugin not installed"}

            # Load plugin
            await self._load_plugin(plugin_name)

            # Update database
            db = await get_database()
            await db.execute(
                "UPDATE plugins SET is_enabled = true WHERE name = $1",
                plugin_name
            )

            self.enabled_plugins[plugin_name] = self.installed_plugins[plugin_name]

            logger.info(f"Enabled plugin: {plugin_name}")
            return {"success": True, "message": f"Plugin {plugin_name} enabled"}

        except Exception as e:
            logger.error(f"Error enabling plugin {plugin_name}: {e}")
            return {"success": False, "error": str(e)}

    async def disable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Disable plugin"""
        try:
            if plugin_name not in self.enabled_plugins:
                return {"success": False, "error": "Plugin not enabled"}

            # Unload plugin
            await self._unload_plugin(plugin_name)

            # Update database
            db = await get_database()
            await db.execute(
                "UPDATE plugins SET is_enabled = false WHERE name = $1",
                plugin_name
            )

            if plugin_name in self.enabled_plugins:
                del self.enabled_plugins[plugin_name]

            logger.info(f"Disabled plugin: {plugin_name}")
            return {"success": True, "message": f"Plugin {plugin_name} disabled"}

        except Exception as e:
            logger.error(f"Error disabling plugin {plugin_name}: {e}")
            return {"success": False, "error": str(e)}

    async def uninstall_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Uninstall plugin"""
        try:
            # Disable plugin first
            if plugin_name in self.enabled_plugins:
                await self.disable_plugin(plugin_name)

            # Cleanup sandbox
            await self.security_manager.cleanup_sandbox(plugin_name)

            # Remove plugin files
            plugin_path = Path(settings.PLUGINS_DIR) / plugin_name
            if plugin_path.exists():
                shutil.rmtree(plugin_path)

            # Remove from database
            db = await get_database()
            await db.execute("DELETE FROM plugins WHERE name = $1", plugin_name)

            # Remove from memory
            if plugin_name in self.installed_plugins:
                del self.installed_plugins[plugin_name]

            logger.info(f"Uninstalled plugin: {plugin_name}")
            return {"success": True, "message": f"Plugin {plugin_name} uninstalled"}

        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _load_plugin(self, plugin_name: str):
        """Load plugin into memory"""
        try:
            plugin_data = self.installed_plugins[plugin_name]
            plugin_path = Path(plugin_data['install_path'])

            # Load plugin manifest
            manifest_path = plugin_path / "plugin.json"
            with open(manifest_path, 'r') as f:
                manifest = PluginManifest(**json.load(f))

            # Load plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}",
                plugin_path / manifest.entry_point
            )

            if spec and spec.loader:
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)

                # Initialize plugin
                if hasattr(plugin_module, 'initialize'):
                    await plugin_module.initialize()

                self.enabled_plugins[plugin_name] = {
                    "manifest": manifest,
                    "module": plugin_module,
                    "loaded_at": datetime.now()
                }

                logger.info(f"Loaded plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            raise

    async def _unload_plugin(self, plugin_name: str):
        """Unload plugin from memory"""
        try:
            if plugin_name in self.enabled_plugins:
                plugin = self.enabled_plugins[plugin_name]

                # Cleanup plugin
                if hasattr(plugin.get("module"), 'cleanup'):
                    await plugin["module"].cleanup()

                del self.enabled_plugins[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")

    async def execute_plugin(self, plugin_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin method with performance monitoring"""
        try:
            if plugin_name not in self.enabled_plugins:
                return {"success": False, "error": "Plugin not enabled"}

            plugin = self.enabled_plugins[plugin_name]
            manifest = plugin["manifest"]
            module = plugin["module"]

            # Start performance monitoring
            start_time = datetime.now()
            start_memory = psutil.Process().memory_info().rss

            try:
                # Execute plugin method
                if hasattr(module, method):
                    result = await getattr(module, method)(**params)
                else:
                    return {"success": False, "error": f"Method {method} not found"}

                # Record performance metrics
                end_time = datetime.now()
                end_memory = psutil.Process().memory_info().rss

                execution_time = (end_time - start_time).total_seconds() * 1000
                memory_usage = (end_memory - start_memory) / 1024 / 1024  # MB

                await self._record_plugin_performance(plugin_name, method, execution_time, memory_usage)

                return {
                    "success": True,
                    "result": result,
                    "performance": {
                        "execution_time": execution_time,
                        "memory_usage": memory_usage
                    }
                }

            except Exception as plugin_error:
                logger.error(f"Plugin execution error in {plugin_name}.{method}: {plugin_error}")
                return {"success": False, "error": str(plugin_error)}

        except Exception as e:
            logger.error(f"Error executing plugin {plugin_name}.{method}: {e}")
            return {"success": False, "error": str(e)}

    async def _record_plugin_performance(self, plugin_name: str, method: str, execution_time: float, memory_usage: float):
        """Record plugin performance metrics"""
        try:
            db = await get_database()

            # Record execution time
            await db.execute("""
                INSERT INTO performance_metrics (metric_name, metric_value, metric_type, component, tags)
                VALUES ($1, $2, $3, $4, $5)
            """, f"plugin_execution_time", str(execution_time), "histogram", "plugin_manager", {
                "plugin": plugin_name,
                "method": method
            })

            # Record memory usage
            await db.execute("""
                INSERT INTO performance_metrics (metric_name, metric_value, metric_type, component, tags)
                VALUES ($1, $2, $3, $4, $5)
            """, f"plugin_memory_usage", str(memory_usage), "gauge", "plugin_manager", {
                "plugin": plugin_name,
                "method": method
            })

        except Exception as e:
            logger.error(f"Error recording plugin performance: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get plugin manager status"""
        return {
            "installed_plugins": len(self.installed_plugins),
            "enabled_plugins": len(self.enabled_plugins),
            "registry_plugins": len(self.plugin_registry),
            "security_manager_active": self.security_manager is not None,
            "sandboxes_active": len(self.security_manager.sandbox_containers) if self.security_manager else 0,
            "plugins": {
                name: {
                    "enabled": name in self.enabled_plugins,
                    "loaded_at": plugin.get("loaded_at").isoformat() if plugin.get("loaded_at") else None
                }
                for name, plugin in self.installed_plugins.items()
            }
        }

    async def list_available_plugins(self) -> List[Dict[str, Any]]:
        """List available plugins from registry"""
        return list(self.plugin_registry.values())

    async def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """Search plugins by name or description"""
        results = []
        query_lower = query.lower()

        for plugin in self.plugin_registry.values():
            if (query_lower in plugin.get('name', '').lower() or
                query_lower in plugin.get('description', '').lower() or
                query_lower in ' '.join(plugin.get('tags', [])).lower()):
                results.append(plugin)

        return results

    async def cleanup(self):
        """Cleanup plugin manager"""
        try:
            logger.info("Cleaning up Plugin Manager...")

            # Disable all plugins
            for plugin_name in list(self.enabled_plugins.keys()):
                await self.disable_plugin(plugin_name)

            # Cleanup security manager
            if self.security_manager:
                for plugin_name in list(self.security_manager.sandbox_containers.keys()):
                    await self.security_manager.cleanup_sandbox(plugin_name)

            logger.info("Plugin Manager cleanup complete")

        except Exception as e:
            logger.error(f"Error during Plugin Manager cleanup: {e}")