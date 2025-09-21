# ARTIFACTOR Backend - FastAPI with PostgreSQL and Redis
# Multi-stage build for optimal image size and security

# =====================================
# BUILD STAGE
# =====================================
FROM python:3.11-slim as builder

# Set build arguments
ARG ENVIRONMENT=production

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/requirements-dev.txt /tmp/requirements-dev.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt && \
    if [ "$ENVIRONMENT" = "development" ]; then \
        pip install -r /tmp/requirements-dev.txt; \
    fi

# =====================================
# PRODUCTION STAGE
# =====================================
FROM python:3.11-slim as production

# Metadata
LABEL maintainer="ARTIFACTOR Team" \
      description="ARTIFACTOR v3.0 FastAPI Backend" \
      version="3.0.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    # Clipboard support
    xclip \
    xsel \
    # Image processing
    libmagic1 \
    # Text processing
    pandoc \
    # Archive support
    unzip \
    zip \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r artifactor && useradd -r -g artifactor artifactor

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/
COPY backend/pyproject.toml /app/
COPY simple-claude-downloader.py /app/legacy/

# Copy entrypoint and scripts
COPY backend/scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/{downloads,uploads,models,logs,config,search_index} && \
    chown -R artifactor:artifactor /app && \
    chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER artifactor

# Expose ports
EXPOSE 8000 9090

# Default command
CMD ["/app/scripts/start.sh"]

# =====================================
# DEVELOPMENT STAGE
# =====================================
FROM production as development

# Switch to root to install development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
COPY backend/requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install -r /tmp/requirements-dev.txt

# Install pre-commit hooks (optional)
RUN pip install pre-commit

# Switch back to non-root user
USER artifactor

# Override command for development
CMD ["/app/scripts/start-dev.sh"]