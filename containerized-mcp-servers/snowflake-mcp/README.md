# Snowflake MCP Server

A containerized Model Context Protocol (MCP) server for Snowflake operations. This Docker container provides a complete MCP server that can connect to Snowflake and execute various database operations through the MCP protocol.

## Features

- **Complete Snowflake Integration**: Execute queries, manage tables, and perform database operations
- **Environment Variable Configuration**: Easy configuration through environment variables
- **Authentication Support**: Both username/password and key pair authentication
- **Connection Management**: Built-in connection pooling and retry logic
- **Health Checks**: Container health monitoring and validation
- **Multi-platform Support**: Supports both AMD64 and ARM64 architectures

## Quick Start

### Using Docker Run

```bash
# Basic usage with username/password authentication
docker run -e SNOWFLAKE_ACCOUNT=myaccount.region \
           -e SNOWFLAKE_USER=myuser \
           -e SNOWFLAKE_PASSWORD=mypassword \
           -e SNOWFLAKE_DATABASE=mydatabase \
           -e SNOWFLAKE_SCHEMA=myschema \
           -e SNOWFLAKE_WAREHOUSE=mywarehouse \
           snowflake-mcp:latest
```

### Using Docker Compose

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your Snowflake credentials:
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
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier | `mycompany.us-east-1` |
| `SNOWFLAKE_USER` | Snowflake username | `john_doe` |

#### Authentication Variables (choose one method)

**Method 1: Username/Password**
| Variable | Description | Example |
|----------|-------------|---------|
| `SNOWFLAKE_PASSWORD` | Snowflake password | `mypassword123` |

**Method 2: Key Pair Authentication**
| Variable | Description | Example |
|----------|-------------|---------|
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to private key file | `/app/keys/snowflake_key.p8` |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Key passphrase (optional) | `mykeypassphrase` |

#### Optional Connection Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SNOWFLAKE_DATABASE` | Default database | None | `ANALYTICS_DB` |
| `SNOWFLAKE_SCHEMA` | Default schema | `PUBLIC` | `REPORTING` |
| `SNOWFLAKE_WAREHOUSE` | Default warehouse | None | `COMPUTE_WH` |
| `SNOWFLAKE_ROLE` | Default role | None | `ANALYST_ROLE` |

#### Connection Tuning Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SNOWFLAKE_TIMEOUT` | Query timeout (seconds) | `120` | `300` |
| `SNOWFLAKE_MAX_RETRIES` | Maximum retry attempts | `3` | `5` |
| `SNOWFLAKE_RETRY_DELAY` | Retry delay (seconds) | `5` | `10` |
| `SNOWFLAKE_POOL_SIZE` | Connection pool size | `5` | `10` |
| `SNOWFLAKE_POOL_TIMEOUT` | Pool timeout (seconds) | `30` | `60` |

## Authentication Methods

### Username/Password Authentication

The simplest authentication method using username and password:

```bash
docker run -e SNOWFLAKE_ACCOUNT=myaccount.region \
           -e SNOWFLAKE_USER=myuser \
           -e SNOWFLAKE_PASSWORD=mypassword \
           snowflake-mcp:latest
```

### Key Pair Authentication

For enhanced security, use key pair authentication:

1. Generate a private key:
   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt
   ```

2. Mount the key file and configure:
   ```bash
   docker run -v /path/to/keys:/app/keys:ro \
              -e SNOWFLAKE_ACCOUNT=myaccount.region \
              -e SNOWFLAKE_USER=myuser \
              -e SNOWFLAKE_PRIVATE_KEY_PATH=/app/keys/snowflake_key.p8 \
              snowflake-mcp:latest
   ```

## Available MCP Tools

The server provides the following MCP tools:

### Connection Management
- `ping` - Test server responsiveness
- `test_connection` - Test Snowflake connection and return basic info

### Database Discovery
- `list_databases` - List all accessible databases
- `list_schemas` - List schemas in a database
- `list_tables` - List tables in a schema
- `list_warehouses` - List available warehouses

### Table Operations
- `get_table_schema` - Get detailed table schema information
- `describe_table` - Get comprehensive table metadata
- `create_table` - Create a new table
- `insert_data` - Insert data into a table

### Query Execution
- `execute_query` - Execute SQL queries with full result sets

### Warehouse Management
- `get_warehouse_status` - Get warehouse status information
- `start_warehouse` - Start/resume a warehouse
- `stop_warehouse` - Suspend a warehouse

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
docker build -t snowflake-mcp:latest .

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t snowflake-mcp:latest .
```

## Deployment Examples

### Docker Compose with Secrets

```yaml
version: '3.8'

services:
  snowflake-mcp:
    image: snowflake-mcp:latest
    environment:
      - SNOWFLAKE_ACCOUNT=myaccount.region
      - SNOWFLAKE_USER=myuser
      - SNOWFLAKE_DATABASE=mydatabase
      - SNOWFLAKE_SCHEMA=myschema
      - SNOWFLAKE_WAREHOUSE=mywarehouse
    secrets:
      - snowflake_password
    environment:
      - SNOWFLAKE_PASSWORD_FILE=/run/secrets/snowflake_password

secrets:
  snowflake_password:
    file: ./secrets/snowflake_password.txt
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: snowflake-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: snowflake-mcp
  template:
    metadata:
      labels:
        app: snowflake-mcp
    spec:
      containers:
      - name: snowflake-mcp
        image: snowflake-mcp:latest
        env:
        - name: SNOWFLAKE_ACCOUNT
          value: "myaccount.region"
        - name: SNOWFLAKE_USER
          value: "myuser"
        - name: SNOWFLAKE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: snowflake-secret
              key: password
        - name: SNOWFLAKE_DATABASE
          value: "mydatabase"
        - name: SNOWFLAKE_WAREHOUSE
          value: "mywarehouse"
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
  "family": "snowflake-mcp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "snowflake-mcp",
      "image": "snowflake-mcp:latest",
      "environment": [
        {"name": "SNOWFLAKE_ACCOUNT", "value": "myaccount.region"},
        {"name": "SNOWFLAKE_USER", "value": "myuser"},
        {"name": "SNOWFLAKE_DATABASE", "value": "mydatabase"}
      ],
      "secrets": [
        {
          "name": "SNOWFLAKE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:snowflake-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/snowflake-mcp",
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
gcloud run deploy snowflake-mcp \
  --image=snowflake-mcp:latest \
  --set-env-vars="SNOWFLAKE_ACCOUNT=myaccount.region,SNOWFLAKE_USER=myuser,SNOWFLAKE_DATABASE=mydatabase" \
  --set-secrets="SNOWFLAKE_PASSWORD=snowflake-password:latest" \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# Create container instance
az container create \
  --resource-group myResourceGroup \
  --name snowflake-mcp \
  --image snowflake-mcp:latest \
  --environment-variables \
    SNOWFLAKE_ACCOUNT=myaccount.region \
    SNOWFLAKE_USER=myuser \
    SNOWFLAKE_DATABASE=mydatabase \
  --secure-environment-variables \
    SNOWFLAKE_PASSWORD=mypassword \
  --cpu 0.5 \
  --memory 1
```

## Troubleshooting

### Common Issues

#### Connection Timeout
```
Error: Connection timeout
```
**Solution**: Increase the timeout value:
```bash
-e SNOWFLAKE_TIMEOUT=300
```

#### Authentication Failed
```
Error: Authentication failed
```
**Solutions**:
1. Verify account identifier format: `account.region` or `account.region.snowflakecomputing.com`
2. Check username and password
3. Ensure user has necessary permissions
4. For key pair auth, verify key format and path

#### Database/Schema Not Found
```
Error: Database 'MYDB' does not exist or not authorized
```
**Solutions**:
1. Verify database and schema names
2. Check user permissions
3. Use correct case (Snowflake is case-sensitive)

#### Container Won't Start
```
Error: Configuration error: Missing required Snowflake configuration: account
```
**Solution**: Ensure all required environment variables are set:
```bash
docker run -e SNOWFLAKE_ACCOUNT=myaccount \
           -e SNOWFLAKE_USER=myuser \
           -e SNOWFLAKE_PASSWORD=mypassword \
           snowflake-mcp:latest
```

### Health Check Failures

If health checks are failing:

1. Check container logs:
   ```bash
   docker logs snowflake-mcp-server
   ```

2. Test the connection manually:
   ```bash
   docker exec -it snowflake-mcp-server python -c "
   import server
   import asyncio
   asyncio.run(server.test_authentication())
   "
   ```

3. Verify environment variables:
   ```bash
   docker exec -it snowflake-mcp-server env | grep SNOWFLAKE
   ```

### Performance Tuning

For better performance with large datasets:

```bash
# Increase connection pool and timeouts
-e SNOWFLAKE_POOL_SIZE=10 \
-e SNOWFLAKE_TIMEOUT=600 \
-e SNOWFLAKE_MAX_RETRIES=5
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
docker-compose logs -f snowflake-mcp

# Docker run
docker logs -f snowflake-mcp-server
```

## Security Considerations

### Secrets Management

1. **Never hardcode credentials** in Dockerfiles or compose files
2. **Use Docker secrets** or external secret management systems
3. **Mount private keys** as read-only volumes
4. **Use environment variables** for configuration
5. **Rotate credentials** regularly

### Network Security

1. **Use private networks** for container communication
2. **Limit container privileges** (runs as non-root user)
3. **Enable TLS** for Snowflake connections (enabled by default)
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
docker run --rm -e SNOWFLAKE_ACCOUNT=test snowflake-mcp:latest python -c "import server; print('Tests passed')"
```

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review container logs for error messages
3. Verify your Snowflake connection settings
4. Ensure all required environment variables are set

## License

This project is licensed under the MIT License - see the LICENSE file for details.