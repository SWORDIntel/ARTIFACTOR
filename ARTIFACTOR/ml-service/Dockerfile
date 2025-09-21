# ARTIFACTOR ML Service - Scikit-learn, Sentence Transformers, FAISS
# Optimized for machine learning workloads with GPU support

# =====================================
# BUILD STAGE
# =====================================
FROM python:3.11-slim as builder

# Set build arguments
ARG ENABLE_GPU=false
ARG CUDA_VERSION=11.8

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    curl \
    git \
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
COPY ml-service/requirements.txt /tmp/requirements.txt
COPY ml-service/requirements-gpu.txt /tmp/requirements-gpu.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt && \
    if [ "$ENABLE_GPU" = "true" ]; then \
        pip install -r /tmp/requirements-gpu.txt; \
    fi

# =====================================
# PRODUCTION STAGE
# =====================================
FROM python:3.11-slim as production

# Metadata
LABEL maintainer="ARTIFACTOR Team" \
      description="ARTIFACTOR v3.0 ML Service" \
      version="3.0.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    liblapack3 \
    libgomp1 \
    curl \
    ca-certificates \
    # For text processing
    pandoc \
    # For image processing
    libmagic1 \
    # For PDF processing
    poppler-utils \
    # For document parsing
    antiword \
    unrtf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r mluser && useradd -r -g mluser mluser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY ml-service/app /app/app
COPY ml-service/scripts /app/scripts
COPY ml-service/requirements.txt /app/

# Copy entrypoint scripts
RUN chmod +x /app/scripts/*.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/{models,search_index,logs,data,cache} && \
    chown -R mluser:mluser /app && \
    chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    TRANSFORMERS_CACHE=/app/cache/transformers \
    HF_HOME=/app/cache/huggingface \
    TORCH_HOME=/app/cache/torch

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Switch to non-root user
USER mluser

# Expose ports
EXPOSE 8001 9091

# Default command
CMD ["/app/scripts/start.sh"]

# =====================================
# GPU STAGE (Optional)
# =====================================
FROM nvidia/cuda:11.8-runtime-ubuntu20.04 as gpu

# Metadata
LABEL maintainer="ARTIFACTOR Team" \
      description="ARTIFACTOR v3.0 ML Service (GPU)" \
      version="3.0.0"

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libcublas11 \
    libcurand10 \
    libcusparse11 \
    libcusolver11 \
    curl \
    ca-certificates \
    pandoc \
    libmagic1 \
    poppler-utils \
    antiword \
    unrtf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create symbolic link for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Create non-root user
RUN groupadd -r mluser && useradd -r -g mluser mluser

# Set working directory
WORKDIR /app

# Copy application code
COPY ml-service/app /app/app
COPY ml-service/scripts /app/scripts
COPY ml-service/requirements.txt /app/
COPY ml-service/requirements-gpu.txt /app/

# Install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r requirements.txt && \
    python -m pip install -r requirements-gpu.txt

# Copy entrypoint scripts
RUN chmod +x /app/scripts/*.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/{models,search_index,logs,data,cache} && \
    chown -R mluser:mluser /app && \
    chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/app/cache/transformers \
    HF_HOME=/app/cache/huggingface \
    TORCH_HOME=/app/cache/torch \
    CUDA_VISIBLE_DEVICES=0 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Switch to non-root user
USER mluser

# Expose ports
EXPOSE 8001 9091

# Default command
CMD ["/app/scripts/start.sh"]