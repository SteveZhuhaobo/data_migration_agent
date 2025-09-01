# Design Document

## Overview

This design creates a containerized distribution system for three MCP servers (Snowflake, Databricks, and SQL Server) by packaging each into separate Docker containers. The solution provides isolated, deployable containers that can be published to container registries and easily deployed across different environments.

## Architecture

### High-Level Structure
```
containerized-mcp-servers/
├── snowflake-mcp/
│   ├── Dockerfile
│   ├── server.py (copied from Snowflake_MCP.py)
│   ├── requirements.txt
│   ├── config/
│   │   └── config.template.yaml
│   ├── docker-compose.yml
│   ├── build.sh
│   └── README.md
├── databricks-mcp/
│   ├── Dockerfile
│   ├── server.py (copied from Databricks_MCP.py)
│   ├── requirements.txt
│   ├── config/
│   │   └── config.template.yaml
│   ├── docker-compose.yml
│   ├── build.sh
│   └── README.md
├── sqlserver-mcp/
│   ├── Dockerfile
│   ├── server.py (copied from SQL_MCP.py)
│   ├── requirements.txt
│   ├── config/
│   │   └── config.template.yaml
│   ├── docker-compose.yml
│   ├── build.sh
│   └── README.md
└── scripts/
    ├── build-all.sh
    ├── publish-all.sh
    └── test-all.sh
```

### Container Design Principles

1. **Isolation**: Each MCP server runs in its own container with minimal dependencies
2. **Configuration**: Environment variable-based configuration with template files
3. **Security**: No hardcoded credentials, all sensitive data via environment variables
4. **Portability**: Containers work across different platforms (Linux, Windows, macOS)
5. **Optimization**: Multi-stage builds for smaller final images

## Components and Interfaces

### Base Container Configuration

Each container will use a Python 3.11 slim base image with the following structure:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose MCP port (stdio-based, no network port needed)
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import server; print('OK')" || exit 1

# Run the server
CMD ["python", "server.py"]
```

### Snowflake MCP Container

**Dependencies:**
- snowflake-connector-python>=3.6.0
- cryptography>=41.0.0
- mcp>=1.0.0
- pyyaml>=6.0.1

**Environment Variables:**
- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
- `SNOWFLAKE_USER`: Username
- `SNOWFLAKE_PASSWORD`: Password (optional if using key auth)
- `SNOWFLAKE_PRIVATE_KEY_PATH`: Path to private key file (optional)
- `SNOWFLAKE_DATABASE`: Default database
- `SNOWFLAKE_SCHEMA`: Default schema
- `SNOWFLAKE_WAREHOUSE`: Default warehouse
- `SNOWFLAKE_ROLE`: Default role

### Databricks MCP Container

**Dependencies:**
- databricks-sql-connector>=3.0.0
- requests>=2.31.0
- mcp>=1.0.0
- pyyaml>=6.0

**Environment Variables:**
- `DATABRICKS_SERVER_HOSTNAME`: Databricks workspace hostname
- `DATABRICKS_HTTP_PATH`: SQL warehouse HTTP path
- `DATABRICKS_ACCESS_TOKEN`: Personal access token
- `DATABRICKS_CATALOG`: Default catalog
- `DATABRICKS_SCHEMA`: Default schema

### SQL Server MCP Container

**Dependencies:**
- pyodbc
- mcp>=1.0.0
- pyyaml>=6.0

**Environment Variables:**
- `SQLSERVER_SERVER`: SQL Server hostname
- `SQLSERVER_DATABASE`: Database name
- `SQLSERVER_USERNAME`: Username (if not using Windows auth)
- `SQLSERVER_PASSWORD`: Password (if not using Windows auth)
- `SQLSERVER_USE_WINDOWS_AUTH`: Boolean for Windows authentication
- `SQLSERVER_DRIVER`: ODBC driver name
- `SQLSERVER_ENCRYPT`: Encryption setting
- `SQLSERVER_TRUST_CERTIFICATE`: Trust server certificate setting

## Data Models

### Configuration Template Structure

Each server will have a `config.template.yaml` file that shows the expected configuration structure:

```yaml
# Snowflake Template
snowflake:
  account: "${SNOWFLAKE_ACCOUNT}"
  user: "${SNOWFLAKE_USER}"
  password: "${SNOWFLAKE_PASSWORD}"
  database: "${SNOWFLAKE_DATABASE:-}"
  schema: "${SNOWFLAKE_SCHEMA:-default}"
  warehouse: "${SNOWFLAKE_WAREHOUSE:-}"
  role: "${SNOWFLAKE_ROLE:-}"
  timeout: 120
  max_retries: 3
  retry_delay: 5
  pool_size: 5
  pool_timeout: 30
```

### Docker Compose Configuration

Each server will include a `docker-compose.yml` for easy local deployment:

```yaml
version: '3.8'
services:
  snowflake-mcp:
    build: .
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}
      - SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA}
      - SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
```

## Error Handling

### Configuration Validation
- Validate required environment variables at startup
- Provide clear error messages for missing or invalid configuration
- Support both environment variables and config file approaches

### Connection Management
- Implement retry logic for database connections
- Handle authentication failures gracefully
- Provide health checks for container orchestration

### Logging Strategy
- Structured logging with configurable levels
- Container-friendly logging (stdout/stderr)
- Include correlation IDs for request tracing

## Testing Strategy

### Unit Testing
- Test each MCP server's core functionality
- Mock database connections for isolated testing
- Validate configuration parsing and environment variable handling

### Integration Testing
- Test containers with real database connections
- Validate MCP protocol compliance
- Test container startup and health checks

### End-to-End Testing
- Test complete deployment scenarios
- Validate docker-compose configurations
- Test container registry publishing and pulling

### Testing Scripts
```bash
# Test individual containers
./scripts/test-snowflake.sh
./scripts/test-databricks.sh
./scripts/test-sqlserver.sh

# Test all containers
./scripts/test-all.sh
```

## Build and Deployment Strategy

### Multi-Stage Builds
Use multi-stage Docker builds to optimize image size:
1. **Build stage**: Install build dependencies and compile packages
2. **Runtime stage**: Copy only necessary files and runtime dependencies

### Tagging Strategy
- `latest`: Latest stable version
- `v1.0.0`: Semantic versioning for releases
- `dev`: Development builds
- `{server}-latest`: Server-specific latest tags

### Registry Support
Support publishing to multiple registries:
- GitHub Container Registry (ghcr.io)
- Docker Hub
- Azure Container Registry
- Private registries

### Build Scripts
```bash
# Build individual containers
./snowflake-mcp/build.sh
./databricks-mcp/build.sh
./sqlserver-mcp/build.sh

# Build all containers
./scripts/build-all.sh

# Publish to registries
./scripts/publish-all.sh --registry ghcr.io --tag v1.0.0
```

## Security Considerations

### Secrets Management
- No hardcoded credentials in images
- Support for Docker secrets
- Environment variable validation
- Optional integration with secret management systems

### Container Security
- Run as non-root user
- Minimal base image (Python slim)
- Regular security updates
- Vulnerability scanning in CI/CD

### Network Security
- No unnecessary network ports exposed
- Support for network policies
- TLS/SSL configuration for database connections

## Documentation Strategy

### README Structure
Each container will include comprehensive documentation:
1. **Quick Start**: Basic usage with docker run
2. **Configuration**: All environment variables and options
3. **Examples**: Common deployment scenarios
4. **Troubleshooting**: Common issues and solutions
5. **Development**: How to build and modify

### Usage Examples
```bash
# Quick start with Snowflake MCP
docker run -e SNOWFLAKE_ACCOUNT=myaccount \
           -e SNOWFLAKE_USER=myuser \
           -e SNOWFLAKE_PASSWORD=mypass \
           ghcr.io/username/snowflake-mcp:latest

# Using docker-compose
cd snowflake-mcp
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

## Monitoring and Observability

### Health Checks
- Container health checks for orchestration
- MCP server responsiveness checks
- Database connection validation

### Metrics Collection
- Optional Prometheus metrics endpoint
- Container resource usage monitoring
- Database connection pool metrics

### Logging Integration
- Structured JSON logging
- Log aggregation compatibility (ELK, Fluentd)
- Configurable log levels