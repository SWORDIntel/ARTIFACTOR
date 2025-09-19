#!/usr/bin/env python3
"""
Test script to verify the complete venv system works
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description, timeout=30):
    """Run a command and show results"""
    print(f"\n🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        success = result.returncode == 0
        print(f"   Status: {'✅ Success' if success else '❌ Failed'}")

        if result.stdout.strip():
            lines = result.stdout.strip().split('\n')[:5]  # First 5 lines
            for line in lines:
                print(f"   Output: {line}")
            if len(result.stdout.strip().split('\n')) > 5:
                print(f"   ... (truncated)")

        if result.stderr.strip() and not success:
            print(f"   Error: {result.stderr.strip()[:200]}")

        return success

    except subprocess.TimeoutExpired:
        print(f"   Status: ⏰ Timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"   Status: ❌ Exception: {e}")
        return False

def main():
    """Test the complete venv system"""
    print("🧪 Testing Claude Artifact Downloader - Virtual Environment System")
    print("=" * 70)

    # Test 1: Check venv manager status
    success1 = run_command([
        sys.executable, "claude-artifact-venv-manager.py", "--info"
    ], "Checking virtual environment status")

    # Test 2: Test unified launcher status
    success2 = run_command([
        sys.executable, "claude-artifact-launcher.py", "--status"
    ], "Testing unified launcher status")

    # Test 3: Test venv Python execution
    if success1:
        venv_python = "/home/john/.claude-artifacts/venv/bin/python"
        if Path(venv_python).exists():
            success3 = run_command([
                venv_python, "-c", "import requests, psutil; print('Dependencies available')"
            ], "Testing venv dependency availability")
        else:
            success3 = False
            print("   Status: ❌ Venv Python not found")
    else:
        success3 = False

    # Test 4: Test package listing
    success4 = run_command([
        sys.executable, "claude-artifact-venv-manager.py", "--info"
    ], "Checking installed packages")

    # Test 5: Test non-GUI coordinator (quick test)
    success5 = run_command([
        sys.executable, "test-agent-coordination.py"
    ], "Testing agent coordination (non-GUI)", timeout=15)

    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"=" * 30)

    tests = [
        ("Venv Manager Status", success1),
        ("Unified Launcher", success2),
        ("Venv Dependencies", success3),
        ("Package Information", success4),
        ("Agent Coordination", success5)
    ]

    passed = sum(1 for _, success in tests if success)
    total = len(tests)

    for test_name, success in tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! Virtual environment system is working correctly.")
        print("\n🚀 Ready to use:")
        print("   python3 claude-artifact-launcher.py --coordinator  # GUI version")
        print("   python3 claude-artifact-launcher.py --downloader   # CLI version")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)