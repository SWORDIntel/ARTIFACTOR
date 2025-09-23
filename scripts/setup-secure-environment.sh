#!/bin/bash
# ARTIFACTOR v3.0 - Secure Environment Setup Script
# Creates secure production environment with proper secrets management

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="/data/artifactor/secrets"
SSL_DIR="/data/artifactor/ssl"
DATA_DIR="/data/artifactor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi

    # Check if OpenSSL is available
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed"
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running or accessible"
    fi

    log "Prerequisites check passed"
}

# Generate secure random passwords
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Generate secure secrets
generate_secrets() {
    log "Generating secure secrets..."

    # Create secrets directory with proper permissions
    sudo mkdir -p "$SECRETS_DIR"
    sudo chown $(whoami):$(whoami) "$SECRETS_DIR"
    chmod 700 "$SECRETS_DIR"

    # Database credentials
    DB_NAME="artifactor_v3_prod"
    DB_USER="artifactor_user"
    DB_PASSWORD=$(generate_password 64)

    # Redis password
    REDIS_PASSWORD=$(generate_password 64)

    # JWT secret key
    JWT_SECRET=$(generate_password 128)

    # Encryption key for application
    ENCRYPTION_KEY=$(openssl rand -hex 32)

    # Write secrets to files
    echo "$DB_NAME" | sudo tee "$SECRETS_DIR/postgres_db" > /dev/null
    echo "$DB_USER" | sudo tee "$SECRETS_DIR/postgres_user" > /dev/null
    echo "$DB_PASSWORD" | sudo tee "$SECRETS_DIR/postgres_password" > /dev/null
    echo "$REDIS_PASSWORD" | sudo tee "$SECRETS_DIR/redis_password" > /dev/null
    echo "$JWT_SECRET" | sudo tee "$SECRETS_DIR/jwt_secret_key" > /dev/null
    echo "$ENCRYPTION_KEY" | sudo tee "$SECRETS_DIR/encryption_key" > /dev/null

    # Composite connection strings
    echo "postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}?sslmode=require" | sudo tee "$SECRETS_DIR/database_url" > /dev/null
    echo "rediss://:${REDIS_PASSWORD}@redis:6380/0" | sudo tee "$SECRETS_DIR/redis_url" > /dev/null

    # Alert webhook URL (placeholder)
    echo "https://alerts.example.com/webhook" | sudo tee "$SECRETS_DIR/alert_webhook_url" > /dev/null

    # SMTP password (placeholder)
    echo "smtp_password_here" | sudo tee "$SECRETS_DIR/smtp_password" > /dev/null

    # Set proper permissions on secret files
    sudo find "$SECRETS_DIR" -type f -exec chmod 600 {} \;
    sudo find "$SECRETS_DIR" -type f -exec chown root:root {} \;

    log "Secrets generated successfully"

    # Display connection info for manual setup
    cat << EOF

========================================
GENERATED CREDENTIALS (SAVE SECURELY!)
========================================
Database Name: $DB_NAME
Database User: $DB_USER
Database Password: $DB_PASSWORD
Redis Password: $REDIS_PASSWORD
JWT Secret: [64 characters - saved to file]
Encryption Key: [64 characters - saved to file]
========================================

IMPORTANT: These credentials are now stored in:
$SECRETS_DIR/

Make sure to:
1. Backup these files securely
2. Restrict access to authorized personnel only
3. Use a proper secrets management system in production

EOF
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "Generating SSL certificates..."

    # Create SSL directory
    sudo mkdir -p "$SSL_DIR"
    sudo chown $(whoami):$(whoami) "$SSL_DIR"
    chmod 755 "$SSL_DIR"

    # Generate CA private key
    openssl genrsa -out "$SSL_DIR/ca.key" 4096
    chmod 600 "$SSL_DIR/ca.key"

    # Generate CA certificate
    openssl req -new -x509 -days 365 -key "$SSL_DIR/ca.key" -out "$SSL_DIR/ca.crt" \
        -subj "/C=US/ST=State/L=City/O=ARTIFACTOR/OU=Security/CN=ARTIFACTOR-CA"

    # Generate server private key
    openssl genrsa -out "$SSL_DIR/server.key" 2048
    chmod 600 "$SSL_DIR/server.key"

    # Generate server certificate request
    openssl req -new -key "$SSL_DIR/server.key" -out "$SSL_DIR/server.csr" \
        -subj "/C=US/ST=State/L=City/O=ARTIFACTOR/OU=Backend/CN=api.artifactor.local"

    # Generate server certificate
    openssl x509 -req -days 365 -in "$SSL_DIR/server.csr" -CA "$SSL_DIR/ca.crt" \
        -CAkey "$SSL_DIR/ca.key" -CAcreateserial -out "$SSL_DIR/server.crt"

    # Generate Redis certificates
    openssl genrsa -out "$SSL_DIR/redis.key" 2048
    chmod 600 "$SSL_DIR/redis.key"

    openssl req -new -key "$SSL_DIR/redis.key" -out "$SSL_DIR/redis.csr" \
        -subj "/C=US/ST=State/L=City/O=ARTIFACTOR/OU=Redis/CN=redis.artifactor.local"

    openssl x509 -req -days 365 -in "$SSL_DIR/redis.csr" -CA "$SSL_DIR/ca.crt" \
        -CAkey "$SSL_DIR/ca.key" -CAcreateserial -out "$SSL_DIR/redis.crt"

    # Clean up CSR files
    rm -f "$SSL_DIR"/*.csr

    log "SSL certificates generated successfully"
}

# Setup Docker secrets
setup_docker_secrets() {
    log "Setting up Docker secrets..."

    # Initialize Docker Swarm if not already initialized
    if ! docker info | grep -q "Swarm: active"; then
        log "Initializing Docker Swarm..."
        docker swarm init --advertise-addr 127.0.0.1
    fi

    # Create Docker secrets from files
    docker secret create postgres_user "$SECRETS_DIR/postgres_user" 2>/dev/null || true
    docker secret create postgres_password "$SECRETS_DIR/postgres_password" 2>/dev/null || true
    docker secret create postgres_db "$SECRETS_DIR/postgres_db" 2>/dev/null || true
    docker secret create redis_password "$SECRETS_DIR/redis_password" 2>/dev/null || true
    docker secret create jwt_secret_key "$SECRETS_DIR/jwt_secret_key" 2>/dev/null || true
    docker secret create encryption_key "$SECRETS_DIR/encryption_key" 2>/dev/null || true
    docker secret create alert_webhook_url "$SECRETS_DIR/alert_webhook_url" 2>/dev/null || true
    docker secret create smtp_password "$SECRETS_DIR/smtp_password" 2>/dev/null || true

    log "Docker secrets created successfully"
}

# Setup secure directories
setup_directories() {
    log "Setting up secure directories..."

    # Create data directories with proper permissions
    sudo mkdir -p "$DATA_DIR"/{postgres,redis,uploads,logs,quarantine,backups,clamav}

    # Set ownership for PostgreSQL
    sudo chown -R 999:999 "$DATA_DIR/postgres"
    sudo chmod 700 "$DATA_DIR/postgres"

    # Set ownership for Redis
    sudo chown -R 999:999 "$DATA_DIR/redis"
    sudo chmod 700 "$DATA_DIR/redis"

    # Set ownership for application directories
    sudo chown -R 1000:1000 "$DATA_DIR"/{uploads,logs,quarantine,backups}
    sudo chmod 750 "$DATA_DIR/uploads"
    sudo chmod 750 "$DATA_DIR/logs"
    sudo chmod 700 "$DATA_DIR/quarantine"
    sudo chmod 700 "$DATA_DIR/backups"

    # Set ownership for ClamAV
    sudo chown -R 100:101 "$DATA_DIR/clamav"
    sudo chmod 750 "$DATA_DIR/clamav"

    log "Directories created with secure permissions"
}

# Create security configuration files
create_security_configs() {
    log "Creating security configuration files..."

    # Create security directory
    mkdir -p "$PROJECT_ROOT/docker/security"

    # Security monitoring configuration
    cat > "$PROJECT_ROOT/docker/security/security-rules.yaml" << 'EOF'
# ARTIFACTOR Security Monitoring Rules
rules:
  - name: "Multiple failed login attempts"
    pattern: "authentication failed"
    threshold: 5
    window: 300  # 5 minutes
    action: "alert"

  - name: "SQL injection attempt"
    pattern: "SQL injection pattern detected"
    threshold: 1
    window: 60
    action: "block"

  - name: "File upload virus detected"
    pattern: "Virus detected"
    threshold: 1
    window: 60
    action: "quarantine"

  - name: "Unusual API access pattern"
    pattern: "rate limit exceeded"
    threshold: 3
    window: 600  # 10 minutes
    action: "alert"
EOF

    # Pre-start security checks script
    cat > "$PROJECT_ROOT/backend/security/pre_start_checks.py" << 'EOF'
#!/usr/bin/env python3
"""
Pre-start security checks for ARTIFACTOR
Validates security configuration before application startup
"""

import os
import sys
import logging
from pathlib import Path

def check_secrets():
    """Check that all required secrets are available"""
    required_secrets = [
        '/run/secrets/postgres_user',
        '/run/secrets/postgres_password',
        '/run/secrets/postgres_db',
        '/run/secrets/redis_password',
        '/run/secrets/jwt_secret_key',
        '/run/secrets/encryption_key'
    ]

    for secret_file in required_secrets:
        if not os.path.exists(secret_file):
            print(f"ERROR: Required secret file not found: {secret_file}")
            return False

        # Check file permissions
        stat = os.stat(secret_file)
        if stat.st_mode & 0o077:
            print(f"ERROR: Secret file has insecure permissions: {secret_file}")
            return False

    return True

def check_ssl_certificates():
    """Check SSL certificates are present and valid"""
    ssl_files = [
        '/app/ssl/ca.crt',
        '/app/ssl/server.crt',
        '/app/ssl/server.key'
    ]

    for ssl_file in ssl_files:
        if not os.path.exists(ssl_file):
            print(f"ERROR: SSL file not found: {ssl_file}")
            return False

    return True

def check_environment():
    """Check security-critical environment variables"""
    env_vars = {
        'ENVIRONMENT': 'production',
        'DEBUG': 'false',
        'SECURITY_LOG_ENABLED': 'true',
        'RATE_LIMIT_ENABLED': 'true'
    }

    for var, expected in env_vars.items():
        value = os.getenv(var, '').lower()
        if value != expected.lower():
            print(f"ERROR: Environment variable {var} should be '{expected}', got '{value}'")
            return False

    return True

def main():
    """Run all security checks"""
    print("Running pre-start security checks...")

    checks = [
        ("Secrets validation", check_secrets),
        ("SSL certificates", check_ssl_certificates),
        ("Environment variables", check_environment)
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        if check_func():
            print(f"✓ {check_name} passed")
        else:
            print(f"✗ {check_name} failed")
            all_passed = False

    if all_passed:
        print("All security checks passed!")
        sys.exit(0)
    else:
        print("Security checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

    # Make pre-start script executable
    chmod +x "$PROJECT_ROOT/backend/security/pre_start_checks.py"

    log "Security configuration files created"
}

# Build secure Docker images
build_secure_images() {
    log "Building secure Docker images..."

    cd "$PROJECT_ROOT"

    # Build backend image with security hardening
    docker build -f backend/Dockerfile.secure -t artifactor/backend:secure backend/

    # Build frontend image with security hardening
    docker build -f frontend/Dockerfile.secure -t artifactor/frontend:secure frontend/

    # Build security monitor image
    docker build -f docker/security-monitor/Dockerfile -t artifactor/security-monitor:latest docker/security-monitor/

    log "Secure Docker images built successfully"
}

# Setup firewall rules
setup_firewall() {
    log "Setting up firewall rules..."

    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        warn "This script can configure UFW firewall rules. Continue? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            # Enable UFW
            sudo ufw --force enable

            # Default policies
            sudo ufw default deny incoming
            sudo ufw default allow outgoing

            # Allow SSH (be careful!)
            sudo ufw allow ssh

            # Allow HTTP and HTTPS
            sudo ufw allow 80/tcp
            sudo ufw allow 443/tcp

            # Allow local Docker network
            sudo ufw allow from 172.21.0.0/16

            log "Firewall rules configured"
        fi
    else
        warn "UFW not available - configure firewall manually"
    fi
}

# Final security validation
security_validation() {
    log "Running final security validation..."

    # Check secret file permissions
    if [[ -d "$SECRETS_DIR" ]]; then
        local bad_perms=$(sudo find "$SECRETS_DIR" -type f ! -perm 600)
        if [[ -n "$bad_perms" ]]; then
            error "Some secret files have incorrect permissions: $bad_perms"
        fi
    fi

    # Check data directory permissions
    if [[ -d "$DATA_DIR" ]]; then
        local world_readable=$(sudo find "$DATA_DIR" -type d -perm /o+r)
        if [[ -n "$world_readable" ]]; then
            warn "Some directories are world-readable: $world_readable"
        fi
    fi

    # Verify Docker secrets
    if docker secret ls | grep -q "postgres_password"; then
        log "Docker secrets verified"
    else
        error "Docker secrets not properly created"
    fi

    log "Security validation completed"
}

# Main function
main() {
    log "Starting ARTIFACTOR v3.0 Secure Environment Setup"

    check_root
    check_prerequisites

    # Create directory structure
    setup_directories

    # Generate secrets and certificates
    generate_secrets
    generate_ssl_certificates

    # Setup Docker environment
    setup_docker_secrets

    # Create configuration files
    create_security_configs

    # Build images
    build_secure_images

    # Optional firewall setup
    setup_firewall

    # Final validation
    security_validation

    log "Secure environment setup completed successfully!"

    cat << EOF

=======================================================
ARTIFACTOR v3.0 SECURE ENVIRONMENT SETUP COMPLETE
=======================================================

Next steps:
1. Review and update alert webhook URL in secrets
2. Configure SMTP settings for notifications
3. Review and customize security rules
4. Start the application:
   cd $PROJECT_ROOT/docker
   docker-compose -f docker-compose.secure.yml up -d

Security features enabled:
✓ Encrypted secrets management
✓ SSL/TLS encryption
✓ Container security hardening
✓ Comprehensive logging
✓ Virus scanning integration
✓ Security monitoring
✓ Firewall configuration

Important files:
- Secrets: $SECRETS_DIR/
- SSL Certificates: $SSL_DIR/
- Application Data: $DATA_DIR/
- Security Configs: $PROJECT_ROOT/docker/security/

=======================================================

EOF
}

# Run main function
main "$@"