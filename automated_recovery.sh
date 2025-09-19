#!/bin/bash

# Automated Recovery Script for Etherscan API Deployment
# Comprehensive failure detection and automatic recovery procedures

set -euo pipefail

# Configuration
LOG_FILE="/var/log/etherscan_recovery.log"
COMPOSE_FILE="docker-compose.yml"
MAX_RETRIES=3
HEALTH_CHECK_TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "${YELLOW}$@${NC}"; }
error() { log "ERROR" "${RED}$@${NC}"; }
success() { log "SUCCESS" "${GREEN}$@${NC}"; }

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running"
        return 1
    fi
    return 0
}

# Check container health
check_container_health() {
    local container_name=$1
    local status

    if ! docker ps --filter "name=$container_name" --format "{{.Status}}" | grep -q "Up"; then
        warn "Container $container_name is not running"
        return 1
    fi

    # Check health status if available
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")

    case "$status" in
        "healthy")
            return 0
            ;;
        "unhealthy")
            warn "Container $container_name is unhealthy"
            return 1
            ;;
        *)
            info "Container $container_name health status: $status"
            return 0
            ;;
    esac
}

# Restart container with retry logic
restart_container() {
    local container_name=$1
    local retry=0

    while [ $retry -lt $MAX_RETRIES ]; do
        info "Restarting container: $container_name (attempt $((retry + 1))/$MAX_RETRIES)"

        if docker restart "$container_name"; then
            sleep 10
            if check_container_health "$container_name"; then
                success "Container $container_name restarted successfully"
                return 0
            fi
        fi

        retry=$((retry + 1))
        sleep 5
    done

    error "Failed to restart container: $container_name after $MAX_RETRIES attempts"
    return 1
}

# Check API endpoint health
check_api_health() {
    local url=${1:-"http://localhost:8080/health"}
    local timeout=${2:-$HEALTH_CHECK_TIMEOUT}

    if curl -sf --max-time "$timeout" "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    if docker exec etherscan-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        return 0
    else
        return 1
    fi
}

# Clear Redis cache
clear_redis_cache() {
    info "Clearing Redis cache"
    if docker exec etherscan-redis redis-cli FLUSHALL; then
        success "Redis cache cleared"
        return 0
    else
        error "Failed to clear Redis cache"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local threshold=${1:-85}
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$usage" -gt "$threshold" ]; then
        warn "Disk usage is at ${usage}% (threshold: ${threshold}%)"
        return 1
    else
        info "Disk usage: ${usage}%"
        return 0
    fi
}

# Clean Docker resources
clean_docker() {
    info "Cleaning Docker resources"

    # Remove unused containers
    docker container prune -f

    # Remove unused images
    docker image prune -f

    # Remove unused volumes (be careful with this)
    # docker volume prune -f

    # Remove unused networks
    docker network prune -f

    success "Docker cleanup completed"
}

# Check system resources
check_system_resources() {
    # Check memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 85 ]; then
        warn "High memory usage: ${memory_usage}%"
    else
        info "Memory usage: ${memory_usage}%"
    fi

    # Check CPU load
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_percent=$(echo "$load_avg * 100 / $cpu_cores" | bc -l | awk '{printf "%.0f", $1}')

    if [ "$load_percent" -gt 80 ]; then
        warn "High CPU load: ${load_percent}%"
    else
        info "CPU load: ${load_percent}%"
    fi
}

# Comprehensive health check
comprehensive_health_check() {
    info "Starting comprehensive health check"
    local issues=0

    # Check Docker
    if ! check_docker; then
        error "Docker is not available"
        ((issues++))
    fi

    # Check containers
    local containers=("etherscan-api" "etherscan-redis" "etherscan-nginx" "etherscan-prometheus")
    for container in "${containers[@]}"; do
        if ! check_container_health "$container"; then
            ((issues++))
        fi
    done

    # Check API health
    if ! check_api_health; then
        warn "API health check failed"
        ((issues++))
    fi

    # Check Redis
    if ! check_redis; then
        warn "Redis connectivity check failed"
        ((issues++))
    fi

    # Check disk space
    if ! check_disk_space; then
        ((issues++))
    fi

    # Check system resources
    check_system_resources

    if [ $issues -eq 0 ]; then
        success "All health checks passed"
        return 0
    else
        warn "Found $issues issues during health check"
        return 1
    fi
}

# Automated recovery procedure
automated_recovery() {
    info "Starting automated recovery procedure"

    # Step 1: Check basic connectivity
    if ! check_docker; then
        error "Docker is not running. Please start Docker service manually."
        exit 1
    fi

    # Step 2: Check and restart unhealthy containers
    local containers=("etherscan-api" "etherscan-redis" "etherscan-nginx" "etherscan-prometheus")
    for container in "${containers[@]}"; do
        if ! check_container_health "$container"; then
            if ! restart_container "$container"; then
                error "Critical failure: Cannot restart $container"
                # Try to restart the entire stack
                info "Attempting to restart entire Docker stack"
                docker-compose down
                sleep 5
                docker-compose up -d
                break
            fi
        fi
    done

    # Step 3: Check API after container recovery
    sleep 15  # Give services time to start
    if ! check_api_health; then
        warn "API still unhealthy after container restart"

        # Try clearing cache
        if check_redis; then
            clear_redis_cache
            sleep 5
        fi

        # Check again
        if ! check_api_health; then
            error "API recovery failed. Manual intervention required."
            return 1
        fi
    fi

    # Step 4: Clean up if disk space is low
    if ! check_disk_space 80; then
        clean_docker
    fi

    success "Automated recovery completed successfully"
    return 0
}

# Monitor mode - continuous health monitoring
monitor_mode() {
    local interval=${1:-300}  # Default 5 minutes

    info "Starting monitor mode (checking every ${interval} seconds)"

    while true; do
        if ! comprehensive_health_check; then
            warn "Issues detected, starting automated recovery"
            if automated_recovery; then
                success "Automated recovery successful"
            else
                error "Automated recovery failed - alerting required"
                # Here you could send alerts (email, Slack, etc.)
            fi
        fi

        sleep "$interval"
    done
}

# Generate system status report
status_report() {
    info "Generating system status report"

    echo "==============================================="
    echo "ETHERSCAN API SYSTEM STATUS REPORT"
    echo "Generated: $(date)"
    echo "==============================================="

    echo -e "\n🐳 DOCKER CONTAINERS:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo -e "\n💾 DISK USAGE:"
    df -h /

    echo -e "\n💻 MEMORY USAGE:"
    free -h

    echo -e "\n⚡ CPU LOAD:"
    uptime

    echo -e "\n🌐 NETWORK CONNECTIVITY:"
    if check_api_health; then
        echo "✅ API Health: OK"
    else
        echo "❌ API Health: FAILED"
    fi

    if check_redis; then
        echo "✅ Redis: OK"
    else
        echo "❌ Redis: FAILED"
    fi

    echo -e "\n📊 DOCKER STATS (5 second sample):"
    timeout 5s docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "Docker stats unavailable"

    echo "==============================================="
}

# Main function
main() {
    case "${1:-help}" in
        "check")
            comprehensive_health_check
            ;;
        "recover")
            automated_recovery
            ;;
        "monitor")
            monitor_mode "${2:-300}"
            ;;
        "status")
            status_report
            ;;
        "clean")
            clean_docker
            ;;
        "restart")
            info "Restarting entire Docker stack"
            docker-compose down
            docker-compose up -d
            sleep 15
            comprehensive_health_check
            ;;
        "help"|*)
            echo "Etherscan API Automated Recovery Script"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  check     - Run comprehensive health check"
            echo "  recover   - Run automated recovery procedure"
            echo "  monitor   - Start continuous monitoring (optional: interval in seconds)"
            echo "  status    - Generate detailed status report"
            echo "  clean     - Clean unused Docker resources"
            echo "  restart   - Restart entire Docker stack"
            echo "  help      - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 check                 # Run health check"
            echo "  $0 recover               # Run recovery"
            echo "  $0 monitor 600           # Monitor every 10 minutes"
            echo "  $0 status                # Show status report"
            ;;
    esac
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Run main function with all arguments
main "$@"