# Multi-stage production Dockerfile for Etherscan API
# DOCKER-AGENT Implementation with Security Best Practices

# Stage 1: Builder
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim AS production

# Install runtime dependencies and security updates
RUN apt-get update && apt-get install -y \
    tini \
    curl \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r etherscan && \
    useradd -r -g etherscan -d /app -s /bin/bash etherscan

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application files with proper ownership
COPY --chown=etherscan:etherscan etherscan_connector.py .
COPY --chown=etherscan:etherscan api_server.py .
COPY --chown=etherscan:etherscan entrypoint.sh .
COPY --chown=etherscan:etherscan healthcheck.py .

# Create necessary directories with proper permissions
RUN mkdir -p logs data && \
    chown -R etherscan:etherscan /app && \
    chmod +x entrypoint.sh

# Switch to non-root user
USER etherscan

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run the application
CMD ["./entrypoint.sh"]