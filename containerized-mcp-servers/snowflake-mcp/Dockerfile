# Multi-stage build for Snowflake MCP Server
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY requirements-test.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user -r requirements-test.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local

# Copy application code
COPY server.py .
COPY startup.py .
COPY env_validator.py .
COPY health_check.py .
COPY config/ ./config/
COPY test_server.py .
COPY test_integration.py .

# Set ownership
RUN chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Add local Python packages to PATH
ENV PATH=/home/mcpuser/.local/bin:$PATH

# Environment variables for configuration
# Note: Sensitive values like SNOWFLAKE_PASSWORD should be set at runtime, not in the image
ENV SNOWFLAKE_ACCOUNT=""
ENV SNOWFLAKE_USER=""
ENV SNOWFLAKE_DATABASE=""
ENV SNOWFLAKE_SCHEMA="PUBLIC"
ENV SNOWFLAKE_WAREHOUSE=""
ENV SNOWFLAKE_ROLE=""
ENV SNOWFLAKE_TIMEOUT="120"
ENV SNOWFLAKE_MAX_RETRIES="3"
ENV SNOWFLAKE_RETRY_DELAY="5"
ENV SNOWFLAKE_POOL_SIZE="5"
ENV SNOWFLAKE_POOL_TIMEOUT="30"

# Health check using the health check module
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python health_check.py || exit 1

# Expose port (though MCP uses stdio, this is for potential future HTTP support)
EXPOSE 8000

# Run the server directly
CMD ["python", "server.py"]