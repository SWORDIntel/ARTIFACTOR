#!/bin/bash

# ARTIFACTOR v3.0.0 - Environment Setup Script
# Configures all environment variables for secure deployment

set -e  # Exit on any error

echo "🚀 ARTIFACTOR v3.0.0 Environment Setup"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENV_FILE=".env"
ENV_EXAMPLE_FILE=".env.example"

# Function to generate secure random string
generate_secret() {
    openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "$(date +%s | sha256sum | base64 | head -c 32)"
}

# Function to validate input safely
validate_input() {
    local input="$1"
    local type="$2"

    # Remove dangerous characters
    input=$(echo "$input" | tr -d '`;|&$()<>{}[]\\"\047')

    case "$type" in
        "port")
            if [[ "$input" =~ ^[0-9]+$ ]] && [ "$input" -ge 1 ] && [ "$input" -le 65535 ]; then
                echo "$input"
            else
                echo ""
            fi
            ;;
        "alphanumeric")
            if [[ "$input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
                echo "$input"
            else
                echo ""
            fi
            ;;
        "url")
            if [[ "$input" =~ ^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$ ]]; then
                echo "$input"
            else
                echo ""
            fi
            ;;
        "path")
            # Allow only safe path characters
            if [[ "$input" =~ ^[a-zA-Z0-9/_.-]+$ ]]; then
                echo "$input"
            else
                echo ""
            fi
            ;;
        "boolean")
            case "${input,,}" in
                "true"|"false") echo "$input" ;;
                *) echo "" ;;
            esac
            ;;
        *)
            # Default safe alphanumeric with some symbols
            if [[ "$input" =~ ^[a-zA-Z0-9@._-]+$ ]]; then
                echo "$input"
            else
                echo ""
            fi
            ;;
    esac
}

# Function to prompt for input with default and validation
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local input_type="${4:-general}"
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo -n -e "${BLUE}${prompt} [${default}]: ${NC}"
        read -r input

        if [ -z "$input" ]; then
            export "$var_name"="$default"
            return 0
        else
            validated_input=$(validate_input "$input" "$input_type")
            if [ -n "$validated_input" ]; then
                export "$var_name"="$validated_input"
                return 0
            else
                echo -e "${RED}Invalid input for $input_type. Please try again (attempt $attempt/$max_attempts)${NC}"
                attempt=$((attempt + 1))
            fi
        fi
    done

    echo -e "${YELLOW}Max attempts reached, using default: $default${NC}"
    export "$var_name"="$default"
}

echo -e "${YELLOW}Setting up environment configuration...${NC}"

# Check if .env already exists
EXISTING_CONFIG=false
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Found existing $ENV_FILE${NC}"
    echo -n -e "${BLUE}Do you want to (u)pdate, (r)ecreate, or (k)eep existing? (u/r/k) [u]: ${NC}"
    read -r action

    case "${action:-u}" in
        k|K)
            echo -e "${GREEN}Keeping existing configuration${NC}"
            EXISTING_CONFIG=true
            ;;
        r|R)
            echo -e "${YELLOW}Will recreate configuration with new keys${NC}"
            ;;
        u|U|*)
            echo -e "${BLUE}Will update configuration, preserving existing keys${NC}"
            EXISTING_CONFIG=true
            ;;
    esac
fi

# Load existing configuration if updating
if [ "$EXISTING_CONFIG" = true ] && [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}Loading existing configuration...${NC}"

    # Validate .env file before sourcing
    if [ -r "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
        # Check for suspicious content before sourcing
        if ! grep -q '[;&|$`]' "$ENV_FILE" && ! grep -q '$(\|`\|\\x' "$ENV_FILE"; then
            # Source existing values safely
            set -a  # automatically export all variables
            source "$ENV_FILE" 2>/dev/null || {
                echo -e "${RED}Error: Could not load existing configuration${NC}"
                EXISTING_CONFIG=false
            }
            set +a  # disable automatic export
            echo -e "${GREEN}✓ Loaded existing configuration${NC}"
        else
            echo -e "${RED}Warning: .env file contains potentially unsafe content, skipping load${NC}"
            EXISTING_CONFIG=false
        fi
    else
        echo -e "${RED}Warning: .env file is not readable or empty${NC}"
        EXISTING_CONFIG=false
    fi
fi

echo -e "${BLUE}Configuring application settings...${NC}"

# Generate or preserve secret key
if [ "$EXISTING_CONFIG" = true ] && [ -n "$SECRET_KEY" ]; then
    echo -e "${GREEN}✓ Using existing SECRET_KEY${NC}"
else
    SECRET_KEY=$(generate_secret)
    echo -e "${GREEN}✓ Generated new SECRET_KEY${NC}"
fi

# Database configuration
prompt_with_default "Database name" "${POSTGRES_DB:-artifactor_v3}" "POSTGRES_DB" "alphanumeric"
prompt_with_default "Database user" "${POSTGRES_USER:-artifactor_user}" "POSTGRES_USER" "alphanumeric"

# Generate or preserve database password
if [ "$EXISTING_CONFIG" = true ] && [ -n "$POSTGRES_PASSWORD" ]; then
    echo -e "${GREEN}✓ Using existing database password${NC}"
else
    echo -e "${BLUE}Generating secure database password...${NC}"
    POSTGRES_PASSWORD=$(generate_secret | head -c 16)
    echo -e "${GREEN}✓ Generated new database password${NC}"
fi

# Database URL
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"

# Redis configuration
prompt_with_default "Redis URL" "${REDIS_URL:-redis://redis:6379}" "REDIS_URL" "url"

# Environment mode
current_env="${ENVIRONMENT:-development}"
echo -n -e "${BLUE}Environment mode (development/production) [${current_env}]: ${NC}"
read -r env_mode
if [ -z "$env_mode" ]; then
    env_mode="$current_env"
fi

if [ "$env_mode" = "production" ]; then
    DEBUG="false"
else
    DEBUG="true"
fi

# API Configuration
prompt_with_default "API Host" "${API_HOST:-0.0.0.0}" "API_HOST" "general"
prompt_with_default "API Port" "${API_PORT:-8000}" "API_PORT" "port"

# Frontend Configuration
prompt_with_default "Frontend Port" "${FRONTEND_PORT:-3000}" "FRONTEND_PORT" "port"
API_URL="http://localhost:${API_PORT}/api"
WS_URL="ws://localhost:${API_PORT}/ws"

# CORS Configuration
if [ "$env_mode" = "production" ]; then
    prompt_with_default "CORS Origins (comma-separated)" "${CORS_ORIGINS:-https://yourdomain.com}" "CORS_ORIGINS" "url"
else
    CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}"
fi

# Security Configuration
prompt_with_default "JWT Token Expiry (minutes)" "${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-15}" "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" "port"
prompt_with_default "JWT Refresh Token Expiry (days)" "${JWT_REFRESH_TOKEN_EXPIRE_DAYS:-7}" "JWT_REFRESH_TOKEN_EXPIRE_DAYS" "port"

# File Upload Configuration
prompt_with_default "Max Upload Size (MB)" "${MAX_UPLOAD_SIZE_MB:-50}" "MAX_UPLOAD_SIZE_MB" "port"
prompt_with_default "Upload Directory" "${UPLOAD_DIR:-./uploads}" "UPLOAD_DIR" "path"

# Agent Configuration
prompt_with_default "Enable Agent Coordination" "${AGENT_COORDINATION_ENABLED:-true}" "AGENT_COORDINATION_ENABLED" "boolean"
prompt_with_default "V2 Compatibility Mode" "${V2_COMPATIBILITY:-true}" "V2_COMPATIBILITY" "boolean"

# Logging Configuration
if [ "$env_mode" = "production" ]; then
    LOG_LEVEL="INFO"
else
    LOG_LEVEL="DEBUG"
fi

echo
echo -e "${YELLOW}Creating environment files...${NC}"

# Create .env file
cat > "$ENV_FILE" << EOF
# ARTIFACTOR v3.0.0 Environment Configuration
# Generated on $(date)

# Application
SECRET_KEY=${SECRET_KEY}
DEBUG=${DEBUG}
ENVIRONMENT=${env_mode}
LOG_LEVEL=${LOG_LEVEL}

# Database
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=${DATABASE_URL}

# Redis
REDIS_URL=${REDIS_URL}

# API Configuration
API_HOST=${API_HOST}
API_PORT=${API_PORT}

# Frontend Configuration
FRONTEND_PORT=${FRONTEND_PORT}
REACT_APP_API_URL=${API_URL}
REACT_APP_WS_URL=${WS_URL}

# CORS
CORS_ORIGINS=${CORS_ORIGINS}

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES}
JWT_REFRESH_TOKEN_EXPIRE_DAYS=${JWT_REFRESH_TOKEN_EXPIRE_DAYS}

# File Upload
MAX_UPLOAD_SIZE_MB=${MAX_UPLOAD_SIZE_MB}
UPLOAD_DIR=${UPLOAD_DIR}

# Agent Configuration
AGENT_COORDINATION_ENABLED=${AGENT_COORDINATION_ENABLED}
V2_COMPATIBILITY=${V2_COMPATIBILITY}

# Docker Network
COMPOSE_PROJECT_NAME=artifactor
EOF

# Create .env.example file
cat > "$ENV_EXAMPLE_FILE" << EOF
# ARTIFACTOR v3.0.0 Environment Configuration Template
# Copy this file to .env and configure your values

# Application
SECRET_KEY=your-secret-key-here
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Database
POSTGRES_DB=artifactor_v3
POSTGRES_USER=artifactor_user
POSTGRES_PASSWORD=your-database-password
DATABASE_URL=postgresql://user:password@postgres:5432/database

# Redis
REDIS_URL=redis://redis:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# File Upload
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=./uploads

# Agent Configuration
AGENT_COORDINATION_ENABLED=true
V2_COMPATIBILITY=true

# Docker Network
COMPOSE_PROJECT_NAME=artifactor
EOF

# Make files read-only for security
chmod 600 "$ENV_FILE"
chmod 644 "$ENV_EXAMPLE_FILE"

echo -e "${GREEN}✓ Created $ENV_FILE${NC}"
echo -e "${GREEN}✓ Created $ENV_EXAMPLE_FILE${NC}"

# Create docker-compose override for local development
if [ "$env_mode" = "development" ]; then
    cat > "docker-compose.override.yml" << EOF
# Development overrides for docker-compose
services:
  backend:
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - FAST_REFRESH=true
      - GENERATE_SOURCEMAP=true
EOF
    echo -e "${GREEN}✓ Created docker-compose.override.yml for development${NC}"
fi

echo
echo -e "${GREEN}🎉 Environment setup complete!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review your .env file: cat .env"
echo "2. Start the services: docker-compose up -d"
echo "3. Check service status: docker-compose ps"
echo
echo -e "${YELLOW}Important Security Notes:${NC}"
echo "• Never commit .env to version control"
echo "• Use strong passwords in production"
echo "• Regularly rotate your SECRET_KEY"
echo "• Review CORS settings for production"
echo
echo -e "${BLUE}Configuration Summary:${NC}"
echo "• Environment: $env_mode"
echo "• Database: $POSTGRES_DB"
echo "• API: http://localhost:$API_PORT"
echo "• Frontend: http://localhost:$FRONTEND_PORT"
if [ "$EXISTING_CONFIG" = true ]; then
    echo "• Credentials: Preserved existing"
else
    echo "• Secret Key: Generated (64 chars)"
    echo "• Database Password: Generated (16 chars)"
fi

# Ask about launching Docker
echo
echo -n -e "${BLUE}Do you want to start the Docker services now? (Y/n): ${NC}"
read -r start_docker

if [[ "${start_docker:-y}" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Starting Docker services...${NC}"

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi

    # Validate docker-compose.yml exists and is readable
    if [ ! -f "docker-compose.yml" ] || [ ! -r "docker-compose.yml" ]; then
        echo -e "${RED}Error: docker-compose.yml not found or not readable${NC}"
        exit 1
    fi

    # Start services
    echo -e "${BLUE}Running: docker-compose up -d${NC}"
    if timeout 300 docker-compose up -d; then
        echo -e "${GREEN}✅ Docker services started successfully!${NC}"

        # Wait a moment for services to initialize
        echo -e "${BLUE}Waiting for services to initialize...${NC}"
        sleep 5

        # Check service status
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps

        echo
        echo -e "${GREEN}🎉 ARTIFACTOR is now running!${NC}"
        echo -e "${BLUE}Access your application:${NC}"
        echo "• Frontend: http://localhost:$FRONTEND_PORT"
        echo "• API: http://localhost:$API_PORT"
        echo "• API Docs: http://localhost:$API_PORT/docs"

        # Check if services are healthy
        echo -e "${BLUE}Health check in 30 seconds...${NC}"
        sleep 30

        if curl -s http://localhost:$API_PORT/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API is responding${NC}"
        else
            echo -e "${YELLOW}⚠️  API not yet ready (may need more time)${NC}"
        fi

        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is responding${NC}"
        else
            echo -e "${YELLOW}⚠️  Frontend not yet ready (may need more time)${NC}"
        fi

    else
        echo -e "${RED}❌ Failed to start Docker services${NC}"
        echo -e "${YELLOW}Try manually: docker-compose up -d${NC}"
        echo -e "${YELLOW}Check logs: docker-compose logs${NC}"
    fi
else
    echo -e "${BLUE}Services not started. Run manually when ready:${NC}"
    echo "  docker-compose up -d"
fi

if [ "$env_mode" = "production" ]; then
    echo
    echo -e "${RED}⚠️  PRODUCTION DEPLOYMENT CHECKLIST:${NC}"
    echo "□ Review all environment variables"
    echo "□ Configure SSL/TLS certificates"
    echo "□ Set up proper backup procedures"
    echo "□ Configure monitoring and alerting"
    echo "□ Review security settings"
    echo "□ Test database connections"
    echo "□ Verify CORS configuration"
fi