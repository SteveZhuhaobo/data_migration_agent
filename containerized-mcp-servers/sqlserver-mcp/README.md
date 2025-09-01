# SQL Server MCP Server

A containerized Model Context Protocol (MCP) server for SQL Server operations. This Docker container provides a complete MCP server that can connect to SQL Server and execute various database operations through the MCP protocol.

## Features

- **Complete SQL Server Integration**: Execute queries, manage tables, and perform database operations
- **Environment Variable Configuration**: Easy configuration through environment variables
- **Authentication Support**: Both SQL Server and Windows authentication
- **Connection Management**: Built-in connection handling and retry logic
- **Health Checks**: Container health monitoring and validation
- **Multi-platform Support**: Supports both AMD64 and ARM64 architectures
- **ODBC Driver Support**: Includes Microsoft ODBC Driver 17 for SQL Server

## Quick Start

### Using Docker Run

```bash
# Basic usage with SQL Server authentication
docker run -e SQLSERVER_SERVER=myserver.database.windows.net \
           -e SQLSERVER_DATABASE=mydatabase \
           -e SQLSERVER_USERNAME=myuser \
           -e SQLSERVER_PASSWORD=mypassword \
           sqlserver-mcp:latest
```

### Using Docker Compose

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your SQL Server credentials:
   ```bash
   # Edit .env with your settings
   nano .env
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SQLSERVER_SERVER` | SQL Server hostname or IP | `myserver.database.windows.net` |

#### Authentication Variables (choose one method)

**Method 1: SQL Server Authentication**
| Variable | Description | Example |
|----------|-------------|---------|
| `SQLSERVER_USERNAME` | SQL Server username | `sa` |
| `SQLSERVER_PASSWORD` | SQL Server password | `MyPassword123!` |

**Method 2: Windows Authentication**
| Variable | Description | Example |
|----------|-------------|---------|
| `SQLSERVER_USE_WINDOWS_AUTH` | Use Windows authentication | `true` |

#### Optional Connection Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SQLSERVER_DATABASE` | Default database | `master` | `MyDatabase` |
| `SQLSERVER_DRIVER` | ODBC driver name | `ODBC Driver 17 for SQL Server` | `ODBC Driver 18 for SQL Server` |
| `SQLSERVER_ENCRYPT` | Encrypt connection | `yes` | `no` |
| `SQLSERVER_TRUST_CERTIFICATE` | Trust server certificate | `yes` | `no` |

## Authentication Methods

### SQL Server Authentication

The most common authentication method using username and password:

```bash
docker run -e SQLSERVER_SERVER=myserver \
           -e SQLSERVER_DATABASE=mydatabase \
           -e SQLSERVER_USERNAME=myuser \
           -e SQLSERVER_PASSWORD=mypassword \
           sqlserver-mcp:latest
```

### Windows Authentication

For domain-joined environments (requires additional container configuration):

```bash
docker run -e SQLSERVER_SERVER=myserver \
           -e SQLSERVER_DATABASE=mydatabase \
           -e SQLSERVER_USE_WINDOWS_AUTH=true \
           sqlserver-mcp:latest
```

## Available MCP Tools

The server provides the following MCP tools:

### Connection Management
- `test_connection` - Test SQL Server connection and return basic database info

### Database Discovery
- `list_tables` - List all tables in the SQL Server database
- `get_table_schema` - Get detailed table schema information

### Table Operations
- `create_table` - Create a new table in SQL Server
- `insert_data` - Insert data into a SQL Server table

### Query Execution
- `execute_query` - Execute SQL queries with full result sets

## Building the Container

### Build Script

Use the provided build script for easy building:

```bash
# Build with default settings
./build.sh

# Build with specific tag
./build.sh v1.0.0

# Build with registry prefix
REGISTRY=ghcr.io/myorg ./build.sh v1.0.0

# Build and test
./build.sh --test

# Build without cache
./build.sh --no-cache
```

### Manual Build

```bash
# Build the image
docker build -t sqlserver-mcp:latest .

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t sqlserver-mcp:latest .
```

## Deployment Examples

### Docker Compose with Secrets

```yaml
version: '3.8'

services:
  sqlserver-mcp:
    image: sqlserver-mcp:latest
    environment:
      - SQLSERVER_SERVER=myserver.database.windows.net
      - SQLSERVER_DATABASE=mydatabase
      - SQLSERVER_USERNAME=myuser
    secrets:
      - sqlserver_password
    environment:
      - SQLSERVER_PASSWORD_FILE=/run/secrets/sqlserver_password

secrets:
  sqlserver_password:
    file: ./secrets/sqlserver_password.txt
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sqlserver-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sqlserver-mcp
  template:
    metadata:
      labels:
        app: sqlserver-mcp
    spec:
      containers:
      - name: sqlserver-mcp
        image: sqlserver-mcp:latest
        env:
        - name: SQLSERVER_SERVER
          value: "myserver.database.windows.net"
        - name: SQLSERVER_DATABASE
          value: "mydatabase"
        - name: SQLSERVER_USERNAME
          value: "myuser"
        - name: SQLSERVER_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sqlserver-secret
              key: password
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import server; print('OK')"
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import server; print('OK')"
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Cloud Container Services

#### AWS ECS Task Definition

```json
{
  "family": "sqlserver-mcp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "sqlserver-mcp",
      "image": "sqlserver-mcp:latest",
      "environment": [
        {"name": "SQLSERVER_SERVER", "value": "myserver.database.windows.net"},
        {"name": "SQLSERVER_DATABASE", "value": "mydatabase"},
        {"name": "SQLSERVER_USERNAME", "value": "myuser"}
      ],
      "secrets": [
        {
          "name": "SQLSERVER_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:sqlserver-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/sqlserver-mcp",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy sqlserver-mcp \
  --image=sqlserver-mcp:latest \
  --set-env-vars="SQLSERVER_SERVER=myserver,SQLSERVER_DATABASE=mydatabase,SQLSERVER_USERNAME=myuser" \
  --set-secrets="SQLSERVER_PASSWORD=sqlserver-password:latest" \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# Create container instance
az container create \
  --resource-group myResourceGroup \
  --name sqlserver-mcp \
  --image sqlserver-mcp:latest \
  --environment-variables \
    SQLSERVER_SERVER=myserver.database.windows.net \
    SQLSERVER_DATABASE=mydatabase \
    SQLSERVER_USERNAME=myuser \
  --secure-environment-variables \
    SQLSERVER_PASSWORD=mypassword \
  --cpu 0.5 \
  --memory 1
```

## Troubleshooting

### Common Issues

#### Connection Timeout
```
Error: Connection timeout
```
**Solution**: Check network connectivity and server availability:
```bash
# Test network connectivity
docker run --rm sqlserver-mcp:latest ping myserver.database.windows.net
```

#### Authentication Failed
```
Error: Login failed for user 'myuser'
```
**Solutions**:
1. Verify username and password
2. Check if user exists and has necessary permissions
3. Ensure SQL Server authentication is enabled
4. For Azure SQL Database, use the full username format: `user@servername`

#### Driver Not Found
```
Error: Data source name not found and no default driver specified
```
**Solutions**:
1. Verify ODBC driver is installed (should be included in container)
2. Check driver name in `SQLSERVER_DRIVER` environment variable
3. List available drivers:
   ```bash
   docker exec -it sqlserver-mcp-server odbcinst -q -d
   ```

#### SSL/TLS Issues
```
Error: SSL Provider: The certificate chain was issued by an authority that is not trusted
```
**Solutions**:
1. Set `SQLSERVER_TRUST_CERTIFICATE=yes`
2. Or disable encryption: `SQLSERVER_ENCRYPT=no`
3. For production, use proper SSL certificates

#### Container Won't Start
```
Error: SQLSERVER_SERVER environment variable is required
```
**Solution**: Ensure all required environment variables are set:
```bash
docker run -e SQLSERVER_SERVER=myserver \
           -e SQLSERVER_USERNAME=myuser \
           -e SQLSERVER_PASSWORD=mypassword \
           sqlserver-mcp:latest
```

### Health Check Failures

If health checks are failing:

1. Check container logs:
   ```bash
   docker logs sqlserver-mcp-server
   ```

2. Test the connection manually:
   ```bash
   docker exec -it sqlserver-mcp-server python -c "
   import server
   import asyncio
   result = asyncio.run(server.test_connection())
   print(result)
   "
   ```

3. Verify environment variables:
   ```bash
   docker exec -it sqlserver-mcp-server env | grep SQLSERVER
   ```

### Performance Tuning

For better performance with large datasets:

```bash
# Increase connection timeout
-e SQLSERVER_CONNECTION_TIMEOUT=60
```

### Logging

Enable detailed logging:

```bash
# Add to docker-compose.yml or docker run
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=DEBUG
```

View logs:
```bash
# Docker Compose
docker-compose logs -f sqlserver-mcp

# Docker run
docker logs -f sqlserver-mcp-server
```

## Security Considerations

### Secrets Management

1. **Never hardcode credentials** in Dockerfiles or compose files
2. **Use Docker secrets** or external secret management systems
3. **Use environment variables** for configuration
4. **Rotate credentials** regularly

### Network Security

1. **Use private networks** for container communication
2. **Limit container privileges** (runs as non-root user)
3. **Enable TLS** for SQL Server connections (enabled by default)
4. **Use firewall rules** to restrict access

### Container Security

1. **Regular updates**: Keep base images and dependencies updated
2. **Vulnerability scanning**: Scan images for security vulnerabilities
3. **Resource limits**: Set appropriate CPU and memory limits
4. **Read-only filesystem**: Mount application directories as read-only when possible

## Development

### Local Development

1. Clone the repository
2. Build the container:
   ```bash
   ./build.sh --test
   ```
3. Run with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   docker-compose up
   ```

### Testing

Run the test suite:
```bash
# Build and test
./build.sh --test

# Manual testing
docker run --rm -e SQLSERVER_SERVER=test sqlserver-mcp:latest python -c "import server; print('Tests passed')"
```

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review container logs for error messages
3. Verify your SQL Server connection settings
4. Ensure all required environment variables are set

## License

This project is licensed under the MIT License - see the LICENSE file for details.