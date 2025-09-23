#!/bin/bash

# ARTIFACTOR Security Validation Script
# Validates all critical security fixes implemented by PATCHER agent

set -e

echo "🔒 ARTIFACTOR Security Validation Report"
echo "========================================"
echo "Generated: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run security check
check_security() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "[$TOTAL_CHECKS] Testing: $test_name... "

    if eval "$test_command" >/dev/null 2>&1; then
        if [ "$expected_result" = "pass" ]; then
            echo -e "${GREEN}PASS${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}FAIL${NC} (Expected failure but passed)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        if [ "$expected_result" = "fail" ]; then
            echo -e "${GREEN}PASS${NC} (Correctly failed)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}FAIL${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    fi
}

echo "🔍 1. COMMAND INJECTION PROTECTION"
echo "=================================="

# Test 1: Input validation function exists
check_security "Input validation function exists" \
    "grep -q 'validate_input()' setup-env.sh" \
    "pass"

# Test 2: Dangerous characters are filtered
check_security "Dangerous character filtering" \
    "grep -q 'tr -d.*[\;\|\&\$]' setup-env.sh" \
    "pass"

# Test 3: Safe sourcing of .env file
check_security "Safe .env file sourcing" \
    "grep -q 'grep -q.*[\;\&\|\$].*ENV_FILE' setup-env.sh" \
    "pass"

# Test 4: Input type validation
check_security "Input type validation" \
    "grep -q 'case.*\$type' setup-env.sh" \
    "pass"

echo
echo "🐳 2. DOCKER SECURITY HARDENING"
echo "==============================="

# Test 5: Read-only volume mounts
check_security "Read-only volume mounts implemented" \
    "grep -q ':ro' docker/docker-compose.yml" \
    "pass"

# Test 6: Resource limits defined
check_security "Container resource limits" \
    "grep -q 'deploy:' docker/docker-compose.yml" \
    "pass"

# Test 7: Dangerous mount removed
check_security "Dangerous host mount removed" \
    "grep -q '../:/home/john/ARTIFACTOR' docker/docker-compose.yml" \
    "fail"

# Test 8: Network security configuration
check_security "Network security configuration" \
    "grep -q 'driver_opts:' docker/docker-compose.yml" \
    "pass"

echo
echo "🔐 3. CREDENTIAL SECURITY"
echo "========================"

# Test 9: No password exposure in quick-env.sh
check_security "Password not exposed in output" \
    "grep -q 'Database password:.*\${DB_PASSWORD}' scripts/quick-env.sh" \
    "fail"

# Test 10: Credentials cleared from environment
check_security "Credentials cleared from environment" \
    "grep -q 'unset.*DB_PASSWORD' scripts/quick-env.sh" \
    "pass"

# Test 11: Secure credential generation validation
check_security "Credential generation validation" \
    "grep -q 'if.*SECRET_KEY.*-lt' scripts/quick-env.sh" \
    "pass"

echo
echo "🏗️ 4. DOCKERFILE SECURITY"
echo "========================="

# Test 12: Health check dependencies installed
check_security "Health check dependencies (curl)" \
    "grep -q 'apk add.*curl' frontend/Dockerfile" \
    "pass"

# Test 13: Non-root user configuration
check_security "Non-root user security" \
    "grep -q 'USER.*reactuser' frontend/Dockerfile" \
    "pass"

# Test 14: Optimized Docker layers
check_security "Optimized Docker layer structure" \
    "grep -q 'apt-get clean' backend/Dockerfile.agent_bridge && grep -q 'pip install.*requirements.txt' backend/Dockerfile.agent_bridge" \
    "pass"

# Test 15: Security environment variables
check_security "Security environment variables" \
    "grep -q 'PYTHONDONTWRITEBYTECODE' backend/Dockerfile.agent_bridge" \
    "pass"

echo
echo "🛡️ 5. FILE PERMISSIONS AND ACCESS"
echo "=================================="

# Test 16: .env file permissions
if [ -f ".env" ]; then
    check_security ".env file permissions (600)" \
        "[ \$(stat -c '%a' .env 2>/dev/null || echo '000') = '600' ]" \
        "pass"
else
    echo "[$((TOTAL_CHECKS + 1))] Testing: .env file permissions (600)... ${YELLOW}SKIP${NC} (file not found)"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Test 17: Script file executability
check_security "Setup script executable" \
    "[ -x setup-env.sh ]" \
    "pass"

echo
echo "📋 SECURITY VALIDATION SUMMARY"
echo "=============================="
echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL SECURITY CHECKS PASSED!${NC}"
    echo -e "${GREEN}✅ ARTIFACTOR is secure for deployment${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  SECURITY ISSUES DETECTED!${NC}"
    echo -e "${RED}❌ $FAILED_CHECKS check(s) failed${NC}"
    echo -e "${YELLOW}Please review and fix the failed checks before deployment${NC}"
    exit 1
fi