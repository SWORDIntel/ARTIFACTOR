# React Frontend Dockerfile for ARTIFACTOR v3.0
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies and curl for health checks
RUN apk add --no-cache curl && \
    npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY . .

# Create non-root user with proper permissions
RUN addgroup -g 1001 -S nodejs && \
    adduser -S reactuser -u 1001 -G nodejs && \
    chown -R reactuser:nodejs /app && \
    chmod -R 755 /app

# Switch to non-root user
USER reactuser

# Expose port
EXPOSE 3000

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Development command (override for production)
CMD ["npm", "start"]