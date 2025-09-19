#!/bin/bash

# SSL Certificate Generation for Portainer
# DOCKER-AGENT: Secure SSL setup for container management

set -euo pipefail

# Configuration
SSL_DIR="$(dirname "$0")"
CERT_NAME="portainer"
DOMAIN="portainer.localhost"
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="Etherscan Docker Stack"
ORG_UNIT="IT Department"
VALID_DAYS=365

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

# Check if OpenSSL is available
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        error_exit "OpenSSL is not installed"
    fi
    log "${GREEN}✓ OpenSSL is available${NC}"
}

# Create SSL directory if it doesn't exist
create_ssl_dir() {
    if [ ! -d "$SSL_DIR" ]; then
        mkdir -p "$SSL_DIR" || error_exit "Failed to create SSL directory"
        log "${GREEN}✓ Created SSL directory: $SSL_DIR${NC}"
    fi
}

# Generate private key
generate_private_key() {
    log "${BLUE}ℹ Generating private key...${NC}"

    if openssl genpkey -algorithm RSA -out "${SSL_DIR}/${CERT_NAME}.key" -pkeyopt rsa_keygen_bits:2048; then
        chmod 600 "${SSL_DIR}/${CERT_NAME}.key"
        log "${GREEN}✓ Private key generated: ${CERT_NAME}.key${NC}"
    else
        error_exit "Failed to generate private key"
    fi
}

# Create certificate signing request configuration
create_csr_config() {
    log "${BLUE}ℹ Creating CSR configuration...${NC}"

    cat > "${SSL_DIR}/${CERT_NAME}.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=${COUNTRY}
ST=${STATE}
L=${CITY}
O=${ORG}
OU=${ORG_UNIT}
CN=${DOMAIN}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = localhost
DNS.3 = portainer
DNS.4 = etherscan-portainer
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    log "${GREEN}✓ CSR configuration created${NC}"
}

# Generate certificate signing request
generate_csr() {
    log "${BLUE}ℹ Generating certificate signing request...${NC}"

    if openssl req -new -key "${SSL_DIR}/${CERT_NAME}.key" -out "${SSL_DIR}/${CERT_NAME}.csr" -config "${SSL_DIR}/${CERT_NAME}.conf"; then
        log "${GREEN}✓ Certificate signing request generated: ${CERT_NAME}.csr${NC}"
    else
        error_exit "Failed to generate certificate signing request"
    fi
}

# Generate self-signed certificate
generate_certificate() {
    log "${BLUE}ℹ Generating self-signed certificate...${NC}"

    if openssl x509 -req -in "${SSL_DIR}/${CERT_NAME}.csr" -signkey "${SSL_DIR}/${CERT_NAME}.key" -out "${SSL_DIR}/${CERT_NAME}.crt" -days ${VALID_DAYS} -extensions v3_req -extfile "${SSL_DIR}/${CERT_NAME}.conf"; then
        chmod 644 "${SSL_DIR}/${CERT_NAME}.crt"
        log "${GREEN}✓ Self-signed certificate generated: ${CERT_NAME}.crt${NC}"
        log "${GREEN}✓ Certificate valid for ${VALID_DAYS} days${NC}"
    else
        error_exit "Failed to generate certificate"
    fi
}

# Verify certificate
verify_certificate() {
    log "${BLUE}ℹ Verifying certificate...${NC}"

    # Check certificate validity
    if openssl x509 -in "${SSL_DIR}/${CERT_NAME}.crt" -text -noout > /dev/null 2>&1; then
        log "${GREEN}✓ Certificate is valid${NC}"

        # Show certificate details
        local expiry_date
        expiry_date=$(openssl x509 -in "${SSL_DIR}/${CERT_NAME}.crt" -noout -dates | grep notAfter | cut -d= -f2)
        log "${BLUE}ℹ Certificate expires: $expiry_date${NC}"

        # Show subject alternative names
        local san
        san=$(openssl x509 -in "${SSL_DIR}/${CERT_NAME}.crt" -noout -text | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/^[[:space:]]*//')
        if [ -n "$san" ]; then
            log "${BLUE}ℹ Subject Alternative Names: $san${NC}"
        fi
    else
        error_exit "Generated certificate is invalid"
    fi
}

# Create certificate bundle (if needed)
create_bundle() {
    log "${BLUE}ℹ Creating certificate bundle...${NC}"

    # Combine certificate and key for applications that need it
    cat "${SSL_DIR}/${CERT_NAME}.crt" "${SSL_DIR}/${CERT_NAME}.key" > "${SSL_DIR}/${CERT_NAME}.pem"
    chmod 600 "${SSL_DIR}/${CERT_NAME}.pem"

    log "${GREEN}✓ Certificate bundle created: ${CERT_NAME}.pem${NC}"
}

# Set proper permissions
set_permissions() {
    log "${BLUE}ℹ Setting proper file permissions...${NC}"

    # Set ownership to portainer user (UID 1000)
    chown -R 1000:1000 "$SSL_DIR" 2>/dev/null || true

    # Set restrictive permissions
    chmod 700 "$SSL_DIR"
    chmod 600 "${SSL_DIR}/${CERT_NAME}.key" "${SSL_DIR}/${CERT_NAME}.pem"
    chmod 644 "${SSL_DIR}/${CERT_NAME}.crt"
    chmod 644 "${SSL_DIR}/${CERT_NAME}.conf" "${SSL_DIR}/${CERT_NAME}.csr"

    log "${GREEN}✓ File permissions set correctly${NC}"
}

# Clean up temporary files
cleanup() {
    log "${BLUE}ℹ Cleaning up temporary files...${NC}"

    rm -f "${SSL_DIR}/${CERT_NAME}.csr" "${SSL_DIR}/${CERT_NAME}.conf"

    log "${GREEN}✓ Cleanup completed${NC}"
}

# Generate Diffie-Hellman parameters for additional security
generate_dhparam() {
    log "${BLUE}ℹ Generating Diffie-Hellman parameters (this may take a while)...${NC}"

    if openssl dhparam -out "${SSL_DIR}/dhparam.pem" 2048; then
        chmod 644 "${SSL_DIR}/dhparam.pem"
        log "${GREEN}✓ Diffie-Hellman parameters generated${NC}"
    else
        log "${YELLOW}⚠ Failed to generate Diffie-Hellman parameters (optional)${NC}"
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --domain DOMAIN     Set domain name (default: portainer.localhost)"
    echo "  --days DAYS         Certificate validity in days (default: 365)"
    echo "  --country CODE      Country code (default: US)"
    echo "  --state STATE       State/Province (default: California)"
    echo "  --city CITY         City (default: San Francisco)"
    echo "  --org ORG           Organization (default: Etherscan Docker Stack)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Generate with defaults"
    echo "  $0 --domain portainer.example.com    # Custom domain"
    echo "  $0 --days 730                        # 2-year certificate"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --days)
                VALID_DAYS="$2"
                shift 2
                ;;
            --country)
                COUNTRY="$2"
                shift 2
                ;;
            --state)
                STATE="$2"
                shift 2
                ;;
            --city)
                CITY="$2"
                shift 2
                ;;
            --org)
                ORG="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log "${RED}✗ Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Show certificate information
show_certificate_info() {
    log "${BLUE}ℹ Certificate Information:${NC}"
    echo "  Domain: $DOMAIN"
    echo "  Valid for: $VALID_DAYS days"
    echo "  Country: $COUNTRY"
    echo "  State: $STATE"
    echo "  City: $CITY"
    echo "  Organization: $ORG"
    echo "  Files created:"
    echo "    - ${SSL_DIR}/${CERT_NAME}.key (Private Key)"
    echo "    - ${SSL_DIR}/${CERT_NAME}.crt (Certificate)"
    echo "    - ${SSL_DIR}/${CERT_NAME}.pem (Bundle)"
    echo "    - ${SSL_DIR}/dhparam.pem (DH Parameters)"
}

# Main function
main() {
    parse_arguments "$@"

    log "${BLUE}ℹ Starting SSL certificate generation for Portainer...${NC}"

    check_openssl
    create_ssl_dir
    generate_private_key
    create_csr_config
    generate_csr
    generate_certificate
    verify_certificate
    create_bundle
    generate_dhparam
    set_permissions
    cleanup

    show_certificate_info

    log "${GREEN}✓ SSL certificate generation completed successfully!${NC}"
    log "${YELLOW}⚠ Remember to add the certificate to your browser's trusted certificates${NC}"
    log "${BLUE}ℹ For production use, consider using Let's Encrypt or a proper CA${NC}"
}

# Execute main function with all arguments
main "$@"