"""
ARTIFACTOR v3.0 Plugin SDK
Development toolkit and API interface for community plugin developers
"""

import asyncio
import logging
import json
import os
import tempfile
import shutil
import zipfile
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime
import uuid
import inspect
from abc import ABC, abstractmethod

import jinja2
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PluginAPI:
    """
    Main API interface for plugin development
    Provides access to ARTIFACTOR systems and agent coordination
    """

    def __init__(self, plugin_name: str, agent_bridge=None):
        self.plugin_name = plugin_name
        self.agent_bridge = agent_bridge
        self._event_listeners = {}
        self._ui_components = {}

    # Core API Methods

    async def log(self, level: str, message: str, **kwargs):
        """Log message with plugin context"""
        plugin_logger = logging.getLogger(f"plugin.{self.plugin_name}")
        getattr(plugin_logger, level.lower())(message, extra=kwargs)

    async def get_config(self, key: str = None) -> Union[Dict[str, Any], Any]:
        """Get plugin configuration"""
        try:
            # This would integrate with ARTIFACTOR's configuration system
            # For now, return mock data
            config = {
                "plugin_name": self.plugin_name,
                "version": "1.0.0",
                "enabled": True
            }

            if key:
                return config.get(key)
            return config

        except Exception as e:
            await self.log("error", f"Error getting config: {e}")
            return None

    async def set_config(self, key: str, value: Any) -> bool:
        """Set plugin configuration"""
        try:
            # This would integrate with ARTIFACTOR's configuration system
            await self.log("info", f"Config updated: {key} = {value}")
            return True

        except Exception as e:
            await self.log("error", f"Error setting config: {e}")
            return False

    # Agent Integration

    async def invoke_agent(self, agent_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke ARTIFACTOR agent"""
        try:
            if not self.agent_bridge:
                return {"success": False, "error": "Agent bridge not available"}

            result = await self.agent_bridge.invoke_agent(agent_name, task_data)
            await self.log("info", f"Invoked agent {agent_name}: {result.get('success', False)}")
            return result

        except Exception as e:
            await self.log("error", f"Error invoking agent {agent_name}: {e}")
            return {"success": False, "error": str(e)}

    async def register_agent_handler(self, agent_name: str, handler: Callable) -> bool:
        """Register handler for agent callbacks"""
        try:
            # This would register with the agent coordination system
            await self.log("info", f"Registered handler for agent: {agent_name}")
            return True

        except Exception as e:
            await self.log("error", f"Error registering agent handler: {e}")
            return False

    # Database Integration

    async def execute_query(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute database query (with plugin permissions)"""
        try:
            # This would integrate with ARTIFACTOR's database with proper permissions
            await self.log("info", f"Executing query: {query[:50]}...")

            # Mock response
            return [{"result": "mock_data"}]

        except Exception as e:
            await self.log("error", f"Database query error: {e}")
            return []

    async def get_artifacts(self, filter_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get artifacts with optional filtering"""
        try:
            # Mock artifact data
            artifacts = [
                {
                    "id": "artifact-1",
                    "title": "Sample Artifact",
                    "content": "Sample content",
                    "file_type": "text",
                    "created_at": datetime.now().isoformat()
                }
            ]

            await self.log("info", f"Retrieved {len(artifacts)} artifacts")
            return artifacts

        except Exception as e:
            await self.log("error", f"Error getting artifacts: {e}")
            return []

    async def create_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new artifact"""
        try:
            # This would create an artifact in ARTIFACTOR's system
            artifact_id = str(uuid.uuid4())
            artifact_data["id"] = artifact_id
            artifact_data["created_at"] = datetime.now().isoformat()

            await self.log("info", f"Created artifact: {artifact_id}")
            return {"success": True, "artifact_id": artifact_id}

        except Exception as e:
            await self.log("error", f"Error creating artifact: {e}")
            return {"success": False, "error": str(e)}

    # UI Integration

    async def register_ui_component(self, component_type: str, component_data: Dict[str, Any]) -> bool:
        """Register UI component with ARTIFACTOR"""
        try:
            component_id = f"{self.plugin_name}_{component_type}_{uuid.uuid4().hex[:8]}"
            self._ui_components[component_id] = {
                "type": component_type,
                "plugin": self.plugin_name,
                "data": component_data,
                "registered_at": datetime.now().isoformat()
            }

            await self.log("info", f"Registered UI component: {component_id}")
            return True

        except Exception as e:
            await self.log("error", f"Error registering UI component: {e}")
            return False

    async def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send notification to ARTIFACTOR UI"""
        try:
            # This would send notifications to the web interface
            await self.log("info", f"Sent notification: {notification_data.get('message', 'No message')}")
            return True

        except Exception as e:
            await self.log("error", f"Error sending notification: {e}")
            return False

    # Event System

    async def emit_event(self, event_name: str, event_data: Dict[str, Any]) -> bool:
        """Emit event to ARTIFACTOR event system"""
        try:
            # This would emit events to ARTIFACTOR's event system
            await self.log("info", f"Emitted event: {event_name}")
            return True

        except Exception as e:
            await self.log("error", f"Error emitting event: {e}")
            return False

    async def listen_event(self, event_name: str, handler: Callable) -> bool:
        """Listen for ARTIFACTOR events"""
        try:
            if event_name not in self._event_listeners:
                self._event_listeners[event_name] = []

            self._event_listeners[event_name].append(handler)
            await self.log("info", f"Listening for event: {event_name}")
            return True

        except Exception as e:
            await self.log("error", f"Error listening for event: {e}")
            return False

    # Utility Methods

    async def get_temp_directory(self) -> Path:
        """Get temporary directory for plugin use"""
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=f"artifactor_plugin_{self.plugin_name}_"))
            await self.log("debug", f"Created temp directory: {temp_dir}")
            return temp_dir

        except Exception as e:
            await self.log("error", f"Error creating temp directory: {e}")
            raise

    async def download_file(self, url: str, destination: Path) -> bool:
        """Download file to destination"""
        try:
            # This would use ARTIFACTOR's HTTP client with proper security
            await self.log("info", f"Downloaded file from {url} to {destination}")
            return True

        except Exception as e:
            await self.log("error", f"Error downloading file: {e}")
            return False

class BasePlugin(ABC):
    """
    Base class for ARTIFACTOR plugins
    Provides standard structure and required methods
    """

    def __init__(self, name: str):
        self.name = name
        self.version = "1.0.0"
        self.api_version = "1.0"
        self.api: Optional[PluginAPI] = None
        self.config = {}

    @abstractmethod
    async def initialize(self):
        """Initialize the plugin (required)"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources (required)"""
        pass

    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status (optional override)"""
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self.api is not None,
            "config_loaded": bool(self.config)
        }

    def set_api(self, api: PluginAPI):
        """Set the plugin API instance"""
        self.api = api

class PluginScaffold:
    """
    Plugin scaffolding generator for creating new plugins
    """

    def __init__(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.DictLoader(self._get_templates())
        )

    def _get_templates(self) -> Dict[str, str]:
        """Get plugin templates"""
        return {
            "plugin.json": '''{{plugin_manifest}}''',
            "main.py": '''{{main_py_template}}''',
            "README.md": '''{{readme_template}}''',
            "__init__.py": '''{{init_template}}''',
            "requirements.txt": '''{{requirements_template}}''',
            "tests/test_plugin.py": '''{{test_template}}'''
        }

    async def create_plugin(self, plugin_config: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """Create new plugin from template"""
        try:
            plugin_name = plugin_config["name"]
            plugin_dir = output_dir / plugin_name

            # Create plugin directory
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Generate plugin.json
            plugin_manifest = {
                "name": plugin_config["name"],
                "version": plugin_config.get("version", "1.0.0"),
                "description": plugin_config.get("description", ""),
                "author": plugin_config.get("author", ""),
                "license": plugin_config.get("license", "MIT"),
                "entry_point": "main.py",
                "api_version": "1.0",
                "min_artifactor_version": "3.0.0",
                "dependencies": plugin_config.get("dependencies", []),
                "python_requirements": plugin_config.get("python_requirements", []),
                "permissions": plugin_config.get("permissions", []),
                "sandbox_mode": plugin_config.get("sandbox_mode", True),
                "network_access": plugin_config.get("network_access", False),
                "agent_integration": plugin_config.get("agent_integration", False),
                "config_schema": plugin_config.get("config_schema", {}),
                "default_config": plugin_config.get("default_config", {})
            }

            # Write plugin.json
            with open(plugin_dir / "plugin.json", 'w') as f:
                json.dump(plugin_manifest, f, indent=2)

            # Generate main.py
            main_py_content = self._generate_main_py(plugin_config)
            with open(plugin_dir / "main.py", 'w') as f:
                f.write(main_py_content)

            # Generate README.md
            readme_content = self._generate_readme(plugin_config)
            with open(plugin_dir / "README.md", 'w') as f:
                f.write(readme_content)

            # Generate requirements.txt
            requirements = plugin_config.get("python_requirements", [])
            if requirements:
                with open(plugin_dir / "requirements.txt", 'w') as f:
                    f.write('\n'.join(requirements))

            # Create tests directory
            tests_dir = plugin_dir / "tests"
            tests_dir.mkdir(exist_ok=True)

            # Generate test file
            test_content = self._generate_test_file(plugin_config)
            with open(tests_dir / "test_plugin.py", 'w') as f:
                f.write(test_content)

            # Create __init__.py
            with open(plugin_dir / "__init__.py", 'w') as f:
                f.write(f'"""ARTIFACTOR Plugin: {plugin_name}"""')

            return {
                "success": True,
                "plugin_dir": str(plugin_dir),
                "files_created": [
                    "plugin.json",
                    "main.py",
                    "README.md",
                    "requirements.txt",
                    "tests/test_plugin.py",
                    "__init__.py"
                ]
            }

        except Exception as e:
            logger.error(f"Error creating plugin scaffold: {e}")
            return {"success": False, "error": str(e)}

    def _generate_main_py(self, plugin_config: Dict[str, Any]) -> str:
        """Generate main.py template"""
        plugin_name = plugin_config["name"]
        class_name = ''.join(word.capitalize() for word in plugin_name.replace('-', '_').split('_'))

        return f'''"""
{plugin_config.get("description", plugin_name + " Plugin")}
ARTIFACTOR v3.0 Plugin
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from plugin_sdk import BasePlugin, PluginAPI

logger = logging.getLogger(__name__)

class {class_name}Plugin(BasePlugin):
    """
    {plugin_config.get("description", plugin_name + " plugin for ARTIFACTOR")}
    """

    def __init__(self):
        super().__init__("{plugin_name}")
        self.version = "{plugin_config.get("version", "1.0.0")}"

    async def initialize(self):
        """Initialize the plugin"""
        try:
            await self.api.log("info", "Initializing {plugin_name} plugin...")

            # Load configuration
            self.config = await self.api.get_config()

            # Initialize plugin components
            await self._setup_components()

            await self.api.log("info", "{plugin_name} plugin initialized successfully")

        except Exception as e:
            await self.api.log("error", f"Failed to initialize {plugin_name} plugin: {{e}}")
            raise

    async def _setup_components(self):
        """Setup plugin components"""
        try:
            # Add your plugin initialization code here
            pass

        except Exception as e:
            await self.api.log("error", f"Error setting up components: {{e}}")
            raise

    # Plugin API Methods

    async def example_method(self, param1: str, param2: int = 0) -> Dict[str, Any]:
        """Example plugin method"""
        try:
            await self.api.log("info", f"Example method called with param1={{param1}}, param2={{param2}}")

            # Add your plugin logic here
            result = {{
                "success": True,
                "param1": param1,
                "param2": param2,
                "timestamp": await self._get_timestamp()
            }}

            return result

        except Exception as e:
            await self.api.log("error", f"Error in example_method: {{e}}")
            return {{"success": False, "error": str(e)}}

    async def _get_timestamp(self) -> str:
        """Helper method to get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def cleanup(self):
        """Cleanup plugin resources"""
        try:
            await self.api.log("info", "Cleaning up {plugin_name} plugin...")

            # Add cleanup code here

            await self.api.log("info", "{plugin_name} plugin cleanup complete")

        except Exception as e:
            await self.api.log("error", f"Error during cleanup: {{e}}")

# Plugin instance (required by ARTIFACTOR plugin system)
plugin_instance = {class_name}Plugin()

# Plugin API exports (required by ARTIFACTOR plugin system)
async def initialize():
    """Plugin initialization entry point"""
    await plugin_instance.initialize()

async def cleanup():
    """Plugin cleanup entry point"""
    await plugin_instance.cleanup()

async def get_status() -> Dict[str, Any]:
    """Get plugin status"""
    return await plugin_instance.get_status()

# Public API methods (add your plugin methods here)
async def example_method(param1: str, param2: int = 0) -> Dict[str, Any]:
    """Example plugin method"""
    return await plugin_instance.example_method(param1, param2)
'''

    def _generate_readme(self, plugin_config: Dict[str, Any]) -> str:
        """Generate README.md template"""
        plugin_name = plugin_config["name"]
        description = plugin_config.get("description", "")

        return f'''# {plugin_name}

{description}

## Installation

1. Download or clone this plugin
2. Install in ARTIFACTOR using the Plugin Manager
3. Configure the plugin settings
4. Enable the plugin

## Configuration

This plugin supports the following configuration options:

```json
{{
  // Add your configuration schema here
}}
```

## Usage

### Example Usage

```python
# Example of using this plugin
result = await plugin.example_method("test", 42)
print(result)
```

## API Methods

### example_method(param1, param2=0)

Example method description.

**Parameters:**
- `param1` (str): Description of param1
- `param2` (int, optional): Description of param2. Default: 0

**Returns:**
- `Dict[str, Any]`: Result dictionary

## Development

### Testing

Run tests with:

```bash
python -m pytest tests/
```

### Building

Create a plugin package:

```bash
python setup.py sdist
```

## License

{plugin_config.get("license", "MIT")}

## Author

{plugin_config.get("author", "")}
'''

    def _generate_test_file(self, plugin_config: Dict[str, Any]) -> str:
        """Generate test file template"""
        plugin_name = plugin_config["name"]
        class_name = ''.join(word.capitalize() for word in plugin_name.replace('-', '_').split('_'))

        return f'''"""
Tests for {plugin_name} plugin
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Import your plugin
from main import {class_name}Plugin, plugin_instance
from plugin_sdk import PluginAPI

class TestPlugin:
    """Test suite for {plugin_name} plugin"""

    def setup_method(self):
        """Setup test environment"""
        self.plugin = {class_name}Plugin()
        self.mock_api = AsyncMock(spec=PluginAPI)
        self.plugin.set_api(self.mock_api)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test plugin initialization"""
        await self.plugin.initialize()
        self.mock_api.log.assert_called()

    @pytest.mark.asyncio
    async def test_example_method(self):
        """Test example method"""
        result = await self.plugin.example_method("test", 42)

        assert result["success"] is True
        assert result["param1"] == "test"
        assert result["param2"] == 42
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test plugin cleanup"""
        await self.plugin.cleanup()
        self.mock_api.log.assert_called()

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get status method"""
        status = await self.plugin.get_status()

        assert "name" in status
        assert status["name"] == "{plugin_name}"
        assert "version" in status

if __name__ == "__main__":
    pytest.main([__file__])
'''

class PluginValidator:
    """
    Plugin validation and testing utilities
    """

    def __init__(self):
        self.validation_rules = {
            "required_files": ["plugin.json", "main.py"],
            "required_manifest_fields": ["name", "version", "description", "author", "entry_point"],
            "required_api_methods": ["initialize", "cleanup"]
        }

    async def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin structure and implementation"""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "info": []
            }

            # Check required files
            for required_file in self.validation_rules["required_files"]:
                file_path = plugin_path / required_file
                if not file_path.exists():
                    validation_result["errors"].append(f"Missing required file: {required_file}")
                    validation_result["valid"] = False

            # Validate plugin.json
            manifest_path = plugin_path / "plugin.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)

                    # Check required fields
                    for field in self.validation_rules["required_manifest_fields"]:
                        if field not in manifest:
                            validation_result["errors"].append(f"Missing required manifest field: {field}")
                            validation_result["valid"] = False

                    # Validate version format
                    version = manifest.get("version", "")
                    if not self._validate_version(version):
                        validation_result["warnings"].append(f"Invalid version format: {version}")

                except json.JSONDecodeError as e:
                    validation_result["errors"].append(f"Invalid JSON in plugin.json: {e}")
                    validation_result["valid"] = False

            # Validate main.py
            main_py_path = plugin_path / "main.py"
            if main_py_path.exists():
                validation_result.update(await self._validate_main_py(main_py_path))

            # Check for security issues
            security_result = await self._scan_security(plugin_path)
            validation_result["security"] = security_result

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {e}"],
                "warnings": [],
                "info": []
            }

    async def _validate_main_py(self, main_py_path: Path) -> Dict[str, List[str]]:
        """Validate main.py implementation"""
        result = {"errors": [], "warnings": [], "info": []}

        try:
            with open(main_py_path, 'r') as f:
                content = f.read()

            # Check for required API methods
            for method in self.validation_rules["required_api_methods"]:
                if f"async def {method}(" not in content:
                    result["errors"].append(f"Missing required method: {method}")

            # Check for plugin instance
            if "plugin_instance" not in content:
                result["warnings"].append("No plugin_instance variable found")

            # Check for proper imports
            if "from plugin_sdk import" not in content:
                result["warnings"].append("Plugin SDK import not found")

        except Exception as e:
            result["errors"].append(f"Error reading main.py: {e}")

        return result

    async def _scan_security(self, plugin_path: Path) -> Dict[str, Any]:
        """Basic security scan of plugin code"""
        security_result = {
            "safe": True,
            "issues": [],
            "warnings": []
        }

        try:
            dangerous_patterns = [
                'os.system',
                'subprocess.call',
                'eval(',
                'exec(',
                '__import__',
                'open(',
                'file('
            ]

            for py_file in plugin_path.rglob("*.py"):
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern in dangerous_patterns:
                    if pattern in content:
                        security_result["issues"].append({
                            "type": "dangerous_function",
                            "pattern": pattern,
                            "file": str(py_file.relative_to(plugin_path))
                        })
                        security_result["safe"] = False

        except Exception as e:
            security_result["warnings"].append(f"Security scan error: {e}")

        return security_result

    def _validate_version(self, version: str) -> bool:
        """Validate version format (simple semver)"""
        try:
            parts = version.split('.')
            return len(parts) == 3 and all(part.isdigit() for part in parts)
        except:
            return False

class PluginSDK:
    """
    Main SDK class providing development tools and utilities
    """

    def __init__(self):
        self.scaffold = PluginScaffold()
        self.validator = PluginValidator()

    async def create_plugin(self, plugin_config: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """Create new plugin from template"""
        return await self.scaffold.create_plugin(plugin_config, output_dir)

    async def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """Validate plugin"""
        return await self.validator.validate_plugin(plugin_path)

    async def package_plugin(self, plugin_path: Path, output_path: Path) -> Dict[str, Any]:
        """Package plugin for distribution"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in plugin_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(plugin_path)
                        zipf.write(file_path, arcname)

            return {
                "success": True,
                "package_path": str(output_path),
                "size": output_path.stat().st_size
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_api_documentation(self) -> Dict[str, Any]:
        """Get comprehensive API documentation"""
        return {
            "plugin_api": {
                "description": "Main API interface for plugin development",
                "methods": {
                    "log": "Log message with plugin context",
                    "get_config": "Get plugin configuration",
                    "set_config": "Set plugin configuration",
                    "invoke_agent": "Invoke ARTIFACTOR agent",
                    "execute_query": "Execute database query",
                    "get_artifacts": "Get artifacts with filtering",
                    "create_artifact": "Create new artifact",
                    "register_ui_component": "Register UI component",
                    "send_notification": "Send notification to UI",
                    "emit_event": "Emit event to event system",
                    "listen_event": "Listen for ARTIFACTOR events",
                    "get_temp_directory": "Get temporary directory",
                    "download_file": "Download file securely"
                }
            },
            "base_plugin": {
                "description": "Base class for plugin development",
                "required_methods": ["initialize", "cleanup"],
                "optional_methods": ["get_status"]
            },
            "manifest_schema": {
                "required_fields": ["name", "version", "description", "author", "entry_point"],
                "optional_fields": ["dependencies", "permissions", "ui_components", "config_schema"]
            }
        }