# LiteLLM Gateway Dockerfile
FROM python:3.11-slim

LABEL maintainer="InsightPulseAI Engineering <admin@insightpulseai.net>"
LABEL description="LiteLLM multi-model gateway for AI Workbench"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install LiteLLM
RUN pip install --no-cache-dir litellm[proxy]==1.50.0

# Create app directory
WORKDIR /app

# Copy configuration
COPY config.yaml /app/config.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 9090

# Run LiteLLM proxy
CMD ["litellm", "--config", "/app/config.yaml", "--port", "8080"]
