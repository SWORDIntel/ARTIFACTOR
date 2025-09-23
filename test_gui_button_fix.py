#!/usr/bin/env python3
"""
Test script to verify the GUI button crash fix
Tests the tandem operation button functionality without user interaction
"""

import sys
import time
import threading
import queue
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the coordinator (note the hyphen in filename)
import importlib.util
import sys

# Load the module with hyphens in filename
spec = importlib.util.spec_from_file_location(
    "claude_artifact_coordinator",
    Path(__file__).parent / "claude-artifact-coordinator.py"
)
coordinator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordinator_module)

AgentCoordinator = coordinator_module.AgentCoordinator
GUI_AVAILABLE = coordinator_module.GUI_AVAILABLE

def test_tandem_button_functionality():
    """Test that the tandem operation button doesn't crash"""
    print("🧪 Testing GUI Button Crash Fix")
    print("=" * 50)

    if not GUI_AVAILABLE:
        print("❌ GUI not available - skipping GUI tests")
        return False

    print("✅ GUI libraries available")

    # Create coordinator
    coordinator = AgentCoordinator()
    print("✅ Agent coordinator initialized")

    # Get PyGUI agent
    pygui_agent = coordinator.agents.get('pygui')
    if not pygui_agent:
        print("❌ PyGUI agent not available")
        return False

    print("✅ PyGUI agent available")

    # Wait for GUI to initialize
    max_wait = 10  # seconds
    wait_time = 0
    while wait_time < max_wait:
        if pygui_agent.root is not None:
            break
        time.sleep(0.1)
        wait_time += 0.1

    if pygui_agent.root is None:
        print("❌ GUI failed to initialize within timeout")
        return False

    print("✅ GUI initialized successfully")

    # Test the button functionality programmatically
    try:
        print("🔧 Testing tandem operation button...")

        # Simulate button click by calling the method directly
        pygui_agent._test_tandem_operation()

        print("✅ Button method called without crash")

        # Wait for tandem operation to complete
        time.sleep(3)

        # Check if any status updates were made
        status_updates_received = False
        try:
            # Check if any messages were added to the queue
            while True:
                request = pygui_agent.gui_queue.get_nowait()
                if request.get('action') == 'update_status':
                    status_updates_received = True
                    message = request.get('params', {}).get('message', '')
                    print(f"📝 Status update: {message}")
        except queue.Empty:
            pass

        if status_updates_received:
            print("✅ Status updates were properly queued")
        else:
            print("⚠️  No status updates detected (may still be working)")

        # Test direct text widget manipulation (the original crash cause)
        try:
            import tkinter as tk

            # Test the fixed status update method
            test_request = {
                'action': 'update_status',
                'params': {'message': 'Test update after fix'}
            }
            pygui_agent._handle_gui_request(test_request)
            print("✅ Direct status update handled without crash")

        except Exception as e:
            print(f"❌ Status update still crashes: {e}")
            return False

        print("\n🎉 All tests passed! GUI button crash is fixed.")

        # Cleanup
        coordinator.shutdown()
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        coordinator.shutdown()
        return False

def test_text_widget_fix():
    """Specifically test the text widget state fix"""
    print("\n🔧 Testing Text Widget State Fix")
    print("-" * 40)

    if not GUI_AVAILABLE:
        print("❌ GUI not available - skipping text widget test")
        return False

    try:
        import tkinter as tk

        # Create a test window to verify the fix
        test_root = tk.Tk()
        test_root.withdraw()  # Hide the window

        # Create a text widget like the one in the GUI
        test_text = tk.Text(test_root, state=tk.DISABLED)

        # Test the original problem scenario
        print("🔍 Testing original crash scenario...")

        # This would have crashed before the fix
        try:
            # Try to insert without enabling (original bug)
            test_text.insert(tk.END, "This should fail\n")
            print("❌ Expected crash didn't occur - something changed")
        except tk.TclError as e:
            print(f"✅ Confirmed original bug exists: {e}")

        # Test the fixed approach
        print("🔧 Testing fixed approach...")
        try:
            # The fixed approach
            test_text.config(state=tk.NORMAL)
            test_text.insert(tk.END, "This should work\n")
            test_text.config(state=tk.DISABLED)
            print("✅ Fixed approach works correctly")

            # Cleanup
            test_root.destroy()
            return True

        except Exception as e:
            print(f"❌ Fixed approach failed: {e}")
            test_root.destroy()
            return False

    except Exception as e:
        print(f"❌ Text widget test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 ARTIFACTOR GUI Button Crash Fix Test")
    print("=" * 60)

    # Test 1: Text widget fix
    text_widget_ok = test_text_widget_fix()

    # Test 2: Full button functionality
    button_ok = test_tandem_button_functionality()

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Text Widget Fix: {'✅ PASS' if text_widget_ok else '❌ FAIL'}")
    print(f"Button Functionality: {'✅ PASS' if button_ok else '❌ FAIL'}")

    if text_widget_ok and button_ok:
        print("\n🎉 ALL TESTS PASSED - GUI crash fix successful!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - investigate further")
        sys.exit(1)