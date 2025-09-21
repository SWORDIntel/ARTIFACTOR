#!/bin/bash

# ARTIFACTOR Docker Setup Validation Script
# Tests all Docker infrastructure components

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${BLUE}ℹ${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "=============================================="
echo "ARTIFACTOR Docker Setup Validation"
echo "=============================================="

# Check 1: Docker availability
info "Checking Docker availability..."
if command -v docker >/dev/null 2>&1; then
    success "Docker is installed: $(docker --version)"
else
    error "Docker is not installed"
    exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
    success "Docker Compose is installed: $(docker-compose --version)"
else
    error "Docker Compose is not installed"
    exit 1
fi

# Check 2: Required files exist
info "Checking required files..."
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-entrypoint.sh"
    ".dockerignore"
    "Makefile"
    "simple-claude-downloader.py"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        success "Found: $file"
    else
        error "Missing: $file"
        exit 1
    fi
done

# Check 3: Scripts are executable
info "Checking script permissions..."
if [[ -x "docker-entrypoint.sh" ]]; then
    success "docker-entrypoint.sh is executable"
else
    warning "docker-entrypoint.sh not executable - fixing..."
    chmod +x docker-entrypoint.sh
    success "Fixed docker-entrypoint.sh permissions"
fi

if [[ -x "scripts/run-artifactor.sh" ]]; then
    success "scripts/run-artifactor.sh is executable"
else
    warning "scripts/run-artifactor.sh not executable - fixing..."
    chmod +x scripts/run-artifactor.sh
    success "Fixed scripts/run-artifactor.sh permissions"
fi

# Check 4: Downloads directory
info "Checking downloads directory..."
if [[ -d "downloads" ]]; then
    success "Downloads directory exists"
else
    warning "Downloads directory missing - creating..."
    mkdir -p downloads
    success "Created downloads directory"
fi

# Check 5: Dockerfile syntax
info "Validating Dockerfile..."
if docker run --rm -i hadolint/hadolint < Dockerfile >/dev/null 2>&1; then
    success "Dockerfile syntax is valid"
else
    warning "Dockerfile linting failed (this is usually not critical)"
fi

# Check 6: Docker Compose syntax
info "Validating docker-compose.yml..."
if docker-compose config >/dev/null 2>&1; then
    success "docker-compose.yml syntax is valid"
else
    error "docker-compose.yml has syntax errors"
    exit 1
fi

# Check 7: Python script syntax
info "Validating Python script..."
if python3 -m py_compile simple-claude-downloader.py 2>/dev/null; then
    success "Python script syntax is valid"
else
    error "Python script has syntax errors"
    exit 1
fi

# Check 8: Makefile targets
info "Testing Makefile targets..."
if make help >/dev/null 2>&1; then
    success "Makefile help target works"
else
    error "Makefile help target failed"
    exit 1
fi

# Check 9: Environment setup
info "Checking environment setup..."
if [[ -f ".env.example" ]]; then
    success "Environment example file exists"
    if [[ ! -f ".env" ]]; then
        info "Creating .env from example..."
        cp .env.example .env
        success "Created .env file"
    fi
else
    warning "No .env.example file found"
fi

# Check 10: Quick runner script
info "Testing quick runner script..."
if ./scripts/run-artifactor.sh --help >/dev/null 2>&1; then
    success "Quick runner script works"
else
    error "Quick runner script failed"
    exit 1
fi

# Check 11: Network prerequisites
info "Checking network prerequisites..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    success "Internet connectivity available"
else
    warning "No internet connectivity - Docker builds may fail"
fi

# Check 12: X11 availability (for clipboard)
info "Checking X11 availability..."
if [[ -n "$DISPLAY" ]]; then
    success "DISPLAY variable set: $DISPLAY"
    if [[ -S "/tmp/.X11-unix/X0" ]]; then
        success "X11 socket available"
    else
        warning "X11 socket not found - clipboard may not work"
    fi
else
    warning "No DISPLAY set - clipboard functionality will be limited"
fi

echo ""
echo "=============================================="
success "ARTIFACTOR Docker setup validation complete!"
echo "=============================================="
echo ""

info "Next steps:"
echo "1. Build the image:     make build"
echo "2. Test clipboard:      make run"
echo "3. Test with URL:       make run-url URL=https://example.com"
echo "4. Interactive mode:    make run-interactive"
echo "5. Get shell access:    make shell"
echo ""

info "For detailed usage, see:"
echo "- make examples"
echo "- cat DOCKER_README.md"
echo "- ./scripts/run-artifactor.sh --help"