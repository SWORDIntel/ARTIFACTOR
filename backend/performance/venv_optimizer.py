"""
Virtual Environment Optimizer
Optimized virtual environment management with intelligent caching and dependency resolution
"""

import os
import sys
import json
import time
import hashlib
import shutil
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import tempfile
import concurrent.futures

logger = logging.getLogger(__name__)

@dataclass
class PackageInfo:
    """Package information with optimization metadata"""
    name: str
    version: str
    size: int = 0
    install_time: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    cached: bool = False
    cache_hit: bool = False

@dataclass
class VenvMetrics:
    """Virtual environment performance metrics"""
    creation_time: float = 0.0
    package_install_time: float = 0.0
    total_packages: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    disk_usage: int = 0
    creation_method: str = "standard"

class OptimizedVenvManager:
    """High-performance virtual environment manager with intelligent caching"""

    def __init__(
        self,
        base_dir: str = "./venvs",
        cache_dir: str = "./venv_cache",
        enable_cache: bool = True,
        parallel_installs: bool = True,
        max_workers: int = 4
    ):
        self.base_dir = Path(base_dir)
        self.cache_dir = Path(cache_dir)
        self.enable_cache = enable_cache
        self.parallel_installs = parallel_installs
        self.max_workers = max_workers

        # Create directories
        self.base_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache management
        self.package_cache: Dict[str, str] = {}
        self.dependency_cache: Dict[str, List[str]] = {}
        self.wheel_cache = self.cache_dir / "wheels"
        self.wheel_cache.mkdir(exist_ok=True)

        # Performance tracking
        self.metrics: Dict[str, VenvMetrics] = {}

        # Load existing cache
        self._load_cache()

    def _load_cache(self):
        """Load existing cache data"""
        cache_file = self.cache_dir / "cache_metadata.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)
                    self.package_cache = cache_data.get('packages', {})
                    self.dependency_cache = cache_data.get('dependencies', {})
                logger.info(f"Loaded cache with {len(self.package_cache)} packages")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save cache data"""
        cache_file = self.cache_dir / "cache_metadata.json"
        try:
            cache_data = {
                'packages': self.package_cache,
                'dependencies': self.dependency_cache,
                'last_updated': datetime.now().isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    async def create_venv_optimized(
        self,
        name: str,
        requirements: List[str],
        python_version: str = None,
        force_recreate: bool = False
    ) -> Tuple[bool, VenvMetrics]:
        """Create optimized virtual environment with advanced caching"""
        start_time = time.time()
        metrics = VenvMetrics()

        venv_path = self.base_dir / name
        requirements_hash = self._hash_requirements(requirements)

        # Check if venv already exists and is valid
        if not force_recreate and await self._is_venv_valid(venv_path, requirements_hash):
            logger.info(f"Virtual environment '{name}' already exists and is valid")
            metrics.creation_time = time.time() - start_time
            metrics.creation_method = "cached_venv"
            return True, metrics

        # Remove existing venv if recreating
        if venv_path.exists():
            shutil.rmtree(venv_path)

        try:
            # Create base virtual environment
            await self._create_base_venv(venv_path, python_version)
            metrics.creation_time = time.time() - start_time

            # Install packages with optimization
            install_start = time.time()
            await self._install_packages_optimized(venv_path, requirements, metrics)
            metrics.package_install_time = time.time() - install_start

            # Save venv metadata
            await self._save_venv_metadata(venv_path, requirements_hash, requirements)

            # Update metrics
            metrics.total_packages = len(requirements)
            metrics.disk_usage = self._calculate_venv_size(venv_path)

            self.metrics[name] = metrics
            self._save_cache()

            logger.info(
                f"Created optimized venv '{name}' in {metrics.creation_time:.2f}s "
                f"(install: {metrics.package_install_time:.2f}s, "
                f"cache hits: {metrics.cache_hits})"
            )

            return True, metrics

        except Exception as e:
            logger.error(f"Failed to create venv '{name}': {e}")
            if venv_path.exists():
                shutil.rmtree(venv_path)
            return False, metrics

    async def _create_base_venv(self, venv_path: Path, python_version: str = None):
        """Create base virtual environment"""
        python_cmd = python_version or sys.executable

        # Use faster venv creation methods
        if shutil.which('uv'):
            # Use uv for ultra-fast venv creation
            cmd = ['uv', 'venv', str(venv_path)]
            if python_version:
                cmd.extend(['--python', python_version])
        else:
            # Fall back to standard venv
            cmd = [python_cmd, '-m', 'venv', str(venv_path)]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Failed to create venv: {stderr.decode()}")

    async def _install_packages_optimized(
        self,
        venv_path: Path,
        requirements: List[str],
        metrics: VenvMetrics
    ):
        """Install packages with advanced optimization strategies"""
        pip_cmd = self._get_pip_command(venv_path)

        # Prepare installation strategies
        cached_packages = []
        uncached_packages = []

        for req in requirements:
            package_key = self._normalize_requirement(req)
            if self.enable_cache and package_key in self.package_cache:
                cached_packages.append(req)
                metrics.cache_hits += 1
            else:
                uncached_packages.append(req)
                metrics.cache_misses += 1

        # Install cached packages first (faster)
        if cached_packages:
            await self._install_from_cache(pip_cmd, cached_packages)

        # Install uncached packages
        if uncached_packages:
            if self.parallel_installs and len(uncached_packages) > 3:
                await self._install_packages_parallel(pip_cmd, uncached_packages)
            else:
                await self._install_packages_sequential(pip_cmd, uncached_packages)

            # Update cache for newly installed packages
            await self._update_package_cache(uncached_packages)

    async def _install_from_cache(self, pip_cmd: List[str], packages: List[str]):
        """Install packages from wheel cache"""
        if not packages:
            return

        # Build command with cache options
        cmd = pip_cmd + [
            'install',
            '--find-links', str(self.wheel_cache),
            '--no-index',  # Use only cached wheels
            '--no-deps',   # Dependencies should also be cached
        ] + packages

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Fall back to normal installation
                logger.warning(f"Cache install failed, falling back: {stderr.decode()}")
                await self._install_packages_sequential(pip_cmd, packages)

        except Exception as e:
            logger.warning(f"Cache install error: {e}")
            await self._install_packages_sequential(pip_cmd, packages)

    async def _install_packages_parallel(self, pip_cmd: List[str], packages: List[str]):
        """Install packages in parallel for faster installation"""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def install_package(package: str):
            async with semaphore:
                cmd = pip_cmd + [
                    'install',
                    '--no-cache-dir',
                    '--find-links', str(self.wheel_cache),
                    package
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise RuntimeError(f"Failed to install {package}: {stderr.decode()}")

        # Install packages in parallel
        tasks = [install_package(pkg) for pkg in packages]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _install_packages_sequential(self, pip_cmd: List[str], packages: List[str]):
        """Install packages sequentially with optimization"""
        if not packages:
            return

        # Use pip install with optimizations
        cmd = pip_cmd + [
            'install',
            '--upgrade',
            '--no-cache-dir',
            '--find-links', str(self.wheel_cache),
            '--prefer-binary',  # Prefer binary wheels
            '--no-warn-script-location',
        ] + packages

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Failed to install packages: {stderr.decode()}")

    async def _update_package_cache(self, packages: List[str]):
        """Update package cache with newly installed packages"""
        for package in packages:
            package_key = self._normalize_requirement(package)
            self.package_cache[package_key] = datetime.now().isoformat()

            # Download wheel for future use
            await self._cache_package_wheel(package)

    async def _cache_package_wheel(self, package: str):
        """Download and cache package wheel"""
        try:
            cmd = [
                sys.executable, '-m', 'pip', 'download',
                '--only-binary=:all:',
                '--dest', str(self.wheel_cache),
                '--no-deps',
                package
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

        except Exception as e:
            logger.debug(f"Failed to cache wheel for {package}: {e}")

    def _get_pip_command(self, venv_path: Path) -> List[str]:
        """Get pip command for virtual environment"""
        if os.name == 'nt':  # Windows
            pip_path = venv_path / 'Scripts' / 'pip.exe'
        else:  # Unix-like
            pip_path = venv_path / 'bin' / 'pip'

        return [str(pip_path)]

    def _hash_requirements(self, requirements: List[str]) -> str:
        """Generate hash for requirements list"""
        normalized = [self._normalize_requirement(req) for req in sorted(requirements)]
        content = '\n'.join(normalized)
        return hashlib.sha256(content.encode()).hexdigest()

    def _normalize_requirement(self, requirement: str) -> str:
        """Normalize requirement string for consistent caching"""
        # Remove whitespace and normalize case
        return requirement.strip().lower()

    async def _is_venv_valid(self, venv_path: Path, requirements_hash: str) -> bool:
        """Check if virtual environment is valid and up-to-date"""
        if not venv_path.exists():
            return False

        # Check metadata file
        metadata_file = venv_path / '.venv_metadata.json'
        if not metadata_file.exists():
            return False

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
                return metadata.get('requirements_hash') == requirements_hash
        except Exception:
            return False

    async def _save_venv_metadata(
        self,
        venv_path: Path,
        requirements_hash: str,
        requirements: List[str]
    ):
        """Save virtual environment metadata"""
        metadata = {
            'requirements_hash': requirements_hash,
            'requirements': requirements,
            'created_at': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': sys.platform
        }

        metadata_file = venv_path / '.venv_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _calculate_venv_size(self, venv_path: Path) -> int:
        """Calculate virtual environment disk usage"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(venv_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
            return total_size
        except Exception:
            return 0

    async def cleanup_old_venvs(self, max_age_days: int = 30):
        """Clean up old virtual environments"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        for venv_dir in self.base_dir.iterdir():
            if not venv_dir.is_dir():
                continue

            try:
                metadata_file = venv_dir / '.venv_metadata.json'
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        created_at = datetime.fromisoformat(metadata['created_at'])

                    if created_at < cutoff_date:
                        shutil.rmtree(venv_dir)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old venv: {venv_dir.name}")

            except Exception as e:
                logger.debug(f"Error cleaning venv {venv_dir.name}: {e}")

        return cleaned_count

    async def optimize_cache(self):
        """Optimize package cache by removing unused wheels"""
        if not self.wheel_cache.exists():
            return

        # Get list of cached packages still in use
        used_packages = set()
        for venv_dir in self.base_dir.iterdir():
            if venv_dir.is_dir():
                metadata_file = venv_dir / '.venv_metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                            for req in metadata.get('requirements', []):
                                used_packages.add(self._normalize_requirement(req))
                    except Exception:
                        pass

        # Remove unused wheels
        removed_count = 0
        for wheel_file in self.wheel_cache.glob('*.whl'):
            package_name = wheel_file.name.split('-')[0].lower()
            if package_name not in used_packages:
                wheel_file.unlink()
                removed_count += 1

        logger.info(f"Optimized cache: removed {removed_count} unused wheels")
        return removed_count

    def get_venv_info(self, name: str) -> Optional[Dict]:
        """Get virtual environment information"""
        venv_path = self.base_dir / name
        if not venv_path.exists():
            return None

        metadata_file = venv_path / '.venv_metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)

                # Add current metrics
                if name in self.metrics:
                    metadata['metrics'] = self.metrics[name].__dict__

                # Add current size
                metadata['current_size'] = self._calculate_venv_size(venv_path)

                return metadata
            except Exception:
                pass

        return {
            'name': name,
            'path': str(venv_path),
            'exists': True,
            'size': self._calculate_venv_size(venv_path)
        }

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        wheel_count = len(list(self.wheel_cache.glob('*.whl')))
        cache_size = sum(f.stat().st_size for f in self.wheel_cache.rglob('*') if f.is_file())

        total_cache_hits = sum(m.cache_hits for m in self.metrics.values())
        total_cache_misses = sum(m.cache_misses for m in self.metrics.values())
        hit_rate = total_cache_hits / max(total_cache_hits + total_cache_misses, 1)

        return {
            'cached_packages': len(self.package_cache),
            'cached_wheels': wheel_count,
            'cache_size_bytes': cache_size,
            'cache_hit_rate': hit_rate,
            'total_cache_hits': total_cache_hits,
            'total_cache_misses': total_cache_misses,
            'venvs_created': len(self.metrics)
        }

# Global venv manager instance
venv_manager = OptimizedVenvManager()

# Utility functions for easy use
async def create_optimized_venv(
    name: str,
    requirements: List[str],
    **kwargs
) -> Tuple[bool, VenvMetrics]:
    """Create optimized virtual environment"""
    return await venv_manager.create_venv_optimized(name, requirements, **kwargs)

async def get_or_create_venv(
    name: str,
    requirements: List[str],
    **kwargs
) -> Tuple[bool, VenvMetrics]:
    """Get existing venv or create optimized one"""
    return await venv_manager.create_venv_optimized(name, requirements, **kwargs)