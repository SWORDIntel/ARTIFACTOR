#!/usr/bin/env python3
"""
Claude Artifact Downloader - Virtual Environment Manager
Automatically creates and manages isolated Python environment with dependencies
"""

import os
import sys
import subprocess
import shutil
import venv
from pathlib import Path
import json
import logging
import time
from typing import Dict, List, Optional, Tuple

class VenvManager:
    """Manages virtual environment creation and dependency installation"""

    def __init__(self, project_name: str = "claude-artifact-downloader",
                 base_dir: Optional[str] = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path.home() / ".claude-artifacts"
        self.venv_dir = self.base_dir / "venv"
        self.config_file = self.base_dir / "venv-config.json"

        # Setup logging
        self.logger = self._setup_logging()

        # Create base directory
        self.base_dir.mkdir(exist_ok=True)

        # Required dependencies
        self.required_packages = [
            "requests>=2.31.0",
            "urllib3>=2.0.0",
            "psutil>=5.9.0",
            "pyperclip>=1.8.2",
            "cryptography>=41.0.0",
            "certifi>=2023.7.22",
            "charset-normalizer>=3.2.0",
            "idna>=3.4"
        ]

        # Optional GUI dependencies
        self.gui_packages = [
            "pillow>=10.0.0",
            "matplotlib>=3.7.0"
        ]

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for venv manager"""
        logger = logging.getLogger('venv_manager')
        logger.setLevel(logging.INFO)

        # Console handler
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def is_venv_valid(self) -> bool:
        """Check if virtual environment exists and is valid"""
        if not self.venv_dir.exists():
            return False

        # Check for Python executable
        python_exe = self.get_python_executable()
        if not python_exe or not Path(python_exe).exists():
            return False

        # Check if pip is available
        pip_exe = self.get_pip_executable()
        if not pip_exe or not Path(pip_exe).exists():
            return False

        # Check configuration
        if not self.config_file.exists():
            return False

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # Verify venv was created with current Python version
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            venv_version = config.get('python_version', '')

            if not venv_version.startswith(current_version):
                self.logger.warning(f"Venv Python version {venv_version} != current {current_version}")
                return False

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Invalid venv config: {e}")
            return False

        return True

    def create_venv(self, force: bool = False) -> bool:
        """Create virtual environment"""
        if self.is_venv_valid() and not force:
            self.logger.info("Virtual environment already exists and is valid")
            return True

        if force and self.venv_dir.exists():
            self.logger.info("Removing existing virtual environment...")
            shutil.rmtree(self.venv_dir)

        self.logger.info(f"Creating virtual environment at {self.venv_dir}")

        try:
            # Create venv
            venv_builder = venv.EnvBuilder(
                system_site_packages=False,
                clear=True,
                symlinks=False,
                upgrade=True,
                with_pip=True,
                prompt=f"({self.project_name})"
            )

            venv_builder.create(self.venv_dir)

            # Verify creation
            python_exe = self.get_python_executable()
            if not python_exe or not Path(python_exe).exists():
                raise RuntimeError("Failed to create Python executable")

            # Update pip
            self.logger.info("Updating pip...")
            result = subprocess.run([
                python_exe, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                self.logger.warning(f"Pip upgrade failed: {result.stderr}")

            # Save configuration
            config = {
                'created_at': time.time(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'python_executable': str(python_exe),
                'project_name': self.project_name,
                'base_dir': str(self.base_dir),
                'venv_dir': str(self.venv_dir)
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            self.logger.info("Virtual environment created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create virtual environment: {e}")
            return False

    def install_dependencies(self, include_gui: bool = True) -> bool:
        """Install required dependencies"""
        if not self.is_venv_valid():
            self.logger.error("No valid virtual environment found")
            return False

        python_exe = self.get_python_executable()
        packages = self.required_packages.copy()

        if include_gui:
            packages.extend(self.gui_packages)

        self.logger.info(f"Installing {len(packages)} packages...")

        try:
            # Install packages
            cmd = [python_exe, "-m", "pip", "install"] + packages

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )

            if result.returncode == 0:
                self.logger.info("All dependencies installed successfully")

                # Update config with installed packages
                installed_packages = self.get_installed_packages()
                config = self.load_config()
                config['installed_packages'] = installed_packages
                config['last_install'] = time.time()

                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                return True
            else:
                self.logger.error(f"Package installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Package installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Package installation error: {e}")
            return False

    def get_python_executable(self) -> Optional[str]:
        """Get path to Python executable in venv"""
        if os.name == 'nt':  # Windows
            python_exe = self.venv_dir / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            python_exe = self.venv_dir / "bin" / "python"

        return str(python_exe) if python_exe.exists() else None

    def get_pip_executable(self) -> Optional[str]:
        """Get path to pip executable in venv"""
        if os.name == 'nt':  # Windows
            pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            pip_exe = self.venv_dir / "bin" / "pip"

        return str(pip_exe) if pip_exe.exists() else None

    def get_activation_script(self) -> Optional[str]:
        """Get path to activation script"""
        if os.name == 'nt':  # Windows
            activate_script = self.venv_dir / "Scripts" / "activate.bat"
        else:  # Unix/Linux/macOS
            activate_script = self.venv_dir / "bin" / "activate"

        if activate_script.exists():
            return str(activate_script)
        else:
            self.logger.warning(f"Activation script not found: {activate_script}")
            return None

    def get_installed_packages(self) -> Dict[str, str]:
        """Get list of installed packages with versions"""
        python_exe = self.get_python_executable()
        if not python_exe:
            return {}

        try:
            result = subprocess.run([
                python_exe, "-m", "pip", "list", "--format=json"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg['name']: pkg['version'] for pkg in packages}
            else:
                self.logger.warning(f"Failed to get package list: {result.stderr}")
                return {}

        except Exception as e:
            self.logger.warning(f"Error getting package list: {e}")
            return {}

    def load_config(self) -> Dict:
        """Load venv configuration"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}")
            return {}

    def check_dependencies(self) -> Tuple[List[str], List[str]]:
        """Check which dependencies are missing"""
        installed = self.get_installed_packages()
        installed_names = {name.lower().replace('-', '_') for name in installed.keys()}

        missing = []
        available = []

        for package in self.required_packages:
            package_name = package.split('>=')[0].split('==')[0].lower().replace('-', '_')
            if package_name in installed_names:
                available.append(package)
            else:
                missing.append(package)

        return available, missing

    def setup_complete_environment(self, force_recreate: bool = False,
                                 include_gui: bool = True) -> bool:
        """Complete environment setup with venv and dependencies"""
        self.logger.info("Setting up complete Python environment...")

        # Step 1: Create/verify virtual environment
        if not self.create_venv(force=force_recreate):
            self.logger.error("Failed to create virtual environment")
            return False

        # Step 2: Install dependencies
        if not self.install_dependencies(include_gui=include_gui):
            self.logger.error("Failed to install dependencies")
            return False

        # Step 3: Verify installation
        available, missing = self.check_dependencies()

        if missing:
            self.logger.warning(f"Some packages are still missing: {missing}")
            return False

        self.logger.info(f"Environment setup complete! {len(available)} packages installed")
        return True

    def get_environment_info(self) -> Dict:
        """Get comprehensive environment information"""
        config = self.load_config()
        installed_packages = self.get_installed_packages()
        available, missing = self.check_dependencies()

        return {
            'venv_valid': self.is_venv_valid(),
            'venv_dir': str(self.venv_dir),
            'python_executable': self.get_python_executable(),
            'pip_executable': self.get_pip_executable(),
            'activation_script': self.get_activation_script(),
            'config': config,
            'installed_packages': installed_packages,
            'available_dependencies': available,
            'missing_dependencies': missing,
            'total_packages': len(installed_packages),
            'required_packages': len(self.required_packages),
            'setup_complete': len(missing) == 0
        }

    def generate_launcher_script(self, script_name: str = "launch-with-venv.sh") -> str:
        """Generate launcher script that activates venv"""
        launcher_path = self.base_dir / script_name

        if os.name == 'nt':  # Windows
            launcher_content = f'''@echo off
REM Claude Artifact Downloader Launcher (Windows)
set VENV_DIR={self.venv_dir}
set PYTHON_EXE={self.get_python_executable()}

if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found
    echo Run: python claude-artifact-venv-manager.py --setup
    pause
    exit /b 1
)

echo Activating virtual environment...
call "%VENV_DIR%\\Scripts\\activate.bat"

echo Starting Claude Artifact Downloader...
"%PYTHON_EXE%" claude-artifact-coordinator.py %*

pause
'''
        else:  # Unix/Linux/macOS
            launcher_content = f'''#!/bin/bash
# Claude Artifact Downloader Launcher (Unix)
set -e

VENV_DIR="{self.venv_dir}"
PYTHON_EXE="{self.get_python_executable()}"
ACTIVATE_SCRIPT="{self.get_activation_script()}"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "Error: Virtual environment not found"
    echo "Run: python3 claude-artifact-venv-manager.py --setup"
    exit 1
fi

echo "Activating virtual environment..."
source "$ACTIVATE_SCRIPT"

echo "Starting Claude Artifact Downloader..."
exec "$PYTHON_EXE" claude-artifact-coordinator.py "$@"
'''

        # Write launcher script
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)

        # Make executable on Unix
        if os.name != 'nt':
            os.chmod(launcher_path, 0o755)

        self.logger.info(f"Launcher script created: {launcher_path}")
        return str(launcher_path)

    def cleanup(self) -> bool:
        """Remove virtual environment and config"""
        self.logger.info("Cleaning up virtual environment...")

        try:
            if self.venv_dir.exists():
                shutil.rmtree(self.venv_dir)

            if self.config_file.exists():
                self.config_file.unlink()

            self.logger.info("Cleanup completed")
            return True

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return False

def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Claude Artifact Downloader - Virtual Environment Manager')
    parser.add_argument('--setup', action='store_true', help='Setup complete environment')
    parser.add_argument('--force', action='store_true', help='Force recreate environment')
    parser.add_argument('--no-gui', action='store_true', help='Skip GUI dependencies')
    parser.add_argument('--info', action='store_true', help='Show environment info')
    parser.add_argument('--cleanup', action='store_true', help='Remove environment')
    parser.add_argument('--launcher', action='store_true', help='Generate launcher script')
    parser.add_argument('--project-name', default='claude-artifact-downloader', help='Project name')
    parser.add_argument('--base-dir', help='Base directory for venv')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create manager
    manager = VenvManager(
        project_name=args.project_name,
        base_dir=args.base_dir
    )

    try:
        if args.cleanup:
            print("🧹 Cleaning up virtual environment...")
            success = manager.cleanup()
            print("✅ Cleanup completed" if success else "❌ Cleanup failed")
            return 0 if success else 1

        elif args.info:
            print("📊 Environment Information:")
            print("=" * 50)
            info = manager.get_environment_info()

            print(f"Venv Valid: {'✅' if info['venv_valid'] else '❌'}")
            print(f"Venv Directory: {info['venv_dir']}")
            print(f"Python Executable: {info['python_executable']}")
            print(f"Setup Complete: {'✅' if info['setup_complete'] else '❌'}")
            print(f"Total Packages: {info['total_packages']}")
            print(f"Missing Dependencies: {len(info['missing_dependencies'])}")

            if info['missing_dependencies']:
                print("\nMissing packages:")
                for pkg in info['missing_dependencies']:
                    print(f"  - {pkg}")

            return 0

        elif args.setup:
            print("🚀 Setting up virtual environment...")
            success = manager.setup_complete_environment(
                force_recreate=args.force,
                include_gui=not args.no_gui
            )

            if success:
                print("✅ Environment setup completed successfully!")

                # Generate launcher script
                launcher_path = manager.generate_launcher_script()
                print(f"📝 Launcher script created: {launcher_path}")

                # Show usage info
                print("\n🎯 Usage:")
                print(f"  Direct: {manager.get_python_executable()} claude-artifact-coordinator.py")
                print(f"  Launcher: {launcher_path}")

            else:
                print("❌ Environment setup failed")

            return 0 if success else 1

        elif args.launcher:
            if not manager.is_venv_valid():
                print("❌ No valid virtual environment found. Run --setup first.")
                return 1

            launcher_path = manager.generate_launcher_script()
            print(f"✅ Launcher script created: {launcher_path}")
            return 0

        else:
            # Default: check status and offer setup
            info = manager.get_environment_info()

            if info['venv_valid'] and info['setup_complete']:
                print("✅ Virtual environment is ready!")
                print(f"   Python: {info['python_executable']}")
                print(f"   Packages: {info['total_packages']} installed")

                # Show launcher if available
                launcher = manager.base_dir / "launch-with-venv.sh"
                if launcher.exists():
                    print(f"   Launcher: {launcher}")

            else:
                print("⚠️  Virtual environment not ready")
                print("   Run: python3 claude-artifact-venv-manager.py --setup")

            return 0

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())