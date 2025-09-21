#!/bin/bash

# ARTIFACTOR Quick Runner Script
# Simplified script for running ARTIFACTOR without docker-compose

set -e

# Configuration
IMAGE_NAME="artifactor:latest"
CONTAINER_NAME="artifactor-$(date +%s)"
DOWNLOADS_DIR="$(pwd)/downloads"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Usage function
usage() {
    echo "ARTIFACTOR Quick Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [DOWNLOADER_ARGS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help"
    echo "  -b, --build             Build image before running"
    echo "  -d, --downloads DIR     Downloads directory (default: ./downloads)"
    echo "  -n, --name NAME         Container name prefix"
    echo "  --no-clipboard          Disable clipboard access"
    echo "  --shell                 Get shell access instead of running downloader"
    echo ""
    echo "Examples:"
    echo "  $0 --clipboard                    # Download from clipboard"
    echo "  $0 --url https://example.com      # Download from URL"
    echo "  $0 --interactive                  # Interactive mode"
    echo "  $0 --file input.txt               # Process file"
    echo "  $0 --shell                        # Get shell access"
}

# Parse arguments
BUILD_IMAGE=false
ENABLE_CLIPBOARD=true
SHELL_MODE=false
DOWNLOADER_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build)
            BUILD_IMAGE=true
            shift
            ;;
        -d|--downloads)
            DOWNLOADS_DIR="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2-$(date +%s)"
            shift 2
            ;;
        --no-clipboard)
            ENABLE_CLIPBOARD=false
            shift
            ;;
        --shell)
            SHELL_MODE=true
            shift
            ;;
        *)
            DOWNLOADER_ARGS+=("$1")
            shift
            ;;
    esac
done

# Create downloads directory
mkdir -p "$DOWNLOADS_DIR"
info "Downloads directory: $DOWNLOADS_DIR"

# Build image if requested
if [[ "$BUILD_IMAGE" == true ]]; then
    info "Building ARTIFACTOR image..."
    docker build -t "$IMAGE_NAME" .
    success "Image built successfully"
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    error "Image $IMAGE_NAME not found. Build it first with --build option."
    exit 1
fi

# Prepare Docker run command
DOCKER_CMD=(
    docker run
    --rm
    --name "$CONTAINER_NAME"
    -v "$DOWNLOADS_DIR:/app/downloads"
)

# Add clipboard access if enabled
if [[ "$ENABLE_CLIPBOARD" == true ]]; then
    # Check if we're on Linux with X11
    if [[ -n "$DISPLAY" && -S "/tmp/.X11-unix/X0" ]]; then
        info "Enabling X11 clipboard access"
        DOCKER_CMD+=(
            -e DISPLAY="$DISPLAY"
            -v /tmp/.X11-unix:/tmp/.X11-unix:rw
            --cap-add SYS_ADMIN
            --security-opt apparmor:unconfined
        )
    else
        warning "X11 not available - clipboard functionality may be limited"
    fi
fi

# Add interactive mode if needed
if [[ "$SHELL_MODE" == true || " ${DOWNLOADER_ARGS[*]} " =~ " --interactive " ]]; then
    DOCKER_CMD+=(-it)
fi

# Add image
DOCKER_CMD+=("$IMAGE_NAME")

# Add shell or downloader arguments
if [[ "$SHELL_MODE" == true ]]; then
    DOCKER_CMD+=(/bin/bash)
    info "Starting shell in ARTIFACTOR container..."
else
    DOCKER_CMD+=("${DOWNLOADER_ARGS[@]}")
    info "Running ARTIFACTOR with args: ${DOWNLOADER_ARGS[*]}"
fi

# Run the container
"${DOCKER_CMD[@]}"

# Show results
if [[ "$SHELL_MODE" == false ]]; then
    if [[ -d "$DOWNLOADS_DIR" && -n "$(ls -A "$DOWNLOADS_DIR" 2>/dev/null)" ]]; then
        success "Download completed. Files in: $DOWNLOADS_DIR"
        echo "Downloaded files:"
        ls -la "$DOWNLOADS_DIR"
    else
        warning "No files downloaded to $DOWNLOADS_DIR"
    fi
fi