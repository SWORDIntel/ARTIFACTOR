#!/bin/bash
# ARTIFACTOR Backend Services Management Script
# Purpose: Simplified management interface for backend services
# Usage: ./docker/backend-services.sh [start|stop|restart|status|logs|validate|backup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/backend-compose.yml"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ARTIFACTOR v3.0 - Backend Services Manager              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found in $PROJECT_ROOT"
        print_info "Creating .env from template..."

        cat > "$PROJECT_ROOT/.env" <<EOF
# ARTIFACTOR Backend Configuration
# Generated: $(date)

# Database Configuration
POSTGRES_DB=artifactor_v3
POSTGRES_USER=artifactor
POSTGRES_PASSWORD=$(openssl rand -base64 24)

# Security Configuration
SECRET_KEY=$(openssl rand -hex 32)

# Optional Configuration
DEBUG=false
ML_CLASSIFICATION_ENABLED=true
SEMANTIC_SEARCH_ENABLED=true
COLLABORATION_ENABLED=true
PLUGIN_SYSTEM_ENABLED=true
METRICS_ENABLED=true
AUDIT_LOGGING_ENABLED=true
EOF
        print_success "Created .env file with secure random credentials"
        print_info "Review and customize $PROJECT_ROOT/.env as needed"
    fi
}

# Command functions
cmd_start() {
    print_header
    print_info "Starting ARTIFACTOR backend services..."
    echo ""

    docker-compose -f "$COMPOSE_FILE" up -d

    echo ""
    print_success "Backend services started"
    print_info "Waiting for services to become healthy..."
    sleep 5

    echo ""
    cmd_status
}

cmd_stop() {
    print_header
    print_info "Stopping ARTIFACTOR backend services..."
    echo ""

    docker-compose -f "$COMPOSE_FILE" down

    echo ""
    print_success "Backend services stopped"
}

cmd_restart() {
    print_header
    print_info "Restarting ARTIFACTOR backend services..."
    echo ""

    docker-compose -f "$COMPOSE_FILE" restart

    echo ""
    print_success "Backend services restarted"
    sleep 5
    cmd_status
}

cmd_status() {
    print_header
    print_info "Backend services status:"
    echo ""

    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    print_info "Service health:"

    # PostgreSQL
    if docker ps --format '{{.Names}}' | grep -q "artifactor_backend_postgres"; then
        if docker exec artifactor_backend_postgres pg_isready -U artifactor >/dev/null 2>&1; then
            print_success "PostgreSQL: healthy"
        else
            print_error "PostgreSQL: unhealthy"
        fi
    else
        print_error "PostgreSQL: not running"
    fi

    # Redis
    if docker ps --format '{{.Names}}' | grep -q "artifactor_backend_redis"; then
        if docker exec artifactor_backend_redis redis-cli ping >/dev/null 2>&1; then
            print_success "Redis: healthy"
        else
            print_error "Redis: unhealthy"
        fi
    else
        print_error "Redis: not running"
    fi

    # Backend API
    if docker ps --format '{{.Names}}' | grep -q "artifactor_backend_api"; then
        if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
            print_success "Backend API: healthy"
            print_info "API Documentation: http://localhost:8000/docs"
        else
            print_warning "Backend API: starting up or unhealthy"
        fi
    else
        print_error "Backend API: not running"
    fi

    echo ""
    print_info "Access points:"
    echo "  • API:         http://localhost:8000"
    echo "  • Docs:        http://localhost:8000/docs"
    echo "  • PostgreSQL:  localhost:5432"
    echo "  • Redis:       localhost:6379"
}

cmd_logs() {
    print_header

    if [ -n "$1" ]; then
        print_info "Showing logs for: $1"
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        print_info "Showing logs for all services (Ctrl+C to exit)"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

cmd_validate() {
    print_header

    if [ -f "$SCRIPT_DIR/validate-backend-services.sh" ]; then
        print_info "Running validation tests..."
        echo ""
        "$SCRIPT_DIR/validate-backend-services.sh"
    else
        print_error "Validation script not found"
        exit 1
    fi
}

cmd_backup() {
    print_header
    print_info "Creating backup of backend data..."
    echo ""

    BACKUP_DIR="$PROJECT_ROOT/backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    mkdir -p "$BACKUP_DIR"

    # PostgreSQL backup
    print_info "Backing up PostgreSQL database..."
    docker exec artifactor_backend_postgres pg_dump -U artifactor artifactor_v3 > "$BACKUP_DIR/postgres_${TIMESTAMP}.sql"
    print_success "PostgreSQL backup: $BACKUP_DIR/postgres_${TIMESTAMP}.sql"

    # Redis backup
    print_info "Backing up Redis data..."
    docker exec artifactor_backend_redis redis-cli BGSAVE >/dev/null 2>&1
    sleep 2
    docker cp artifactor_backend_redis:/data/dump.rdb "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
    print_success "Redis backup: $BACKUP_DIR/redis_${TIMESTAMP}.rdb"

    # Uploads backup
    print_info "Backing up upload data..."
    docker run --rm \
        -v artifactor_backend_upload_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/uploads_${TIMESTAMP}.tar.gz" -C /data . 2>/dev/null
    print_success "Uploads backup: $BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz"

    echo ""
    print_success "Backup completed: $BACKUP_DIR"
    print_info "Backup timestamp: $TIMESTAMP"
}

cmd_clean() {
    print_header
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        print_info "Aborted"
        exit 0
    fi

    print_info "Stopping and removing all services and data..."
    docker-compose -f "$COMPOSE_FILE" down -v

    print_success "All services and data removed"
}

cmd_shell() {
    local service=$1

    if [ -z "$service" ]; then
        print_error "Usage: $0 shell [postgres|redis|backend]"
        exit 1
    fi

    case "$service" in
        postgres)
            docker exec -it artifactor_backend_postgres psql -U artifactor -d artifactor_v3
            ;;
        redis)
            docker exec -it artifactor_backend_redis redis-cli
            ;;
        backend)
            docker exec -it artifactor_backend_api /bin/bash
            ;;
        *)
            print_error "Invalid service: $service"
            print_info "Available: postgres, redis, backend"
            exit 1
            ;;
    esac
}

cmd_help() {
    print_header
    cat <<EOF
Backend Services Management Commands:

  start       Start all backend services
  stop        Stop all backend services
  restart     Restart all backend services
  status      Show service status and health
  logs [svc]  Show logs (optionally for specific service)
  validate    Run comprehensive validation tests
  backup      Create backup of all data
  clean       Remove all services and data (DESTRUCTIVE!)
  shell <svc> Open shell in service (postgres|redis|backend)
  help        Show this help message

Examples:
  $0 start
  $0 status
  $0 logs backend
  $0 shell postgres
  $0 backup

Services:
  • artifactor_backend_postgres  - PostgreSQL 15 database
  • artifactor_backend_redis     - Redis 7 cache
  • artifactor_backend_api       - FastAPI backend

Documentation:
  $SCRIPT_DIR/BACKEND_SETUP.md

EOF
}

# Main execution
main() {
    check_prerequisites

    local command=${1:-help}
    shift || true

    case "$command" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$@"
            ;;
        validate)
            cmd_validate
            ;;
        backup)
            cmd_backup
            ;;
        clean)
            cmd_clean
            ;;
        shell)
            cmd_shell "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
