# Databricks MCP Server

A containerized Model Context Protocol (MCP) server for Databricks operations. This server provides a standardized interface to interact with Databricks SQL warehouses, clusters, and jobs through the MCP protocol.

## Features

- **SQL Operations**: Execute queries, manage schemas, tables, and data
- **Cluster Management**: List and monitor Databricks compute clusters
- **Job Management**: Trigger and monitor Databricks jobs
- **Warehouse Management**: Check and manage SQL warehouse status
- **Multi-platform Support**: Available for Linux AMD64 and ARM64 architectures
- **Environment Variable Configuration**: Easy deployment with environment variables
- **Health Checks**: Built-in container health monitoring

## Quick Start

### Using Docker

```bash
# Run with environment variables
docker run -e DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com \
           -e DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id \
           -e DATABRICKS_ACCESS_TOKEN=your-token \
           databricks-mcp:latest
```

### Using Docker Compose

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Databricks credentials:
```bash
# Edit the .env file with your actual values
nano .env
```

3. Start the service:
```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABRICKS_SERVER_HOSTNAME` | Yes | - | Databricks workspace hostname (without https://) |
| `DATABRICKS_HTTP_PATH` | Yes | - | SQL warehouse HTTP path |
| `DATABRICKS_ACCESS_TOKEN` | Yes | - | Personal access token for authentication |
| `DATABRICKS_CATALOG` | No | `hive_metastore` | Default catalog to use |
| `DATABRICKS_SCHEMA` | No | `default` | Default schema to use |

### Configuration File (Optional)

You can also use a configuration file instead of environment variables. Mount a `config.yaml` file to `/app/config/config.yaml`:

```yaml
databricks:
  server_hostname: "your-workspace.cloud.databricks.com"
  http_path: "/sql/1.0/warehouses/your-warehouse-id"
  access_token: "your-token"
  catalog: "hive_metastore"
  schema: "default"
```

## Available Tools

### SQL Operations
- `execute_query`: Execute SQL queries and return results
- `list_catalogs`: List all available catalogs
- `list_schemas`: List schemas in a catalog
- `list_tables`: List tables in a schema
- `get_table_schema`: Get detailed schema information for a table
- `describe_table`: Get comprehensive table metadata
- `create_table`: Create a new table
- `insert_data`: Insert data into a table

### Cluster Management
- `list_clusters`: List available compute clusters
- `get_cluster_status`: Get status information for a specific cluster

### Job Management
- `list_jobs`: List available Databricks jobs
- `run_job`: Trigger execution of a Databricks job
- `get_job_run_status`: Get status of a job run

### Utility
- `check_warehouse_status`: Check and start SQL warehouse if needed
- `ping`: Simple connectivity test

## Building from Source

### Prerequisites
- Docker
- Docker Buildx (for multi-platform builds)

### Build Commands

```bash
# Basic build
./build.sh

# Build with specific tag
./build.sh -t v1.0.0

# Build for specific registry
./build.sh -r ghcr.io/username -t v1.0.0

# Build and push to registry
./build.sh -r ghcr.io/username -t v1.0.0 --push

# Build with tests
./build.sh --test

# Build without cache
./build.sh --no-cache
```

### Build Script Options

| Option | Description |
|--------|-------------|
| `-t, --tag` | Set the image tag (default: latest) |
| `-r, --registry` | Set the registry prefix |
| `-p, --platform` | Set target platforms (default: linux/amd64,linux/arm64) |
| `--push` | Push the image to registry after building |
| `--no-cache` | Build without using cache |
| `--test` | Run tests after building |
| `-h, --help` | Show help message |

## Deployment Examples

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: databricks-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: databricks-mcp
  template:
    metadata:
      labels:
        app: databricks-mcp
    spec:
      containers:
      - name: databricks-mcp
        image: databricks-mcp:latest
        env:
        - name: DATABRICKS_SERVER_HOSTNAME
          valueFrom:
            secretKeyRef:
              name: databricks-secrets
              key: hostname
        - name: DATABRICKS_HTTP_PATH
          valueFrom:
            secretKeyRef:
              name: databricks-secrets
              key: http-path
        - name: DATABRICKS_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: databricks-secrets
              key: access-token
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
```

### Docker Swarm

```yaml
version: '3.8'
services:
  databricks-mcp:
    image: databricks-mcp:latest
    environment:
      - DATABRICKS_SERVER_HOSTNAME_FILE=/run/secrets/databricks_hostname
      - DATABRICKS_HTTP_PATH_FILE=/run/secrets/databricks_http_path
      - DATABRICKS_ACCESS_TOKEN_FILE=/run/secrets/databricks_token
    secrets:
      - databricks_hostname
      - databricks_http_path
      - databricks_token
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

secrets:
  databricks_hostname:
    external: true
  databricks_http_path:
    external: true
  databricks_token:
    external: true
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Authentication failed: Invalid access token
```
**Solution**: Verify your `DATABRICKS_ACCESS_TOKEN` is correct and has the necessary permissions.

#### 2. Connection Timeouts
```
Error: Connection timeout: Please check your server hostname
```
**Solutions**:
- Verify `DATABRICKS_SERVER_HOSTNAME` is correct (without https://)
- Check network connectivity to Databricks
- Ensure firewall allows outbound HTTPS connections

#### 3. Warehouse Not Running
```
Error: Warehouse check failed: Warehouse is STOPPED
```
**Solution**: The server will automatically attempt to start the warehouse. Wait a few minutes for it to start.

#### 4. Invalid HTTP Path
```
Error: Invalid http_path - must start with '/'
```
**Solution**: Ensure `DATABRICKS_HTTP_PATH` follows the format `/sql/1.0/warehouses/{warehouse-id}`

### Debugging

#### Enable Debug Logging
```bash
docker run -e PYTHONUNBUFFERED=1 \
           -e DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com \
           -e DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id \
           -e DATABRICKS_ACCESS_TOKEN=your-token \
           databricks-mcp:latest
```

#### Check Container Health
```bash
# Check if container is healthy
docker ps

# View container logs
docker logs databricks-mcp-server

# Execute health check manually
docker exec databricks-mcp-server python -c "import server; print('OK')"
```

#### Test Connection
```bash
# Test basic connectivity
docker run --rm -e DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com \
                -e DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id \
                -e DATABRICKS_ACCESS_TOKEN=your-token \
                databricks-mcp:latest python -c "
import asyncio
from server import ping_tool
print(asyncio.run(ping_tool()))
"
```

### Performance Tuning

#### Resource Limits
Adjust container resources based on your workload:

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G      # Increase for heavy queries
      cpus: '1.0'     # Increase for concurrent operations
    reservations:
      memory: 512M
      cpus: '0.5'
```

#### Connection Pool Settings
For high-throughput scenarios, consider adjusting connection settings in your config file:

```yaml
databricks:
  # ... other settings ...
connection:
  timeout: 300        # Increase for long-running queries
  max_retries: 5      # Increase for unreliable networks
  retry_delay: 10     # Increase delay between retries
  pool_size: 10       # Increase for concurrent connections
```

## Security Considerations

### Secrets Management
- Never include credentials in the Docker image
- Use Docker secrets, Kubernetes secrets, or external secret management systems
- Rotate access tokens regularly
- Use least-privilege access tokens

### Network Security
- Run containers in isolated networks
- Use TLS/SSL for all Databricks connections
- Implement network policies in Kubernetes
- Monitor and log all database operations

### Container Security
- The container runs as a non-root user (mcpuser)
- Uses minimal base image (Python slim)
- Regular security updates recommended
- Scan images for vulnerabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review container logs for error details
3. Verify Databricks connectivity and permissions
4. Open an issue with detailed error information