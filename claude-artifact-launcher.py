#!/usr/bin/env python3
"""
Claude Artifact Downloader - Unified Launcher
Automatically manages virtual environment and launches the application
"""

import os
import sys
import subprocess
from pathlib import Path
import json

class UnifiedLauncher:
    """Unified launcher that handles venv setup and application launch"""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.venv_manager_script = self.script_dir / "claude-artifact-venv-manager.py"
        self.coordinator_script = self.script_dir / "claude-artifact-coordinator.py"
        self.downloader_script = self.script_dir / "claude-artifact-downloader.py"

        # Get venv info from manager
        self.venv_info = self._get_venv_info()

    def _get_venv_info(self):
        """Get virtual environment information"""
        try:
            result = subprocess.run([
                sys.executable, str(self.venv_manager_script), "--info"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse the output to extract info
                lines = result.stdout.strip().split('\n')
                info = {}
                for line in lines:
                    if ':' in line and any(key in line for key in ['Venv Valid', 'Python Executable', 'Setup Complete']):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            info[key] = value

                return info
            else:
                return {}

        except Exception as e:
            print(f"Warning: Could not get venv info: {e}")
            return {}

    def ensure_environment(self, force_setup=False):
        """Ensure virtual environment is set up"""
        venv_valid = self.venv_info.get('Venv Valid', '❌') == '✅'
        setup_complete = self.venv_info.get('Setup Complete', '❌') == '✅'

        if not venv_valid or not setup_complete or force_setup:
            print("🚀 Setting up virtual environment...")

            cmd = [sys.executable, str(self.venv_manager_script), "--setup"]
            if force_setup:
                cmd.append("--force")

            result = subprocess.run(cmd, timeout=300)  # 5 minutes timeout

            if result.returncode != 0:
                print("❌ Failed to set up virtual environment")
                return False

            # Refresh venv info
            self.venv_info = self._get_venv_info()

        return True

    def get_venv_python(self):
        """Get path to Python executable in venv"""
        python_exe = self.venv_info.get('Python Executable', '').strip()

        if python_exe and python_exe != 'None' and Path(python_exe).exists():
            return python_exe

        # Fallback: try to find it manually
        base_dir = Path.home() / ".claude-artifacts"
        venv_dir = base_dir / "venv"

        if os.name == 'nt':  # Windows
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            python_exe = venv_dir / "bin" / "python"

        return str(python_exe) if python_exe.exists() else None

    def launch_application(self, app_type="coordinator", args=None):
        """Launch the specified application"""
        if not self.ensure_environment():
            return False

        python_exe = self.get_venv_python()
        if not python_exe:
            print("❌ Could not find Python executable in virtual environment")
            return False

        # Select script based on app type
        scripts = {
            "coordinator": self.coordinator_script,
            "downloader": self.downloader_script,
            "venv-manager": self.venv_manager_script
        }

        script = scripts.get(app_type)
        if not script or not script.exists():
            print(f"❌ Script not found: {script}")
            return False

        print(f"🚀 Launching {app_type}...")

        # Build command
        cmd = [python_exe, str(script)]
        if args:
            cmd.extend(args)

        try:
            # Use exec to replace current process (better for launchers)
            if os.name != 'nt':  # Unix-like systems
                os.execv(python_exe, cmd)
            else:  # Windows
                result = subprocess.run(cmd)
                return result.returncode == 0

        except Exception as e:
            print(f"❌ Failed to launch application: {e}")
            return False

    def show_status(self):
        """Show current status"""
        print("📊 Claude Artifact Downloader Status")
        print("=" * 40)

        venv_valid = self.venv_info.get('Venv Valid', '❌')
        setup_complete = self.venv_info.get('Setup Complete', '❌')
        python_exe = self.venv_info.get('Python Executable', 'Not found')

        print(f"Virtual Environment: {venv_valid}")
        print(f"Setup Complete: {setup_complete}")
        print(f"Python Executable: {python_exe}")

        # Check script availability
        print(f"\nScript Availability:")
        scripts = {
            "Coordinator": self.coordinator_script,
            "Downloader": self.downloader_script,
            "Venv Manager": self.venv_manager_script
        }

        for name, script in scripts.items():
            status = "✅" if script.exists() else "❌"
            print(f"  {name}: {status} {script}")

        # Show usage
        print(f"\n🎯 Usage:")
        print(f"  Status: python3 {Path(__file__).name} --status")
        print(f"  Setup: python3 {Path(__file__).name} --setup")
        print(f"  Launch Coordinator: python3 {Path(__file__).name} --coordinator")
        print(f"  Launch Downloader: python3 {Path(__file__).name} --downloader")

def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Claude Artifact Downloader - Unified Launcher')
    parser.add_argument('--setup', action='store_true', help='Setup virtual environment')
    parser.add_argument('--force-setup', action='store_true', help='Force recreate environment')
    parser.add_argument('--status', action='store_true', help='Show status information')
    parser.add_argument('--coordinator', action='store_true', help='Launch coordinator with GUI')
    parser.add_argument('--downloader', action='store_true', help='Launch CLI downloader')
    parser.add_argument('--venv-manager', action='store_true', help='Launch venv manager')

    args, unknown_args = parser.parse_known_args()

    launcher = UnifiedLauncher()

    try:
        if args.setup or args.force_setup:
            success = launcher.ensure_environment(force_setup=args.force_setup)
            print("✅ Setup completed" if success else "❌ Setup failed")
            return 0 if success else 1

        elif args.status:
            launcher.show_status()
            return 0

        elif args.coordinator:
            success = launcher.launch_application("coordinator", unknown_args)
            return 0 if success else 1

        elif args.downloader:
            success = launcher.launch_application("downloader", unknown_args)
            return 0 if success else 1

        elif args.venv_manager:
            success = launcher.launch_application("venv-manager", unknown_args)
            return 0 if success else 1

        else:
            # Default: show status and launch coordinator
            launcher.show_status()

            print(f"\n🚀 Launching Coordinator...")
            success = launcher.launch_application("coordinator", unknown_args)
            return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())