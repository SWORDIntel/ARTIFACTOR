#!/bin/bash

# Portainer Health Check Script
# DOCKER-AGENT: Comprehensive health monitoring for Portainer

set -euo pipefail

# Configuration
PORTAINER_HOST="localhost"
PORTAINER_PORT="9000"
PORTAINER_HTTPS_PORT="9443"
TIMEOUT=10
RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if Portainer is responding on HTTP
check_http() {
    local attempt=1
    while [ $attempt -le $RETRIES ]; do
        if curl -f -s --connect-timeout $TIMEOUT "http://${PORTAINER_HOST}:${PORTAINER_PORT}/api/status" > /dev/null 2>&1; then
            log "${GREEN}✓ HTTP endpoint healthy${NC}"
            return 0
        fi
        log "${YELLOW}⚠ HTTP check attempt $attempt failed${NC}"
        ((attempt++))
        sleep 2
    done
    return 1
}

# Check if Portainer is responding on HTTPS
check_https() {
    local attempt=1
    while [ $attempt -le $RETRIES ]; do
        if curl -f -s -k --connect-timeout $TIMEOUT "https://${PORTAINER_HOST}:${PORTAINER_HTTPS_PORT}/api/status" > /dev/null 2>&1; then
            log "${GREEN}✓ HTTPS endpoint healthy${NC}"
            return 0
        fi
        log "${YELLOW}⚠ HTTPS check attempt $attempt failed${NC}"
        ((attempt++))
        sleep 2
    done
    return 1
}

# Check Docker socket connectivity
check_docker_socket() {
    if [ -S "/var/run/docker.sock" ]; then
        log "${GREEN}✓ Docker socket available${NC}"
        return 0
    else
        log "${RED}✗ Docker socket not available${NC}"
        return 1
    fi
}

# Check data directory
check_data_directory() {
    if [ -d "/data" ] && [ -w "/data" ]; then
        log "${GREEN}✓ Data directory accessible${NC}"
        return 0
    else
        log "${RED}✗ Data directory not accessible${NC}"
        return 1
    fi
}

# Check memory usage
check_memory() {
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

    if [ "$memory_usage" -lt 80 ]; then
        log "${GREEN}✓ Memory usage: ${memory_usage}%${NC}"
        return 0
    elif [ "$memory_usage" -lt 90 ]; then
        log "${YELLOW}⚠ Memory usage: ${memory_usage}%${NC}"
        return 0
    else
        log "${RED}✗ Memory usage critical: ${memory_usage}%${NC}"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local disk_usage
    disk_usage=$(df /data | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$disk_usage" -lt 80 ]; then
        log "${GREEN}✓ Disk usage: ${disk_usage}%${NC}"
        return 0
    elif [ "$disk_usage" -lt 90 ]; then
        log "${YELLOW}⚠ Disk usage: ${disk_usage}%${NC}"
        return 0
    else
        log "${RED}✗ Disk usage critical: ${disk_usage}%${NC}"
        return 1
    fi
}

# Main health check function
main() {
    log "Starting Portainer health check..."

    local checks_passed=0
    local total_checks=6

    # Run all health checks
    check_docker_socket && ((checks_passed++))
    check_data_directory && ((checks_passed++))
    check_memory && ((checks_passed++))
    check_disk_space && ((checks_passed++))
    check_http && ((checks_passed++))
    check_https && ((checks_passed++))

    # Report results
    log "Health check results: ${checks_passed}/${total_checks} checks passed"

    if [ $checks_passed -eq $total_checks ]; then
        log "${GREEN}✓ All health checks passed - Portainer is healthy${NC}"
        exit 0
    elif [ $checks_passed -ge 4 ]; then
        log "${YELLOW}⚠ Some health checks failed but service is functional${NC}"
        exit 0
    else
        log "${RED}✗ Multiple health checks failed - Portainer is unhealthy${NC}"
        exit 1
    fi
}

# Execute main function
main "$@"