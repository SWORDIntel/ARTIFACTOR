"""
ARTIFACTOR v3.0 Plugin API Router
RESTful API endpoints for plugin management, installation, and execution
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any, List, Optional
import asyncio
import json
import tempfile
import shutil
from pathlib import Path

from ..models import User, Plugin
from ..database import get_database
from ..services.plugin_manager import PluginManager
from ..services.agent_bridge import AgentCoordinationBridge
from ..middleware.auth import get_current_user

router = APIRouter()
security = HTTPBearer()

# Global plugin manager instance (will be injected)
plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    """Dependency to get plugin manager instance"""
    if not plugin_manager:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    return plugin_manager

@router.get("/", response_model=Dict[str, Any])
async def list_plugins(
    enabled_only: bool = Query(False, description="Only return enabled plugins"),
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """List all installed plugins"""
    try:
        db = await get_database()

        query = "SELECT * FROM plugins"
        params = []

        if enabled_only:
            query += " WHERE is_enabled = $1"
            params.append(True)

        query += " ORDER BY name"

        plugins = await db.fetch(query, *params)

        plugin_list = []
        for plugin_row in plugins:
            plugin_data = dict(plugin_row)
            plugin_data['id'] = str(plugin_data['id'])
            plugin_data['created_at'] = plugin_data['installed_at'].isoformat()
            plugin_data['updated_at'] = plugin_data['updated_at'].isoformat() if plugin_data['updated_at'] else None
            plugin_list.append(plugin_data)

        return {
            "success": True,
            "plugins": plugin_list,
            "total": len(plugin_list),
            "enabled_count": len([p for p in plugin_list if p['is_enabled']])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {e}")

@router.get("/registry", response_model=Dict[str, Any])
async def list_registry_plugins(
    search: Optional[str] = Query(None, description="Search query"),
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """List available plugins from registry"""
    try:
        if search:
            plugins = await pm.search_plugins(search)
        else:
            plugins = await pm.list_available_plugins()

        return {
            "success": True,
            "plugins": plugins,
            "total": len(plugins)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list registry plugins: {e}")

@router.post("/install", response_model=Dict[str, Any])
async def install_plugin(
    background_tasks: BackgroundTasks,
    plugin_file: Optional[UploadFile] = File(None),
    plugin_url: Optional[str] = None,
    plugin_name: Optional[str] = None,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Install plugin from file, URL, or registry"""
    try:
        if not any([plugin_file, plugin_url, plugin_name]):
            raise HTTPException(
                status_code=400,
                detail="Must provide plugin_file, plugin_url, or plugin_name"
            )

        # Determine plugin source
        plugin_source = None

        if plugin_file:
            # Handle uploaded file
            temp_file = Path(tempfile.mktemp(suffix='.zip'))
            try:
                with open(temp_file, 'wb') as f:
                    shutil.copyfileobj(plugin_file.file, f)
                plugin_source = temp_file
            except Exception as e:
                if temp_file.exists():
                    temp_file.unlink()
                raise HTTPException(status_code=400, detail=f"Failed to save uploaded file: {e}")

        elif plugin_url:
            plugin_source = plugin_url

        elif plugin_name:
            # Look up in registry
            registry_plugins = await pm.list_available_plugins()
            registry_plugin = next((p for p in registry_plugins if p['name'] == plugin_name), None)

            if not registry_plugin:
                raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found in registry")

            plugin_source = registry_plugin.get('download_url')
            if not plugin_source:
                raise HTTPException(status_code=400, detail=f"No download URL for plugin {plugin_name}")

        # Install plugin in background
        async def install_task():
            try:
                result = await pm.install_plugin(plugin_source, str(current_user.id))
                # Log installation result
                if result.get("success"):
                    print(f"Plugin installation completed: {result}")
                else:
                    print(f"Plugin installation failed: {result}")
            except Exception as e:
                print(f"Plugin installation error: {e}")
            finally:
                # Cleanup temp file if created
                if plugin_file and isinstance(plugin_source, Path) and plugin_source.exists():
                    plugin_source.unlink()

        background_tasks.add_task(install_task)

        return {
            "success": True,
            "message": "Plugin installation started",
            "status": "installing"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start plugin installation: {e}")

@router.post("/{plugin_name}/enable", response_model=Dict[str, Any])
async def enable_plugin(
    plugin_name: str,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Enable installed plugin"""
    try:
        result = await pm.enable_plugin(plugin_name)

        if result["success"]:
            return {
                "success": True,
                "message": f"Plugin {plugin_name} enabled successfully",
                "plugin_name": plugin_name
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable plugin: {e}")

@router.post("/{plugin_name}/disable", response_model=Dict[str, Any])
async def disable_plugin(
    plugin_name: str,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Disable plugin"""
    try:
        result = await pm.disable_plugin(plugin_name)

        if result["success"]:
            return {
                "success": True,
                "message": f"Plugin {plugin_name} disabled successfully",
                "plugin_name": plugin_name
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable plugin: {e}")

@router.delete("/{plugin_name}", response_model=Dict[str, Any])
async def uninstall_plugin(
    plugin_name: str,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Uninstall plugin"""
    try:
        result = await pm.uninstall_plugin(plugin_name)

        if result["success"]:
            return {
                "success": True,
                "message": f"Plugin {plugin_name} uninstalled successfully",
                "plugin_name": plugin_name
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to uninstall plugin: {e}")

@router.get("/{plugin_name}", response_model=Dict[str, Any])
async def get_plugin_details(
    plugin_name: str,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Get plugin details"""
    try:
        db = await get_database()
        plugin = await db.fetchrow("SELECT * FROM plugins WHERE name = $1", plugin_name)

        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")

        plugin_data = dict(plugin)
        plugin_data['id'] = str(plugin_data['id'])
        plugin_data['created_at'] = plugin_data['installed_at'].isoformat()
        plugin_data['updated_at'] = plugin_data['updated_at'].isoformat() if plugin_data['updated_at'] else None

        # Add runtime information
        if plugin_name in pm.enabled_plugins:
            plugin_data['runtime_info'] = {
                "loaded": True,
                "loaded_at": pm.enabled_plugins[plugin_name].get("loaded_at").isoformat()
            }
        else:
            plugin_data['runtime_info'] = {"loaded": False}

        return {
            "success": True,
            "plugin": plugin_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin details: {e}")

@router.post("/{plugin_name}/execute", response_model=Dict[str, Any])
async def execute_plugin_method(
    plugin_name: str,
    execution_request: Dict[str, Any],
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Execute plugin method"""
    try:
        method = execution_request.get("method")
        params = execution_request.get("params", {})

        if not method:
            raise HTTPException(status_code=400, detail="Method name is required")

        result = await pm.execute_plugin(plugin_name, method, params)

        if result["success"]:
            return {
                "success": True,
                "result": result["result"],
                "performance": result.get("performance"),
                "plugin_name": plugin_name,
                "method": method
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "plugin_name": plugin_name,
                "method": method
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute plugin method: {e}")

@router.get("/{plugin_name}/status", response_model=Dict[str, Any])
async def get_plugin_status(
    plugin_name: str,
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Get plugin status and health information"""
    try:
        db = await get_database()
        plugin = await db.fetchrow("SELECT * FROM plugins WHERE name = $1", plugin_name)

        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")

        # Get runtime status
        is_enabled = plugin['is_enabled']
        is_loaded = plugin_name in pm.enabled_plugins

        status = {
            "plugin_name": plugin_name,
            "installed": True,
            "enabled": is_enabled,
            "loaded": is_loaded,
            "version": plugin['version'],
            "health": "healthy" if is_loaded else ("disabled" if is_enabled else "installed"),
        }

        # Add performance metrics if available
        performance_query = """
            SELECT metric_name, AVG(CAST(metric_value AS FLOAT)) as avg_value, COUNT(*) as count
            FROM performance_metrics
            WHERE component = 'plugin_manager' AND tags->>'plugin' = $1
            AND timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY metric_name
        """

        metrics = await db.fetch(performance_query, plugin_name)
        if metrics:
            status["performance"] = {
                row["metric_name"]: {
                    "average": row["avg_value"],
                    "count": row["count"]
                }
                for row in metrics
            }

        return {
            "success": True,
            "status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin status: {e}")

@router.get("/system/status", response_model=Dict[str, Any])
async def get_plugin_system_status(
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Get overall plugin system status"""
    try:
        status = pm.get_status()

        # Add database statistics
        db = await get_database()
        db_stats = await db.fetchrow("""
            SELECT
                COUNT(*) as total_plugins,
                COUNT(*) FILTER (WHERE is_enabled = true) as enabled_plugins,
                COUNT(*) FILTER (WHERE is_system_plugin = true) as system_plugins
            FROM plugins
        """)

        if db_stats:
            status.update({
                "database_stats": dict(db_stats)
            })

        return {
            "success": True,
            "system_status": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin system status: {e}")

@router.post("/system/reload", response_model=Dict[str, Any])
async def reload_plugin_system(
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Reload plugin system (admin only)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Reload all enabled plugins
        enabled_plugins = list(pm.enabled_plugins.keys())

        for plugin_name in enabled_plugins:
            await pm.disable_plugin(plugin_name)
            await pm.enable_plugin(plugin_name)

        return {
            "success": True,
            "message": f"Reloaded {len(enabled_plugins)} plugins",
            "reloaded_plugins": enabled_plugins
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload plugin system: {e}")

@router.get("/performance/metrics", response_model=Dict[str, Any])
async def get_plugin_performance_metrics(
    plugin_name: Optional[str] = Query(None, description="Filter by plugin name"),
    hours: int = Query(24, description="Hours of history to retrieve"),
    pm: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user)
):
    """Get plugin performance metrics"""
    try:
        db = await get_database()

        query = """
            SELECT
                tags->>'plugin' as plugin_name,
                tags->>'method' as method_name,
                metric_name,
                AVG(CAST(metric_value AS FLOAT)) as avg_value,
                MIN(CAST(metric_value AS FLOAT)) as min_value,
                MAX(CAST(metric_value AS FLOAT)) as max_value,
                COUNT(*) as count
            FROM performance_metrics
            WHERE component = 'plugin_manager'
            AND timestamp > NOW() - INTERVAL '%s hours'
        """

        params = [hours]

        if plugin_name:
            query += " AND tags->>'plugin' = $%d" % (len(params) + 1)
            params.append(plugin_name)

        query += """
            GROUP BY tags->>'plugin', tags->>'method', metric_name
            ORDER BY plugin_name, method_name, metric_name
        """

        metrics = await db.fetch(query, *params)

        # Organize metrics by plugin and method
        organized_metrics = {}
        for metric in metrics:
            plugin = metric["plugin_name"] or "unknown"
            method = metric["method_name"] or "unknown"

            if plugin not in organized_metrics:
                organized_metrics[plugin] = {}

            if method not in organized_metrics[plugin]:
                organized_metrics[plugin][method] = {}

            organized_metrics[plugin][method][metric["metric_name"]] = {
                "average": metric["avg_value"],
                "minimum": metric["min_value"],
                "maximum": metric["max_value"],
                "count": metric["count"]
            }

        return {
            "success": True,
            "metrics": organized_metrics,
            "time_range_hours": hours
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {e}")

# Plugin Manager initialization function (called from main.py)
async def initialize_plugin_router(agent_bridge: AgentCoordinationBridge):
    """Initialize plugin router with dependencies"""
    global plugin_manager

    try:
        plugin_manager = PluginManager(agent_bridge)
        await plugin_manager.initialize()
        return plugin_manager

    except Exception as e:
        raise Exception(f"Failed to initialize plugin router: {e}")