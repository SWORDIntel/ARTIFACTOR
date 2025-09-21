#!/bin/bash

# ARTIFACTOR Docker Entrypoint Script
# Handles clipboard access and environment setup for containers

set -e

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

# Display banner
echo "=================================================="
blue "  ARTIFACTOR - Claude.ai Artifact Downloader"
echo "=================================================="

# Environment setup
export DISPLAY="${DISPLAY:-:0}"
export HOME="/home/artifactor"

# Clipboard access setup
setup_clipboard() {
    echo "Setting up clipboard access..."

    # Check if DISPLAY is available
    if [ -n "$DISPLAY" ]; then
        green "✓ DISPLAY variable set: $DISPLAY"
    else
        yellow "⚠ No DISPLAY set - clipboard functionality may be limited"
    fi

    # Test clipboard tools
    if command -v xclip >/dev/null 2>&1; then
        green "✓ xclip available"
    else
        red "✗ xclip not found"
    fi

    if command -v xsel >/dev/null 2>&1; then
        green "✓ xsel available"
    else
        yellow "⚠ xsel not found"
    fi
}

# Health check function
health_check() {
    echo "Running health check..."

    # Check Python
    if python3 --version >/dev/null 2>&1; then
        green "✓ Python 3 working"
    else
        red "✗ Python 3 not working"
        exit 1
    fi

    # Check requests module
    if python3 -c "import requests" >/dev/null 2>&1; then
        green "✓ requests module available"
    else
        red "✗ requests module not available"
        exit 1
    fi

    # Check downloader script
    if [ -f "/app/simple-claude-downloader.py" ]; then
        green "✓ Downloader script found"
    else
        red "✗ Downloader script not found"
        exit 1
    fi

    # Check downloads directory
    if [ -d "/app/downloads" ]; then
        green "✓ Downloads directory ready"
    else
        red "✗ Downloads directory not found"
        exit 1
    fi
}

# Usage information
show_usage() {
    echo
    blue "USAGE EXAMPLES:"
    echo "  # Download from clipboard:"
    echo "  docker run --rm -v \"\$(pwd)/downloads:/app/downloads\" -e DISPLAY=\$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix artifactor --clipboard"
    echo
    echo "  # Download from URL:"
    echo "  docker run --rm -v \"\$(pwd)/downloads:/app/downloads\" artifactor --url https://example.com/artifact"
    echo
    echo "  # Interactive mode:"
    echo "  docker run --rm -it -v \"\$(pwd)/downloads:/app/downloads\" artifactor --interactive"
    echo
    echo "  # Using docker-compose:"
    echo "  docker-compose run artifactor --clipboard"
    echo
    blue "AVAILABLE OPTIONS:"
    python3 /app/simple-claude-downloader.py --help
}

# Main execution
main() {
    # Run setup
    setup_clipboard

    # Handle special commands
    case "$1" in
        "health"|"--health")
            health_check
            exit 0
            ;;
        "usage"|"--usage")
            show_usage
            exit 0
            ;;
        "--help"|"-h"|"help"|"")
            show_usage
            exit 0
            ;;
    esac

    # Run health check before executing
    health_check
    echo

    # Execute the downloader with all arguments
    green "Starting ARTIFACTOR..."
    exec python3 /app/simple-claude-downloader.py "$@"
}

# Execute main function
main "$@"