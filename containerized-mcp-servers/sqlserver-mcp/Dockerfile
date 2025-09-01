# Multi-stage build for SQL Server MCP Server
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    gnupg2 \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies including ODBC driver
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    ca-certificates \
    lsb-release \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
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
COPY test_startup.py .
COPY env_validator.py .
COPY health_check.py .
COPY test_connection.py .
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
ENV SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server"
ENV SQLSERVER_SERVER=""
ENV SQLSERVER_DATABASE="master"
ENV SQLSERVER_USERNAME=""
ENV SQLSERVER_PASSWORD=""
ENV SQLSERVER_USE_WINDOWS_AUTH="false"
ENV SQLSERVER_ENCRYPT="yes"
ENV SQLSERVER_TRUST_CERTIFICATE="yes"

# Health check using the health check module
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python health_check.py || exit 1

# Expose port (though MCP uses stdio, this is for potential future HTTP support)
EXPOSE 8000

# Run the server with startup wrapper
CMD ["python", "startup.py"]