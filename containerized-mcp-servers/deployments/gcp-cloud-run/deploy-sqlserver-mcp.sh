#!/bin/bash

# Google Cloud Run deployment script for SQL Server MCP Server
# Usage: ./deploy-sqlserver-mcp.sh <service-name> <project-id> <region>

set -e

# Check if required parameters are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <service-name> <project-id> <region>"
    echo "Example: $0 sqlserver-mcp my-project-id us-central1"
    exit 1
fi

SERVICE_NAME=$1
PROJECT_ID=$2
REGION=$3
IMAGE=${IMAGE:-"ghcr.io/your-org/sqlserver-mcp:latest"}

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

# Create secrets in Secret Manager
echo "Creating secrets in Secret Manager..."
echo -n "$SQLSERVER_PASSWORD" | gcloud secrets create sqlserver-password --data-file=- --replication-policy=automatic || echo "Secret already exists"

# Deploy to Cloud Run
echo "Deploying SQL Server MCP Server to Cloud Run..."

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
    --set-env-vars="SQLSERVER_SERVER=$SQLSERVER_SERVER,SQLSERVER_DATABASE=$SQLSERVER_DATABASE,SQLSERVER_USERNAME=$SQLSERVER_USERNAME,SQLSERVER_DRIVER=${SQLSERVER_DRIVER:-ODBC Driver 18 for SQL Server},SQLSERVER_ENCRYPT=${SQLSERVER_ENCRYPT:-yes},SQLSERVER_TRUST_CERTIFICATE=${SQLSERVER_TRUST_CERTIFICATE:-no}" \
    --set-secrets="SQLSERVER_PASSWORD=sqlserver-password:latest" \
    --labels="environment=production,service=sqlserver-mcp"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)")

echo ""
echo "Deployment completed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "To view logs: gcloud logs read --service=$SERVICE_NAME --platform=managed --region=$REGION"
echo "To delete: gcloud run services delete $SERVICE_NAME --platform=managed --region=$REGION --quiet"