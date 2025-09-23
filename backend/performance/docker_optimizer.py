"""
Docker Performance Optimizer
Multi-stage builds, layer optimization, and container resource management
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DockerOptimizationConfig:
    """Docker optimization configuration"""
    enable_multi_stage: bool = True
    use_alpine_base: bool = True
    optimize_layers: bool = True
    enable_build_cache: bool = True
    compress_images: bool = True
    remove_build_tools: bool = True
    optimize_python_packages: bool = True

class DockerOptimizer:
    """Docker performance and size optimizer"""

    def __init__(self, config: DockerOptimizationConfig = None):
        self.config = config or DockerOptimizationConfig()

    def generate_optimized_backend_dockerfile(self) -> str:
        """Generate optimized backend Dockerfile with multi-stage build"""
        dockerfile_content = '''# FastAPI Backend Dockerfile for ARTIFACTOR v3.0 - Performance Optimized
# Multi-stage build for minimal production image

# Build stage
FROM python:3.11-alpine as builder

# Install build dependencies
RUN apk add --no-cache \\
    gcc \\
    musl-dev \\
    libffi-dev \\
    postgresql-dev \\
    python3-dev \\
    build-base \\
    curl-dev

# Set build environment variables
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-alpine as production

# Install runtime dependencies only
RUN apk add --no-cache \\
    libpq \\
    curl \\
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONPATH=/app \\
    PORT=8000

# Create non-root user
RUN addgroup -g 1000 appgroup && \\
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Set working directory
WORKDIR /app

# Create required directories with proper permissions
RUN mkdir -p uploads logs && \\
    chown -R appuser:appgroup /app

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check with optimized frequency
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production command with optimizations
CMD ["gunicorn", "main:app", \\
     "--worker-class", "uvicorn.workers.UvicornWorker", \\
     "--workers", "4", \\
     "--worker-connections", "1000", \\
     "--max-requests", "1000", \\
     "--max-requests-jitter", "100", \\
     "--timeout", "30", \\
     "--keepalive", "5", \\
     "--bind", "0.0.0.0:8000", \\
     "--log-level", "info", \\
     "--access-logfile", "-", \\
     "--error-logfile", "-"]
'''
        return dockerfile_content

    def generate_optimized_frontend_dockerfile(self) -> str:
        """Generate optimized frontend Dockerfile with multi-stage build"""
        dockerfile_content = '''# React Frontend Dockerfile for ARTIFACTOR v3.0 - Performance Optimized
# Multi-stage build for minimal production image

# Build stage
FROM node:18-alpine as builder

# Set build environment variables
ENV NODE_ENV=production \\
    NPM_CONFIG_LOGLEVEL=warn \\
    NPM_CONFIG_PRODUCTION=false

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with optimizations
RUN npm ci --only=production --silent && \\
    npm cache clean --force

# Copy source code
COPY . .

# Build application with optimizations
ENV GENERATE_SOURCEMAP=false \\
    INLINE_RUNTIME_CHUNK=false \\
    IMAGE_INLINE_SIZE_LIMIT=0

RUN npm run build

# Production stage
FROM nginx:alpine as production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy optimized nginx configuration
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 101 -S nginx && \\
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \\
    chown -R nginx:nginx /var/cache/nginx && \\
    chmod -R 755 /usr/share/nginx/html

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/ || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
'''
        return dockerfile_content

    def generate_optimized_compose(self) -> str:
        """Generate optimized Docker Compose configuration"""
        compose_content = '''version: '3.8'

# ARTIFACTOR v3.0 - Performance Optimized Docker Compose

services:
  # PostgreSQL Database - Performance Optimized
  postgres:
    image: postgres:15-alpine
    container_name: artifactor_postgres_optimized
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-artifactor_v3}
      POSTGRES_USER: ${POSTGRES_USER:-artifactor}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-artifactor}
      POSTGRES_INITDB_ARGS: "--data-checksums --encoding=UTF8 --locale=C"
      # Performance tuning
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
      POSTGRES_WORK_MEM: 16MB
      POSTGRES_MAINTENANCE_WORK_MEM: 256MB
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: "0.9"
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_DEFAULT_STATISTICS_TARGET: 100
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init/postgres:/docker-entrypoint-initdb.d
      - ./docker/postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5432:5432"
    networks:
      - artifactor_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U artifactor -d artifactor_v3"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    command: postgres -c config_file=/etc/postgresql/postgresql.conf

  # Redis Cache - Performance Optimized
  redis:
    image: redis:7-alpine
    container_name: artifactor_redis_optimized
    environment:
      # Redis performance tuning
      REDIS_MAXMEMORY: 512mb
      REDIS_MAXMEMORY_POLICY: allkeys-lru
      REDIS_SAVE: "900 1 300 10 60 10000"
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - artifactor_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 128M
          cpus: '0.1'
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "--latency-history", "-i", "1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # FastAPI Backend - Performance Optimized
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile.optimized
      cache_from:
        - artifactor_backend:latest
      target: production
    image: artifactor_backend:optimized
    container_name: artifactor_backend_optimized
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-artifactor}:${POSTGRES_PASSWORD:-artifactor}@postgres:5432/${POSTGRES_DB:-artifactor_v3}
      - REDIS_URL=redis://redis:6379
      - DEBUG=${DEBUG:-false}
      - SECRET_KEY=${SECRET_KEY}
      - WORKERS=4
      - WORKER_CONNECTIONS=1000
      - MAX_REQUESTS=1000
      - TIMEOUT=30
      - KEEP_ALIVE=5
    volumes:
      - upload_data:/app/uploads
      - logs_data:/app/logs
    ports:
      - "8000:8000"
    networks:
      - artifactor_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s

  # React Frontend - Performance Optimized
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile.optimized
      cache_from:
        - artifactor_frontend:latest
      target: production
    image: artifactor_frontend:optimized
    container_name: artifactor_frontend_optimized
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
      - REACT_APP_WS_URL=ws://localhost:8000/ws
      - NODE_ENV=production
    ports:
      - "3000:80"
    networks:
      - artifactor_network
    depends_on:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 64M
          cpus: '0.1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Nginx Reverse Proxy - Performance Optimized
  nginx:
    image: nginx:alpine
    container_name: artifactor_nginx_optimized
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - upload_data:/var/www/uploads:ro
      - logs_data:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - artifactor_network
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
        reservations:
          memory: 32M
          cpus: '0.05'
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 5s
      retries: 3
    profiles:
      - production

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
  upload_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/uploads
  logs_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/logs

networks:
  artifactor_network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: artifactor_opt
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
      com.docker.network.driver.mtu: 1500
    ipam:
      driver: default
      config:
        - subnet: 172.22.0.0/16
          gateway: 172.22.0.1
    internal: false
    attachable: false
'''
        return compose_content

    def generate_nginx_config(self) -> str:
        """Generate optimized Nginx configuration"""
        nginx_config = '''# Nginx Performance Optimized Configuration
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;

    # Buffer settings
    client_body_buffer_size 128k;
    client_max_body_size 100m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Caching
    open_file_cache max=10000 inactive=5m;
    open_file_cache_valid 2m;
    open_file_cache_min_uses 1;
    open_file_cache_errors on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream backend
    upstream backend {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Upstream frontend
    upstream frontend {
        least_conn;
        server frontend:80 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    include /etc/nginx/conf.d/*.conf;
}
'''
        return nginx_config

    def generate_nginx_site_config(self) -> str:
        """Generate optimized Nginx site configuration"""
        site_config = '''# ARTIFACTOR v3.0 - Performance Optimized Site Configuration
server {
    listen 80;
    server_name localhost;
    root /var/www/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # WebSocket endpoints
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket specific settings
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Auth endpoints with stricter rate limiting
    location /api/auth/ {
        limit_req zone=login burst=5 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files with caching
    location /static/ {
        alias /var/www/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";

        # Optimize static file serving
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }

    # Frontend application
    location / {
        try_files $uri $uri/ @frontend;

        # Cache static assets
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }

    # Frontend fallback
    location @frontend {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Caching for HTML
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Deny access to hidden files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
'''
        return site_config

    def generate_dockerignore(self) -> str:
        """Generate optimized .dockerignore file"""
        dockerignore_content = '''# Docker ignore file for ARTIFACTOR v3.0 - Performance Optimized

# Version control
.git
.gitignore
.gitattributes

# Documentation
*.md
docs/
README*

# Development files
.env.local
.env.development
.env.test
.vscode/
.idea/
*.log
*.pid

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Testing
.coverage
.pytest_cache/
.tox/
.nox/
htmlcov/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# Build artifacts
*.tar.gz
*.zip
*.rar
*.7z

# Temporary files
*.tmp
*.temp
.tmp/
.temp/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Docker
Dockerfile*
docker-compose*
.dockerignore
'''
        return dockerignore_content

    def write_optimized_files(self, output_dir: str = "./docker"):
        """Write all optimized Docker files to output directory"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Backend Dockerfile
        backend_dockerfile = output_path / "Dockerfile.backend.optimized"
        backend_dockerfile.write_text(self.generate_optimized_backend_dockerfile())

        # Frontend Dockerfile
        frontend_dockerfile = output_path / "Dockerfile.frontend.optimized"
        frontend_dockerfile.write_text(self.generate_optimized_frontend_dockerfile())

        # Docker Compose
        compose_file = output_path / "docker-compose.optimized.yml"
        compose_file.write_text(self.generate_optimized_compose())

        # Nginx configuration
        nginx_dir = output_path / "nginx"
        nginx_dir.mkdir(exist_ok=True)

        (nginx_dir / "nginx.conf").write_text(self.generate_nginx_config())
        (nginx_dir / "default.conf").write_text(self.generate_nginx_site_config())

        # Dockerignore
        dockerignore_file = output_path / ".dockerignore"
        dockerignore_file.write_text(self.generate_dockerignore())

        logger.info(f"Optimized Docker files written to {output_dir}")

    def generate_build_script(self) -> str:
        """Generate optimized build script"""
        script_content = '''#!/bin/bash
# ARTIFACTOR v3.0 - Optimized Docker Build Script

set -e

echo "🚀 Starting optimized Docker build for ARTIFACTOR v3.0..."

# Build arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Enable BuildKit for better performance
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build backend with optimizations
echo "📦 Building optimized backend image..."
docker build \\
    --file docker/Dockerfile.backend.optimized \\
    --target production \\
    --build-arg BUILD_DATE="$BUILD_DATE" \\
    --build-arg VCS_REF="$VCS_REF" \\
    --cache-from artifactor_backend:latest \\
    --tag artifactor_backend:optimized \\
    --tag artifactor_backend:latest \\
    backend/

# Build frontend with optimizations
echo "🎨 Building optimized frontend image..."
docker build \\
    --file docker/Dockerfile.frontend.optimized \\
    --target production \\
    --build-arg BUILD_DATE="$BUILD_DATE" \\
    --build-arg VCS_REF="$VCS_REF" \\
    --cache-from artifactor_frontend:latest \\
    --tag artifactor_frontend:optimized \\
    --tag artifactor_frontend:latest \\
    frontend/

# Display image sizes
echo "📊 Image sizes:"
docker images | grep artifactor | sort

# Optional: Run security scan
if command -v docker scan &> /dev/null; then
    echo "🔒 Running security scan..."
    docker scan artifactor_backend:optimized || true
    docker scan artifactor_frontend:optimized || true
fi

# Start optimized stack
echo "🏁 Starting optimized Docker stack..."
docker-compose -f docker/docker-compose.optimized.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout 120 bash -c 'until docker-compose -f docker/docker-compose.optimized.yml ps | grep -q "healthy"; do sleep 5; done'

echo "✅ ARTIFACTOR v3.0 optimized build complete!"
echo "🌐 Application available at: http://localhost"
echo "📊 API documentation: http://localhost/api/docs"
'''
        return script_content

# Global Docker optimizer instance
docker_optimizer = DockerOptimizer()