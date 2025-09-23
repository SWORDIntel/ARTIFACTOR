#!/bin/bash

# ARTIFACTOR v3.0.0 - Quick Environment Setup
# Minimal interactive setup for fast deployment

set -e

echo "🚀 ARTIFACTOR Quick Environment Setup"
echo "======================================"

# Generate secure credentials
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "$(date +%s | sha256sum | base64 | head -c 64)")
DB_PASSWORD=$(openssl rand -hex 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || echo "$(date +%s | sha256sum | base64 | head -c 32)")

# Validate generated credentials
if [ ${#SECRET_KEY} -lt 32 ]; then
    echo "Error: Failed to generate secure SECRET_KEY"
    exit 1
fi

if [ ${#DB_PASSWORD} -lt 16 ]; then
    echo "Error: Failed to generate secure database password"
    exit 1
fi

# Create .env with secure defaults
cat > .env << EOF
# ARTIFACTOR v3.0.0 - Quick Setup Configuration
SECRET_KEY=${SECRET_KEY}
DEBUG=false
ENVIRONMENT=production

# Database
POSTGRES_DB=artifactor_v3
POSTGRES_USER=artifactor_user
POSTGRES_PASSWORD=${DB_PASSWORD}
DATABASE_URL=postgresql://artifactor_user:${DB_PASSWORD}@postgres:5432/artifactor_v3

# Redis
REDIS_URL=redis://redis:6379

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000

# Features
AGENT_COORDINATION_ENABLED=true
V2_COMPATIBILITY=true
MAX_UPLOAD_SIZE_MB=50

# Docker
COMPOSE_PROJECT_NAME=artifactor
EOF

chmod 600 .env

# Verify .env file was created successfully
if [ ! -f ".env" ] || [ ! -s ".env" ]; then
    echo "Error: Failed to create .env file"
    exit 1
fi

# Clear sensitive variables from environment
unset SECRET_KEY
unset DB_PASSWORD

echo "✅ Created .env with secure credentials"
echo "🔐 Secret key: [Generated 64-char hex]"
echo "🔑 Database password: [Generated 32-char hex - stored in .env]"
echo ""
echo "⚠️  SECURITY NOTICE:"
echo "• Database credentials are stored securely in .env file"
echo "• Never share .env file contents"
echo "• Access credentials via: grep POSTGRES_PASSWORD .env"
echo ""
echo "Ready to deploy:"
echo "  docker-compose up -d"