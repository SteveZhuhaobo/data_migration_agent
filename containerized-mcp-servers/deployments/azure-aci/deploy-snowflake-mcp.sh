#!/bin/bash

# Azure Container Instances deployment script for Snowflake MCP Server
# Usage: ./deploy-snowflake-mcp.sh <resource-group> <container-name>

set -e

# Check if required parameters are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <resource-group> <container-name>"
    echo "Example: $0 my-resource-group snowflake-mcp-prod"
    exit 1
fi

RESOURCE_GROUP=$1
CONTAINER_NAME=$2
LOCATION=${LOCATION:-"East US"}
IMAGE=${IMAGE:-"ghcr.io/your-org/snowflake-mcp:latest"}

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
if [ -z "$SNOWFLAKE_ACCOUNT" ]; then
    read -p "Enter Snowflake Account: " SNOWFLAKE_ACCOUNT
fi

if [ -z "$SNOWFLAKE_USER" ]; then
    read -p "Enter Snowflake User: " SNOWFLAKE_USER
fi

if [ -z "$SNOWFLAKE_PASSWORD" ]; then
    read -s -p "Enter Snowflake Password: " SNOWFLAKE_PASSWORD
    echo
fi

if [ -z "$SNOWFLAKE_DATABASE" ]; then
    read -p "Enter Snowflake Database: " SNOWFLAKE_DATABASE
fi

if [ -z "$SNOWFLAKE_WAREHOUSE" ]; then
    read -p "Enter Snowflake Warehouse: " SNOWFLAKE_WAREHOUSE
fi

echo "Deploying Snowflake MCP Server to Azure Container Instances..."

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
        SNOWFLAKE_ACCOUNT="$SNOWFLAKE_ACCOUNT" \
        SNOWFLAKE_USER="$SNOWFLAKE_USER" \
        SNOWFLAKE_DATABASE="$SNOWFLAKE_DATABASE" \
        SNOWFLAKE_WAREHOUSE="$SNOWFLAKE_WAREHOUSE" \
        SNOWFLAKE_SCHEMA="${SNOWFLAKE_SCHEMA:-public}" \
        SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-}" \
    --secure-environment-variables \
        SNOWFLAKE_PASSWORD="$SNOWFLAKE_PASSWORD" \
    --ports 8080 \
    --protocol TCP \
    --os-type Linux \
    --assign-identity \
    --tags \
        Environment=production \
        Service=snowflake-mcp \
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