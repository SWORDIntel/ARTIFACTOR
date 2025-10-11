#!/bin/bash
# ARTIFACTOR Backend Services Validation Script
# Purpose: Verify backend services are running correctly
# Usage: ./docker/validate-backend-services.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Print functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ARTIFACTOR v3.0 - Backend Services Validation           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    ((TOTAL_TESTS++))
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

print_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Test Summary                                              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "Total Tests:  ${TOTAL_TESTS}"
    echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests failed. Check logs above.${NC}"
        return 1
    fi
}

# Test functions
test_docker_compose_file() {
    print_test "Docker Compose file exists and is valid"

    if [ ! -f "$SCRIPT_DIR/backend-compose.yml" ]; then
        print_failure "backend-compose.yml not found"
        return
    fi

    if docker-compose -f "$SCRIPT_DIR/backend-compose.yml" config --quiet 2>/dev/null; then
        print_success "Docker Compose configuration is valid"
    else
        print_failure "Docker Compose configuration is invalid"
    fi
}

test_env_file() {
    print_test "Environment file (.env) exists"

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_failure ".env file not found in $PROJECT_ROOT"
        print_info "Create .env file with required variables (see BACKEND_SETUP.md)"
        return
    fi

    print_success ".env file exists"

    # Check required variables
    print_test "Required environment variables are set"
    local required_vars=("POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD" "SECRET_KEY")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$PROJECT_ROOT/.env" 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required variables present in .env"
    else
        print_failure "Missing variables: ${missing_vars[*]}"
    fi
}

test_docker_running() {
    print_test "Docker daemon is running"

    if docker info >/dev/null 2>&1; then
        print_success "Docker is running"
    else
        print_failure "Docker is not running"
        print_info "Start Docker: sudo systemctl start docker"
        return
    fi
}

test_container_status() {
    local container_name=$1
    local expected_status=$2

    print_test "Container $container_name is $expected_status"

    local status=$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null || echo "not_found")

    if [ "$status" == "$expected_status" ]; then
        print_success "Container $container_name is $expected_status"
    else
        print_failure "Container $container_name status: $status (expected: $expected_status)"
    fi
}

test_container_health() {
    local container_name=$1

    print_test "Container $container_name health check"

    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_failure "Container $container_name is not running"
        return
    fi

    local health=$(docker inspect -f '{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no_healthcheck")

    case "$health" in
        "healthy")
            print_success "Container $container_name is healthy"
            ;;
        "unhealthy")
            print_failure "Container $container_name is unhealthy"
            ;;
        "starting")
            print_info "Container $container_name is still starting up"
            ((PASSED_TESTS++))
            ;;
        "no_healthcheck")
            print_info "Container $container_name has no health check configured"
            ((PASSED_TESTS++))
            ;;
        *)
            print_failure "Container $container_name health: $health"
            ;;
    esac
}

test_postgres_connection() {
    print_test "PostgreSQL database connection"

    if ! docker ps --format '{{.Names}}' | grep -q "^artifactor_backend_postgres$"; then
        print_failure "PostgreSQL container not running"
        return
    fi

    if docker exec artifactor_backend_postgres pg_isready -U artifactor >/dev/null 2>&1; then
        print_success "PostgreSQL accepting connections"
    else
        print_failure "PostgreSQL not accepting connections"
    fi
}

test_redis_connection() {
    print_test "Redis cache connection"

    if ! docker ps --format '{{.Names}}' | grep -q "^artifactor_backend_redis$"; then
        print_failure "Redis container not running"
        return
    fi

    local response=$(docker exec artifactor_backend_redis redis-cli ping 2>/dev/null || echo "FAILED")

    if [ "$response" == "PONG" ]; then
        print_success "Redis responding to PING"
    else
        print_failure "Redis not responding"
    fi
}

test_backend_api_health() {
    print_test "Backend API health endpoint"

    if ! docker ps --format '{{.Names}}' | grep -q "^artifactor_backend_api$"; then
        print_failure "Backend API container not running"
        return
    fi

    # Wait up to 30 seconds for API to be ready
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
            print_success "Backend API health check passed"
            return
        fi
        ((attempt++))
        sleep 1
    done

    print_failure "Backend API not responding after ${max_attempts}s"
}

test_backend_api_docs() {
    print_test "Backend API documentation endpoints"

    if curl -sf http://localhost:8000/docs >/dev/null 2>&1; then
        print_success "Swagger UI accessible at http://localhost:8000/docs"
    else
        print_failure "Swagger UI not accessible"
    fi
}

test_network_connectivity() {
    print_test "Container network connectivity"

    if ! docker ps --format '{{.Names}}' | grep -q "^artifactor_backend_api$"; then
        print_failure "Backend API container not running"
        return
    fi

    # Test backend can reach postgres
    if docker exec artifactor_backend_api ping -c 1 postgres >/dev/null 2>&1; then
        print_success "Backend can reach PostgreSQL"
    else
        print_failure "Backend cannot reach PostgreSQL"
    fi

    # Test backend can reach redis
    if docker exec artifactor_backend_api ping -c 1 redis >/dev/null 2>&1; then
        print_success "Backend can reach Redis"
    else
        print_failure "Backend cannot reach Redis"
    fi
}

test_volume_mounts() {
    print_test "Docker volumes exist"

    local volumes=("artifactor_backend_postgres_data" "artifactor_backend_redis_data" "artifactor_backend_upload_data")
    local all_exist=true

    for vol in "${volumes[@]}"; do
        if docker volume inspect "$vol" >/dev/null 2>&1; then
            print_info "Volume $vol exists"
        else
            print_failure "Volume $vol does not exist"
            all_exist=false
        fi
    done

    if [ "$all_exist" == true ]; then
        print_success "All required volumes exist"
    fi
}

test_port_accessibility() {
    print_test "Service ports are accessible"

    local ports=(8000 5432 6379)
    local port_names=("Backend API" "PostgreSQL" "Redis")

    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${port_names[$i]}

        if nc -z localhost "$port" 2>/dev/null; then
            print_success "$name accessible on port $port"
        else
            print_failure "$name not accessible on port $port"
        fi
    done
}

test_cors_configuration() {
    print_test "CORS configuration for Chrome extension"

    if ! docker ps --format '{{.Names}}' | grep -q "^artifactor_backend_api$"; then
        print_failure "Backend API container not running"
        return
    fi

    # Check if ALLOWED_ORIGINS includes chrome-extension
    if docker exec artifactor_backend_api env | grep -q "chrome-extension"; then
        print_success "Chrome extension CORS configured"
    else
        print_failure "Chrome extension CORS not configured"
    fi
}

# Main execution
main() {
    print_header

    print_info "Starting backend services validation..."
    echo ""

    # Pre-flight checks
    test_docker_compose_file
    test_env_file
    test_docker_running
    echo ""

    # Check if services are running
    print_info "Checking service status..."
    test_container_status "artifactor_backend_postgres" "running"
    test_container_status "artifactor_backend_redis" "running"
    test_container_status "artifactor_backend_api" "running"
    echo ""

    # Health checks
    print_info "Running health checks..."
    test_container_health "artifactor_backend_postgres"
    test_container_health "artifactor_backend_redis"
    test_container_health "artifactor_backend_api"
    echo ""

    # Service connectivity
    print_info "Testing service connectivity..."
    test_postgres_connection
    test_redis_connection
    test_backend_api_health
    test_backend_api_docs
    echo ""

    # Network and infrastructure
    print_info "Validating infrastructure..."
    test_network_connectivity
    test_volume_mounts
    test_port_accessibility
    test_cors_configuration
    echo ""

    # Print summary
    print_summary
}

# Run main function
main
exit $?
