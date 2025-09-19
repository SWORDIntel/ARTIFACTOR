#!/bin/bash

# Portainer Backup Script
# DOCKER-AGENT: Automated backup system for Portainer data and configuration

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/portainer/backup"
DATA_DIR="/data"
CONFIG_DIR="/opt/portainer/config"
BACKUP_RETENTION_DAYS=30
BACKUP_PREFIX="portainer-backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_PREFIX}_${DATE}.tar.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Check if running as correct user
check_permissions() {
    if [ ! -w "$BACKUP_DIR" ]; then
        error_exit "No write permission to backup directory: $BACKUP_DIR"
    fi

    if [ ! -r "$DATA_DIR" ]; then
        error_exit "No read permission to data directory: $DATA_DIR"
    fi

    log "${GREEN}✓ Permissions validated${NC}"
}

# Create backup directory if it doesn't exist
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"
        log "${GREEN}✓ Created backup directory: $BACKUP_DIR${NC}"
    fi
}

# Get Portainer container status
get_portainer_status() {
    if command -v docker &> /dev/null; then
        local container_id
        container_id=$(docker ps -q -f name=portainer 2>/dev/null || echo "")

        if [ -n "$container_id" ]; then
            log "${BLUE}ℹ Portainer container is running (ID: $container_id)${NC}"
            return 0
        else
            log "${YELLOW}⚠ Portainer container not found or not running${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠ Docker command not available${NC}"
        return 1
    fi
}

# Create backup
create_backup() {
    log "${BLUE}ℹ Starting backup creation...${NC}"

    local temp_dir
    temp_dir=$(mktemp -d) || error_exit "Failed to create temporary directory"

    # Ensure cleanup of temp directory
    trap "rm -rf $temp_dir" EXIT

    # Copy Portainer data
    if [ -d "$DATA_DIR" ]; then
        log "${BLUE}ℹ Backing up Portainer data...${NC}"
        cp -r "$DATA_DIR" "$temp_dir/data" || error_exit "Failed to copy data directory"
    fi

    # Copy configuration files
    if [ -d "$CONFIG_DIR" ]; then
        log "${BLUE}ℹ Backing up configuration files...${NC}"
        cp -r "$CONFIG_DIR" "$temp_dir/config" || error_exit "Failed to copy config directory"
    fi

    # Create metadata file
    cat > "$temp_dir/backup_metadata.json" << EOF
{
    "backup_date": "$(date -Iseconds)",
    "backup_version": "1.0",
    "portainer_version": "$(docker exec portainer /portainer --version 2>/dev/null || echo 'unknown')",
    "backup_type": "full",
    "backed_up_components": [
        "portainer_data",
        "configuration_files",
        "ssl_certificates"
    ],
    "backup_size_bytes": "$(du -sb $temp_dir | cut -f1)"
}
EOF

    # Create compressed backup
    log "${BLUE}ℹ Creating compressed backup archive...${NC}"
    tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" -C "$temp_dir" . || error_exit "Failed to create backup archive"

    # Verify backup
    if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
        local backup_size
        backup_size=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
        log "${GREEN}✓ Backup created successfully: ${BACKUP_FILE} (Size: $backup_size)${NC}"
    else
        error_exit "Backup file not found after creation"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "${BLUE}ℹ Cleaning up old backups (older than $BACKUP_RETENTION_DAYS days)...${NC}"

    local deleted_count=0
    local total_size_freed=0

    # Find and delete old backup files
    while IFS= read -r -d '' file; do
        local file_size
        file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        total_size_freed=$((total_size_freed + file_size))
        rm -f "$file"
        ((deleted_count++))
        log "${YELLOW}⚠ Deleted old backup: $(basename "$file")${NC}"
    done < <(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -print0 2>/dev/null)

    if [ $deleted_count -eq 0 ]; then
        log "${GREEN}✓ No old backups to clean${NC}"
    else
        local size_freed_mb=$((total_size_freed / 1024 / 1024))
        log "${GREEN}✓ Cleaned $deleted_count old backups (freed ${size_freed_mb}MB)${NC}"
    fi
}

# List available backups
list_backups() {
    log "${BLUE}ℹ Available backups:${NC}"

    local backup_count=0
    local total_size=0

    while IFS= read -r -d '' file; do
        local file_size file_date file_name
        file_name=$(basename "$file")
        file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        file_date=$(stat -c%y "$file" 2>/dev/null | cut -d' ' -f1)
        total_size=$((total_size + file_size))
        ((backup_count++))

        local size_mb=$((file_size / 1024 / 1024))
        echo "  - $file_name (${size_mb}MB, $file_date)"
    done < <(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -print0 2>/dev/null | sort -z)

    if [ $backup_count -eq 0 ]; then
        log "${YELLOW}⚠ No backups found${NC}"
    else
        local total_size_mb=$((total_size / 1024 / 1024))
        log "${GREEN}✓ Found $backup_count backups (total size: ${total_size_mb}MB)${NC}"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        error_exit "Backup file not found: $backup_file"
    fi

    log "${BLUE}ℹ Verifying backup integrity: $(basename "$backup_file")${NC}"

    # Test archive integrity
    if tar -tzf "$backup_file" > /dev/null 2>&1; then
        log "${GREEN}✓ Backup archive integrity verified${NC}"

        # Check if metadata exists
        if tar -tzf "$backup_file" | grep -q "backup_metadata.json"; then
            log "${GREEN}✓ Backup metadata found${NC}"
        else
            log "${YELLOW}⚠ Backup metadata missing${NC}"
        fi

        return 0
    else
        log "${RED}✗ Backup archive is corrupted${NC}"
        return 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  create     Create a new backup (default)"
    echo "  list       List available backups"
    echo "  verify     Verify latest backup integrity"
    echo "  verify FILE Verify specific backup file"
    echo "  cleanup    Clean old backups only"
    echo "  help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  BACKUP_RETENTION_DAYS  Days to keep backups (default: 30)"
}

# Main function
main() {
    local action="${1:-create}"

    case "$action" in
        create)
            log "${BLUE}ℹ Starting Portainer backup process...${NC}"
            check_permissions
            create_backup_dir
            get_portainer_status
            create_backup
            cleanup_old_backups
            list_backups
            log "${GREEN}✓ Backup process completed successfully${NC}"
            ;;
        list)
            list_backups
            ;;
        verify)
            if [ -n "${2:-}" ]; then
                verify_backup "$2"
            else
                # Verify latest backup
                local latest_backup
                latest_backup=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
                if [ -n "$latest_backup" ]; then
                    verify_backup "$latest_backup"
                else
                    log "${YELLOW}⚠ No backups found to verify${NC}"
                fi
            fi
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        help)
            show_usage
            ;;
        *)
            log "${RED}✗ Unknown action: $action${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"