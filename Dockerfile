# AEC Design Management RAG System - Dockerfile
# Multi-stage build for production deployment

# =============================================================================
# Stage 1: Base Image with Python and System Dependencies
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 aecuser && \
    mkdir -p /app && \
    chown -R aecuser:aecuser /app

WORKDIR /app

# =============================================================================
# Stage 2: Dependencies Installation
# =============================================================================
FROM base as dependencies

# Copy requirements
COPY --chown=aecuser:aecuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 3: Application
# =============================================================================
FROM dependencies as application

# Switch to non-root user
USER aecuser

# Copy application code
COPY --chown=aecuser:aecuser src/ ./src/
COPY --chown=aecuser:aecuser config/ ./config/
COPY --chown=aecuser:aecuser scripts/ ./scripts/
COPY --chown=aecuser:aecuser .env.example ./

# Create data directories
RUN mkdir -p ./data/{uploads,processed,cache,graphrag,chroma_db} ./logs

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command: Run FastAPI application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
