# ARTIFACTOR Frontend - React 18 with TypeScript and Material-UI
# Multi-stage build for optimal image size and performance

# =====================================
# BUILD STAGE
# =====================================
FROM node:18-alpine as builder

# Set build arguments
ARG REACT_APP_API_URL=http://localhost:8000
ARG REACT_APP_WS_URL=ws://localhost:8000
ARG REACT_APP_VERSION=3.0.0
ARG REACT_APP_ENVIRONMENT=production
ARG REACT_APP_GITHUB_CLIENT_ID
ARG REACT_APP_ENABLE_PWA=true
ARG REACT_APP_ENABLE_OFFLINE=true

# Set environment variables
ENV REACT_APP_API_URL=$REACT_APP_API_URL \
    REACT_APP_WS_URL=$REACT_APP_WS_URL \
    REACT_APP_VERSION=$REACT_APP_VERSION \
    REACT_APP_ENVIRONMENT=$REACT_APP_ENVIRONMENT \
    REACT_APP_GITHUB_CLIENT_ID=$REACT_APP_GITHUB_CLIENT_ID \
    REACT_APP_ENABLE_PWA=$REACT_APP_ENABLE_PWA \
    REACT_APP_ENABLE_OFFLINE=$REACT_APP_ENABLE_OFFLINE \
    NODE_ENV=production \
    GENERATE_SOURCEMAP=false \
    INLINE_RUNTIME_CHUNK=false

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    && npm install -g npm@latest

# Copy package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock* ./

# Install dependencies
RUN if [ -f yarn.lock ]; then \
        yarn install --frozen-lockfile --production=false; \
    else \
        npm ci --only=production=false; \
    fi

# Copy source code
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/tsconfig.json ./
COPY frontend/.env* ./

# Build application
RUN if [ -f yarn.lock ]; then \
        yarn build; \
    else \
        npm run build; \
    fi

# =====================================
# PRODUCTION STAGE
# =====================================
FROM nginx:1.25-alpine as production

# Metadata
LABEL maintainer="ARTIFACTOR Team" \
      description="ARTIFACTOR v3.0 React Frontend" \
      version="3.0.0"

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates \
    bash

# Copy built application from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/default.conf /etc/nginx/conf.d/default.conf

# Copy health check script
COPY frontend/scripts/healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

# Create nginx user and set permissions
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Create directories for runtime
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    chown -R nginx:nginx /var/cache/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# =====================================
# DEVELOPMENT STAGE
# =====================================
FROM node:18-alpine as development

# Install development dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock* ./

# Install all dependencies (including dev)
RUN if [ -f yarn.lock ]; then \
        yarn install; \
    else \
        npm install; \
    fi

# Copy source code
COPY frontend/ .

# Expose development port
EXPOSE 3000

# Start development server
CMD if [ -f yarn.lock ]; then \
        yarn start; \
    else \
        npm start; \
    fi