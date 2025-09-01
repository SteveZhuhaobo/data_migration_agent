# Multi-stage build for SQL Server MCP Server
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    unixodbc-dev \
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

# Install runtime dependencies including ODBC driver
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local

# Copy application code
COPY server.py .
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
ENV SQLSERVER_DRIVER="ODBC Driver 17 for SQL Server"
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

# Run the server
CMD ["python", "server.py"]