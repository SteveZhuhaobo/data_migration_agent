# Environment Variables Reference

This document provides a comprehensive reference for all environment variables supported by the Databricks MCP Server.

## Overview

Environment variables provide the highest precedence configuration method and are recommended for:
- Secure credential management
- CI/CD pipelines
- Docker/container deployments
- Production environments

## Required Environment Variables

These variables must be set for the server to function:

### `DATABRICKS_SERVER_HOSTNAME`
- **Description**: Your Databricks workspace hostname
- **Format**: Hostname without protocol (no `https://`)
- **Example**: `my-company.cloud.databricks.com`
- **Required**: Yes

### `DATABRICKS_HTTP_PATH`
- **Description**: HTTP path for your SQL warehouse or cluster
- **Format**: Must start with `/`
- **Examples**:
  - SQL Warehouse: `/sql/1.0/warehouses/abc123def456`
  - Cluster: `/sql/protocolv1/o/1234567890123456/0123-456789-abc123`
- **Required**: Yes

### `DATABRICKS_ACCESS_TOKEN`
- **Description**: Personal access token for authentication
- **Format**: String token (usually starts with `dapi`)
- **Example**: `dapi1234567890abcdef1234567890abcdef`
- **Required**: Yes
- **Security Note**: Keep this secret and rotate regularly

## Optional Environment Variables

These variables have default values and can be omitted:

### `DATABRICKS_CATALOG`
- **Description**: Default catalog to use for operations
- **Default**: `hive_metastore`
- **Examples**: `main`, `samples`, `dev_catalog`
- **Required**: No

### `DATABRICKS_SCHEMA`
- **Description**: Default schema/database to use for operations
- **Default**: `default`
- **Examples**: `information_schema`, `analytics`, `staging`
- **Required**: No

### `DATABRICKS_TIMEOUT`
- **Description**: Connection timeout in seconds
- **Default**: `120`
- **Format**: Positive integer
- **Examples**: `60`, `300`, `600`
- **Required**: No

### `DATABRICKS_MCP_LOG_LEVEL`
- **Description**: Logging level for the MCP server
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Required**: No

## Configuration Examples

### Basic Setup (Minimum Required)
```bash
export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123def456"
export DATABRICKS_ACCESS_TOKEN="dapi1234567890abcdef"
```

### Complete Setup (All Options)
```bash
# Required
export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123def456"
export DATABRICKS_ACCESS_TOKEN="dapi1234567890abcdef"

# Optional
export DATABRICKS_CATALOG="main"
export DATABRICKS_SCHEMA="analytics"
export DATABRICKS_TIMEOUT="300"
export DATABRICKS_MCP_LOG_LEVEL="DEBUG"
```

### Development Environment
```bash
export DATABRICKS_SERVER_HOSTNAME="dev-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/dev-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="dev-token-here"
export DATABRICKS_CATALOG="dev_catalog"
export DATABRICKS_SCHEMA="sandbox"
export DATABRICKS_TIMEOUT="300"
export DATABRICKS_MCP_LOG_LEVEL="DEBUG"
```

### Production Environment
```bash
export DATABRICKS_SERVER_HOSTNAME="prod-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/prod-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="prod-token-here"
export DATABRICKS_CATALOG="main"
export DATABRICKS_SCHEMA="production"
export DATABRICKS_TIMEOUT="120"
export DATABRICKS_MCP_LOG_LEVEL="WARNING"
```

## Platform-Specific Setup

### Linux/macOS (Bash/Zsh)
```bash
# Set for current session
export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"

# Add to shell profile for persistence
echo 'export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"' >> ~/.bashrc
echo 'export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"' >> ~/.bashrc
echo 'export DATABRICKS_ACCESS_TOKEN="your-token-here"' >> ~/.bashrc

# Reload shell configuration
source ~/.bashrc
```

### Windows (PowerShell)
```powershell
# Set for current session
$env:DATABRICKS_SERVER_HOSTNAME = "my-workspace.cloud.databricks.com"

# Set permanently for user
[Environment]::SetEnvironmentVariable("DATABRICKS_SERVER_HOSTNAME", "my-workspace.cloud.databricks.com", "User")
[Environment]::SetEnvironmentVariable("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc123", "User")
[Environment]::SetEnvironmentVariable("DATABRICKS_ACCESS_TOKEN", "your-token-here", "User")
```

### Windows (Command Prompt)
```cmd
# Set for current session
set DATABRICKS_SERVER_HOSTNAME=my-workspace.cloud.databricks.com

# Set permanently
setx DATABRICKS_SERVER_HOSTNAME "my-workspace.cloud.databricks.com"
setx DATABRICKS_HTTP_PATH "/sql/1.0/warehouses/abc123"
setx DATABRICKS_ACCESS_TOKEN "your-token-here"
```

## Docker/Container Usage

### Docker Run
```bash
docker run -e DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com" \
           -e DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123" \
           -e DATABRICKS_ACCESS_TOKEN="your-token-here" \
           databricks-mcp-server
```

### Docker Compose
```yaml
version: '3.8'
services:
  databricks-mcp:
    image: databricks-mcp-server
    environment:
      - DATABRICKS_SERVER_HOSTNAME=my-workspace.cloud.databricks.com
      - DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
      - DATABRICKS_ACCESS_TOKEN=your-token-here
      - DATABRICKS_CATALOG=main
      - DATABRICKS_SCHEMA=analytics
      - DATABRICKS_MCP_LOG_LEVEL=INFO
```

### Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: databricks-credentials
type: Opaque
stringData:
  server-hostname: "my-workspace.cloud.databricks.com"
  http-path: "/sql/1.0/warehouses/abc123"
  access-token: "your-token-here"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: databricks-mcp-server
spec:
  template:
    spec:
      containers:
      - name: databricks-mcp
        image: databricks-mcp-server
        env:
        - name: DATABRICKS_SERVER_HOSTNAME
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: server-hostname
        - name: DATABRICKS_HTTP_PATH
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: http-path
        - name: DATABRICKS_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: databricks-credentials
              key: access-token
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Test Databricks MCP Server
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Databricks MCP Server
      env:
        DATABRICKS_SERVER_HOSTNAME: ${{ secrets.DATABRICKS_SERVER_HOSTNAME }}
        DATABRICKS_HTTP_PATH: ${{ secrets.DATABRICKS_HTTP_PATH }}
        DATABRICKS_ACCESS_TOKEN: ${{ secrets.DATABRICKS_ACCESS_TOKEN }}
      run: |
        uvx databricks-mcp-server --version
```

### GitLab CI
```yaml
test_databricks_mcp:
  script:
    - export DATABRICKS_SERVER_HOSTNAME="$DATABRICKS_SERVER_HOSTNAME"
    - export DATABRICKS_HTTP_PATH="$DATABRICKS_HTTP_PATH"
    - export DATABRICKS_ACCESS_TOKEN="$DATABRICKS_ACCESS_TOKEN"
    - uvx databricks-mcp-server --version
  variables:
    DATABRICKS_SERVER_HOSTNAME: $DATABRICKS_SERVER_HOSTNAME
    DATABRICKS_HTTP_PATH: $DATABRICKS_HTTP_PATH
    DATABRICKS_ACCESS_TOKEN: $DATABRICKS_ACCESS_TOKEN
```

## Security Considerations

### Best Practices
1. **Never hardcode tokens**: Always use environment variables or secure secret management
2. **Use secret management**: Store tokens in CI/CD secret stores, not in code
3. **Rotate regularly**: Change access tokens periodically
4. **Minimal permissions**: Use tokens with only required permissions
5. **Audit access**: Monitor token usage in Databricks audit logs

### Secret Management Tools
- **AWS**: AWS Secrets Manager, Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Secret Manager
- **HashiCorp**: Vault
- **Kubernetes**: Secrets, External Secrets Operator

### Environment File Security
If using `.env` files:
```bash
# Create .env file with restricted permissions
touch .env
chmod 600 .env

# Add to .gitignore
echo ".env" >> .gitignore

# Load environment variables
set -a
source .env
set +a
```

## Validation and Testing

### Check Environment Variables
```bash
# Check if variables are set
echo "Hostname: $DATABRICKS_SERVER_HOSTNAME"
echo "HTTP Path: $DATABRICKS_HTTP_PATH"
echo "Token: ${DATABRICKS_ACCESS_TOKEN:0:10}..." # Show only first 10 chars

# Test configuration
databricks-mcp-server --log-level DEBUG
```

### Validation Script
```bash
#!/bin/bash
# validate-env.sh

required_vars=("DATABRICKS_SERVER_HOSTNAME" "DATABRICKS_HTTP_PATH" "DATABRICKS_ACCESS_TOKEN")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "Error: Missing required environment variables:"
    printf '  %s\n' "${missing_vars[@]}"
    exit 1
else
    echo "All required environment variables are set."
fi
```

## Troubleshooting

### Common Issues

**Variable not found**:
```bash
# Check if variable is set
env | grep DATABRICKS

# Check specific variable
echo $DATABRICKS_SERVER_HOSTNAME
```

**Variable not persisting**:
```bash
# Add to shell profile
echo 'export DATABRICKS_SERVER_HOSTNAME="value"' >> ~/.bashrc
source ~/.bashrc
```

**Special characters in values**:
```bash
# Use quotes for values with special characters
export DATABRICKS_ACCESS_TOKEN="dapi-abc123!@#$%"
```

**Windows path issues**:
```powershell
# Use forward slashes in HTTP paths
$env:DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/abc123"
```

For more troubleshooting help, see the main [README.md](README.md#troubleshooting) file.