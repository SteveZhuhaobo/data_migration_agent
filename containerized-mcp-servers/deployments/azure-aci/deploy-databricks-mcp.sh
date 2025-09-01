#!/bin/bash

# Azure Container Instances deployment script for Databricks MCP Server
# Usage: ./deploy-databricks-mcp.sh <resource-group> <container-name>

set -e

# Check if required parameters are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <resource-group> <container-name>"
    echo "Example: $0 my-resource-group databricks-mcp-prod"
    exit 1
fi

RESOURCE_GROUP=$1
CONTAINER_NAME=$2
LOCATION=${LOCATION:-"East US"}
IMAGE=${IMAGE:-"ghcr.io/your-org/databricks-mcp:latest"}

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo "Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    echo "Please log in to Azure CLI first: az login"
    exit 1
fi

# Prompt for required environment variables if not set
if [ -z "$DATABRICKS_SERVER_HOSTNAME" ]; then
    read -p "Enter Databricks Server Hostname (e.g., your-workspace.databricks.com): " DATABRICKS_SERVER_HOSTNAME
fi

if [ -z "$DATABRICKS_HTTP_PATH" ]; then
    read -p "Enter Databricks HTTP Path (e.g., /sql/1.0/warehouses/your-warehouse-id): " DATABRICKS_HTTP_PATH
fi

if [ -z "$DATABRICKS_ACCESS_TOKEN" ]; then
    read -s -p "Enter Databricks Access Token: " DATABRICKS_ACCESS_TOKEN
    echo
fi

echo "Deploying Databricks MCP Server to Azure Container Instances..."

# Create the container instance
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --image "$IMAGE" \
    --location "$LOCATION" \
    --cpu 0.5 \
    --memory 1 \
    --restart-policy OnFailure \
    --environment-variables \
        DATABRICKS_SERVER_HOSTNAME="$DATABRICKS_SERVER_HOSTNAME" \
        DATABRICKS_HTTP_PATH="$DATABRICKS_HTTP_PATH" \
        DATABRICKS_CATALOG="${DATABRICKS_CATALOG:-}" \
        DATABRICKS_SCHEMA="${DATABRICKS_SCHEMA:-}" \
    --secure-environment-variables \
        DATABRICKS_ACCESS_TOKEN="$DATABRICKS_ACCESS_TOKEN" \
    --ports 8080 \
    --protocol TCP \
    --os-type Linux \
    --assign-identity \
    --tags \
        Environment=production \
        Service=databricks-mcp \
        ManagedBy=azure-cli

echo "Container deployment initiated. Checking status..."

# Wait for the container to be in running state
echo "Waiting for container to start..."
az container wait \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --condition Running \
    --timeout 300

# Show container details
echo "Container deployed successfully!"
az container show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --query "{Name:name,State:containers[0].instanceView.currentState.state,IP:ipAddress.ip,FQDN:ipAddress.fqdn}" \
    --output table

echo ""
echo "To view logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "To delete: az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes"