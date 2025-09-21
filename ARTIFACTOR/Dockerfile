# ARTIFACTOR - Claude.ai Artifact Downloader
# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --user requests

# Final stage
FROM python:3.11-slim

# Metadata
LABEL maintainer="ARTIFACTOR Team"
LABEL description="Simple Claude.ai artifact downloader with clipboard support"
LABEL version="1.0.0"

# Create non-root user for security
RUN groupadd -r artifactor && useradd -r -g artifactor artifactor

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Clipboard tools
    xclip \
    xsel \
    # Basic utilities
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /home/artifactor/.local

# Set up working directory
WORKDIR /app

# Copy application files
COPY simple-claude-downloader.py /app/
COPY docker-entrypoint.sh /app/

# Create downloads directory with proper permissions
RUN mkdir -p /app/downloads \
    && chown -R artifactor:artifactor /app \
    && chmod +x /app/docker-entrypoint.sh \
    && chmod +x /app/simple-claude-downloader.py

# Set up PATH for user packages
ENV PATH="/home/artifactor/.local/bin:${PATH}"
ENV PYTHONPATH="/home/artifactor/.local/lib/python3.11/site-packages"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; print('OK')" || exit 1

# Switch to non-root user
USER artifactor

# Volume for downloads
VOLUME ["/app/downloads"]

# Default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["--help"]