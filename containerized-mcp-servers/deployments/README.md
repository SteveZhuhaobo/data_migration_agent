# Deployment Guide

This directory contains deployment examples and configurations for running the containerized MCP servers across different container orchestration platforms and cloud services.

## Available Deployment Options

### Container Orchestration Platforms

- **[Kubernetes](./kubernetes/)** - Production-ready Kubernetes manifests with secrets, configmaps, and network policies
- **[Docker Swarm](./docker-swarm/)** - Docker Swarm stack files with secrets and config management

### Cloud Container Services

- **[AWS ECS](./aws-ecs/)** - Amazon Elastic Container Service task definitions with Fargate support
- **[Azure Container Instances](./azure-aci/)** - Azure Container Instances deployment scripts
- **[Google Cloud Run](./gcp-cloud-run/)** - Google Cloud Run deployment scripts with Secret Manager integration

## Quick Start by Platform

### Kubernetes

1. **Prerequisites**: kubectl configured with cluster access
2. **Deploy**: 
   ```bash
   # Edit the YAML files with your credentials
   kubectl apply -f kubernetes/snowflake-mcp.yaml
   ```
3. **Verify**: `kubectl get pods -l app=snowflake-mcp`

### Docker Swarm

1. **Prerequisites**: Docker Swarm cluster initialized
2. **Setup secrets**:
   ```bash
   echo "your-password" | docker secret create snowflake_password -
   docker config create snowflake_config config.yaml
   ```
3. **Deploy**: `docker stack deploy -c docker-swarm/snowflake-mcp-stack.yml snowflake`

### AWS ECS

1. **Prerequisites**: AWS CLI configured, ECS cluster created
2. **Register task definition**:
   ```bash
   aws ecs register-task-definition --cli-input-json file://aws-ecs/snowflake-mcp-task-definition.json
   ```
3. **Create service**:
   ```bash
   aws ecs create-service --cluster my-cluster --service-name snowflake-mcp --task-definition snowflake-mcp
   ```

### Azure Container Instances

1. **Prerequisites**: Azure CLI installed and logged in
2. **Deploy**: 
   ```bash
   chmod +x azure-aci/deploy-snowflake-mcp.sh
   ./azure-aci/deploy-snowflake-mcp.sh my-resource-group snowflake-mcp-prod
   ```

### Google Cloud Run

1. **Prerequisites**: gcloud CLI installed and authenticated
2. **Deploy**:
   ```bash
   chmod +x gcp-cloud-run/deploy-snowflake-mcp.sh
   ./gcp-cloud-run/deploy-snowflake-mcp.sh snowflake-mcp my-project-id us-central1
   ```

## Configuration Management

### Environment Variables

All deployment examples support configuration through environment variables:

#### Snowflake MCP Server
- `SNOWFLAKE_ACCOUNT` - Your Snowflake account identifier
- `SNOWFLAKE_USER` - Username for authentication
- `SNOWFLAKE_PASSWORD` - Password (use secrets management)
- `SNOWFLAKE_DATABASE` - Default database
- `SNOWFLAKE_SCHEMA` - Default schema
- `SNOWFLAKE_WAREHOUSE` - Default warehouse
- `SNOWFLAKE_ROLE` - Default role (optional)

#### Databricks MCP Server
- `DATABRICKS_SERVER_HOSTNAME` - Databricks workspace hostname
- `DATABRICKS_HTTP_PATH` - SQL warehouse HTTP path
- `DATABRICKS_ACCESS_TOKEN` - Personal access token (use secrets management)
- `DATABRICKS_CATALOG` - Default catalog (optional)
- `DATABRICKS_SCHEMA` - Default schema (optional)

#### SQL Server MCP Server
- `SQLSERVER_SERVER` - SQL Server hostname
- `SQLSERVER_DATABASE` - Database name
- `SQLSERVER_USERNAME` - Username for authentication
- `SQLSERVER_PASSWORD` - Password (use secrets management)
- `SQLSERVER_DRIVER` - ODBC driver name
- `SQLSERVER_ENCRYPT` - Enable encryption (yes/no)
- `SQLSERVER_TRUST_CERTIFICATE` - Trust server certificate (yes/no)

### Secrets Management

Each platform provides secure ways to manage sensitive data:

#### Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-secret
type: Opaque
stringData:
  password: "your-secure-password"
```

#### Docker Swarm
```bash
echo "your-password" | docker secret create db_password -
```

#### AWS ECS
```json
"secrets": [
  {
    "name": "DB_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
  }
]
```

#### Azure Container Instances
```bash
--secure-environment-variables DB_PASSWORD=your-password
```

#### Google Cloud Run
```bash
gcloud secrets create db-password --data-file=-
--set-secrets="DB_PASSWORD=db-password:latest"
```

## Resource Requirements

### Minimum Requirements
- **CPU**: 0.1 cores
- **Memory**: 256MB
- **Storage**: 1GB (for container image and logs)

### Recommended Production Settings
- **CPU**: 0.5 cores
- **Memory**: 512MB
- **Replicas**: 2+ for high availability
- **Health checks**: Enabled with appropriate timeouts

## Networking and Security

### Port Configuration
- **Health Check Port**: 8080 (HTTP)
- **MCP Communication**: stdio-based (no network ports required)

### Security Best Practices

1. **Run as non-root user**: All containers run as user ID 1000
2. **Use secrets management**: Never hardcode credentials
3. **Enable TLS**: Use encrypted connections to databases
4. **Network policies**: Restrict network access where possible
5. **Resource limits**: Set appropriate CPU and memory limits
6. **Regular updates**: Keep container images updated

### Network Policies (Kubernetes)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-server-netpol
spec:
  podSelector:
    matchLabels:
      app: mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: mcp-client
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS for database connections
```

## Monitoring and Logging

### Health Checks

All containers include built-in health checks:

```bash
# Kubernetes
kubectl get pods -l app=snowflake-mcp

# Docker
docker ps --filter "health=healthy"

# Check health manually
docker exec container-name python -c "import health_check; health_check.check_health()"
```

### Logging

#### Structured Logging
All containers output JSON-formatted logs to stdout/stderr for easy aggregation.

#### Log Aggregation Examples

**ELK Stack (Kubernetes)**:
```yaml
spec:
  containers:
  - name: mcp-server
    # ... other config
    volumeMounts:
    - name: logs
      mountPath: /var/log
  - name: filebeat
    image: elastic/filebeat:7.15.0
    # ... filebeat config
```

**CloudWatch (AWS ECS)**:
```json
"logConfiguration": {
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/ecs/mcp-server",
    "awslogs-region": "us-east-1"
  }
}
```

### Metrics Collection

Optional Prometheus metrics can be enabled:

```yaml
# Kubernetes ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mcp-server-metrics
spec:
  selector:
    matchLabels:
      app: mcp-server
  endpoints:
  - port: metrics
    interval: 30s
```

## Scaling and High Availability

### Horizontal Scaling

#### Kubernetes
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Docker Swarm
```yaml
deploy:
  replicas: 3
  update_config:
    parallelism: 1
    delay: 10s
```

### Load Balancing

Since MCP servers use stdio communication, traditional load balancing isn't applicable. Instead, deploy multiple instances and use client-side load balancing or connection pooling.

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check environment variables are set correctly
   - Verify image exists and is accessible
   - Review container logs for startup errors

2. **Database connection failures**
   - Verify network connectivity to database
   - Check credentials and permissions
   - Ensure firewall rules allow connections

3. **Health check failures**
   - Check if health check endpoint is responding
   - Verify container has sufficient resources
   - Review health check timeout settings

### Debugging Commands

```bash
# Kubernetes
kubectl describe pod <pod-name>
kubectl logs <pod-name> -f
kubectl exec -it <pod-name> -- /bin/bash

# Docker
docker logs <container-name> -f
docker exec -it <container-name> /bin/bash
docker inspect <container-name>

# Cloud services
# AWS ECS
aws ecs describe-tasks --cluster <cluster> --tasks <task-arn>
aws logs get-log-events --log-group-name <log-group>

# Azure ACI
az container logs --resource-group <rg> --name <container-name>
az container show --resource-group <rg> --name <container-name>

# Google Cloud Run
gcloud run services describe <service-name> --region <region>
gcloud logs read --service <service-name>
```

## Migration Between Platforms

### From Docker Compose to Kubernetes
1. Convert environment variables to ConfigMaps and Secrets
2. Add resource limits and requests
3. Configure health checks and probes
4. Set up network policies if needed

### From VM to Containers
1. Identify configuration files and convert to environment variables
2. Set up secrets management for sensitive data
3. Configure persistent storage if needed
4. Test connectivity and functionality

## Support and Contributing

For deployment-specific issues:
1. Check the platform-specific documentation
2. Review the troubleshooting section
3. Verify your configuration against the examples
4. Open an issue with deployment details and error logs

When contributing new deployment examples:
1. Follow the existing structure and naming conventions
2. Include comprehensive documentation
3. Test the deployment in a real environment
4. Add troubleshooting notes for common issues