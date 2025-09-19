#!/bin/bash
# Production entrypoint script for Etherscan API
# DOCKER-AGENT Implementation

set -e

echo "🚀 Starting Etherscan API Server"
echo "================================="

# Print environment information
echo "📊 Environment Information:"
echo "   Python Version: $(python --version)"
echo "   Working Directory: $(pwd)"
echo "   User: $(whoami)"
echo "   Date: $(date)"

# Create log directory if it doesn't exist
mkdir -p logs

# Health check before starting
echo "🏥 Performing startup health check..."
if python -c "
import sys
try:
    from etherscan_connector import EtherscanConnector
    from flask import Flask
    from prometheus_client import Counter
    print('✅ All dependencies loaded successfully')
    sys.exit(0)
except ImportError as e:
    print(f'❌ Dependency error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Startup error: {e}')
    sys.exit(1)
"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed - exiting"
    exit 1
fi

# Start the application with Gunicorn
echo "🔄 Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    api_server:app