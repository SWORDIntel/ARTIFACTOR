#!/bin/bash

# ARTIFACTOR v3.0 - Deployment Verification Script
# Comprehensive validation of enterprise deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
BASE_URL="http://localhost"
BACKEND_PORT=8000
FRONTEND_PORT=3000
ML_PORT=8001
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ARTIFACTOR v3.0 Deployment Verification${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if service is responding
check_service() {
    local name="$1"
    local url="$2"
    local timeout="${3:-10}"

    echo -n "Checking $name... "

    if curl -s -f --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check service health endpoint
check_health() {
    local name="$1"
    local url="$2"

    echo -n "Checking $name health... "

    response=$(curl -s -f "$url" 2>/dev/null || echo "ERROR")

    if [[ "$response" != "ERROR" ]]; then
        status=$(echo "$response" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        if [[ "$status" == "healthy" ]] || [[ "$status" == "ok" ]]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Status: $status${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ No response${NC}"
        return 1
    fi
}

# Function to check Docker containers
check_containers() {
    echo -e "${BLUE}Checking Docker containers...${NC}"

    local compose_file
    case "$ENVIRONMENT" in
        "dev"|"development")
            compose_file="docker-compose.dev.yml"
            ;;
        "prod"|"production")
            compose_file="docker-compose.prod.yml"
            ;;
        "enterprise")
            compose_file="docker-compose.enterprise.yml"
            ;;
        *)
            compose_file="docker-compose.dev.yml"
            ;;
    esac

    if [[ -f "$compose_file" ]]; then
        echo "Using compose file: $compose_file"

        # Check if containers are running
        running_containers=$(docker-compose -f "$compose_file" ps --services --filter "status=running" 2>/dev/null | wc -l)
        total_containers=$(docker-compose -f "$compose_file" ps --services 2>/dev/null | wc -l)

        echo "Running containers: $running_containers/$total_containers"

        if [[ "$running_containers" -gt 0 ]]; then
            echo -e "${GREEN}✓ Containers are running${NC}"

            # Show container status
            echo ""
            echo "Container Status:"
            docker-compose -f "$compose_file" ps
            echo ""
        else
            echo -e "${RED}✗ No containers running${NC}"
            echo "Try running: make dev (for development) or make prod (for production)"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ Compose file $compose_file not found${NC}"
    fi
}

# Function to check core services
check_core_services() {
    echo -e "${BLUE}Checking core services...${NC}"

    local failed=0

    # Frontend
    if ! check_service "Frontend" "$BASE_URL:$FRONTEND_PORT"; then
        ((failed++))
    fi

    # Backend API
    if ! check_service "Backend API" "$BASE_URL:$BACKEND_PORT"; then
        ((failed++))
    fi

    # Backend Health
    if ! check_health "Backend" "$BASE_URL:$BACKEND_PORT/health"; then
        ((failed++))
    fi

    # ML Service
    if ! check_service "ML Service" "$BASE_URL:$ML_PORT"; then
        ((failed++))
    fi

    # ML Service Health
    if ! check_health "ML Service" "$BASE_URL:$ML_PORT/health"; then
        ((failed++))
    fi

    echo ""
    return $failed
}

# Function to check monitoring services
check_monitoring() {
    echo -e "${BLUE}Checking monitoring services...${NC}"

    local failed=0

    # Prometheus
    if ! check_service "Prometheus" "$BASE_URL:$PROMETHEUS_PORT"; then
        ((failed++))
    fi

    # Grafana
    if ! check_service "Grafana" "$BASE_URL:$GRAFANA_PORT"; then
        ((failed++))
    fi

    echo ""
    return $failed
}

# Function to check API endpoints
check_api_endpoints() {
    echo -e "${BLUE}Checking API endpoints...${NC}"

    local failed=0
    local base_api="$BASE_URL:$BACKEND_PORT/api/v1"

    # Root endpoint
    echo -n "Checking API root... "
    if curl -s -f "$BASE_URL:$BACKEND_PORT/" > /dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((failed++))
    fi

    # OpenAPI docs
    echo -n "Checking API docs... "
    if curl -s -f "$base_api/docs" > /dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((failed++))
    fi

    # Health endpoint details
    echo -n "Checking health details... "
    health_response=$(curl -s "$BASE_URL:$BACKEND_PORT/health" 2>/dev/null)
    if [[ -n "$health_response" ]]; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "Health response:"
        echo "$health_response" | jq . 2>/dev/null || echo "$health_response"
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((failed++))
    fi

    echo ""
    return $failed
}

# Function to check database connectivity
check_database() {
    echo -e "${BLUE}Checking database connectivity...${NC}"

    # Try to connect to database through backend API
    echo -n "Checking database via API... "
    health_response=$(curl -s "$BASE_URL:$BACKEND_PORT/health" 2>/dev/null)

    if [[ -n "$health_response" ]]; then
        db_status=$(echo "$health_response" | jq -r '.services.database // "unknown"' 2>/dev/null)
        if [[ "$db_status" == "healthy" ]]; then
            echo -e "${GREEN}✓ Database connected${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Database status: $db_status${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Cannot check database status${NC}"
        return 1
    fi
}

# Function to check redis connectivity
check_redis() {
    echo -e "${BLUE}Checking Redis connectivity...${NC}"

    echo -n "Checking Redis via API... "
    health_response=$(curl -s "$BASE_URL:$BACKEND_PORT/health" 2>/dev/null)

    if [[ -n "$health_response" ]]; then
        redis_status=$(echo "$health_response" | jq -r '.services.redis // "unknown"' 2>/dev/null)
        if [[ "$redis_status" == "healthy" ]]; then
            echo -e "${GREEN}✓ Redis connected${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Redis status: $redis_status${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Cannot check Redis status${NC}"
        return 1
    fi
}

# Function to show service URLs
show_service_urls() {
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "Frontend:        ${GREEN}$BASE_URL:$FRONTEND_PORT${NC}"
    echo -e "Backend API:     ${GREEN}$BASE_URL:$BACKEND_PORT${NC}"
    echo -e "API Docs:        ${GREEN}$BASE_URL:$BACKEND_PORT/api/v1/docs${NC}"
    echo -e "ML Service:      ${GREEN}$BASE_URL:$ML_PORT${NC}"
    echo -e "Prometheus:      ${GREEN}$BASE_URL:$PROMETHEUS_PORT${NC}"
    echo -e "Grafana:         ${GREEN}$BASE_URL:$GRAFANA_PORT${NC}"

    if [[ "$ENVIRONMENT" == "dev" ]] || [[ "$ENVIRONMENT" == "development" ]]; then
        echo -e "PgAdmin:         ${GREEN}$BASE_URL:5050${NC}"
        echo -e "Redis Commander: ${GREEN}$BASE_URL:8081${NC}"
    fi
    echo ""
}

# Function to run performance test
run_performance_test() {
    echo -e "${BLUE}Running basic performance test...${NC}"

    echo -n "Testing API response time... "
    start_time=$(date +%s%3N)
    if curl -s -f "$BASE_URL:$BACKEND_PORT/health" > /dev/null; then
        end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))

        if [[ $response_time -lt 1000 ]]; then
            echo -e "${GREEN}✓ ${response_time}ms${NC}"
        elif [[ $response_time -lt 2000 ]]; then
            echo -e "${YELLOW}⚠ ${response_time}ms (acceptable)${NC}"
        else
            echo -e "${RED}✗ ${response_time}ms (slow)${NC}"
        fi
    else
        echo -e "${RED}✗ No response${NC}"
    fi

    echo ""
}

# Function to show recommendations
show_recommendations() {
    echo -e "${BLUE}Recommendations:${NC}"

    case "$ENVIRONMENT" in
        "dev"|"development")
            echo "• Development environment detected"
            echo "• Use 'make dev-logs' to view logs"
            echo "• Use 'make shell-backend' or 'make shell-frontend' for debugging"
            echo "• Access development tools like PgAdmin and Redis Commander"
            ;;
        "prod"|"production")
            echo "• Production environment detected"
            echo "• Monitor using Grafana dashboards"
            echo "• Check 'make prod-logs' for any issues"
            echo "• Ensure SSL certificates are configured for HTTPS"
            ;;
        "enterprise")
            echo "• Enterprise deployment detected"
            echo "• Monitor auto-scaling behavior"
            echo "• Review backup and disaster recovery procedures"
            echo "• Configure alerting for critical services"
            ;;
    esac

    echo "• Run 'make health' for detailed health checks"
    echo "• Run 'make test' to execute the full test suite"
    echo ""
}

# Main execution
main() {
    local total_failed=0

    # Check Docker containers
    check_containers

    # Wait a moment for services to be ready
    echo "Waiting for services to be ready..."
    sleep 5

    # Check core services
    if ! check_core_services; then
        ((total_failed++))
    fi

    # Check database and Redis
    if ! check_database; then
        ((total_failed++))
    fi

    if ! check_redis; then
        ((total_failed++))
    fi

    # Check monitoring (optional for dev)
    if [[ "$ENVIRONMENT" == "prod" ]] || [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "enterprise" ]]; then
        if ! check_monitoring; then
            echo -e "${YELLOW}⚠ Some monitoring services are not available${NC}"
        fi
    fi

    # Check API endpoints
    if ! check_api_endpoints; then
        ((total_failed++))
    fi

    # Run performance test
    run_performance_test

    # Show results
    echo -e "${BLUE}========================================${NC}"
    if [[ $total_failed -eq 0 ]]; then
        echo -e "${GREEN}✓ ARTIFACTOR v3.0 is running successfully!${NC}"
    else
        echo -e "${YELLOW}⚠ ARTIFACTOR v3.0 is running with some issues${NC}"
        echo -e "${YELLOW}  Failed checks: $total_failed${NC}"
    fi
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Show service URLs
    show_service_urls

    # Show recommendations
    show_recommendations

    # Exit with error code if there were failures
    if [[ $total_failed -gt 0 ]]; then
        exit 1
    fi
}

# Check if required tools are available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠ jq is not installed - some checks will be limited${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is required but not installed${NC}"
    exit 1
fi

# Run main function
main

echo -e "${GREEN}Deployment verification completed!${NC}"