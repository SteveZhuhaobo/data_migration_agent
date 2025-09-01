#!/bin/bash

# Google Cloud Run deployment script for Databricks MCP Server
# Usage: ./deploy-databricks-mcp.sh <service-name> <project-id> <region>

set -e

# Check if required parameters are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <service-name> <project-id> <region>"
    echo "Example: $0 databricks-mcp my-project-id us-central1"
    exit 1
fi

SERVICE_NAME=$1
PROJECT_ID=$2
REGION=$3
IMAGE=${IMAGE:-"ghcr.io/your-org/databricks-mcp:latest"}

# Check if gcloud CLI is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud CLI is not installed. Please install it first."
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
    echo "Please authenticate with Google Cloud: gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

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

# Create secrets in Secret Manager
echo "Creating secrets in Secret Manager..."
echo -n "$DATABRICKS_ACCESS_TOKEN" | gcloud secrets create databricks-access-token --data-file=- --replication-policy=automatic || echo "Secret already exists"

# Deploy to Cloud Run
echo "Deploying Databricks MCP Server to Cloud Run..."

gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300 \
    --set-env-vars="DATABRICKS_SERVER_HOSTNAME=$DATABRICKS_SERVER_HOSTNAME,DATABRICKS_HTTP_PATH=$DATABRICKS_HTTP_PATH,DATABRICKS_CATALOG=${DATABRICKS_CATALOG:-},DATABRICKS_SCHEMA=${DATABRICKS_SCHEMA:-}" \
    --set-secrets="DATABRICKS_ACCESS_TOKEN=databricks-access-token:latest" \
    --labels="environment=production,service=databricks-mcp"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)")

echo ""
echo "Deployment completed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "To view logs: gcloud logs read --service=$SERVICE_NAME --platform=managed --region=$REGION"
echo "To delete: gcloud run services delete $SERVICE_NAME --platform=managed --region=$REGION --quiet"