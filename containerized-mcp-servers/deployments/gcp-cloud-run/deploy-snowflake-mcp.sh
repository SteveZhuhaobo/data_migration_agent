#!/bin/bash

# Google Cloud Run deployment script for Snowflake MCP Server
# Usage: ./deploy-snowflake-mcp.sh <service-name> <project-id> <region>

set -e

# Check if required parameters are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <service-name> <project-id> <region>"
    echo "Example: $0 snowflake-mcp my-project-id us-central1"
    exit 1
fi

SERVICE_NAME=$1
PROJECT_ID=$2
REGION=$3
IMAGE=${IMAGE:-"ghcr.io/your-org/snowflake-mcp:latest"}

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

# Create secrets in Secret Manager
echo "Creating secrets in Secret Manager..."
echo -n "$SNOWFLAKE_PASSWORD" | gcloud secrets create snowflake-password --data-file=- --replication-policy=automatic || echo "Secret already exists"

# Deploy to Cloud Run
echo "Deploying Snowflake MCP Server to Cloud Run..."

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
    --set-env-vars="SNOWFLAKE_ACCOUNT=$SNOWFLAKE_ACCOUNT,SNOWFLAKE_USER=$SNOWFLAKE_USER,SNOWFLAKE_DATABASE=$SNOWFLAKE_DATABASE,SNOWFLAKE_WAREHOUSE=$SNOWFLAKE_WAREHOUSE,SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA:-public},SNOWFLAKE_ROLE=${SNOWFLAKE_ROLE:-}" \
    --set-secrets="SNOWFLAKE_PASSWORD=snowflake-password:latest" \
    --labels="environment=production,service=snowflake-mcp"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)")

echo ""
echo "Deployment completed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "To view logs: gcloud logs read --service=$SERVICE_NAME --platform=managed --region=$REGION"
echo "To delete: gcloud run services delete $SERVICE_NAME --platform=managed --region=$REGION --quiet"