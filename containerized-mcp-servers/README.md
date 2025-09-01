# Containerized MCP Servers

A collection of containerized Model Context Protocol (MCP) servers for popular databases and data platforms. Each server is packaged as a standalone Docker container that can be easily deployed across different environments.

## Available Servers

- **Snowflake MCP Server** - Connect to Snowflake data warehouses
- **Databricks MCP Server** - Connect to Databricks SQL warehouses  
- **SQL Server MCP Server** - Connect to Microsoft SQL Server databases

## Quick Start

### Prerequisites

- Docker installed on your system
- Valid credentials for your target database/platform

### Running a Server

Each server can be run with a simple Docker command. Here's how to get started with any of the three servers:

#### Snowflake MCP Server

```bash
docker run -e SNOWFLAKE_ACCOUNT=your-account \
           -e SNOWFLAKE_USER=your-username \
           -e SNOWFLAKE_PASSWORD=your-password \
           -e SNOWFLAKE_DATABASE=your-database \
           -e SNOWFLAKE_WAREHOUSE=your-warehouse \
           ghcr.io/your-org/snowflake-mcp:latest
```

#### Databricks MCP Server

```bash
docker run -e DATABRICKS_SERVER_HOSTNAME=your-workspace.databricks.com \
           -e DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id \
           -e DATABRICKS_ACCESS_TOKEN=your-token \
           ghcr.io/your-org/databricks-mcp:latest
```

#### SQL Server MCP Server

```bash
docker run -e SQLSERVER_SERVER=your-server \
           -e SQLSERVER_DATABASE=your-database \
           -e SQLSERVER_USERNAME=your-username \
           -e SQLSERVER_PASSWORD=your-password \
           ghcr.io/your-org/sqlserver-mcp:latest
```

### Using Docker Compose

For easier management, each server includes a docker-compose.yml file:

```bash
# Navigate to the server directory
cd snowflake-mcp  # or databricks-mcp, sqlserver-mcp

# Copy and edit environment file
cp .env.example .env
# Edit .env with your credentials

# Start the server
docker-compose up -d
```

## Server-Specific Documentation

Each server has its own comprehensive documentation:

- [Snowflake MCP Server](./snowflake-mcp/README.md)
- [Databricks MCP Server](./databricks-mcp/README.md)  
- [SQL Server MCP Server](./sqlserver-mcp/README.md)

## Container Orchestration Examples

### Docker Swarm

Deploy any server to a Docker Swarm cluster:

```bash
# Create a Docker secret for sensitive data
echo "your-password" | docker secret create db_password -

# Deploy the service
docker service create \
  --name snowflake-mcp \
  --secret db_password \
  --env SNOWFLAKE_ACCOUNT=your-account \
  --env SNOWFLAKE_USER=your-username \
  --env SNOWFLAKE_PASSWORD_FILE=/run/secrets/db_password \
  ghcr.io/your-org/snowflake-mcp:latest
```

### Kubernetes

Basic Kubernetes deployment example:

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
        image: ghcr.io/your-org/snowflake-mcp:latest
        env:
        - name: SNOWFLAKE_ACCOUNT
          value: "your-account"
        - name: SNOWFLAKE_USER
          value: "your-username"
        - name: SNOWFLAKE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: snowflake-secret
              key: password
```

### Cloud Container Services

#### AWS ECS

```json
{
  "family": "snowflake-mcp",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "snowflake-mcp",
      "image": "ghcr.io/your-org/snowflake-mcp:latest",
      "memory": 512,
      "environment": [
        {"name": "SNOWFLAKE_ACCOUNT", "value": "your-account"},
        {"name": "SNOWFLAKE_USER", "value": "your-username"}
      ],
      "secrets": [
        {
          "name": "SNOWFLAKE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:snowflake-password"
        }
      ]
    }
  ]
}
```

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name snowflake-mcp \
  --image ghcr.io/your-org/snowflake-mcp:latest \
  --environment-variables \
    SNOWFLAKE_ACCOUNT=your-account \
    SNOWFLAKE_USER=your-username \
  --secure-environment-variables \
    SNOWFLAKE_PASSWORD=your-password
```

#### Google Cloud Run

```bash
gcloud run deploy snowflake-mcp \
  --image ghcr.io/your-org/snowflake-mcp:latest \
  --set-env-vars SNOWFLAKE_ACCOUNT=your-account,SNOWFLAKE_USER=your-username \
  --set-secrets SNOWFLAKE_PASSWORD=snowflake-password:latest \
  --platform managed \
  --region us-central1
```

## Building from Source

### Build Individual Servers

```bash
# Build Snowflake MCP server
cd snowflake-mcp
./build.sh

# Build Databricks MCP server  
cd databricks-mcp
./build.sh

# Build SQL Server MCP server
cd sqlserver-mcp
./build.sh
```

### Build All Servers

```bash
# Build all servers at once
./scripts/build-all.sh

# Test all servers
./scripts/test-all.sh

# Publish to container registry
./scripts/publish-all.sh --registry ghcr.io --tag v1.0.0
```

## Configuration

### Environment Variables

Each server supports configuration through environment variables. Common patterns:

- **Connection Details**: Server hostnames, ports, databases
- **Authentication**: Usernames, passwords, tokens, key files
- **Behavior**: Timeouts, retry settings, connection pools

### Configuration Files

Servers also support YAML configuration files mounted as volumes:

```bash
docker run -v ./config.yaml:/app/config/config.yaml \
           ghcr.io/your-org/snowflake-mcp:latest
```

### Secrets Management

For production deployments, use proper secrets management:

- Docker secrets for Swarm
- Kubernetes secrets for K8s clusters
- AWS Secrets Manager for ECS
- Azure Key Vault for ACI
- Google Secret Manager for Cloud Run

## Health Checks and Monitoring

All containers include built-in health checks:

```bash
# Check container health
docker ps  # Look for "healthy" status

# View health check logs
docker inspect container-name | grep Health -A 10
```

### Monitoring Integration

Containers support structured logging and optional metrics:

- JSON-formatted logs for log aggregation
- Optional Prometheus metrics endpoint
- Container resource monitoring
- Database connection health

## Security

### Best Practices

- Run containers as non-root users
- Use secrets management for credentials
- Enable TLS/SSL for database connections
- Regular security updates via automated builds
- Network policies for container isolation

### Vulnerability Scanning

All images are automatically scanned for vulnerabilities in the CI/CD pipeline.

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify network connectivity to database
   - Check credentials and permissions
   - Review firewall and security group settings

2. **Container Won't Start**
   - Check required environment variables
   - Review container logs: `docker logs container-name`
   - Verify image compatibility with your platform

3. **Performance Issues**
   - Monitor container resource usage
   - Adjust connection pool settings
   - Check database query performance

### Getting Help

- Check server-specific README files for detailed troubleshooting
- Review container logs for error messages
- Verify configuration against provided examples

## Contributing

### Development Setup

1. Clone the repository
2. Navigate to the server directory you want to work on
3. Make your changes
4. Test locally with `./build.sh && docker-compose up`
5. Run the test suite with `./run_tests.sh`

### Testing

Each server includes comprehensive tests:

```bash
# Run unit tests
python -m pytest test_server.py

# Run integration tests  
python -m pytest test_integration.py

# Run all tests
./run_tests.sh
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- Check the server-specific documentation
- Review troubleshooting guides
- Open an issue on GitHub