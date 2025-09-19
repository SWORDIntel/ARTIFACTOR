#!/bin/bash

# Portainer Deployment Script
# DOCKER-AGENT: Automated deployment and management for Portainer

set -euo pipefail

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="docker-compose.yml"
PORTAINER_SERVICE="portainer"
BACKUP_DIR="${PROJECT_DIR}/backup"
LOG_FILE="${PROJECT_DIR}/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging function
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Success message
success() {
    log "${GREEN}✓ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠ $1${NC}"
}

# Info message
info() {
    log "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed or not in PATH"
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running"
    fi

    # Check if running as root (for Docker socket access)
    if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
        warning "User is not in docker group. May need sudo for Docker commands"
    fi

    success "Prerequisites check completed"
}

# Create required directories
create_directories() {
    info "Creating required directories..."

    local dirs=(
        "${PROJECT_DIR}/portainer/data"
        "${PROJECT_DIR}/portainer/backup"
        "${PROJECT_DIR}/portainer/ssl"
        "${PROJECT_DIR}/portainer/config"
        "${PROJECT_DIR}/portainer/templates"
        "${BACKUP_DIR}"
        "$(dirname "$LOG_FILE")"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" || error_exit "Failed to create directory: $dir"
            info "Created directory: $dir"
        fi
    done

    success "Directory structure created"
}

# Generate SSL certificates if not present
setup_ssl() {
    info "Setting up SSL certificates..."

    local ssl_script="${PROJECT_DIR}/portainer/ssl/generate_ssl.sh"
    local cert_file="${PROJECT_DIR}/portainer/ssl/portainer.crt"

    if [ ! -f "$cert_file" ]; then
        if [ -f "$ssl_script" ]; then
            info "Generating SSL certificates..."
            cd "${PROJECT_DIR}/portainer/ssl"
            chmod +x "$ssl_script"
            if ./generate_ssl.sh --domain portainer.localhost; then
                success "SSL certificates generated"
            else
                error_exit "Failed to generate SSL certificates"
            fi
        else
            error_exit "SSL generation script not found: $ssl_script"
        fi
    else
        success "SSL certificates already exist"
    fi
}

# Check if Portainer is already running
check_portainer_status() {
    info "Checking Portainer status..."

    if docker ps --format "table {{.Names}}" | grep -q "etherscan-portainer"; then
        info "Portainer is currently running"
        return 0
    else
        info "Portainer is not running"
        return 1
    fi
}

# Build custom Portainer image
build_portainer() {
    info "Building custom Portainer image..."

    cd "$PROJECT_DIR"

    if docker-compose build "$PORTAINER_SERVICE"; then
        success "Portainer image built successfully"
    else
        error_exit "Failed to build Portainer image"
    fi
}

# Deploy Portainer stack
deploy_stack() {
    info "Deploying Portainer stack..."

    cd "$PROJECT_DIR"

    # Pull latest images
    info "Pulling latest base images..."
    docker-compose pull || warning "Some images may not have been pulled"

    # Start the stack
    info "Starting Portainer stack..."
    if docker-compose up -d "$PORTAINER_SERVICE"; then
        success "Portainer stack deployed successfully"
    else
        error_exit "Failed to deploy Portainer stack"
    fi
}

# Wait for Portainer to be healthy
wait_for_health() {
    info "Waiting for Portainer to become healthy..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker inspect --format='{{.State.Health.Status}}' etherscan-portainer 2>/dev/null | grep -q "healthy"; then
            success "Portainer is healthy"
            return 0
        fi

        info "Attempt $attempt/$max_attempts: Portainer not yet healthy, waiting..."
        sleep 10
        ((attempt++))
    done

    error_exit "Portainer failed to become healthy within the timeout period"
}

# Verify deployment
verify_deployment() {
    info "Verifying deployment..."

    # Check if container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "etherscan-portainer"; then
        error_exit "Portainer container is not running"
    fi

    # Check HTTP endpoint
    if curl -f -s --connect-timeout 10 "http://localhost:9000/api/status" > /dev/null; then
        success "HTTP endpoint is accessible"
    else
        warning "HTTP endpoint is not accessible"
    fi

    # Check HTTPS endpoint
    if curl -f -s -k --connect-timeout 10 "https://localhost:9443/api/status" > /dev/null; then
        success "HTTPS endpoint is accessible"
    else
        warning "HTTPS endpoint is not accessible"
    fi

    # Check logs for errors
    local recent_logs
    recent_logs=$(docker logs etherscan-portainer --tail 20 2>&1)

    if echo "$recent_logs" | grep -qi error; then
        warning "Errors detected in recent logs"
        echo "$recent_logs" | grep -i error
    else
        success "No recent errors in logs"
    fi

    success "Deployment verification completed"
}

# Show deployment status
show_status() {
    info "Deployment Status Summary"
    echo
    echo "=================================="
    echo "Portainer Container Management"
    echo "=================================="
    echo

    # Container status
    echo "Container Status:"
    docker ps --filter "name=etherscan-portainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo

    # Health status
    echo "Health Status:"
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' etherscan-portainer 2>/dev/null || echo "unknown")
    echo "  Health: $health_status"
    echo

    # Access URLs
    echo "Access URLs:"
    echo "  HTTP:  http://localhost:9000"
    echo "  HTTPS: https://localhost:9443"
    echo

    # SSL Certificate info
    local cert_file="${PROJECT_DIR}/portainer/ssl/portainer.crt"
    if [ -f "$cert_file" ]; then
        echo "SSL Certificate:"
        local expiry_date
        expiry_date=$(openssl x509 -in "$cert_file" -noout -dates | grep notAfter | cut -d= -f2)
        echo "  Expires: $expiry_date"
        echo
    fi

    # Resource usage
    echo "Resource Usage:"
    docker stats etherscan-portainer --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    echo

    echo "Deployment completed successfully!"
    echo "Access Portainer at: https://localhost:9443"
    echo "Default credentials: admin / portainer123"
    echo
}

# Backup before deployment
backup_existing() {
    if check_portainer_status; then
        info "Creating backup before deployment..."

        local backup_name="pre-deployment-$(date +%Y%m%d_%H%M%S)"
        local backup_script="${PROJECT_DIR}/portainer/scripts/backup.sh"

        if [ -f "$backup_script" ]; then
            if docker exec etherscan-portainer "/opt/portainer/backup/backup.sh" create; then
                success "Backup created: $backup_name"
            else
                warning "Backup creation failed"
            fi
        else
            warning "Backup script not found, skipping backup"
        fi
    fi
}

# Rollback function
rollback() {
    info "Rolling back deployment..."

    # Stop current container
    docker-compose stop "$PORTAINER_SERVICE" || true

    # Find latest backup
    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -name "portainer-backup_*.tar.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        info "Restoring from backup: $(basename "$latest_backup")"

        # Extract backup
        local temp_dir
        temp_dir=$(mktemp -d)
        tar -xzf "$latest_backup" -C "$temp_dir" || error_exit "Failed to extract backup"

        # Restore data
        rm -rf "${PROJECT_DIR}/portainer/data"/*
        cp -r "$temp_dir/data"/* "${PROJECT_DIR}/portainer/data/" || error_exit "Failed to restore data"

        # Cleanup
        rm -rf "$temp_dir"

        # Restart container
        docker-compose start "$PORTAINER_SERVICE"

        success "Rollback completed"
    else
        error_exit "No backup found for rollback"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  deploy      Deploy Portainer stack (default)"
    echo "  status      Show deployment status"
    echo "  restart     Restart Portainer service"
    echo "  stop        Stop Portainer service"
    echo "  start       Start Portainer service"
    echo "  backup      Create backup of Portainer data"
    echo "  rollback    Rollback to previous version"
    echo "  logs        Show Portainer logs"
    echo "  cleanup     Remove stopped containers and unused images"
    echo "  help        Show this help message"
    echo
    echo "Options:"
    echo "  --force     Force operation without prompts"
    echo "  --verbose   Enable verbose output"
    echo "  --no-ssl    Skip SSL certificate generation"
    echo
    echo "Examples:"
    echo "  $0                    # Deploy with default settings"
    echo "  $0 deploy --force     # Force deployment"
    echo "  $0 status             # Show current status"
    echo "  $0 backup             # Create backup"
    echo "  $0 rollback           # Rollback deployment"
}

# Parse command line arguments
parse_arguments() {
    local command="${1:-deploy}"
    local force_flag=""
    local verbose_flag=""
    local no_ssl_flag=""

    shift || true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_flag="true"
                shift
                ;;
            --verbose)
                verbose_flag="true"
                set -x
                shift
                ;;
            --no-ssl)
                no_ssl_flag="true"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done

    # Set global variables
    FORCE_FLAG="$force_flag"
    NO_SSL_FLAG="$no_ssl_flag"

    # Execute command
    case "$command" in
        deploy)
            main_deploy
            ;;
        status)
            show_status
            ;;
        restart)
            docker-compose restart "$PORTAINER_SERVICE"
            success "Portainer service restarted"
            ;;
        stop)
            docker-compose stop "$PORTAINER_SERVICE"
            success "Portainer service stopped"
            ;;
        start)
            docker-compose start "$PORTAINER_SERVICE"
            success "Portainer service started"
            ;;
        backup)
            if check_portainer_status; then
                docker exec etherscan-portainer "/opt/portainer/backup/backup.sh" create
            else
                error_exit "Portainer is not running"
            fi
            ;;
        rollback)
            rollback
            ;;
        logs)
            docker logs etherscan-portainer --tail 50 -f
            ;;
        cleanup)
            docker system prune -f
            success "Docker cleanup completed"
            ;;
        help)
            show_usage
            ;;
        *)
            error_exit "Unknown command: $command"
            ;;
    esac
}

# Main deployment function
main_deploy() {
    log "${PURPLE}Starting Portainer deployment...${NC}"

    check_prerequisites
    create_directories

    if [ "${NO_SSL_FLAG:-}" != "true" ]; then
        setup_ssl
    fi

    if [ "${FORCE_FLAG:-}" != "true" ]; then
        backup_existing
    fi

    build_portainer
    deploy_stack
    wait_for_health
    verify_deployment
    show_status

    log "${GREEN}Portainer deployment completed successfully!${NC}"
}

# Create log file
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Execute main function
parse_arguments "$@"