#!/bin/bash

# Snowflake MCP Server Build Script
# This script builds the Snowflake MCP Docker container

set -e  # Exit on any error

# Configuration
IMAGE_NAME="snowflake-mcp"
IMAGE_TAG="${1:-latest}"
REGISTRY="${REGISTRY:-}"
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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
}

# Function to build the image
build_image() {
    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${full_image_name}"
    fi
    
    log_info "Building Snowflake MCP Server Docker image..."
    log_info "Image name: ${full_image_name}"
    log_info "Platform: ${PLATFORM}"
    
    # Build the image
    if command -v docker buildx >/dev/null 2>&1; then
        # Use buildx for multi-platform builds
        docker buildx build \
            --platform "${PLATFORM}" \
            --tag "${full_image_name}" \
            --load \
            .
    else
        # Fallback to regular docker build
        log_warning "Docker buildx not available, building for current platform only"
        docker build \
            --tag "${full_image_name}" \
            .
    fi
    
    log_success "Successfully built ${full_image_name}"
}

# Function to test the built image
test_image() {
    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${full_image_name}"
    fi
    
    log_info "Testing the built image..."
    
    # Test that the image can start and the health check passes
    if docker run --rm "${full_image_name}" python -c "import server; print('Image test passed')"; then
        log_success "Image test passed"
    else
        log_error "Image test failed"
        exit 1
    fi
}

# Function to show image information
show_image_info() {
    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${full_image_name}"
    fi
    
    log_info "Image information:"
    docker images "${full_image_name}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [TAG] [OPTIONS]"
    echo ""
    echo "Build the Snowflake MCP Server Docker image"
    echo ""
    echo "Arguments:"
    echo "  TAG                 Image tag (default: latest)"
    echo ""
    echo "Environment Variables:"
    echo "  REGISTRY           Container registry prefix (optional)"
    echo "  PLATFORM           Target platforms (default: linux/amd64,linux/arm64)"
    echo ""
    echo "Examples:"
    echo "  $0                 # Build with 'latest' tag"
    echo "  $0 v1.0.0          # Build with 'v1.0.0' tag"
    echo "  REGISTRY=ghcr.io/myorg $0 v1.0.0  # Build with registry prefix"
    echo ""
    echo "Options:"
    echo "  --help, -h         Show this help message"
    echo "  --test             Run image tests after building"
    echo "  --no-cache         Build without using cache"
}

# Parse command line arguments
TEST_IMAGE=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --test)
            TEST_IMAGE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$IMAGE_TAG" ] || [ "$IMAGE_TAG" = "latest" ]; then
                IMAGE_TAG="$1"
            else
                log_error "Too many arguments"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting Snowflake MCP Server build process..."
    
    # Check prerequisites
    check_docker
    
    # Add no-cache flag if specified
    if [ "$NO_CACHE" = true ]; then
        export DOCKER_BUILDKIT=1
        log_info "Building without cache"
    fi
    
    # Build the image
    build_image
    
    # Test the image if requested
    if [ "$TEST_IMAGE" = true ]; then
        test_image
    fi
    
    # Show image information
    show_image_info
    
    log_success "Build process completed successfully!"
    
    # Show next steps
    echo ""
    log_info "Next steps:"
    echo "  1. Test the container: docker-compose up"
    echo "  2. Push to registry: docker push ${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  3. Run the container: docker run -e SNOWFLAKE_ACCOUNT=... -e SNOWFLAKE_USER=... -e SNOWFLAKE_PASSWORD=... ${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:${IMAGE_TAG}"
}

# Run main function
main "$@"