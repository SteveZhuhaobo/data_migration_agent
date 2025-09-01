#!/bin/bash

# Azure Container Instances deployment script for SQL Server MCP Server
# Usage: ./deploy-sqlserver-mcp.sh <resource-group> <container-name>

set -e

# Check if required parameters are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <resource-group> <container-name>"
    echo "Example: $0 my-resource-group sqlserver-mcp-prod"
    exit 1
fi

RESOURCE_GROUP=$1
CONTAINER_NAME=$2
LOCATION=${LOCATION:-"East US"}
IMAGE=${IMAGE:-"ghcr.io/your-org/sqlserver-mcp:latest"}

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
if [ -z "$SQLSERVER_SERVER" ]; then
    read -p "Enter SQL Server hostname (e.g., your-server.database.windows.net): " SQLSERVER_SERVER
fi

if [ -z "$SQLSERVER_DATABASE" ]; then
    read -p "Enter SQL Server Database: " SQLSERVER_DATABASE
fi

if [ -z "$SQLSERVER_USERNAME" ]; then
    read -p "Enter SQL Server Username: " SQLSERVER_USERNAME
fi

if [ -z "$SQLSERVER_PASSWORD" ]; then
    read -s -p "Enter SQL Server Password: " SQLSERVER_PASSWORD
    echo
fi

echo "Deploying SQL Server MCP Server to Azure Container Instances..."

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
        SQLSERVER_SERVER="$SQLSERVER_SERVER" \
        SQLSERVER_DATABASE="$SQLSERVER_DATABASE" \
        SQLSERVER_USERNAME="$SQLSERVER_USERNAME" \
        SQLSERVER_DRIVER="${SQLSERVER_DRIVER:-ODBC Driver 18 for SQL Server}" \
        SQLSERVER_ENCRYPT="${SQLSERVER_ENCRYPT:-yes}" \
        SQLSERVER_TRUST_CERTIFICATE="${SQLSERVER_TRUST_CERTIFICATE:-no}" \
    --secure-environment-variables \
        SQLSERVER_PASSWORD="$SQLSERVER_PASSWORD" \
    --ports 8080 \
    --protocol TCP \
    --os-type Linux \
    --assign-identity \
    --tags \
        Environment=production \
        Service=sqlserver-mcp \
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