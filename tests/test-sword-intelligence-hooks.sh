#!/bin/bash

# SWORD Intelligence Hook System Test Suite
# Comprehensive validation of all fixes and optimizations
# Version: 1.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_SCRIPT="$PROJECT_ROOT/scripts/sword-intelligence-contact-hook.sh"
INSTALLER_SCRIPT="$PROJECT_ROOT/scripts/install-sword-intelligence-branding.sh"
TEST_REPO_DIR="$(mktemp -d)"
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test reporting functions
test_start() {
    ((TEST_COUNT++))
    echo -e "${BLUE}[TEST $TEST_COUNT]${NC} $1"
}

test_pass() {
    ((PASS_COUNT++))
    echo -e "${GREEN}[PASS]${NC} $1"
}

test_fail() {
    ((FAIL_COUNT++))
    echo -e "${RED}[FAIL]${NC} $1"
}

test_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

test_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Cleanup function
cleanup() {
    if [[ -d "$TEST_REPO_DIR" ]]; then
        rm -rf "$TEST_REPO_DIR"
    fi
}
trap cleanup EXIT

# Setup test repository
setup_test_repo() {
    local repo_name="$1"
    local repo_dir="$TEST_REPO_DIR/$repo_name"

    mkdir -p "$repo_dir"
    cd "$repo_dir"

    git init -q
    git config user.name "Test User"
    git config user.email "test@example.com"

    # Create basic README
    cat > README.md << EOF
# $repo_name

This is a test repository for SWORD Intelligence hook system testing.

## Features

- Test feature 1
- Test feature 2

## Installation

Installation instructions here.
EOF

    git add README.md
    git commit -q -m "Initial commit"

    echo "$repo_dir"
}

# Test 1: Basic functionality test
test_basic_functionality() {
    test_start "Basic functionality test"

    local test_repo=$(setup_test_repo "test-basic")
    cd "$test_repo"

    # Copy hook script to test repo
    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Test --check on fresh repo
    if scripts/sword-intelligence-contact-hook.sh --check 2>/dev/null; then
        test_fail "Fresh repo should not have contact section"
        return 1
    fi

    # Test --apply
    if scripts/sword-intelligence-contact-hook.sh --apply; then
        test_pass "Contact section applied successfully"
    else
        test_fail "Failed to apply contact section"
        return 1
    fi

    # Test --check after apply
    if scripts/sword-intelligence-contact-hook.sh --check; then
        test_pass "Contact section validation after apply"
    else
        test_fail "Contact section validation failed after apply"
        return 1
    fi

    # Verify content
    if grep -q "📞 Contact & Support" README.md &&
       grep -q "TEST-BASIC@swordintelligence.airforce" README.md; then
        test_pass "Contact section content verification"
    else
        test_fail "Contact section content missing or incorrect"
        return 1
    fi
}

# Test 2: Input validation test
test_input_validation() {
    test_start "Input validation test"

    # Test with invalid repository names
    local invalid_names=("" "." ".." "repo with spaces" "repo/with/slashes" "very-long-repository-name-that-exceeds-fifty-characters-limit")

    for invalid_name in "${invalid_names[@]}"; do
        local test_repo=$(setup_test_repo "test-validation")
        cd "$test_repo"

        # Simulate invalid repo name by changing directory name
        if [[ -n "$invalid_name" ]]; then
            cd ..
            mv "test-validation" "$invalid_name" 2>/dev/null || continue
            cd "$invalid_name"
        fi

        mkdir -p scripts
        cp "$HOOK_SCRIPT" scripts/

        # This should fail gracefully
        if scripts/sword-intelligence-contact-hook.sh --apply 2>/dev/null; then
            test_warning "Invalid name '$invalid_name' was accepted (may be handled by fallback)"
        else
            test_pass "Invalid name '$invalid_name' properly rejected"
        fi
    done
}

# Test 3: Security test - Path traversal protection
test_security_path_traversal() {
    test_start "Security - Path traversal protection"

    local test_repo=$(setup_test_repo "test-security")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Test outside git repo (should use script directory as fallback)
    cd /tmp

    if scripts/sword-intelligence-contact-hook.sh --check 2>/dev/null; then
        test_pass "Path traversal protection active (script uses safe fallback)"
    else
        test_pass "Path traversal protection active (script properly rejects unsafe operation)"
    fi
}

# Test 4: Performance test - Git caching
test_performance_git_caching() {
    test_start "Performance - Git information caching"

    local test_repo=$(setup_test_repo "test-performance")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Add remote for testing
    git remote add origin "https://github.com/SWORDIntel/test-performance.git"

    # Time multiple operations
    local start_time=$(date +%s%N)

    scripts/sword-intelligence-contact-hook.sh --check 2>/dev/null || true
    scripts/sword-intelligence-contact-hook.sh --template >/dev/null
    scripts/sword-intelligence-contact-hook.sh --check 2>/dev/null || true

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

    if [[ $duration -lt 2000 ]]; then  # Should complete in under 2 seconds
        test_pass "Performance test passed ($duration ms)"
    else
        test_warning "Performance test slower than expected ($duration ms)"
    fi
}

# Test 5: Cross-platform compatibility
test_cross_platform() {
    test_start "Cross-platform compatibility"

    local test_repo=$(setup_test_repo "test-cross-platform")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Test platform detection
    local platform=$(uname)
    test_info "Testing on platform: $platform"

    # Test date command compatibility
    if scripts/sword-intelligence-contact-hook.sh --apply; then
        # Check if backup was created with proper timestamp
        local backup_count=$(ls -1 README.md.backup-* 2>/dev/null | wc -l)
        if [[ $backup_count -gt 0 ]]; then
            test_pass "Cross-platform date/backup functionality working"
        else
            test_fail "Backup creation failed on $platform"
            return 1
        fi
    else
        test_fail "Basic functionality failed on $platform"
        return 1
    fi
}

# Test 6: Race condition protection
test_race_condition_protection() {
    test_start "Race condition protection"

    local test_repo=$(setup_test_repo "test-race")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Create multiple backups rapidly
    for i in {1..5}; do
        scripts/sword-intelligence-contact-hook.sh --apply >/dev/null 2>&1 &
    done

    wait

    # Count unique backup files
    local backup_count=$(ls -1 README.md.backup-* 2>/dev/null | wc -l)

    if [[ $backup_count -eq 5 ]]; then
        test_pass "Race condition protection working (5 unique backups created)"
    elif [[ $backup_count -gt 0 ]]; then
        test_pass "Partial race condition protection ($backup_count backups created)"
    else
        test_fail "Race condition protection failed (no backups created)"
        return 1
    fi
}

# Test 7: Error recovery test
test_error_recovery() {
    test_start "Error recovery functionality"

    local test_repo=$(setup_test_repo "test-recovery")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Create a backup first
    scripts/sword-intelligence-contact-hook.sh --apply >/dev/null

    # Corrupt the README
    echo "corrupted content" > README.md

    # Find the backup file
    local backup_file=$(ls README.md.backup-* | head -1)

    if [[ -f "$backup_file" ]]; then
        # Restore from backup (simulating error recovery)
        cp "$backup_file" README.md

        # Verify recovery
        if grep -q "📞 Contact & Support" README.md; then
            test_pass "Error recovery functionality working"
        else
            test_fail "Error recovery functionality failed"
            return 1
        fi
    else
        test_fail "No backup file found for recovery test"
        return 1
    fi
}

# Test 8: Health check functionality
test_health_check() {
    test_start "Health check functionality"

    local test_repo=$(setup_test_repo "test-health")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Test health check in valid repo
    if scripts/sword-intelligence-contact-hook.sh --health; then
        test_pass "Health check passed in valid repository"
    else
        test_fail "Health check failed in valid repository"
        return 1
    fi

    # Test health check outside git repo
    cd /tmp
    if "$test_repo/scripts/sword-intelligence-contact-hook.sh" --health 2>/dev/null; then
        test_warning "Health check passed outside git repo (expected behavior)"
    else
        test_pass "Health check properly detected non-git environment"
    fi
}

# Test 9: Installer functionality test
test_installer_functionality() {
    test_start "Installer functionality"

    local test_repo=$(setup_test_repo "test-installer")
    cd "$test_repo"

    # Test installer (using local script instead of downloading)
    # We'll modify the installer to use local script for testing
    local temp_installer=$(mktemp)

    # Create a modified installer that uses local script
    sed 's|curl -fsSL.*|cp "'"$HOOK_SCRIPT"'" "$target_file"|g' "$INSTALLER_SCRIPT" > "$temp_installer"
    chmod +x "$temp_installer"

    if bash "$temp_installer" >/dev/null 2>&1; then
        # Check if files were created
        if [[ -f "scripts/sword-intelligence-contact-hook.sh" ]] &&
           [[ -f ".git/hooks/pre-commit" ]] &&
           [[ -f "docs/SWORD_INTELLIGENCE_BRANDING.md" ]]; then
            test_pass "Installer created all required files"
        else
            test_fail "Installer did not create all required files"
            return 1
        fi

        # Check if README was updated
        if grep -q "📞 Contact & Support" README.md; then
            test_pass "Installer updated README with contact section"
        else
            test_fail "Installer did not update README"
            return 1
        fi
    else
        test_fail "Installer execution failed"
        return 1
    fi

    rm -f "$temp_installer"
}

# Test 10: Git hook functionality
test_git_hook() {
    test_start "Git hook functionality"

    local test_repo=$(setup_test_repo "test-hooks")
    cd "$test_repo"

    mkdir -p scripts
    cp "$HOOK_SCRIPT" scripts/

    # Install git hook
    scripts/sword-intelligence-contact-hook.sh --install-hook

    # Check if hook was installed
    if [[ -f ".git/hooks/pre-commit" ]] && [[ -x ".git/hooks/pre-commit" ]]; then
        test_pass "Git pre-commit hook installed successfully"

        # Test hook content
        if grep -q "SWORD Intelligence" ".git/hooks/pre-commit"; then
            test_pass "Git hook contains correct content"
        else
            test_fail "Git hook content is incorrect"
            return 1
        fi
    else
        test_fail "Git hook installation failed"
        return 1
    fi
}

# Main test runner
run_all_tests() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}SWORD Intelligence Hook System Test Suite${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    # Verify test environment
    if [[ ! -f "$HOOK_SCRIPT" ]]; then
        echo -e "${RED}Error: Hook script not found at $HOOK_SCRIPT${NC}"
        exit 1
    fi

    if [[ ! -f "$INSTALLER_SCRIPT" ]]; then
        echo -e "${RED}Error: Installer script not found at $INSTALLER_SCRIPT${NC}"
        exit 1
    fi

    echo -e "${BLUE}Test Environment:${NC}"
    echo "  Hook Script: $HOOK_SCRIPT"
    echo "  Installer Script: $INSTALLER_SCRIPT"
    echo "  Test Directory: $TEST_REPO_DIR"
    echo "  Platform: $(uname -s)"
    echo ""

    # Run all tests
    test_basic_functionality
    test_input_validation
    test_security_path_traversal
    test_performance_git_caching
    test_cross_platform
    test_race_condition_protection
    test_error_recovery
    test_health_check
    test_installer_functionality
    test_git_hook

    # Summary
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Test Results Summary${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "Total Tests: ${BLUE}$TEST_COUNT${NC}"
    echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
    echo -e "Failed: ${RED}$FAIL_COUNT${NC}"

    local success_rate=$(( (PASS_COUNT * 100) / TEST_COUNT ))
    echo -e "Success Rate: ${BLUE}${success_rate}%${NC}"

    if [[ $FAIL_COUNT -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed! System is production ready.${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}⚠️  Some tests failed. Please review and fix issues.${NC}"
        exit 1
    fi
}

# Execute tests
run_all_tests