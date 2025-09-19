#!/usr/bin/env python3
"""
DEBUGGER Agent: Production Timing Fix for File Validation
Addresses file validation timing issues identified in comprehensive debugging analysis.
"""

import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import logging

class EnhancedDebuggerAgent:
    """Enhanced debugger agent with production timing fixes"""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.logger = logging.getLogger('enhanced_debugger')

    def action_validate_output_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced output validation with retry logic and timing buffer
        Addresses timing issues identified in debugging analysis
        """
        expected_files = params.get('expected_files', [])
        max_retries = params.get('max_retries', 3)
        delay_ms = params.get('delay_ms', 50)  # 50ms buffer for filesystem operations

        self.logger.info(f"Enhanced validation: {expected_files} (retries: {max_retries})")

        validation_results = []
        overall_success = True

        for attempt in range(max_retries):
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                time.sleep(delay_ms / 1000.0)  # Convert ms to seconds

            attempt_success = True
            current_results = []

            for file_path in expected_files:
                path = Path(file_path)
                exists = path.exists()

                if exists:
                    size = path.stat().st_size if path.exists() else 0
                    current_results.append({
                        'file': str(path),
                        'exists': True,
                        'size': size,
                        'attempt': attempt + 1
                    })
                else:
                    attempt_success = False
                    current_results.append({
                        'file': str(path),
                        'exists': False,
                        'size': 0,
                        'attempt': attempt + 1
                    })

            if attempt_success:
                validation_results = current_results
                overall_success = True
                break
        else:
            # All retries exhausted
            validation_results = current_results
            overall_success = False

        return {
            'agent_name': 'EnhancedDebuggerAgent',
            'success': overall_success,
            'message': f'Enhanced validation completed. {len(validation_results)} files checked, {max_retries} retries max.',
            'data': {
                'validation_results': validation_results,
                'all_files_valid': overall_success,
                'retries_used': attempt + 1 if not overall_success else attempt + 1,
                'timing_buffer_ms': delay_ms,
                'enhanced': True
            }
        }

    def action_validate_input_enhanced(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced input validation with detailed diagnostics"""
        input_data = params.get('input_data', {})

        self.logger.info("Enhanced input validation with diagnostics")

        validation_checks = {
            'required_fields': self._check_required_fields(input_data),
            'data_types': self._check_data_types(input_data),
            'value_ranges': self._check_value_ranges(input_data),
            'security': self._check_security_constraints(input_data)
        }

        all_passed = all(check['passed'] for check in validation_checks.values())

        return {
            'agent_name': 'EnhancedDebuggerAgent',
            'success': all_passed,
            'message': f'Enhanced input validation completed. {sum(1 for c in validation_checks.values() if c["passed"])}/{len(validation_checks)} checks passed.',
            'data': {
                'validation_checks': validation_checks,
                'all_checks_passed': all_passed,
                'enhanced': True
            }
        }

    def _check_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for required fields in input data"""
        required = ['url', 'output_path']  # Example required fields
        missing = [field for field in required if field not in data]

        return {
            'passed': len(missing) == 0,
            'missing_fields': missing,
            'present_fields': [field for field in required if field in data]
        }

    def _check_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data types"""
        type_checks = []

        if 'url' in data:
            url_valid = isinstance(data['url'], str) and len(data['url']) > 0
            type_checks.append({
                'field': 'url',
                'expected': 'non-empty string',
                'actual': type(data['url']).__name__,
                'valid': url_valid
            })

        if 'output_path' in data:
            path_valid = isinstance(data['output_path'], str) and len(data['output_path']) > 0
            type_checks.append({
                'field': 'output_path',
                'expected': 'non-empty string',
                'actual': type(data['output_path']).__name__,
                'valid': path_valid
            })

        all_valid = all(check['valid'] for check in type_checks)

        return {
            'passed': all_valid,
            'checks': type_checks
        }

    def _check_value_ranges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check value ranges and constraints"""
        range_checks = []

        # Example: Check URL format
        if 'url' in data:
            url = data['url']
            url_format_valid = url.startswith(('http://', 'https://'))
            range_checks.append({
                'field': 'url',
                'constraint': 'valid URL format',
                'value': url[:50] + '...' if len(url) > 50 else url,
                'valid': url_format_valid
            })

        # Example: Check output path format
        if 'output_path' in data:
            path = data['output_path']
            path_format_valid = not path.startswith('/')  # No absolute paths in /tmp
            range_checks.append({
                'field': 'output_path',
                'constraint': 'safe path format',
                'value': path,
                'valid': path_format_valid
            })

        all_valid = all(check['valid'] for check in range_checks)

        return {
            'passed': all_valid,
            'checks': range_checks
        }

    def _check_security_constraints(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check security constraints"""
        security_checks = []

        # Example: Check for dangerous characters
        if 'output_path' in data:
            path = data['output_path']
            dangerous_chars = ['..', '<', '>', '|', '&', ';', '`']
            has_dangerous = any(char in path for char in dangerous_chars)
            security_checks.append({
                'field': 'output_path',
                'constraint': 'no dangerous characters',
                'violations': [char for char in dangerous_chars if char in path],
                'valid': not has_dangerous
            })

        all_valid = all(check['valid'] for check in security_checks)

        return {
            'passed': all_valid,
            'checks': security_checks
        }

def apply_debugger_timing_fix(coordinator):
    """
    Apply the debugging timing fix to an existing coordinator
    This function can be called to enhance an existing coordinator with timing fixes
    """
    if hasattr(coordinator, 'agents') and 'debugger' in coordinator.agents:
        # Replace the debugger agent with enhanced version
        enhanced_debugger = EnhancedDebuggerAgent(coordinator)

        # Add enhanced methods to existing debugger
        coordinator.agents['debugger'].action_validate_output_with_retry = enhanced_debugger.action_validate_output_with_retry
        coordinator.agents['debugger'].action_validate_input_enhanced = enhanced_debugger.action_validate_input_enhanced

        logging.getLogger('debugger_fix').info("Applied enhanced debugger timing fixes")
        return True

    return False

if __name__ == "__main__":
    print("DEBUGGER Timing Fix Module")
    print("=" * 40)
    print("This module provides enhanced debugging capabilities with:")
    print("- File validation retry logic")
    print("- 50ms timing buffer for filesystem operations")
    print("- Enhanced input validation with detailed diagnostics")
    print("- Security constraint checking")
    print("")
    print("Import this module and call apply_debugger_timing_fix(coordinator)")
    print("to enhance an existing coordinator with these debugging fixes.")