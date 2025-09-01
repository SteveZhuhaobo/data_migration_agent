#!/bin/bash

# Databricks MCP Server Build Script
set -e

# Configuration
IMAGE_NAME="databricks-mcp"
REGISTRY="${REGISTRY:-}"
TAG="${TAG:-latest}"
PLATFORM="${PLATFORM:-linux/amd64,linux/arm64}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG          Set the image tag (default: latest)"
    echo "  -r, --registry REGISTRY Set the registry prefix"
    echo "  -p, --platform PLATFORM Set target platforms (default: linux/amd64,linux/arm64)"
    echo "  --push                 Push the image to registry after building"
    echo "  --no-cache             Build without using cache"
    echo "  --test                 Run tests after building"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build with default settings"
    echo "  $0 -t v1.0.0                        # Build with specific tag"
    echo "  $0 -r ghcr.io/username -t v1.0.0    # Build and tag for registry"
    echo "  $0 --push -r ghcr.io/username       # Build and push to registry"
}

# Parse command line arguments
PUSH=false
NO_CACHE=false
RUN_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Construct full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
fi

# Build arguments
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
fi

# Start build process
log_info "Building Databricks MCP Server Docker image..."
log_info "Image name: $FULL_IMAGE_NAME"
log_info "Platform: $PLATFORM"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if buildx is available for multi-platform builds
if [[ "$PLATFORM" == *","* ]]; then
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is required for multi-platform builds"
        exit 1
    fi
    
    # Create builder instance if it doesn't exist
    if ! docker buildx inspect multiarch-builder &> /dev/null; then
        log_info "Creating multi-platform builder..."
        docker buildx create --name multiarch-builder --use
    else
        docker buildx use multiarch-builder
    fi
    
    BUILD_CMD="docker buildx build --platform $PLATFORM"
    if [ "$PUSH" = true ]; then
        BUILD_CMD="$BUILD_CMD --push"
    else
        BUILD_CMD="$BUILD_CMD --load"
    fi
else
    BUILD_CMD="docker build"
fi

# Build the image
log_info "Running build command..."
if $BUILD_CMD $BUILD_ARGS -t "$FULL_IMAGE_NAME" .; then
    log_success "Docker image built successfully: $FULL_IMAGE_NAME"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# Push to registry if requested (for single platform builds)
if [ "$PUSH" = true ] && [[ "$PLATFORM" != *","* ]]; then
    log_info "Pushing image to registry..."
    if docker push "$FULL_IMAGE_NAME"; then
        log_success "Image pushed successfully: $FULL_IMAGE_NAME"
    else
        log_error "Failed to push image to registry"
        exit 1
    fi
fi

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
    log_info "Running container tests..."
    
    # Test that the container starts and responds to ping
    if docker run --rm "$FULL_IMAGE_NAME" python -c "import server; print('Container test passed')"; then
        log_success "Container tests passed"
    else
        log_error "Container tests failed"
        exit 1
    fi
fi

# Show image information
log_info "Build completed successfully!"
log_info "Image details:"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Show usage instructions
echo ""
log_info "Usage instructions:"
echo "  # Run with environment variables:"
echo "  docker run -e DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com \\"
echo "             -e DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id \\"
echo "             -e DATABRICKS_ACCESS_TOKEN=your-token \\"
echo "             $FULL_IMAGE_NAME"
echo ""
echo "  # Run with docker-compose:"
echo "  docker-compose up -d"
echo ""

log_success "Databricks MCP Server build completed!"