#!/usr/bin/env python3
"""
Test script for tandem agent coordination (non-GUI)
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the coordinator but disable GUI
os.environ['DISPLAY'] = ''  # Disable GUI

# Import coordinator components directly
exec(open('claude-artifact-coordinator.py').read())
import json
import time

def test_coordination():
    """Test the coordination system without GUI"""
    print("🚀 Testing Claude Artifact Downloader - Tandem Agent Coordination")
    print("=" * 70)

    # Create coordinator
    coordinator = AgentCoordinator()

    # Test 1: Individual agent functionality
    print("\n1️⃣ Testing Individual Agents:")
    print("-" * 30)

    # Test DEBUGGER
    print("🔍 DEBUGGER - System Health Check:")
    result = coordinator.agents['debugger'].execute_action('system_health_check', {})
    print(f"   Status: {'✅' if result.success else '❌'} {result.message}")
    if result.data and 'health_data' in result.data:
        memory = result.data['health_data'].get('memory', {})
        if memory:
            print(f"   Memory: {memory.get('available_gb', 0):.1f}GB available ({100-memory.get('percent_used', 0):.1f}% free)")

    # Test PYTHON-INTERNAL
    print("\n🐍 PYTHON-INTERNAL - Dependency Check:")
    result = coordinator.agents['python_internal'].execute_action('dependency_check', {})
    print(f"   Status: {'✅' if result.success else '❌'} {result.message}")
    if result.data:
        available = len(result.data.get('available_modules', []))
        missing = len(result.data.get('missing_modules', []))
        print(f"   Modules: {available} available, {missing} missing")

    # Test PYGUI (non-GUI mode)
    print("\n🖥️  PYGUI - Progress Display:")
    result = coordinator.agents['pygui'].execute_action('show_progress', {'operation': 'test_coordination'})
    print(f"   Status: {'✅' if result.success else '❌'} {result.message}")

    # Test 2: Input validation workflow
    print("\n2️⃣ Testing Input Validation Workflow:")
    print("-" * 35)

    test_inputs = [
        {
            'name': 'Valid Input',
            'data': {
                'url': 'https://example.com/test.txt',
                'output_path': '/tmp/test_download.txt'
            }
        },
        {
            'name': 'Invalid URL',
            'data': {
                'url': 'not-a-url',
                'output_path': '/tmp/test.txt'
            }
        },
        {
            'name': 'Missing Fields',
            'data': {
                'url': 'https://example.com/test.txt'
                # missing output_path
            }
        }
    ]

    for test_input in test_inputs:
        print(f"\n📝 Testing: {test_input['name']}")
        result = coordinator.agents['debugger'].execute_action('validate_input', {'input_data': test_input['data']})
        print(f"   Validation: {'✅' if result.success else '❌'} {result.message}")
        if not result.success and result.data:
            for issue in result.data.get('validation_results', []):
                print(f"   Issue: {issue}")

    # Test 3: Tandem coordination workflow
    print("\n3️⃣ Testing Tandem Coordination:")
    print("-" * 30)

    test_params = {
        'url': 'https://httpbin.org/json',
        'output_path': '/tmp/coordination_test.json',
        'expected_files': ['/tmp/coordination_test.json']
    }

    print("🔄 Starting download_artifact workflow...")
    results = coordinator.coordinate_tandem_operation('download_artifact', test_params)

    print(f"\n📊 Workflow Results ({len(results)} agents):")
    for agent_name, result in results.items():
        status_icon = "✅" if result.success else "❌"
        print(f"   {status_icon} {agent_name.upper()}: {result.message}")
        print(f"      Execution time: {result.execution_time:.3f}s")

        # Show relevant data
        if result.data:
            if agent_name == 'debugger' and 'validation_results' in result.data:
                issues = result.data['validation_results']
                if issues:
                    print(f"      Issues found: {len(issues)}")
            elif agent_name == 'python_internal' and 'available_modules' in result.data:
                modules = result.data['available_modules']
                print(f"      Modules ready: {', '.join(modules)}")

    # Test 4: Error handling and recovery
    print("\n4️⃣ Testing Error Handling:")
    print("-" * 25)

    error_test_params = {
        'error_info': 'Connection timeout occurred during download',
        'url': 'https://invalid-domain-12345.com/test.txt'
    }

    print("🔧 Testing error analysis...")
    result = coordinator.agents['debugger'].execute_action('analyze_error', error_test_params)
    print(f"   Analysis: {'✅' if result.success else '❌'} {result.message}")

    if result.data:
        categories = result.data.get('detected_categories', [])
        recommendations = result.data.get('recommendations', [])
        print(f"   Categories: {', '.join(categories) if categories else 'None detected'}")
        print(f"   Recommendations: {len(recommendations)} suggestions")
        for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
            print(f"      {i}. {rec}")

    # Test 5: System status and coordination health
    print("\n5️⃣ System Status:")
    print("-" * 15)

    status = coordinator.get_coordination_status()
    print(f"📈 Active tasks: {status['active_tasks']}")
    print(f"📋 Queue size: {status['queue_size']}")
    print(f"🤖 Agents available: {len(status['agents_available'])} ({', '.join(status['agents_available'])})")

    # Performance summary
    total_execution_time = sum(result.execution_time for result in results.values())
    successful_operations = sum(1 for result in results.values() if result.success)

    print(f"\n🎯 Performance Summary:")
    print(f"   Total execution time: {total_execution_time:.3f}s")
    print(f"   Successful operations: {successful_operations}/{len(results)}")
    print(f"   Success rate: {(successful_operations/len(results)*100):.1f}%")

    # Cleanup
    coordinator.shutdown()
    print(f"\n✅ Coordination system test completed successfully!")

    return True

if __name__ == '__main__':
    try:
        test_coordination()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()